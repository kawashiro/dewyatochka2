# -*- coding=utf-8

""" Tests suite for dewyatochka.core.log.factory """

import logging

import unittest
from unittest.mock import patch

from dewyatochka.core.log.output import *
from dewyatochka.core.config.container import CommonConfig
from dewyatochka.core.config.source.virtual import Empty as EmptySource
from dewyatochka.core.application import VoidApplication
from dewyatochka.core.log.factory import get_daemon_logger


class TestGetDaemonLogger(unittest.TestCase):
    """ Covers dewyatochka.core.log.factory.get_daemon_logger """

    @patch.object(logging.Logger, 'info')
    def test_get_stdout_logger(self, info_method):
        """ Get stdout logger """
        app = VoidApplication()
        app.registry.add_service(CommonConfig(app).load(EmptySource()))

        logger = get_daemon_logger(app)
        self.assertIsInstance(logger().handlers[0], STDOUTHandler)
        info_method.assert_called_once_with('Logging started')

    @patch.object(logging.Logger, 'info')
    def test_get_file_logger(self, info_method):
        """ Get file logger """
        app = VoidApplication()
        app.registry.add_service(CommonConfig(app).load(EmptySource()))

        logger = get_daemon_logger(app, file='/foo.txt')
        self.assertIsInstance(logger().handlers[0], FileHandler)
        info_method.assert_called_once_with('Logging started')

    @patch.object(logging.Logger, 'info')
    def test_get_logger_fail(self, info_method):
        """ Get null logger on fail """
        info_method.side_effect = Exception()

        app = VoidApplication()
        app.registry.add_service(CommonConfig(app).load(EmptySource()))

        logger = get_daemon_logger(app)
        self.assertIsInstance(logger().handlers[0], NullHandler)
        info_method.assert_called_once_with('Logging started')
