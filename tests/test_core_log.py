# coding=utf-8

"""
Tests suite for dewyatochka.core.log
"""

import unittest
import logging
from unittest.mock import patch, Mock, call, PropertyMock
from dewyatochka.core.log import Logger
from testlib.log import *
from testlib.application import VoidApplication


class TestLogger(unittest.TestCase):
    """
    dewyatochka.core.log.Logger
    """

    @patch.object(Logger, 'config')
    def test_register_handler(self, config_property):
        """
        Test log handler registration
        """
        config_property.get = Mock(side_effect=(logging.ERROR,))

        logger = Logger(VoidApplication())
        handler = NullHandler(logger)
        logger.register_handler(handler)

        root_logger = logging.getLogger()
        self.assertEqual(logging.ERROR, root_logger.level)
        self.assertEqual([handler], root_logger.handlers)

        config_property.get.assert_called_once_with('level', logging.INFO)

    @patch('logging.getLogger')
    def test_fatal_error(self, get_logger):
        """
        Test fatal errors logging
        """
        module = 'test_module'
        exception = Exception('Test uncaught exception')
        message = '%s failed: %s'

        module_logger1 = PropertyMock()
        module_logger1.level = logging.INFO
        module_logger2 = PropertyMock()
        module_logger2.level = logging.DEBUG
        get_logger.side_effect = (module_logger1, module_logger2)

        logger = Logger(VoidApplication())
        logger.fatal_error(module, exception)
        logger.fatal_error(module, exception)

        get_logger.assert_has_calls([call(module), call(module)])
        module_logger1.critical.assert_called_once_with(message, module, exception)
        self.assertEqual(0, module_logger1.exception.call_count)
        module_logger2.critical.assert_called_once_with(message, module, exception)
        module_logger2.exception.assert_called_once_with(message, module, exception)

    @patch('logging.getLogger')
    def test_call(self, get_logger):
        """
        Test __call__() magic method
        """
        module = 'test_module'
        Logger(VoidApplication())(module)
        get_logger.assert_called_once_with(module)

    def test_name(self):
        """
        Test service name getter
        """
        self.assertEqual('log', Logger.name())


class TestHandler(unittest.TestCase):
    """
    dewyatochka.core.log.Handler
    """

    def test_init(self):
        """
        Test initializer
        """
        logger = Logger(VoidApplication())
        handler = NullHandler(logger)

        self.assertEqual(handler._logger, logger)
        self.assertEqual('%(asctime)s:%(levelname)s:%(name)s:%(message)s', handler.handler.formatter._fmt)

    def test_getattr(self):
        """
        Test inner handler attribute getter
        """
        self.assertIsNotNone(NullHandler(Logger(VoidApplication())).format)

    def test_handler_property(self):
        """
        Test inner handler getter
        """
        handler = NullHandler(Logger(VoidApplication()))

        self.assertIsInstance(handler.handler, logging.NullHandler)
        self.assertEqual(handler.handler, handler.handler)
