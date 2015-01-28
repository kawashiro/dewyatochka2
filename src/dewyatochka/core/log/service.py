# -*- coding: UTF-8

"""
Common logging implementation
"""

__all__ = ['LoggingService']

import logging
from dewyatochka.core.application import Service


class LoggingService(Service):
    """
    Logging service
    """

    def register_handler(self, handler):
        """
        Register global handler for compatibility with third-party libs
        :param handler: Handler
        :return: void
        """
        logger = logging.getLogger()
        logger.setLevel(self.config.get('level', logging.INFO))

        logger.handlers = []
        logger.addHandler(handler)

    def fatal_error(self, module_name: str, exception: BaseException):
        """
        Log fatal error message
        :param module_name: str
        :param exception: BaseException
        :return: void
        """
        message = '%s failed: %s'
        logger = self(module_name)
        logger.critical(message, module_name, exception)

        if logger.level < logging.INFO:
            logger.exception(message, module_name, exception)

    @classmethod
    def name(cls) -> str:
        """
        Get service unique name
        :return: str
        """
        return 'log'

    def __call__(self, name=None) -> logging.Logger:
        """
        Get global logger instance by name
        :param name: str
        :return: logging.Logger
        """
        return logging.getLogger(name)
