# -*- coding: UTF-8

"""
Logger implementation
"""

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
