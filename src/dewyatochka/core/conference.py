# -*- coding: UTF-8

"""
Chat environment
"""

__all__ = ['Conference', 'ConferenceManager', 'Message']

import time
import threading
import queue
from collections import namedtuple
from dewyatochka.core import plugin
from dewyatochka.core import application
from dewyatochka.core import xmpp
from dewyatochka.core.xmpp import S2SConnectionError

# Message to a conference
Message = namedtuple('Message', ['text', 'target'])

# Interval between conferences state check
_CONFERENCES_CHECK_INTERVAL = 60


class Conference:
    """
    Conference settings structure
    """

    # Room server host
    _server = ''

    # Room name
    _room = ''

    # room@server
    _bare = ''

    # Member nickname
    _nick = ''

    # Cmd prefix
    _prefix = None

    def __init__(self, bare, nick, cmd_prefix=None):
        """
        Create new environment instance
        :param bare: some_room@conference.jabber.example.com
        :param cmd_prefix: Prefix for reserved chat commands
        :return:
        """
        self._room, self._server = bare.split('@')
        self._bare = bare
        self._nick = nick
        self._prefix = cmd_prefix

    @property
    def name(self):
        """
        Get room name
        :return: str
        """
        return self._room

    @property
    def host(self):
        """
        Get room server host
        :return: str
        """
        return self._server

    @property
    def jid(self):
        """
        Get room jid
        :return: str
        """
        return self._bare

    @property
    def member(self):
        """
        Get member nickname
        :return: str
        """
        return self._nick

    @property
    def resource(self):
        """
        Get self conference resource
        :return: str
        """
        return '/'.join((self.jid, self.member))

    @property
    def prefix(self):
        """
        Get chat command prefix
        :return: str
        """
        return self._prefix

    def __repr__(self):
        """
        Representative form
        :return: str
        """
        return '%s[\'%s\']' % (type(self), self.resource)


