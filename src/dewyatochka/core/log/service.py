# -*- coding: UTF-8

""" Logging app service implementation

Classes
=======
    LoggingService -- Logging app service
"""

__all__ = ['LoggingService']

import logging

from dewyatochka.core.application import Application, Service


class LoggingService(Service):
    """ Logging app service """

    def __init__(self, application: Application):
        """ Initialize service & attach an application to it

        :param Application application:
        """
        super().__init__(application)
        self._global_level = logging.NOTSET

    def register_handler(self, handler):
        """ Register global handler for compatibility with third-party libs

        :param Handler handler: Instance of dewyatochka.core.log.output.Handler
        :return None:
        """
        logger = logging.getLogger()
        logger.setLevel(self.logging_level)
        self._global_level = logger.level

        logger.handlers = []
        logger.addHandler(handler)

    def fatal_error(self, module_name: str, exception: Exception):
        """ Log fatal error message

        :param str module_name: Module name to display in log
        :param Exception exception: Exception instance
        :return None:
        """
        logger = self(module_name)

        if self._global_level == logging.DEBUG:
            logger.exception(str(exception))
        else:
            logger.critical(str(exception))

    @property
    def logging_level(self) -> int:
        """ Get logging level

        :return int:
        """
        return self.config.get('level', 'INFO')

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
