# -*- coding: UTF-8

""" Subroutines to create and configure appropriate logger instance

Functions
=========
    get_daemon_logger  -- Get configured logger instance for daemonizeable apps
    get_console_logger -- Get console app logger
"""

__all__ = ['get_daemon_logger', 'get_console_logger']

from dewyatochka.core.application import Application

from .service import LoggingService
from .output import *


# Default message on logging start
_INIT_MESSAGE = 'Logging started'

# Log line formats
_FORMAT_DAEMON_DEFAULT = '%(asctime)s :: %(levelname)-8s :: %(message)s'
_FORMAT_DAEMON_DEBUG = '%(asctime)s :: %(levelname)-8s :: %(name)s :: %(message)s'
_FORMAT_CONSOLE_DEFAULT = '%(levelname).1s: %(message)s'
_FORMAT_CONSOLE_DEBUG = _FORMAT_DAEMON_DEBUG


def get_daemon_logger(application: Application, file=None) -> LoggingService:
    """ Get configured logger instance for daemonizeable apps

    :param Application application: Application instance to configure logger for
    :param str file: Set to None if application has stdout to attach stdout handler instead of file one
    :return LoggingService:
    """
    logger = LoggingService(application)
    log_format = _FORMAT_DAEMON_DEBUG if logger.logging_level == 'DEBUG' else _FORMAT_DAEMON_DEFAULT

    try:
        logger.register_handler(STDOUTHandler(log_format) if file is None else FileHandler(log_format, file))
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
    log_format = _FORMAT_CONSOLE_DEBUG if logger.logging_level == 'DEBUG' else _FORMAT_CONSOLE_DEFAULT

    try:
        logger.register_handler(STDOUTHandler(log_format))
    except:
        # Something wrong with default log handler using null as a fallback
        logger.register_handler(NullHandler(log_format))

    return logger
