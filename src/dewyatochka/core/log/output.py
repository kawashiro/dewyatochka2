# -*- coding: UTF-8

"""
Logger output implementations
"""

__all__ = ['Handler', 'STDOUTHandler', 'FileHandler', 'NullHandler']

import sys
import logging
from abc import ABCMeta, abstractmethod
from dewyatochka.core.log.service import LoggingService


class Handler(metaclass=ABCMeta):
    """
    Wrapper over log handler to be sure to use single custom output format for any output stream
    """

    def __init__(self, logger: LoggingService):
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
    def _create_handler(self) -> logging.Handler:  # pragma: no cover
        """
        Create new handler instance
        :return: logging.Handler
        """
        pass


class STDOUTHandler(Handler):
    """
    Simple console logger
    """

    def _create_handler(self) -> logging.Handler:
        """
        Create new handler instance
        :return: logging.Handler
        """
        return logging.StreamHandler(stream=sys.stdout)


class FileHandler(Handler):
    """
    File logger
    """

    # Default path to the log file
    DEFAULT_FILE = '/var/log/dewyatochka2/dewyatochkad.log'

    def _create_handler(self) -> logging.Handler:
        """
        Create new handler instance
        :return: logging.Handler
        """
        log_file = self._logger.config.get('file', self.DEFAULT_FILE)
        return logging.FileHandler(log_file, delay=True)


class NullHandler(Handler):
    """
    NULL handler wrapper
    """

    def _create_handler(self) -> logging.Handler:
        """
        Create new handler instance
        :return: logging.Handler
        """
        return logging.NullHandler()
