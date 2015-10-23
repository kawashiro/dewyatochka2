# -*- coding=utf-8

""" Tests suite for dewyatochka.core.plugin.subsystem.control.network """

import unittest
from unittest.mock import patch, call, Mock

from dewyatochka.core.plugin.subsystem.control.network import *


class TestMessage(unittest.TestCase):
    """ Tests suite for dewyatochka.core.plugin.subsystem.control.network.Message """

    # Test data dict
    _test_data = data = {'foo': 'bar', 'baz': 42}

    def test_init_from_payload(self):
        """ Test init from already parsed data """
        self.assertEqual(Message(**self._test_data).data, self._test_data)

    def test_attributes(self):
        """ Test data setters / getters """
        message = Message(**self._test_data)
        self.assertEqual(message.foo, 'bar')
        message.baz = 43
        self.assertEqual(message.data, {'foo': 'bar', 'baz': 43})

    def test_encode(self):
        """ Test data encoding """
        message = Message(**self._test_data).encode()
        self.assertEqual(message, b'{"foo": "bar", "baz": 42}\0')

    def test_decode(self):
        """ Test serialized message decoding """
        self.assertEqual(Message.from_bytes(b'{"foo": "bar", "baz": 42}\0').data, self._test_data)
        self.assertRaises(InvalidMessageError, Message.from_bytes, b'')
        self.assertRaises(InvalidMessageError, Message.from_bytes, b'\xCA\xFE\xBA\xBE')


class TestStreamReader(unittest.TestCase):
    """ Tests suite for dewyatochka.core.plugin.subsystem.control.network.StreamReader """

    @staticmethod
    def _get_stream_chunks(messages: list, length: int):
        """ Get stream chunks

        :param list messages:
        :param int length:
        :return generator:
        """
        pos = 0
        stream = b''.join(map(lambda p: Message(**p).encode(), messages)) + b'\x01\0'
        while pos < len(stream):
            yield stream[pos:pos+length]
            pos += length

    def test_read(self):
        """ Test messages reading """
        _assert_equal = self.assertEqual

        def _do_test(chunk_size):
            socket = Mock()
            socket.recv.side_effect = list(self._get_stream_chunks([
                {'foo1': 'bar1'}, {'foo2': 'bar2'}
            ], chunk_size)) + [ConnectionResetError]
            reader = StreamReader(socket)

            _assert_equal(reader.read_message().data, {'foo1': 'bar1'})
            _assert_equal(reader.read_message().data, {'foo2': 'bar2'})
            _assert_equal(reader.read_message(), None)

        _do_test(4)
        _do_test(17)
