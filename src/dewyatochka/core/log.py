# -*- coding: UTF-8

"""
Logger implementation
"""

__all__ = ['ConsoleHandler', 'TempFileHandler']

from dewyatochka.core.application import Service
import sys
import logging


class ConsoleHandler(Service, logging.StreamHandler):
    """
    Simple console logger
    """
    def __init__(self, application):
        """
        Initialize logger instance with stdout output
        :param application:
        :return:
        """
        Service.__init__(self, application)
        logging.StreamHandler.__init__(self, sys.stdout)

        self.setFormatter(logging.Formatter('%(asctime)s:' + logging.BASIC_FORMAT))


class TempFileHandler(Service, logging.FileHandler):  # TODO: Temporary, created for quick installation test
    """
    Simple console logger
    """
    def __init__(self, application):
        """
        Initialize logger instance with stdout output
        :param application:
        :return:
        """
        Service.__init__(self, application)
        logging.FileHandler.__init__(self, '/var/tmp/dewyatochka.log')

        self.setFormatter(logging.Formatter('%(asctime)s:' + logging.BASIC_FORMAT))
