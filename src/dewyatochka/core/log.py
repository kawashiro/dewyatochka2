# -*- coding: UTF-8

"""
Logger implementation
"""

__all__ = ['STDOUTHandler', 'FileHandler']

from dewyatochka.core.application import Service
from dewyatochka.core.config import GlobalConfig
import sys
import logging
from abc import ABCMeta, abstractmethod


class LogHandlerWrapper(Service, metaclass=ABCMeta):
    """
    Wrapper over log handler to use it as an application service
    """

    # Handler instance
    _handler = None

    def __init__(self, application):
        """
        Init logger service
        :param application: Application
        """
        super().__init__(application)
        self.handler.setFormatter(logging.Formatter('%(asctime)s:' + logging.BASIC_FORMAT))

    def __getattr__(self, item):
        """
        Inherit inner handler methods/properties
        :return:
        """
        return getattr(self.handler, item)

    @property
    def handler(self):
        """
        Get handler instance
        :return: logging.Handler
        """
        if not self._handler:
            self._handler = logging.StreamHandler(stream=sys.stdout)

        return self._handler

    @abstractmethod
    def _create_handler(self):
        """
        Create new handler instance
        :return: logging.Handler
        """
        pass


class STDOUTHandler(LogHandlerWrapper):
    """
    Simple console logger
    """
    def _create_handler(self):
        """
        Create new handler instance
        :return: logging.Handler
        """
        return logging.StreamHandler(stream=sys.stdout)


class FileHandler(LogHandlerWrapper):
    """
    File logger
    """
    def _create_handler(self):
        """
        Create new handler instance
        :return: logging.Handler
        """
        log_file = self.config.section('global').get('log_file', GlobalConfig.DEFAULT_LOG_FILE)
        return logging.FileHandler(log_file)
