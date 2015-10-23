# -*- coding=utf-8

""" Tests suite for dewyatochka.core.log.factory """

import logging

import unittest
from unittest.mock import patch

from dewyatochka.core.log.factory import *
from dewyatochka.core.log.output import STDOUTHandler, FileHandler, NullHandler
from dewyatochka.core.log.service import LoggingService
from dewyatochka.core.config.container import CommonConfig
from dewyatochka.core.config.source import virtual
from dewyatochka.core.application import VoidApplication


class TestDaemonLoggerFactory(unittest.TestCase):
    """ Tests suite for dewyatochka.core.log.factory.get_daemon_logger """

    @patch.object(logging.Logger, 'info')
    def test_create_stdout_logger(self, info_method_mock):
        """ Test STDOUT logger instantiation """
        application = VoidApplication()
        application.depend(CommonConfig)

        application.registry.config.load(virtual.Empty())
        logger = get_daemon_logger(application, use_stdout=True)

        info_method_mock.assert_called_once_with('Logging started')
        self.assertIsInstance(logging.getLogger().handlers[0], STDOUTHandler)
        self.assertIsInstance(logger, LoggingService)

    @patch.object(logging.Logger, 'info')
    def test_create_file_logger(self, info_method_mock):
        """ Test file logger instantiation """
        application = VoidApplication()
        application.depend(CommonConfig)

        # Normal
        application.registry.config.load(virtual.Predefined({'log': {'file': '/default.log'}}))
        logger = get_daemon_logger(application)
        info_method_mock.assert_called_once_with('Logging started')
        self.assertIsInstance(logging.getLogger().handlers[0], FileHandler)
        self.assertIsInstance(logger, LoggingService)
        self.assertEqual(logging.getLogger().handlers[0].baseFilename, '/default.log')

        # Default file
        application.registry.config.load(virtual.Empty())
        get_daemon_logger(application)
        self.assertEqual(logging.getLogger().handlers[0].baseFilename, '/var/log/dewyatochka/dewyatochkad.log')

        # On error
        info_method_mock.side_effect = Exception('Something wrong')
        get_daemon_logger(application)
        self.assertIsInstance(logging.getLogger().handlers[0], NullHandler)


class TestConsoleLoggerFactory(unittest.TestCase):
    """ Tests suite for dewyatochka.core.log.factory.get_console_logger """

    def test_create_stdout_logger(self):
        """ Test STDOUT logger instantiation """
        application = VoidApplication()
        application.depend(CommonConfig)

        logger = get_console_logger(application)
        self.assertIsInstance(logging.getLogger().handlers[0], STDOUTHandler)
        self.assertIsInstance(logger, LoggingService)
