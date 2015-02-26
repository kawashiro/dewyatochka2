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
from dewyatochka.core.log import get_logger
from dewyatochka.core.config import get_common_config, get_conferences_config, get_extensions_config
from dewyatochka.core.config.factory import COMMON_CONFIG_DEFAULT_PATH
from dewyatochka.core.plugin.message_sys import service as m_service
from dewyatochka.core.plugin.helper_sys import service as h_service
from dewyatochka.core.plugin.base import Wrapper as BaseWrapper
from dewyatochka.core.plugin.loader import LoaderService

from ._process.conference.connection import ConnectionManager
from ._process.conference.bot import Bot
from ._process.helper import HelpersManager


# App exit codes
_EXIT_CODE_OK = 0
_EXIT_CODE_ERROR = 1
_EXIT_CODE_TERM = 2


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
            self.depend(get_logger(self, params.nodaemon))

            self.depend(get_conferences_config(self))
            self.depend(get_extensions_config(self))

            self.depend(LoaderService)
            self.depend(m_service.Service)
            self.depend(h_service.Service)

            self.depend(HelpersManager)
            self.depend(ConnectionManager)
            self.depend(Bot)

            if not params.nodaemon:
                daemon.detach(lambda *_: self.stop(_EXIT_CODE_OK))
                daemon.acquire_lock(self.registry.config.global_section.get('lock'))

            plugins_loaders = self.registry.plugins.loaders
            self.registry.chat.load(plugins_loaders, m_service.Wrapper(self.registry.chat))
            self.registry.helper.load(plugins_loaders, BaseWrapper(self.registry.helper))

            self.registry.bot.start()
            self.registry.helpers_manager.start()
            self.wait()

        except (KeyboardInterrupt, SystemExit):
            self.registry.log(__name__).info('Interrupted by user')
            self.stop(_EXIT_CODE_TERM)

        except Exception as e:
            self.fatal_error(__name__, e)
            self.stop(_EXIT_CODE_ERROR)

        finally:
            # Stop threads if needed
            for critical_svc in (Bot, HelpersManager):
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
