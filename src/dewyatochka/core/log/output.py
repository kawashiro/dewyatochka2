# -*- coding: UTF-8

""" Log output handlers implementation

Classes
=======
    Handler       -- Abstract output handler
    STDOUTHandler -- Console output handler
    FileHandler   -- Text file output handler
    NullHandler   -- Empty handler (stub)
"""

__all__ = ['Handler', 'STDOUTHandler', 'FileHandler', 'NullHandler']

import sys
from abc import ABCMeta, abstractmethod
import logging

from dewyatochka.core.log.service import LoggingService


class Handler(metaclass=ABCMeta):
    """ Abstract output handler

    Wrapper over log handler to be sure
    to use single custom output format
    for any output stream
    """

    def __init__(self, logger: LoggingService):
        """ Set logging service

        :param LoggingService logger:
        """
        self._logger = logger
        self._handler = None

        log_format = '%(asctime)s :: %(levelname)-8s :: %(name)s :: %(message)s' \
                     if logger.logging_level == 'DEBUG' else \
                     '%(asctime)s :: %(levelname)-8s :: %(message)s'
        self.handler.setFormatter(logging.Formatter(log_format))

    def __getattr__(self, item):
        """ Inherit inner handler methods/properties

        :returns: Depending on inner method attributes
        """
        return getattr(self.handler, item)

    @property
    def handler(self) -> logging.Handler:
        """ Get inner handler instance

        :return logging.Handler:
        """
        if not self._handler:
            self._handler = self._create_handler()

        return self._handler

    @abstractmethod
    def _create_handler(self) -> logging.Handler:  # pragma: no cover
        """ Create new inner handler instance

        :return logging.Handler:
        """
        pass


class STDOUTHandler(Handler):
    """ Console output handler """

    def _create_handler(self) -> logging.Handler:
        """ Create new inner handler instance

        :return logging.Handler:
        """
        return logging.StreamHandler(stream=sys.stdout)


class FileHandler(Handler):
    """ Text file output handler """

    # Default path to the log file
    DEFAULT_FILE = '/var/log/dewyatochka2/dewyatochkad.log'

    def _create_handler(self) -> logging.Handler:
        """ Create new inner handler instance

        :return logging.Handler:
        """
        log_file = self._logger.config.get('file', self.DEFAULT_FILE)
        return logging.FileHandler(log_file, delay=True)


class NullHandler(Handler):
    """ Empty handler (stub) """

    def _create_handler(self) -> logging.Handler:
        """ Create new inner handler instance

        :return logging.Handler:
        """
        return logging.NullHandler()
