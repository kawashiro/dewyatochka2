# -*- coding: UTF-8

""" dewyatochkactl utility implementation

Classes
=======
    Application -- Application class
"""

__all__ = ['Application']

import sys
import argparse

from dewyatochka.core.application import Application as BaseApplication
from dewyatochka.core.config import get_common_config, get_extensions_config
from dewyatochka.core.config.factory import COMMON_CONFIG_DEFAULT_PATH
from dewyatochka.core.log import get_console_logger
from dewyatochka.core.plugin.loader import LoaderService
from dewyatochka.core.plugin.ctl_sys import service as ctl_service


# App exit codes
_EXIT_CODE_OK = 0
_EXIT_CODE_ERROR = 1
_EXIT_CODE_TERM = 2


class Application(BaseApplication):
    """ dewyatochkactl impl """

    @staticmethod
    def _parse_args(args: list):
        """ Parse known arguments

        :param list args:
        :return tuple:
        """
        args_parser = argparse.ArgumentParser()
        args_parser.add_argument('command',
                                 metavar='command',
                                 help='Command name(s) comma separated. Run dewyatochkactl list to see them')
        args_parser.add_argument('--config',
                                 help='Path to config file to use',
                                 default=COMMON_CONFIG_DEFAULT_PATH)

        return args_parser.parse_known_args(args[1:])

    def run(self, args: list):
        """ Run application

        :param list args: Console arguments
        :return None:
        """
        try:
            params, cmd_args = self._parse_args(args)

            self.depend(get_common_config(self, params.config))
            self.depend(get_extensions_config(self))
            self.depend(get_console_logger(self))

            self.depend(LoaderService)
            self.depend(ctl_service.Service)

            plugins_loaders = self.registry.plugins.loaders
            self.registry.ctl.load(plugins_loaders, ctl_service.Wrapper(self.registry.ctl))
            self.registry.ctl.get_command(params.command)(argv=cmd_args)

        except (KeyboardInterrupt, SystemExit):
            self.registry.log(__name__).warning('Interrupted by user')
            self.stop(_EXIT_CODE_TERM)

        except Exception as e:
            self.fatal_error(__name__, e)
            self.stop(_EXIT_CODE_ERROR)

        finally:
            sys.exit(self._exit_code)
