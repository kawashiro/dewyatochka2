# -*- coding=utf-8

""" Tests suite for dewyatochka.core.log.output """

import sys
import struct
import logging

import unittest
from unittest.mock import patch, Mock, call

from dewyatochka.core.log.output import *
from dewyatochka.core.log.service import LEVEL_PROGRESS, LEVEL_NAME_PROGRESS


# Log format stub
_LOG_FORMAT = '%(levelname)s: %(message)s'


class TestHandler(unittest.TestCase):
    """ Tests suite for dewyatochka.core.log.output.Handler """

    def test_init(self):
        """ Test inner handler initialization """
        class _Handler(Handler):
            def _create_handler(self):
                return logging.Handler()

        handler = _Handler(_LOG_FORMAT)
        self.assertIsInstance(handler.handler, logging.Handler)
        self.assertEqual(getattr(handler.formatter, '_fmt'), _LOG_FORMAT)
        self.assertEqual(handler.handler.formatter, handler.formatter)

    @patch('fcntl.ioctl')
    def test_handle(self, ioctl_mock):
        """ Test message handling """
        class _Handler(Handler):
            def _create_handler(self):
                return logging.StreamHandler(stream=handler_stream_mock)

        def _ioctl_side_effect(*_):
            nonlocal ioctl_side_effect_count
            if ioctl_side_effect_count == 2:
                raise Exception()
            ioctl_side_effect_count += 1
            return struct.pack('HH', 0, 25)
        ioctl_side_effect_count = 0

        handler_stream_mock = Mock()
        ioctl_mock.side_effect = _ioctl_side_effect

        records = map(logging.makeLogRecord, [
            {'levelno': logging.INFO, 'levelname': logging.getLevelName(logging.INFO), 'msg': 'info #1'},
            {'levelno': LEVEL_PROGRESS, 'levelname': LEVEL_NAME_PROGRESS, 'msg': 'progress #1_'},
            {'levelno': LEVEL_PROGRESS, 'levelname': LEVEL_NAME_PROGRESS, 'msg': 'progress #2'},
            {'levelno': LEVEL_PROGRESS, 'levelname': LEVEL_NAME_PROGRESS, 'msg': 'progress #3'},
            {'levelno': logging.INFO, 'levelname': logging.getLevelName(logging.INFO), 'msg': 'info #2'},
        ])

        handler = _Handler(_LOG_FORMAT)
        for record in records:
            handler.handle(record)

        handler_stream_mock.write.assert_has_calls([
            call('INFO: info #1'),
            call('\n'),
            call('PROGRESS: progress #1_   '),
            call('\r'),
            call('PROGRESS: progress #2    '),
            call('\r'),
            call('PROGRESS: progress #3'),
            call('\r'),
            call('\n'),
            call('INFO: info #2'),
            call('\n'),
        ])


class TestSTDOUTHandler(unittest.TestCase):
    """ Tests suite for dewyatochka.core.log.output.STDOUTHandler """

    def test_create_handler(self):
        """ Test inner handler instantiation """
        handler = STDOUTHandler(_LOG_FORMAT).handler
        self.assertIsInstance(handler, logging.StreamHandler)
        self.assertEqual(handler.stream, sys.stdout)


class TestFileHandler(unittest.TestCase):
    """ Tests suite for dewyatochka.core.log.output.FileHandler """

    def test_create_handler(self):
        """ Test inner handler instantiation """
        handler = FileHandler(_LOG_FORMAT, '/file.log').handler
        self.assertIsInstance(handler, logging.FileHandler)
        self.assertEqual(handler.baseFilename, '/file.log')
        self.assertIsNone(handler.stream)


class TestNullHandler(unittest.TestCase):
    """ Tests suite for dewyatochka.core.log.output.NullHandler """

    def test_create_handler(self):
        """ Test inner handler instantiation """
        handler = NullHandler(_LOG_FORMAT).handler
        self.assertIsInstance(handler, logging.NullHandler)
