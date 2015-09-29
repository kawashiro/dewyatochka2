# -*- coding: UTF-8

"""  Main services implementation

Classes
=======
    Helper      -- Manages helper threads required by plugins
    ChatManager -- Chat manager service implementation
"""

import threading
from functools import reduce

from dewyatochka.core.application import Application, Service
from dewyatochka.core.network.service import ConnectionManager
from dewyatochka.core.network.service import ChatManager as ChatManager_
from dewyatochka.core.network.entity import Message, GroupChat
from dewyatochka.core.plugin.subsystem.helper.service import Environment
from dewyatochka.core.plugin.subsystem.helper.service import Service as HService
from dewyatochka.core.plugin.subsystem.message.service import Service as MService

__all__ = ['Helper', 'ChatManager']


# Interval between helpers state checks
_HELPER_PERSISTENT_CHECK_INTERVAL = 60


def _thread_wait(thread: threading.Thread, log=None):
    """ Waiting for thread to complete

    :param threading.Thread thread:
    :param logging.Logger log:
    :return None:
    """
    if thread.is_alive():
        if log:
            log.debug('Waiting for thread "%s"', thread.name)
        thread.join()


class Helper(Service):
    """ Manages helper threads required by plugins """

    def __init__(self, application: Application):
        """ Initialize service & attach an application to it

        :param Application application:
        """
        super().__init__(application)

        self._thread = threading.Thread(name=self.name() + '[Monitor]', target=self._run)

    def start(self):
        """ Start manager

        :return None:
        """
        self._thread.start()

    def wait(self):
        """ Wait until stopped

        :return None:
        """
        _thread_wait(self._thread, self.log)

    def _run(self):
        """ Perform helpers control

        :return None:
        """
        try:
            self._start_all()
            self._monitor()
        except Exception as e:
            self.application.fatal_error(__name__, e)

    def _start_all(self):
        """ Start all the helpers

        :return None:
        """
        for helper_env in self.application.registry.get_service(HService).plugins:
            self._start_helper(helper_env)

    def _monitor(self):
        """ Monitor helpers state

        :return None:
        """
        self.application.sleep(_HELPER_PERSISTENT_CHECK_INTERVAL)

        while self.application.running:
            alive_threads = {thread.name for thread in threading.enumerate()}
            self.log.debug('Checking helpers state')

            for helper_env in self.application.registry.get_service(HService).plugins:
                if self._get_thread_name(helper_env) not in alive_threads:
                    self.log.warning('Helper %s died, trying to restart', helper_env)
                    self._start_helper(helper_env)
                else:
                    self.log.debug('Helper %s is running', helper_env)

            self.application.sleep(_HELPER_PERSISTENT_CHECK_INTERVAL)

    def _start_helper(self, helper_env):
        """ Start helper

        :param Environment helper_env:
        :return None:
        """
        self.log.debug('Starting helper %s', helper_env)
        threading.Thread(
            name=self._get_thread_name(helper_env),
            target=helper_env,
            kwargs={'logger': self.log},
            daemon=True
        ).start()

    @staticmethod
    def _get_thread_name(env: Environment) -> str:
        """ Get thread name for the helper

        :param Environment env:
        :return str:
        """
        return 'helper[%s]' % env

    @classmethod
    def name(cls) -> str:
        """ Get service unique name

        :return str:
        """
        return 'helper'


class ChatManager(ChatManager_):
    """ Chat manager service implementation """

    def __init__(self, application: Application):
        """ Initialize service & attach an application to it

        :param Application application:
        """
        super().__init__(application)

        self._monitor_thread = threading.Thread(name=self.name() + '[Monitor]', target=self._monitor)

        self._reader_threads = []
        self._connections = []

    def _create_reader_thread(self, connection: ConnectionManager):
        """ Create reader thread instance

        :param ConnectionManager connection:
        :return:
        """
        return threading.Thread(
            name='{:s}[Reader][{:s}]'.format(self.name(), connection.name()),
            target=self._read,
            args=(connection,)
        )

    def attach_connection_manager(self, connection: ConnectionManager):
        """ Attach a connection manager to take control on

        :param ConnectionManager connection: Connection manager
        :return None:
        """
        self._reader_threads.append(self._create_reader_thread(connection))
        self._connections.append(connection)

    def _monitor(self):
        """ Monitor app state

        :return None:
        """
        try:
            for i in range(len(self._connections)):
                self._connections[i].connect()
                self._reader_threads[i].start()

            self.application.wait()

            for i in range(len(self._connections)):
                self._connections[i].disconnect()
                _thread_wait(self._reader_threads[i], self.log)

        except Exception as e:
            self.application.fatal_error(__name__, e)

    def _read(self, connection_manager: ConnectionManager):
        """ Run process

        :param ConnectionManager connection_manager:
        :return None:
        """
        try:
            # noinspection PyTypeChecker
            for message in connection_manager.input_stream:
                self.log.debug('Received a message from %s <<< %s >>>', message.sender, str(message))
                self._start_message_processing(message)

        except Exception as e:
            self.application.fatal_error(__name__, e)

    def _start_message_processing(self, message: Message):
        """ Start message processing

        :param Message message:
        :return None:
        """
        message_plugins = self.application.registry.get_service(MService).plugins

        for plugin in message_plugins:
            self.log.debug('Passing message processing to a plugin %s', plugin)
            threading.Thread(
                name='message[%s][%x]' % (plugin, id(message)),
                target=plugin,
                kwargs={'logger': self.log, 'message': message},
                daemon=True
            ).start()

    def start(self):
        """ Start thread

        :return None:
        """
        self._monitor_thread.start()

    def wait(self):
        """ Wait until stopped

        :return None:
        """
        _thread_wait(self._monitor_thread, self.log)

    @property
    def alive_chats(self) -> frozenset:
        """ Get alive conferences

        :return frozenset:
        """
        return reduce(lambda val, conn: val.union(conn.alive_chats), self._connections, frozenset())

    def send(self, message: str, chat: GroupChat):
        """ Send a message to groupchat

        :param str message: Message content
        :param GroupChat chat: Destination chat
        :return None:
        """
        for conn in self._connections:
            if chat in conn.alive_chats:
                conn.send(message, chat)
                break
        else:
            raise RuntimeError('Chat %s is not online' % chat)
