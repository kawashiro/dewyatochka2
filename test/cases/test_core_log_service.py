# -*- coding=utf-8

""" Tests suite for dewyatochka.core.log.service """

import logging

import unittest
from unittest.mock import patch, Mock

from dewyatochka.core.log.service import *
from dewyatochka.core.log.output import NullHandler
from dewyatochka.core.config.container import CommonConfig
from dewyatochka.core.config.source import virtual
from dewyatochka.core.application import VoidApplication


class TestLoggerWrapper(unittest.TestCase):
    """ Tests suite for dewyatochka.core.log.service.LoggerWrapper """

    def test_init(self):
        """ Test instantiation """
        logger = logging.Logger('foo')
        wrapper = LoggerWrapper(logger)

        self.assertEqual(wrapper.info, logger.info)

    def test_error(self):
        """ Test error handling """
        class _Logger(logging.Logger):
            error = Mock()
            exception = Mock()

        logger = _Logger('foo')
        wrapper = LoggerWrapper(logger)

        logger.level = logging.DEBUG
        wrapper.error('debug', 'arg1', kwarg1='kwarg1')
        logger.level = logging.INFO
        wrapper.error('info', 'arg2', kwarg2='kwarg2')

        logger.error.assert_called_once_with('info', 'arg2', kwarg2='kwarg2')
        logger.exception.assert_called_once_with('debug', 'arg1', kwarg1='kwarg1')

    def test_progress(self):
        """ Test process progress info logging """
        class _Logger(logging.Logger):
            log = Mock()

        logger = _Logger('foo')
        wrapper = LoggerWrapper(logger)

        wrapper.progress('progress', 'arg', kwarg='kwarg')
        logger.log.assert_called_once_with(LEVEL_PROGRESS, 'progress', 'arg', kwarg='kwarg')


class TestLoggingService(unittest.TestCase):
    """ Tests suite for dewyatochka.core.log.service.LoggingService

    Covers only :meth:`fatal_error`, cause other methods
    are already covered in .log.factory tests suite
    """
    def test_registration(self):
        """ Test global handler and logging service registration """
        null_handler = NullHandler('')

        application = VoidApplication()
        application.depend(CommonConfig)
        application.depend(LoggingService)

        application.registry.config.load(virtual.Predefined({'log': {}}))
        application.registry.log.register_handler(null_handler)
        self.assertEqual(logging.getLogger().handlers, [null_handler])
        self.assertEqual(logging.getLogger().level, logging.INFO)

        application.registry.config.load(virtual.Predefined({'log': {'level': 'ERROR'}}))
        application.registry.log.register_handler(null_handler)
        self.assertEqual(logging.getLogger().level, logging.ERROR)

    def test_call(self):
        """ Test invoking """
        service = LoggingService(VoidApplication())

        wrapper1 = service()
        self.assertIsInstance(wrapper1, LoggerWrapper)
        self.assertEqual(wrapper1.name, 'SVC::log')

        wrapper2 = service('foo')
        self.assertEqual(wrapper2.name, 'foo')

    @patch.object(logging.Logger, 'critical')
    @patch.object(logging.Logger, 'exception')
    def test_fatal_error(self, exception_mock, critical_mock):
        """ Test fatal error logging """
        application = VoidApplication()
        application.depend(CommonConfig)
        application.depend(LoggingService)

        application.registry.config.load(virtual.Predefined({'log': {'level': 'DEBUG'}}))
        application.registry.log.register_handler(NullHandler(''))
        application.registry.log.fatal_error('foo', Exception('Debug exception'))
        exception_mock.assert_called_with('Debug exception')

        application.registry.config.load(virtual.Predefined({'log': {'level': 'INFO'}}))
        application.registry.log.register_handler(NullHandler(''))
        application.registry.log.fatal_error('foo', Exception('Debug exception'))
        critical_mock.assert_called_with('Debug exception')
