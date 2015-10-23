# -*- coding: UTF-8

""" dewyatochkactl utility implementation

Classes
=======
    Application -- Application class

Functions
=========
    main -- Main routine
"""

import sys
import argparse

from dewyatochka.core.application import Application as BaseApplication
from dewyatochka.core.application import EXIT_CODE_TERM
from dewyatochka.core.log import get_console_logger
from dewyatochka.core.plugin.subsystem.control.network import DEFAULT_SOCKET_PATH
from dewyatochka.core.plugin.subsystem.control.service import ClientService

__all__ = ['Application', 'main']


class Application(BaseApplication):
    """ dewyatochkactl impl """

    @staticmethod
    def _parse_args(args: list) -> tuple:
        """ Parse known arguments

        :param list args:
        :return tuple:
        """
        args_parser = argparse.ArgumentParser()
        args_parser.add_argument('command',
                                 metavar='command',
                                 help='Command name(s) comma separated. Run dewyatochkactl list to see them')
        args_parser.add_argument('--socket',
                                 help='Path to daemon\'s control socket',
                                 default=DEFAULT_SOCKET_PATH)

        params, cmd_args = args_parser.parse_known_args(args[1:])
        parsed_args = dict(arg.split('=', 2) for arg in cmd_args)

        return params, parsed_args

    def _init(self):
        """ Init dependent services

        :return None:
        """
        self.depend(get_console_logger(self))
        self.depend(ClientService)

    def _run(self, socket: str, command: str, optional: dict):
        """ Actually run app

        :param str socket:
        :param str command:
        :param dict optional:
        :return None:
        """
        try:
            client = self.registry.control_client

            client.socket = socket
            client.communicate(command, optional)

        except Exception as e:
            raise RuntimeError('Failed to communicate with daemon process at %s: %s' % (socket or '[DEFAULT]', e))

    def run(self, args: list):
        """ Run application

        :param list args: Console arguments
        :return None:
        """
        try:
            params, cmd_args = self._parse_args(args)

            self._init()
            self._run(params.socket, params.command, cmd_args)

        except (KeyboardInterrupt, SystemExit):
            self.stop(EXIT_CODE_TERM)

        except Exception as e:
            self.fatal_error(__name__, e)

        finally:
            sys.exit(self._exit_code)


def main():
    """ Main routine

    :return None:
    """
    app = Application()
    app.run(sys.argv)