class ConferenceManager(application.Service):
    """
    Handles multiple conferences persistence
    """
    # TODO: Very crappy class. Needs refactoring

    # XMPP client instance
    _xmpp_instance = None

    # Configured conferences
    _all_conferences = None

    # Conference with online presence
    _alive_conferences = {}

    # Message queue to communicate with message handlers
    _message_queue = None

    def __init__(self, app):
        """
        Initialize manager
        :param app:
        :return:
        """
        super().__init__(app)
        self._message_queue = queue.Queue()

    def _start_response_sender(self):
        """
        Start sender thread
        :return: void
        """
        def _response_sender(manager):
            """
            Sends messages from the queue
             :param manager: ConferenceManager
             :return: void
            """
            while manager.application.running:
                message = manager.message_queue.get()
                manager.xmpp.send_chat_message(message.text, message.target.bare)

        threading.Thread(
            name='dewyatochka.msg_sender',
            target=_response_sender,
            args=(self,),
            daemon=True
        ).start()

    def _start_messages_handler(self):
        """
        Start messages sender thread
        :return: void
        """
        def _handle_message(message):
            """
            Handle incoming message
            :param message: dict
            :return:
            """
            def _message_handler_wrapper(_handler, _handler_kwargs, _manager):
                """
                Common message handler thread
                :param _handler: callable
                :param _handler_kwargs: dict
                :return: void
                """
                _manager.application.log(__name__).debug(
                    'Started handler %s.%s',
                    _handler.__module__,
                    _handler.__name__
                )

                try:
                    _response_message = Message(_handler.handle(**_handler_kwargs), _handler_kwargs['message']['from'])
                except Exception as e:
                    _manager.application.log(__name__).error(
                        'Handler %s.%s failed: %s',
                        _handler.__module__,
                        _handler.__name__,
                        e
                    )
                    raise

                _manager.application.log(__name__).debug(
                    'Handler %s.%s returned %s',
                    _handler.__module__,
                    _handler.__name__,
                    repr(_response_message.text)
                )
                if _response_message.text is not None:
                    _manager.message_queue.put(_response_message)

            manager = self
            conference = manager.conferences.get(message['from'].bare)
            if not conference:
                return

            handlers = []
            handler_kwargs = {'message': message, 'conference': conference, 'application': manager.application}

            own_message = conference.member == message['from'].resource
            sys_message = not message['from'].resource
            regular_message = not own_message and not sys_message

            if regular_message and conference.prefix and message['body'].startswith(conference.prefix):
                command, *cmd_args = message['body'][len(conference.prefix):].split(' ')
                handler = plugin.get_command_handler(command)
                if handler:
                    handlers.append(handler)
                    handler_kwargs['command'] = command
                    handler_kwargs['command_args'] = cmd_args

            handlers += plugin.get_message_handlers(regular=regular_message, system=sys_message, own=own_message)

            for handler in handlers:
                threading.Thread(
                    name='dewyatochka.msg_handler.%s.%s' % (handler.__module__, handler.__name__),
                    target=_message_handler_wrapper,
                    args=(handler, handler_kwargs, manager),
                    daemon=True
                ).start()

        def _handle_presence_error(presence):
            """
            Handle presence error
            """
            conference = presence['from'].bare
            error = presence['error']['text']

            _manager = self
            _manager.application.log(__name__).error('Failed to send presence to %s: %s', conference, error)
            if conference in _manager.conferences:
                del _manager.conferences[conference]

        self.xmpp.set_message_handler(_handle_message)
        self.xmpp.set_presence_error_handler(_handle_presence_error)

        self.xmpp.connection.process()

    @property
    def message_queue(self):
        """
        Get massages queue
        :return: Queue
        """
        return self._message_queue

    @property
    def xmpp(self):
        """
        Get XMPP client instance
        :return: xmpp.Client
        """
        if not self._xmpp_instance:
            connection_config = self.application.config.section('xmpp')
            self._xmpp_instance = xmpp.Client(
                connection_config['server'],
                connection_config['login'],
                connection_config['password'],
                connection_config.get('port', 5222),
                connection_config.get('resource', ''),
                int(connection_config.get('timeout', xmpp.DEFAULT_TIMEOUT)),
                int(connection_config.get('retry', xmpp.DEFAULT_RETRIES))
            )
        return self._xmpp_instance

    @property
    def conferences(self):
        """
        Get configured conferences indexed by conference jid
        :return: dict
        """
        return self._alive_conferences

    def _enter_conferences(self):
        """
        Enter all conferences
        :return: void
        """
        if self._all_conferences is None:
            self._all_conferences = {
                section.get('room'): Conference(
                    section.get('room'),
                    section.get('nick'),
                    section.get('prefix')
                ) for section in self.application.conferences_config
            }

        for conference in self._all_conferences:
            self._enter_conference(self._all_conferences[conference])

    def _enter_conference(self, conference):
        """
        Enter into a single conference
        :param conference: Conference
        :return: void
        """
        self.application.log(__name__).info('Entering %s as %s' % (
            conference.jid,
            conference.member
        ))
        self.conferences[conference.jid] = conference
        self.xmpp.enter_room(conference.jid, conference.member)

    def _leave_conferences(self):
        """
        Leave all conferences
        :return: void
        """
        self.application.log(__name__).info('Leaving all the conferences')
        for conference in self.conferences.copy():
            self._leave_conference(self.conferences[conference])
        else:
            self.application.log(__name__).info('No alive conferences left')

    def _leave_conference(self, conference):
        """
        Leave a single conference
        :param conference: Conference
        :return: void
        """
        self.application.log(__name__).info('Leaving %s', conference.jid)
        self.xmpp.leave_room(conference.jid, conference.member, '')  # TODO: Maybe move leave reason to config
        del self.conferences[conference.jid]

    def _monitor_conferences_state(self):
        """
        Monitor if conferences are alive
        :return: void
        """
        logger = self.application.log(__name__)
        while True:
            check_at = time.time() + _CONFERENCES_CHECK_INTERVAL
            while time.time() < check_at:
                if not self.application.running:
                    return
                time.sleep(1)
            logger.debug('Performing conferences check')
            for conference_jid in self._all_conferences:
                if conference_jid in self.conferences:
                    # Conference is alive so ping it
                    try:
                        self.xmpp.ping_room(conference_jid)
                    except S2SConnectionError:
                        logger.error('Conference %s is unavailable (ping check failed)', conference_jid)
                        del self.conferences[conference_jid]
                else:
                    # Conference is dead, trying to reenter it
                    self._enter_conference(self._all_conferences[conference_jid])

    def run(self):
        """
        Run messages processing
        :return: void
        """
        try:
            self._start_response_sender()
            self._start_messages_handler()

            self._enter_conferences()

            self._monitor_conferences_state()
        except xmpp.XMPPConnectionError as e:
            self.application.error(__name__, e)
            self.application.log(__name__).critical('Fatal error: Conference manager failed')
        except Exception as e:
            self.xmpp.connection.disconnect()
            self.xmpp.connection.set_stop()
            self.application.error(__name__, e)
            self.application.log(__name__).critical('Fatal error: Conference manager failed')
        else:
            self._leave_conferences()
            time.sleep(1)  # TODO: Check event when all conferences are offline
            self.xmpp.connection.disconnect()
            self.xmpp.connection.set_stop()

    def start(self):
        """
        Start conference manager
        :return: void
        """
        threading.Thread(
            name='dewyatochka.conference_manager',
            target=self.run
        ).start()
