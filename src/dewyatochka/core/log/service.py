# -*- coding: UTF-8

""" Logging app service implementation

Classes
=======
    LoggingService -- Logging app service
"""

__all__ = ['LoggingService']

import logging

from dewyatochka.core.application import Service


class LoggingService(Service):
    """ Logging app service """

    def register_handler(self, handler):
        """ Register global handler for compatibility with third-party libs

        :param Handler handler: Instance of dewyatochka.core.log.output.Handler
        :return None:
        """
        logger = logging.getLogger()
        logger.setLevel(self.config.get('level', logging.INFO))

        logger.handlers = []
        logger.addHandler(handler)

    def fatal_error(self, module_name: str, exception: Exception):
        """ Log fatal error message

        :param str module_name: Module name to display in log
        :param Exception exception: Exception instance
        :return None:
        """
        message = '%s failed: %s'
        logger = self(module_name)
        logger.critical(message, module_name, exception)

        if logger.level < logging.INFO:
            logger.exception(message, module_name, exception)

    @classmethod
    def name(cls) -> str:
        """ Get service unique name

        :return str:
        """
        return 'log'

    def __call__(self, name=None) -> logging.Logger:
        """ Get global logger instance by name

        :param str name: Module name to display in log
        :return logging.Logger:
        """
        return logging.getLogger(name)
