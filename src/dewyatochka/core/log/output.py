# -*- coding: UTF-8

""" Log output handlers implementation

Classes
=======
    Handler       -- Abstract output handler
    STDOUTHandler -- Console output handler
    FileHandler   -- Text file output handler
    NullHandler   -- Empty handler (stub)
"""

import sys
import logging
import fcntl
import termios
import struct
from abc import ABCMeta, abstractmethod
from threading import Lock

from .service import LEVEL_PROGRESS, LEVEL_NAME_PROGRESS

__all__ = ['Handler', 'STDOUTHandler', 'FileHandler', 'NullHandler']


class Handler(metaclass=ABCMeta):
    """ Abstract output handler

    Wrapper over log handler to be sure
    to use single custom output format
    for any output stream
    """

    def __init__(self, log_format: str):
        """ Set logging service

        :param str log_format:
        """
        self._handler = self._create_handler()
        self._handler.setFormatter(logging.Formatter(log_format))

        self._lock = Lock()

    def __getattr__(self, item):
        """ Inherit inner handler methods/properties

        :returns: Depending on inner method attributes
        """
        return getattr(self.handler, item)

    @property
    def __in_cr_mode(self) -> bool:
        """ Check if logger is in \r mode now

        :return bool:
        """
        return self.handler.terminator == '\r'

    def __enable_cr_mode(self):
        """ Enable \r mode

        :return None:
        """
        self.handler.terminator = '\r'

    def __disable_cr_mode(self):
        """ Return to \n mode

        :return None:
        """
        self.handler.terminator = '\n'

    @property
    def __terminal_width(self) -> int:
        """ Get terminal width

        :return int:
        """
        winsize = fcntl.ioctl(self.handler.stream.fileno(), termios.TIOCGWINSZ, struct.pack('HH', 0, 0))
        return struct.unpack('HH', winsize)[1]

    def handle(self, record: logging.LogRecord):
        """ Do whatever it takes to actually log the specified logging record.

        :param logging.LogRecord record: Log record instance to emit
        :return None:
        """
        with self._lock:
            if record.levelno == LEVEL_PROGRESS:
                record.levelname = LEVEL_NAME_PROGRESS
                self.__enable_cr_mode()
                try:
                    padding = ' ' * (self.__terminal_width - len(self.handler.format(record)))
                except:
                    padding = ''
                record.msg += padding

            elif self.__in_cr_mode:
                self.__disable_cr_mode()
                self.handler.stream.write(self.handler.terminator)

            self.handler.handle(record)

    @property
    def handler(self):
        """ Get inner handler instance

        :return logging.Handler:
        """
        return self._handler

    @abstractmethod
    def _create_handler(self) -> logging.StreamHandler:  # pragma: no cover
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

    def __init__(self, log_format: str, file_path: str):
        """ Set logging service

        :param str log_format:
        :param str file_path:
        """
        self._file = file_path
        super().__init__(log_format)

    def _create_handler(self) -> logging.StreamHandler:
        """ Create new inner handler instance

        :return logging.Handler:
        """
        return logging.FileHandler(self._file, delay=True)


class NullHandler(Handler):
    """ Empty handler (stub) """

    def _create_handler(self) -> logging.StreamHandler:
        """ Create new inner handler instance

        :return logging.Handler:
        """
        return logging.NullHandler()
