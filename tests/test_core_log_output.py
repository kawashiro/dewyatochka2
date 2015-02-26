# -*- coding=utf-8

""" Tests suite for dewyatochka.core.log.output """

import sys
import logging

import unittest
from unittest.mock import patch, PropertyMock, Mock

from dewyatochka.core.log.service import LoggingService as Logger
from dewyatochka.core.log.output import *


class TestAbstractHandler(unittest.TestCase):
    """ Covers dewyatochka.core.log.output.Handler """

    def test_init(self):
        """ Test initializer """
        app = Mock()
        app.registry.config.section.side_effect = {'level': 'INFO'}, {'level': 'DEBUG'}
        logger = Logger(app)

        handler = NullHandler(logger)
        self.assertEqual(handler._logger, logger)
        self.assertEqual('%(asctime)s :: %(levelname)-8s :: %(message)s', handler.handler.formatter._fmt)

        handler = NullHandler(logger)
        self.assertEqual(handler._logger, logger)
        self.assertEqual('%(asctime)s :: %(levelname)-8s :: %(name)s :: %(message)s', handler.handler.formatter._fmt)


    def test_getattr(self):
        """ Test inner handler attribute getter """
        self.assertIsNotNone(NullHandler(Logger(Mock())).format)

    def test_handler_property(self):
        """ Test inner handler getter """
        handler = NullHandler(Logger(Mock()))

        self.assertIsInstance(handler.handler, logging.NullHandler)
        self.assertEqual(handler.handler, handler.handler)


class TestSTDOUTHandler(unittest.TestCase):
    """ Covers dewyatochka.core.log.output.STDOUTHandler """

    def test_create_handler(self):
        """ Test inner handler instantiation """
        handler = STDOUTHandler(Logger(Mock()))

        self.assertIsInstance(handler.handler, logging.StreamHandler)
        self.assertEqual(sys.stdout, handler.handler.stream)


class TestFileHandler(unittest.TestCase):
    """ Covers dewyatochka.core.log.output.FileHandler """

    @patch.object(Logger, 'config', new_callable=PropertyMock)
    def test_create_handler(self, config_property):
        """ Test inner handler instantiation """
        config_property.return_value = {'file': '/file/path.log'}
        handler = FileHandler(Logger(Mock()))

        self.assertIsInstance(handler.handler, logging.FileHandler)
        self.assertEqual('/file/path.log', handler.handler.baseFilename)

    @patch.object(Logger, 'config', new_callable=PropertyMock)
    def test_create_handler_default(self, config_property):
        """ Test inner handler instantiation with empty config """
        config_property.return_value = {}
        handler = FileHandler(Logger(Mock()))

        self.assertEqual(FileHandler.DEFAULT_FILE, handler.handler.baseFilename)


class TestNullHandler(unittest.TestCase):
    """ Covers dewyatochka.core.log.output.STDOUTHandler """

    def test_create_handler(self):
        """ Test inner handler instantiation """
        self.assertIsInstance(NullHandler(Logger(Mock())).handler, logging.NullHandler)
