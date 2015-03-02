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
from dewyatochka.core.log import get_logger, get_null_logger
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
        :return argparse.Namespace:
        """
        args_parser = argparse.ArgumentParser()
        args_parser.add_argument('command',
                                 metavar='command',
                                 help='Command name(s) comma separated')
        args_parser.add_argument('--config',
                                 help='Path to config file to use',
                                 default=COMMON_CONFIG_DEFAULT_PATH)
        args_parser.add_argument('--log',
                                 help='Use a configured logger to yield debug info',
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
            self.depend(get_extensions_config(self))

            if params.log:
                self.depend(get_logger(self, has_stdout=True))
            else:
                self.depend(get_null_logger(self))

            self.depend(LoaderService)
            self.depend(ctl_service.Service)

            plugins_loaders = self.registry.plugins.loaders
            self.registry.ctl.load(plugins_loaders, ctl_service.Wrapper(self.registry.ctl))
            self.registry.ctl.get_command(params.command)(argv=args, logger=self.registry.log(__name__))

        except (KeyboardInterrupt, SystemExit):
            self.registry.log(__name__).info('Interrupted by user')
            self.stop(_EXIT_CODE_TERM)

        except Exception as e:
            self.fatal_error(__name__, e)
            self.stop(_EXIT_CODE_ERROR)

        finally:
            sys.exit(self._exit_code)
