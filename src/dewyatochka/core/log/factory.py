# -*- coding: UTF-8

""" Subroutines to create and configure appropriate logger instance

Functions
=========
    get_daemon_logger  -- Get configured logger instance for daemonizeable apps
    get_console_logger -- Get console app logger
"""

from dewyatochka.core.application import Application

from .service import LoggingService
from .output import *

__all__ = ['get_daemon_logger', 'get_console_logger']

# Default path to the log file
_DEFAULT_LOG_FILE_PATH = '/var/log/dewyatochka/dewyatochkad.log'

# Default message on logging start
_INIT_MESSAGE = 'Logging started'

# Log line formats
_FORMAT_DAEMON_DEFAULT = '%(asctime)s :: %(levelname)-8s :: [%(name)s] %(message)s'
_FORMAT_CONSOLE_DEFAULT = '%(levelname)s: %(message)s'


def get_daemon_logger(application: Application, use_stdout=False) -> LoggingService:
    """ Get configured logger instance for daemonizeable apps

    :param Application application: Application instance to configure logger for
    :param bool use_stdout: Set to True to use STDOUT instead of log file configured
    :return LoggingService:
    """
    logger = LoggingService(application)

    log_format = _FORMAT_DAEMON_DEFAULT
    log_file = application.registry.config.section('log').get('file', _DEFAULT_LOG_FILE_PATH)

    try:
        handler = STDOUTHandler(log_format) if use_stdout else FileHandler(log_format, log_file)
        logger.register_handler(handler)
        logger().info(_INIT_MESSAGE)
    except:
        # Something wrong with default log handler using null as a fallback
        logger.register_handler(NullHandler(log_format))

    return logger


def get_console_logger(application: Application) -> LoggingService:
    """ Get console app logger

    :param Application application: App instance
    :return LoggingService:
    """
    logger = LoggingService(application)
    logger.register_handler(STDOUTHandler(_FORMAT_CONSOLE_DEFAULT))

    return logger
