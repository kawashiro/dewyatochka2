# -*- coding: UTF-8

""" XMPP connection management

Classes
=======
    XMPPConnectionManager -- Serves xmpp-connection
    ConnectionConfigError -- Error on invalid xmpp connection config
    ConferenceConfigError -- Error on invalid conference config
    PresenceHelper        -- Serves presence in conferences
"""

import time
from collections import namedtuple
import threading

from dewyatochka.core.application import Application
from dewyatochka.core.config.exception import ConfigError

from ..service import ConnectionManager

from . import client
from .entity import Conference, JID
from .exception import *

__all__ = ['XMPPConnectionManager', 'ConnectionConfigError', 'ConferenceConfigError', 'PresenceHelper']


# Seconds to wait between multiple connections attempts
_XMPP_RECONNECT_INTERVAL = 30

# Conferences check interval
_XMPP_CHECK_INTERVAL = 60

# Max time interval when conference or server is offline
_XMPP_OFFLINE_TIME_LIMIT = 86400


class ConnectionConfigError(ConfigError):
    """ Error on invalid xmpp connection config """
    pass


class ConferenceConfigError(ConfigError):
    """ Error on invalid conference config """
    pass


class PresenceHelper:
    """ Serves presence in conferences """

    # Conference reconnect task structure
    __ReconnectTask = namedtuple('__ReconnectTask', ['conference', 'died_at'])

    def __init__(self, connection_manager):
        """ Init presence manager

        :param XMPPConnectionManager connection_manager:
        :return:
        """
        self._connection_manager = connection_manager

        self._alive_conferences = set()
        self._alive_nicknames = {}
        self._alive_set_lock = threading.Lock()
        self._reconnect_queue = []

        self.__configured_conferences = None
        self.__configured_conferences_lock = threading.Lock()

        self._reconnect_thread = threading.Thread(
            name=self._connection_manager.name() + '[PresenceHelper][Reenter]',
            target=self._do_reconnect
        )
        self._ping_thread = threading.Thread(
            name=self._connection_manager.name() + '[PresenceHelper][Ping]',
            target=self._do_s2s_ping
        )
        self._running = False

    def start(self):
        """ Start conferences management

        :return None:
        """
        self._running = True
        self._reconnect_thread.start()
        self._ping_thread.start()

    def stop(self):
        """ Stop a reconnection thread if it has been started

        :return None:
        """
        self.__assert_started()
        self._running = False

        self._ping_thread.join()
        self._reconnect_thread.join()

    def enter(self, conference: Conference):
        """ Enter a conference

        :param Conference conference: Conference jid with nick
        :return None:
        """
        with self._alive_set_lock:
            self.__assert_started()
            log = self._connection_manager.log

            if conference.bare not in self._alive_conferences:
                log.info('Entering into conference %s as %s', conference.bare.jid, conference.resource)
                self._connection_manager.client.chat.enter(conference.bare, conference.resource)
                self._alive_conferences.add(conference.bare)
                self._alive_nicknames[conference.bare] = conference.resource
            else:
                log.debug('Discarded to enter to a conference %s while it is marked as alive', str(conference))

    def leave(self, conference: Conference):
        """ Leave conference

        :param Conference conference: Conference jid
        :return:
        """
        with self._alive_set_lock:
            self.__assert_started()
            log = self._connection_manager.log
            conference = conference.bare

            if conference in self._alive_conferences and conference in self._alive_nicknames:
                log.info('Leaving conference %s', str(conference))
                self._connection_manager.client.chat.leave(conference, self._alive_nicknames[conference])
                self._alive_conferences.remove(conference)
                del self._alive_nicknames[conference]
            else:
                log.debug('Discarded to leave conference %s while it is not marked as alive', str(conference))

    def clear_state(self):
        """ Flush reconnection queue and mark all conferences as dead

        :return None:
        """
        with self._alive_set_lock:
            self._alive_conferences.clear()
            self._alive_nicknames.clear()
            self._reconnect_queue.clear()

    def enter_all(self):
        """ Enter into all the configured conferences

        :return None:
        """
        self.__assert_started()
        for conference in self._configured_conferences:
            self.enter(conference)

    def leave_all(self):
        """ Leave all the conferences

        :return None:
        """
        self.__assert_started()
        for conference in self._alive_conferences.copy():
            self.leave(conference)

    def schedule_reenter(self, conference: Conference):
        """ Schedule conference reenter

        :param Conference conference: Conference jid with nick
        :return None:
        """
        self.__assert_started()

        log = self._connection_manager.log
        log.error('Server-to-server connection to %s seems to be broken, scheduling reconnect', conference)

        with self._alive_set_lock:
            try:
                self._alive_conferences.remove(conference.bare)
            except KeyError:
                # Failed on the first connection attempt
                pass
            self._reconnect_queue.append(self.__ReconnectTask(self.get_presence_jid(conference), time.time()))

    def get_presence_jid(self, participant: JID) -> Conference:
        """ Get full conference presence JID

        :param JID participant: Full or bare JID
        :return Conference:
        """
        try:
            full_conf_resource = self._alive_nicknames[participant.chat]
            return Conference(participant.login, participant.server, full_conf_resource)

        except KeyError:
            raise XMPPError('Unable to get presence JID for offline conference')

    def is_alive(self, conference: Conference) -> bool:
        """ Check if conference is alive

        :param Conference conference: Conference jid with nick
        :return bool:
        """
        return conference in self._alive_conferences

    @property
    def alive_conferences(self) -> frozenset:
        """ Get alive conferences set

        :return frozenset:
        """
        return frozenset(self._alive_conferences)

    @property
    def _configured_conferences(self) -> set:
        """ Return a set of configured conferences

        :return set of Conference:
        """
        with self.__configured_conferences_lock:
            if self.__configured_conferences is None:
                self.__configured_conferences = set()
                config = self._connection_manager.application.registry.conferences_config

                for conf_name in config:
                    try:
                        conf_config = config.section(conf_name)
                        if not conf_config.get('nick') or not conf_config.get('room'):
                            raise ValueError
                        self.__configured_conferences.add(Conference.from_config(**conf_config))

                    except ValueError:
                        self._connection_manager.log.error('Conference [%s] is not configured properly', conf_name)

        return self.__configured_conferences

    def _do_reconnect(self):
        """ Reconnect queue processing loop

        :return None:
        """
        try:
            app = self._connection_manager.application

            while app.running and self._running:
                postponed = []
                while app.running and self._running and self._reconnect_queue:
                    task = self._reconnect_queue.pop(0)
                    if task.conference.bare in self._alive_conferences:
                        continue  # Conference is alive (task dup)

                    try:
                        if task.died_at + _XMPP_RECONNECT_INTERVAL < time.time():
                            self.enter(task.conference)
                        else:
                            postponed.append(task)
                    except XMPPError as e:
                        self._connection_manager.log.error('Failed to enter into %s as %s: %s (reenter postponed)',
                                                           task.conference.bare, task.conference.resource, e)
                        postponed.append(self.__ReconnectTask(task.conference, time.time()))

                if postponed:
                    self._reconnect_queue.extend(postponed)
                app.sleep(1)

        except Exception as e:
            self._connection_manager.application.fatal_error(__name__, e)

    def _do_s2s_ping(self):
        """ Ping conferences

        :return None:
        """
        try:
            log = self._connection_manager.log
            app = self._connection_manager.application
            app.sleep(_XMPP_CHECK_INTERVAL)

            while app.running and self._running:
                for conference in self._alive_conferences.copy():
                    if not app.running or not self._running:
                        break

                    try:
                        log.debug('Ping %s', conference)
                        pt = self._connection_manager.client.ping(self.get_presence_jid(conference))
                        log.debug('Ping %s succeeded (%f)', conference, pt)

                    except S2SConnectionError:
                        self.schedule_reenter(conference)

                    except Exception as e:
                        log.warn('Failed to ping %s: %s', conference, e)

                app.sleep(_XMPP_CHECK_INTERVAL)
        except Exception as e:
            self._connection_manager.application.fatal_error(__name__, e)

    def __assert_started(self):
        """ Check if start() has been invoked

        :return None:
        """
        if not self._running:
            raise RuntimeError('Presence management is not started')

    def __enter__(self):
        """ Using as a context manager

        :return PresenceHelper:
        """
        if not self._running:
            self.start()

        return self

    def __exit__(self, *_) -> bool:
        """ Stop on exit

        :param _ tuple:
        :return bool:
        """
        if self._running:
            self.stop()

        return False


