# -*- coding: UTF-8

""" Dewyatochka daemon app (dewyatochkad)

Serves conferences and takes a talk with other people

Modules
=======
    application -- Main application implementation
    process     -- Main services implementation

Functions
=========
    main -- Main routine
"""

import argparse
import sys

from dewyatochka.core.application import EXIT_CODE_ERROR
from dewyatochka.core.log import get_daemon_logger
from dewyatochka.core.config import get_common_config, get_conferences_config, get_extensions_config
from dewyatochka.core.config.factory import COMMON_CONFIG_DEFAULT_PATH
from dewyatochka.core.network.xmpp import service as xmpp
from dewyatochka.core.plugin.loader import LoaderService
from dewyatochka.core.plugin.subsystem.message import service as m_service
from dewyatochka.core.plugin.subsystem.helper import service as h_service
from dewyatochka.core.plugin.subsystem.control import service as c_service

from . import application as application_
from . import process

__all__ = ['main', 'application', 'process']


def main(argv=None):
    """ Main routine

    :param list argv:
    :return None:
    """
    try:
        args_parser = argparse.ArgumentParser()
        args_parser.add_argument('--config',
                                 help='Path to config file to use',
                                 default=COMMON_CONFIG_DEFAULT_PATH)
        args_parser.add_argument('--nodaemon',
                                 help='Do not detach process from console',
                                 action='store_true')
        args_parser.add_argument('--pidfile',
                                 help='Path to lock-file',
                                 default=None)
        args = args_parser.parse_args((sys.argv if argv is None else argv)[1:])

        application = application_.DaemonApplication()

        application.depend(get_common_config(application, args.config))
        application.depend(get_daemon_logger(application, args.nodaemon))
        application.depend(get_conferences_config(application))
        application.depend(get_extensions_config(application))

        application.depend(LoaderService)
        application.depend(m_service.Service)
        application.depend(h_service.Service)
        application.depend(c_service.Service)

        application.depend(process.Bootstrap)
        application.depend(process.Scheduler)
        application.depend(process.Daemon)
        application.depend(process.Control)
        application.depend(process.ChatManager, 'bot')
        application.depend(xmpp.XMPPConnectionManager)

    except Exception as bootstrap_error:
        print('Error starting service: %s' % bootstrap_error, file=sys.stderr)
        sys.exit(EXIT_CODE_ERROR)

    application.run([args.nodaemon, args.pidfile])
