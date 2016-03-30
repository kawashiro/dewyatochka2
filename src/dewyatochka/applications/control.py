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
from dewyatochka.core.application import EXIT_CODE_TERM, EXIT_CODE_ERROR
from dewyatochka.core.log import get_console_logger
from dewyatochka.core.plugin.subsystem.control.network import DEFAULT_SOCKET_PATH
from dewyatochka.core.plugin.subsystem.control.service import ClientService

__all__ = ['Application', 'main']


class Application(BaseApplication):
    """ dewyatochkactl impl """

    def run(self, args: list):
        """ Run application

        :param list args: Console arguments
        :return None:
        """
        socket, command, optional = args

        try:
            client = self.registry.control_client

            client.socket = socket
            client.communicate(command, optional)

        except (KeyboardInterrupt, SystemExit):
            self.stop(EXIT_CODE_TERM)

        except Exception as e:
            self.registry.log(__name__).error(
                'Failed to communicate with daemon process at %s: %s', socket or '[DEFAULT]', e
            )
            self.stop(EXIT_CODE_ERROR)

        finally:
            sys.exit(self._exit_code)


def main(argv=None):
    """ Main routine

    :param list argv:
    :return None:
    """
    try:
        args_parser = argparse.ArgumentParser()
        args_parser.add_argument('command',
                                 metavar='command',
                                 help='Command name(s) comma separated. Run dewyatochkactl list to see them')
        args_parser.add_argument('--socket',
                                 help='Path to daemon\'s control socket',
                                 default=DEFAULT_SOCKET_PATH)

        params, cmd_args = args_parser.parse_known_args((sys.argv if argv is None else argv)[1:])
        parsed_cmd_args = dict(arg.split('=', 2) for arg in cmd_args)

        application = Application()

        application.depend(get_console_logger(application))
        application.depend(ClientService)

    except Exception as bootstrap_error:
        print('Fatal error: %s' % bootstrap_error, file=sys.stderr)
        sys.exit(EXIT_CODE_ERROR)

    application.run([params.socket, params.command, parsed_cmd_args])


if __name__ == '__main__':
    main()