class XMPPConnectionManager(ConnectionManager):
    """ Serves xmpp-connection

    Check connections state and provides
    a single stable input stream to work with
    """

    def __init__(self, application: Application, presence_helper=None, xmpp_client=None):
        """ Initialize service & attach an application to it

        :param Application application:
        :param PresenceHelper presence_helper:
        :param client.Client xmpp_client:
        """
        super().__init__(application)

        self.__client = xmpp_client
        self._presence_helper = presence_helper or PresenceHelper(self)

    @property
    def _connection_config(self) -> dict:
        """ Get xmpp connection config options

        :return dict:
        """
        config = {param: self.config.get(param)
                  for param in ('host', 'login', 'password', 'port', 'location')
                  if self.config.get(param)}

        missing_fields = {field for field in ('host', 'login', 'password') if config.get(field) is None}
        if missing_fields:
            raise ConnectionConfigError('Invalid XMPP connection config, missing %s' % ', '.join(missing_fields))

        try:
            config['port'] = int(config['port'])
        except KeyError:
            pass
        except ValueError:
            raise ConnectionConfigError('Invalid port number: %s' % config['port'])

        return config

    def _reconnect(self) -> bool:
        """ Try to reconnect on client connection error

        Return True if reconnection succeeded

        :return bool:
        """
        time_start = time.time()
        success = False
        attempts = 0

        while self.application.running and time.time() - time_start < _XMPP_OFFLINE_TIME_LIMIT:
            try:
                attempts += 1
                self.client.connect()
                self._presence_helper.enter_all()
            except C2SConnectionError as e:
                self.log.error('%s (attempt #%d), sleeping %d seconds before the next attempt',
                               e, attempts, _XMPP_RECONNECT_INTERVAL)
                self.application.sleep(_XMPP_RECONNECT_INTERVAL)
            else:
                success = True
                break

        return success

    @property
    def client(self) -> client.Client:
        """ XMPP client instance getter

        :return client.Client:
        """
        if self.__client is None:
            self.__client = client.create(**self._connection_config)

        return self.__client

    def __try(self, fn, *args, **kwargs):
        """ Try to execute some code with connection errors handling

        :param callable: Function to call
        :param tuple args: Args to path to the function
        :param dict kwargs: Keyword args to path to the function
        :returns: Function return value
        """
        try:
            return fn(*args, **kwargs)

        except ClientDisconnectedError:
            raise

        except MessageError as e:
            self.log.debug(e)

        except C2SConnectionError as e:
            self.log.error(e)
            self._presence_helper.clear_state()
            if not self._reconnect():
                raise

        except S2SConnectionError as e:
            self._presence_helper.schedule_reenter(e.remote)

        return None

    def connect(self):
        """ Establish connection

        :return None:
        """
        self.__try(self.client.connect)
        self.__try(self._presence_helper.start)
        self.__try(self._presence_helper.enter_all)

    @property
    def input_stream(self):
        """ Wrapper over xmpp client input stream

        Implements auto reconnection and conferences re-enter
        if something goes wrong

        :return Message:
        """
        while True:
            try:
                msg = self.__try(self.client.read)
                if msg is not None:
                    if msg.receiver == self.client.jid:
                        msg.receiver = self._presence_helper.get_presence_jid(msg.sender)
                    yield msg

            except ClientDisconnectedError:
                break

    def disconnect(self):
        """ Force disconnection

        :return None:
        """
        try:
            self.__try(self._presence_helper.leave_all)
            self.__try(self._presence_helper.stop)
        except RuntimeError:
            pass

        try:
            self.client.disconnect()
        except ClientDisconnectedError:
            pass

    @property
    def alive_chats(self) -> frozenset:
        """ Get alive conferences

        :return frozenset:
        """
        return self._presence_helper.alive_conferences

    def send(self, message: str, chat: Conference):
        """ Send a message to groupchat

        :param str message: Message content
        :param Conference chat: Chat JID (with nickname)
        :return None:
        """
        if not self._presence_helper.is_alive(chat):
            raise S2SConnectionError('Chat %s is not online now' % chat, remote=chat)

        self.client.chat(message, chat.bare)

    @classmethod
    def name(cls) -> str:
        """ Get service unique name

        :return str:
        """
        return 'xmpp'
