# -*- coding: UTF-8

"""
Logging package
"""

__all__ = ['service', 'output', 'get_logger']

from dewyatochka.core.application import Application
from .service import LoggingService
from .output import *

# Default message on logging start
_INIT_MESSAGE = 'Logging started'


def get_logger(application: Application, has_stdout=True) -> LoggingService:
    """
    Get logger instance
    :param application: Application
    :param has_stdout: bool
    :return: LoggingService
    """
    logger = LoggingService(application)

    try:
        logger.register_handler(STDOUTHandler(logger) if has_stdout else FileHandler(logger))
        logger().info(_INIT_MESSAGE)
    except:
        # Something wrong with default log handler using null as a fallback
        logger.register_handler(NullHandler(logger))

    return logger
