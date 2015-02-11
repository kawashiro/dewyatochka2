# -*- coding=utf-8

""" Tests suite for dewyatochka.core.log.get_logger """

import logging

import unittest
from unittest.mock import patch

from dewyatochka.core.log.output import *
from dewyatochka.core.config.container import CommonConfig
from dewyatochka.core.config.source.virtual import Empty as EmptySource
from dewyatochka.core.application import VoidApplication
from dewyatochka.core.log import get_logger


class TestGetLogger(unittest.TestCase):
    """ Covers dewyatochka.core.log.get_logger """

    @patch.object(logging.Logger, 'info')
    def test_get_stdout_logger(self, info_method):
        """ Get stdout logger """
        app = VoidApplication()
        app.registry.add_service(CommonConfig(app).load(EmptySource()))

        logger = get_logger(app)
        self.assertIsInstance(logger().handlers[0], STDOUTHandler)
        info_method.assert_called_once_with('Logging started')

    @patch.object(logging.Logger, 'info')
    def test_get_file_logger(self, info_method):
        """ Get stdout logger """
        app = VoidApplication()
        app.registry.add_service(CommonConfig(app).load(EmptySource()))

        logger = get_logger(app, has_stdout=False)
        self.assertIsInstance(logger().handlers[0], FileHandler)
        info_method.assert_called_once_with('Logging started')

    @patch.object(logging.Logger, 'info')
    def test_get_logger_fail(self, info_method):
        """ Get stdout logger """
        info_method.side_effect = Exception()

        app = VoidApplication()
        app.registry.add_service(CommonConfig(app).load(EmptySource()))

        logger = get_logger(app)
        self.assertIsInstance(logger().handlers[0], NullHandler)
        info_method.assert_called_once_with('Logging started')
