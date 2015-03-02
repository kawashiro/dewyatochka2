# -*- coding: UTF-8

""" Logging implementation

Modules
=======
    output  -- Log output handlers implementation
    service -- Logging app service implementation

Functions
=========
    get_logger      -- Get configured logger instance
    get_null_logger -- Get null logger
"""

__all__ = ['service', 'output', 'get_logger', 'get_null_logger']

from dewyatochka.core.application import Application

from .service import LoggingService
from .output import *


# Default message on logging start
_INIT_MESSAGE = 'Logging started'


def get_logger(application: Application, has_stdout=True) -> LoggingService:
    """ Get configured logger instance

    :param Application application: Application instance to configure logger for
    :param bool has_stdout: Set to True if application has stdout to attach stdout handler instead of file one
    :return LoggingService:
    """
    logger = LoggingService(application)

    try:
        logger.register_handler(STDOUTHandler(logger) if has_stdout else FileHandler(logger))
        logger().info(_INIT_MESSAGE)
    except:
        # Something wrong with default log handler using null as a fallback
        logger.register_handler(NullHandler(logger))

    return logger


def get_null_logger(application: Application) -> LoggingService:
    """ Get null logger

    :param Application application: App instance
    :return LoggingService:
    """
    logger = LoggingService(application)
    logger.register_handler(NullHandler(logger))

    return logger
