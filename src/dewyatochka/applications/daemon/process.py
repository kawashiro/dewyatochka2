# -*- coding: UTF-8

"""  Main services implementation

Classes
=======
    Daemon          -- Manages daemon threads required by plugins
    Scheduler       -- Launchers helper plugins on a schedule
    ChatManager     -- Chat manager service implementation
    Bootstrap       -- Launches bootstrap tasks
    Control         -- Listens for a control commands
"""

import time
import threading
from functools import reduce
from abc import ABCMeta

from dewyatochka.core.application import Application, StandaloneService
from dewyatochka.core.network.service import ConnectionManager
from dewyatochka.core.network.service import ChatManager as ChatManager_
from dewyatochka.core.network.entity import Message, Participant
from dewyatochka.core.plugin.subsystem.helper.service import Environment
from dewyatochka.core.plugin.subsystem.control.network import SocketListener
from dewyatochka.core.plugin.subsystem.control.network import Message as CTLMessage

__all__ = ['Scheduler', 'Daemon', 'ChatManager', 'Bootstrap', 'Control']


class _HelperService(StandaloneService, metaclass=ABCMeta):
    """ Abstract helper service """

    def _launch_plugin(self, plugin: Environment) -> threading.Thread:
        """ Start helper plugin fn in separate thread

        :param Environment plugin:
        :return threading.Thread:
        """
        thread = threading.Thread(
            name=self._get_thread_name(plugin),
            target=plugin,
            kwargs={'logger': self.log},
            daemon=True
        )
        thread.start()
        return thread

    @classmethod
    def _get_thread_name(cls, plugin: Environment) -> str:
        """ Get thread name for the helper plugin

        :param Environment plugin:
        :return str:
        """
        return '%s[%s]' % (cls.name(), plugin)


class Scheduler(_HelperService):
    """ Launchers helper plugins on a schedule """

    def run(self):
        """ Perform tasks

        :return None:
        """
        try:
            while True:
                self.application.sleep(60 - time.time() % 60)
                if not self.application.running:
                    break
                self._run_scheduled_tasks()

        except Exception as e:
            self.application.fatal_error(self._log_name(), e)

    def _run_scheduled_tasks(self):
        """ Start registered scheduler tasks

        :return None:
        """
        plugins_list = self.application \
            .registry \
            .helper_plugin_provider \
            .schedule_plugins

        for plugin in plugins_list:
            self._launch_plugin(plugin)

    @classmethod
    def name(cls) -> str:
        """ Get service unique name

        :return str:
        """
        return 'scheduler'


class Daemon(_HelperService):
    """ Manages daemon threads required by plugins """

    # Interval between helpers state checks
    _CHECK_INTERVAL = 60

    @property
    def _daemon_plugins(self) -> list:
        """ Daemon plugins list

        :return list:
        """
        return self.application \
            .registry \
            .helper_plugin_provider \
            .daemon_plugins

    def run(self):
        """ Perform helpers control

        :return None:
        """
        try:
            self._start_all()
            self._monitor()
        except Exception as e:
            self.application.fatal_error(self._log_name(), e)

    def _start_all(self):
        """ Start all the helpers

        :return None:
        """
        for plugin in self._daemon_plugins:
            self.log.debug('Starting daemon %s', plugin)
            self._launch_plugin(plugin)

    def _monitor(self):
        """ Monitor helpers state

        :return None:
        """
        self.application.sleep(self._CHECK_INTERVAL)

        while self.application.running:
            alive_threads = {thread.name for thread in threading.enumerate()}
            self.log.debug('Checking daemons state')

            for plugin in self._daemon_plugins:
                if self._get_thread_name(plugin) not in alive_threads:
                    self.log.warning('Daemon %s is down, trying to restart', plugin)
                    self._launch_plugin(plugin)
                else:
                    self.log.debug('Daemon %s is running', plugin)

            self.application.sleep(self._CHECK_INTERVAL)

    @classmethod
    def name(cls) -> str:
        """ Get service unique name

        :return str:
        """
        return 'daemon'


class Bootstrap(_HelperService):
    """ Launches bootstrap tasks """

    def __init__(self, application: Application):
        """ Initialize service & attach an application to it

        :param Application application:
        """
        super().__init__(application)

        self._plugins_threads = []

    def _run(self):
        """ Perform tasks

        :return None:
        """
        plugins_list = self.application \
            .registry \
            .helper_plugin_provider \
            .bootstrap_plugins

        for plugin in plugins_list:
            self.log.debug('Running bootstrap task %s', plugin)
            thread = self._launch_plugin(plugin)
            self._plugins_threads.append(thread)

    def run(self):
        """ Run in the  main thread

        :return None:
        """
        self._run()
        self.wait()

    def wait(self):
        """ Wait until stopped

        :return None:
        """
        for thread in self._plugins_threads:
            self._thread_wait(thread)
        self._plugins_threads.clear()

        super().wait()

    @classmethod
    def name(cls) -> str:
        """ Get service unique name

        :return str:
        """
        return 'bootstrap'


class Control(_HelperService):
    """ Listens for a control commands """

    def __init__(self, application: Application):
        """ Initialize service & attach an application to it

        :param Application application:
        """
        super().__init__(application)
        self._listener = SocketListener(self.config.get('socket'))

    def run(self):
        """ Do job

        :return None:
        """
        try:
            plugins_provider = self.application.registry.control_plugin_provider

            with self._listener as listener:
                for command, source in listener.commands:
                    try:
                        self.log.info('Received a control command "%s"', command.name)
                        plugins_provider.get_command(command.name)(logger=self.log, command=command, source=source)

                    except RuntimeError:
                        source.send(CTLMessage(error='Command %s is not supported' % command.name).encode())

        except Exception as e:
            self.application.fatal_error(self._log_name(), e)

    def wait(self):
        """ Wait until stopped

        :return None:
        """
        self._listener.close()
        super().wait()

    @classmethod
    def name(cls) -> str:
        """ Get service unique name

        :return str:
        """
        return 'control'


class ChatManager(ChatManager_, _HelperService):
    """ Chat manager service implementation """

    def __init__(self, application: Application):
        """ Initialize service & attach an application to it

        :param Application application:
        """
        super().__init__(application)

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

    def run(self):
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
                self._thread_wait(self._reader_threads[i])

        except Exception as e:
            self.application.fatal_error(self._log_name(), e)

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
            self.application.fatal_error(self._log_name(), e)

    def _start_message_processing(self, message: Message):
        """ Start message processing

        :param Message message:
        :return None:
        """
        message_plugins = self.application.registry.message_plugin_provider.plugins

        for plugin in message_plugins:
            threading.Thread(
                name='message[%s][%x]' % (plugin, id(message)),
                target=plugin,
                kwargs={'logger': self.log, 'message': message},
                daemon=True
            ).start()

    @property
    def alive_chats(self) -> frozenset:
        """ Get alive conferences

        :return frozenset:
        """
        return reduce(lambda val, conn: val.union(conn.alive_chats), self._connections, frozenset())

    def send(self, message: str, chat: Participant):
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
