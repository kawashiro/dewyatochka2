# -*- coding: UTF-8

"""
Logging package
"""

__all__ = ['Logger', 'Handler', 'output']

import logging
from abc import ABCMeta, abstractmethod
from dewyatochka.core.application import Service


class Logger(Service):
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


class Handler(metaclass=ABCMeta):
    """
    Wrapper over log handler to be sure to use single custom output format for any output stream
    """

    def __init__(self, logger: Logger):
        """
        Init logger service
        :param logger: Logger
        """
        self._logger = logger
        self._handler = None

        self.handler.setFormatter(logging.Formatter('%(asctime)s:' + logging.BASIC_FORMAT))

    def __getattr__(self, item):
        """
        Inherit inner handler methods/properties
        :return:
        """
        return getattr(self.handler, item)

    @property
    def handler(self) -> logging.Handler:
        """
        Get handler instance
        :return: logging.Handler
        """
        if not self._handler:
            self._handler = self._create_handler()

        return self._handler

    @abstractmethod
    def _create_handler(self) -> logging.Handler:
        """
        Create new handler instance
        :return: logging.Handler
        """
        pass
