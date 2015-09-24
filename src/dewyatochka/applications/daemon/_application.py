# -*- coding: UTF-8

""" Main application implementation

Serves conferences and takes a talk with other people

Classes
=======
    DaemonApp -- Application implementation
"""

__all__ = ['DaemonApp']

import sys
import argparse

from dewyatochka.core import daemon
from dewyatochka.core.application import Application
from dewyatochka.core.log import get_daemon_logger
from dewyatochka.core.config import get_common_config, get_conferences_config, get_extensions_config
from dewyatochka.core.config.factory import COMMON_CONFIG_DEFAULT_PATH
from dewyatochka.core.network.xmpp import service as xmpp
from dewyatochka.core.plugin.subsystem.message import service as m_service
from dewyatochka.core.plugin.subsystem.helper import service as h_service
from dewyatochka.core.plugin.loader import LoaderService

from . import _process


# App exit codes
_EXIT_CODE_OK = 0
_EXIT_CODE_ERROR = 1
_EXIT_CODE_TERM = 2

# Default path to the log file
_DEFAULT_LOG_FILE_PATH = '/var/log/dewyatochka/dewyatochkad.log'

# Path to the lock-file if none is specified
_DEFAULT_LOCK_FILE_PATH = '/var/run/dewyatochka/dewyatochkad.pid'


class DaemonApp(Application):
    """ Application implementation """

    @staticmethod
    def _parse_args(args: list):
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

    def run(self, args: list):
        """ Run application

        :param list args: Console arguments
        :return None:
        """
        try:
            params = self._parse_args(args)

            self.depend(get_common_config(self, params.config))

            log_file = None if params.nodaemon \
                else self.registry.config.section('log').get('file', _DEFAULT_LOG_FILE_PATH)
            self.depend(get_daemon_logger(self, log_file))

            self.depend(get_conferences_config(self))
            self.depend(get_extensions_config(self))

            self.depend(LoaderService)
            self.depend(m_service.Service)
            self.depend(h_service.Service)

            self.depend(_process.Helper)
            self.depend(_process.ChatManager)
            self.depend(xmpp.Connection)
            self.registry.add_service_alias(_process.ChatManager, 'bot')

            if not params.nodaemon:
                daemon.detach(lambda *_: self.stop(_EXIT_CODE_OK))
                daemon.acquire_lock(self.registry.config.global_section.get('lock', _DEFAULT_LOCK_FILE_PATH))

            self.registry.get_service(m_service.Service).load()
            self.registry.get_service(h_service.Service).load()

            self.registry.chat_manager.start()
            self.registry.helper.start()

            self.wait()

        except (KeyboardInterrupt, SystemExit):
            self.registry.log(__name__).warning('Interrupted by user')
            self.stop(_EXIT_CODE_TERM)

        except Exception as e:
            self.fatal_error(__name__, e)
            self.stop(_EXIT_CODE_ERROR)

        finally:
            # Stop threads if needed
            for critical_svc in _process.ChatManager, _process.Helper:
                try:
                    self.registry.get_service(critical_svc).wait()
                except RuntimeError:
                    pass
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
