# -*- coding: UTF-8

"""
Logger output implementations
"""

__all__ = ['STDOUTHandler', 'FileHandler']

import sys
import logging
from dewyatochka.core.log import Handler


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
