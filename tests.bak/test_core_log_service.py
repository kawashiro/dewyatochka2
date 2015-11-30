# -*- coding=utf-8

""" Tests suite for dewyatochka.core.log """

import logging

import unittest
from unittest.mock import patch, Mock, call, PropertyMock

from dewyatochka.core.log.service import LoggingService as Logger
from dewyatochka.core.log.output import NullHandler
from dewyatochka.core.application import VoidApplication


class TestLogger(unittest.TestCase):
    """ Covers dewyatochka.core.log.service.LoggingService """

    @patch.object(Logger, 'config')
    def test_register_handler(self, config_property):
        """ Test log handler registration """
        config_property.__getitem__ = Mock(side_effect=(logging.ERROR, logging.ERROR))

        logger = Logger(VoidApplication())
        handler = NullHandler('')
        logger.register_handler(handler)

        root_logger = logging.getLogger()
        self.assertEqual(logging.ERROR, root_logger.level)
        self.assertEqual([handler], root_logger.handlers)

        config_property.__getitem__.assert_has_calls([call('level')])

    @patch('logging.getLogger')
    def test_fatal_error(self, get_logger):
        """ Test fatal errors logging """
        module = 'test_module'
        exception = Exception('Test uncaught exception')
        message = '%s failed: %s'

        module_logger1 = PropertyMock()
        module_logger1.level = logging.INFO
        module_logger2 = PropertyMock()
        module_logger2.level = logging.DEBUG
        get_logger.side_effect = (module_logger1, module_logger2)

        logger = Logger(VoidApplication())
        logger._global_level = logging.INFO
        logger.fatal_error(module, exception)
        logger._global_level = logging.DEBUG
        logger.fatal_error(module, exception)

        get_logger.assert_has_calls([call(module), call(module)])
        module_logger1.critical.assert_called_once_with(str(exception))
        self.assertEqual(0, module_logger1.exception.call_count)
        self.assertEqual(0, module_logger2.critical.call_count)
        module_logger2.exception.assert_called_once_with(str(exception))

    @patch('logging.getLogger')
    def test_call(self, get_logger):
        """ Test __call__() magic method """
        module = 'test_module'
        Logger(VoidApplication())(module)
        get_logger.assert_called_once_with(module)

    def test_name(self):
        """ Test service name getter """
        self.assertEqual('log', Logger.name())