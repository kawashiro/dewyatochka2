# coding=utf-8

"""
Tests suite for dewyatochka.core.log.output
"""

import sys
import unittest
import logging
from unittest.mock import patch, PropertyMock
from dewyatochka.core.log import Logger
from dewyatochka.core.log.output import *
from testlib.application import VoidApplication


class TestSTDOUTHandler(unittest.TestCase):
    """
    dewyatochka.core.log.output.STDOUTHandler
    """

    def test_create_handler(self):
        """
        Test inner handler instantiation
        """
        handler = STDOUTHandler(Logger(VoidApplication()))

        self.assertIsInstance(handler.handler, logging.StreamHandler)
        self.assertEqual(sys.stdout, handler.handler.stream)


class TestFileHandler(unittest.TestCase):
    """
    dewyatochka.core.log.output.FileHandler
    """

    @patch.object(Logger, 'config', new_callable=PropertyMock)
    def test_create_handler(self, config_property):
        """
        Test inner handler instantiation
        """
        config_property.return_value = {'file': '/file/path.log'}
        handler = FileHandler(Logger(VoidApplication()))

        self.assertIsInstance(handler.handler, logging.FileHandler)
        self.assertEqual('/file/path.log', handler.handler.baseFilename)

    @patch.object(Logger, 'config', new_callable=PropertyMock)
    def test_create_handler_default(self, config_property):
        """
        Test inner handler instantiation with empty config
        """
        config_property.return_value = {}
        handler = FileHandler(Logger(VoidApplication()))

        self.assertEqual(FileHandler.DEFAULT_FILE, handler.handler.baseFilename)
