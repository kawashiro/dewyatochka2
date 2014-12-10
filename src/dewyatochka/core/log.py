# -*- coding: UTF-8

"""
Logger implementation
"""

from abc import ABCMeta, abstractmethod
from dewyatochka.core.application import Service
import sys
import threading

# Predefined log levels
LEVEL_NONE = 0
LEVEL_ERROR = 10
LEVEL_WARN = 100
LEVEL_INFO = 1000
LEVEL_DEBUG = 10000


class Logger(Service, metaclass=ABCMeta):
    """
    Abstract logger
    """
    def write(self, message, level=LEVEL_INFO):
        """
        Write message if needed
        :param message:
        :param level:
        :return: void
        """
        lock = threading.RLock()
        lock.acquire()
        app_log_level = self.application.config.global_section.get('log_level', LEVEL_INFO)
        if app_log_level >= level:
            self._do_write(message, level)

        lock.release()

    @abstractmethod
    def _do_write(self, message, level):
        """
        Implement message output
        :param message: str
        :param level: int
        :return: void
        """
        pass

    def __lshift__(self, other):
        """
        Implement << operator (op-pa ++ style ^^)
        :param other: str
        :return: void
        """
        self.write(other)


class Console(Logger):
    """
    Simple console logger
    """
    def _do_write(self, message, level):
        """
        Implement message output
        :param message: str
        :param level: int
        :return: void
        """
        print(message, file=sys.stdout if level >= LEVEL_INFO else sys.stderr)
