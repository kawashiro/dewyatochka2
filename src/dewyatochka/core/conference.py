# -*- coding: UTF-8

"""
Chat environment
"""

__all__ = ['Conference', 'ConferenceManager', 'Message', 'Worker']

from dewyatochka.core import plugin
from threading import Thread
from collections import namedtuple
from queue import Queue
import threading
from dewyatochka.core.application import Service
from dewyatochka.core.xmpp import Client as XMPPClient

# Message to a conference
Message = namedtuple('Message', ['text', 'target'])


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

    def __init__(self, bare, nick):
        """
        Create new environment instance
        :param bare: some_room@conference.jabber.example.com
        :return:
        """
        self._room, self._server = bare.split('@')
        self._bare = bare
        self._nick = nick

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
        """
        return '/'.join((self.jid, self.member))


class ConferenceManager(Service):
    """
    Handles multiple conferences persistence
    """
    # TODO: Very crappy class. Needs refactoring

    # XMPP client
    _xmpp = None

    # Configured conferences
    _conferences = {}

    # Message queue to communicate with message handlers
    _message_queue = None

    def _handle_message(self, message):
        """
        Handle incoming message
        :param message: dict
        :return:
        """
        def _message_handler(_conference, _message, _handler, _queue, _application):
            """
            Common message handler thread
            :param _conference: Conference
            :param _message: dict
            :param _handler: callable
            :param _queue: Queue
            :param _application: DewyatochkaDaemon
            :return: void
            """
            handler_kwargs = {'message': _message, 'conference': _conference, 'application': _application}
            _response_message = Message(_handler.handle(**handler_kwargs), _message['from'])
            if _response_message is not None:
                _queue.put(_response_message)

        conference = self._conferences.get(message['from'].bare, None)
        if conference is None:
            return

        for handler in plugin.get_message_handlers():
            Thread(
                name='dewyatochka.msg_handler.%s.%s' % (handler.__module__, handler.__name__),
                target=_message_handler,
                args=(conference, message, handler, self._message_queue, self.application)
            ).start()

    def run(self, xmpp, conferences_config):
        """
        Run messages processing
        :param xmpp: xmpp client
        :param conferences_config:
        :return: void
        """
        def _response_sender(_xmpp_client, _queue):
            """
            Sends messages from the queue
             :param _xmpp_client: xmpp.Client
             :param _queue: Queue
             :return: void
            """
            while True:
                _message = _queue.get()
                _xmpp_client.send_chat_message(_message.text, _message.target.bare)

        self._xmpp = xmpp
        self._conferences = {conference.jid: conference for conference in conferences_config}
        self._message_queue = Queue()

        self._xmpp.set_message_handler(self._handle_message)

        Thread(
            name='dewyatochka.msg_sender',
            target=_response_sender,
            args=(self._xmpp, self._message_queue)
        ).start()

        for conference in self._conferences:
            self._xmpp.enter_room(self._conferences[conference].jid, self._conferences[conference].member)

        self._xmpp.connection.process(block=True)


class Worker(Service):
    """
    XMPP-connection worker thread
    """

    def start(self):
        """
        Start thread
        :return: void
        """
        connection_config = self.application.config.section('xmpp')

        xmpp_client = XMPPClient(connection_config['server'], connection_config['login'], connection_config['password'])
        conferences = [
            Conference(section.get('room'), section.get('nick'))
            for section in self.application.conferences_config
        ]

        threading.Thread(
            name='dewyatochka.xmpp',
            target=self.application.conference_manager.run,
            args=(xmpp_client, conferences)
        ).start()
