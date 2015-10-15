# -*- coding: UTF-8

""" Main application implementation

Serves conferences and takes a talk with other people

Classes
=======
    DaemonApp -- Application implementation
"""

import sys
import argparse

from dewyatochka.core import daemon

from dewyatochka.core.application import Application
from dewyatochka.core.application import EXIT_CODE_TERM
from dewyatochka.core.log import get_daemon_logger
from dewyatochka.core.config import get_common_config, get_conferences_config, get_extensions_config
from dewyatochka.core.config.factory import COMMON_CONFIG_DEFAULT_PATH
from dewyatochka.core.network.xmpp import service as xmpp
from dewyatochka.core.plugin.loader import LoaderService
from dewyatochka.core.plugin.subsystem.message import service as m_service
from dewyatochka.core.plugin.subsystem.helper import service as h_service
from dewyatochka.core.plugin.subsystem.control import service as c_service

from . import process

__all__ = ['DaemonApp']


class DaemonApp(Application):
    """ Application implementation """

    @staticmethod
    def __parse_args(args: list):
        """ Parse known arguments

        :param list args:
        :return argparse.Namespace:
        """
        args_parser = argparse.ArgumentParser()
        args_parser.add_argument('--config',
                                 help='Path to config file to use',
                                 default=COMMON_CONFIG_DEFAULT_PATH)
        args_parser.add_argument('--nodaemon',
                                 help='Do not detach process from console',
                                 action='store_true')

        return args_parser.parse_args(args[1:])

    def _init(self, config_file: str, daemon_mode=True):
        """ Init dependent services

        :param str config_file:
        :param bool daemon_mode:
        :return:
        """
        self.depend(get_common_config(self, config_file))

        self.depend(get_daemon_logger(self, not daemon_mode))

        self.depend(get_conferences_config(self))
        self.depend(get_extensions_config(self))

        self.depend(LoaderService)
        self.depend(m_service.Service)
        self.depend(h_service.Service)
        self.depend(c_service.Service)

        self.depend(process.Bootstrap)
        self.depend(process.Scheduler)
        self.depend(process.Daemon)
        self.depend(process.Control)
        self.depend(process.ChatManager, 'bot')
        self.depend(xmpp.Connection)

    def _run(self, daemon_mode=True):
        """ Actually run app

        :param bool daemon_mode:
        :return None:
        """
        if daemon_mode:
            daemon.acquire_lock(self.registry.config.global_section.get('lock'))
            daemon.detach(lambda *_: self.stop())

        self.registry.message_plugin_provider.load()
        self.registry.helper_plugin_provider.load()
        self.registry.control_plugin_provider.load()

        self.registry.bootstrap.run()
        self.registry.daemon.start()
        self.registry.scheduler.start()
        self.registry.chat_manager.start()
        self.registry.control.start()

        self.wait()

    def run(self, args: list):
        """ Run application

        :param list args: Console arguments
        :return None:
        """
        try:
            params = self.__parse_args(args)

            self._init(params.config, not params.nodaemon)
            self._run(not params.nodaemon)

        except (KeyboardInterrupt, SystemExit):
            self.registry.log(__name__).warning('Interrupted by user')
            self.stop(EXIT_CODE_TERM)

        except Exception as e:
            self.fatal_error(__name__, e)

        finally:
            # Stop threads if needed
            for critical_svc in self.registry.all:
                if isinstance(critical_svc, process.CriticalService):
                    critical_svc.wait()
            # Release process lock if needed
            try:
                daemon.release_lock()
            except daemon.ProcessNotLockedError:
                pass
            # Say bye-bye ^-^
            try:
                self.registry.log(__name__).info('Bye-bye~')
            except:
                pass
            # Shut down
            sys.exit(self._exit_code)
