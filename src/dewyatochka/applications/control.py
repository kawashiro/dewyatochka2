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
from dewyatochka.core.plugin.subsystem.control.network import Client, Message, DEFAULT_SOCKET_PATH

__all__ = ['Application', 'main']


class Application(BaseApplication):
    """ dewyatochkactl impl """

    @staticmethod
    def __parse_args(args: list) -> tuple:
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

        return args_parser.parse_known_args(args[1:])

    def __communicate(self, socket: str, command: str, optional: dict):
        """ Communicate with daemon

        :param str socket:
        :param str command:
        :param dict optional:
        :return None:
        """
        log = self.registry.log(__name__)

        with Client(socket) as ctl_client:
            ctl_client.send(Message(name=command, args=optional or {}))

            for msg in ctl_client.input:
                if msg.error:
                    log.error('Server error: %s', msg.error)

                elif msg.text:
                    print(msg.text)

                else:
                    log.error('Unhandled message: %s', str(msg.data))

    def run(self, args: list):
        """ Run application

        :param list args: Console arguments
        :return None:
        """
        try:
            params, cmd_args = self.__parse_args(args)

            self.depend(get_console_logger(self))

            try:
                parsed_args = dict(arg.split('=', 2) for arg in cmd_args)
                self.__communicate(params.socket, params.command, parsed_args)
            except Exception as e:
                raise RuntimeError(
                    'Failed to communicate with daemon process at %s: %s' % (params.socket or '[DEFAULT]', e)
                )

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
