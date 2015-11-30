# -*- coding=utf-8

""" Tests suite for dewyatochka.core.plugin.subsystem.control.network """

import os
import random
import subprocess
import socket as socket_

import unittest
from unittest.mock import Mock

from dewyatochka.core.plugin.subsystem.control.network import *


# Test socket path
_SOCKET_PATH_TPL = os.path.realpath(os.path.dirname(__file__) + '/../files/control/test_%d.sock')


def _get_test_socket_path(n=None) -> str:
    """ Get socket path

    :param int n:
    :return str:
    """
    return _SOCKET_PATH_TPL % (n or random.randint(1, 9000))


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
        message = Message(foo='bar').encode()
        self.assertEqual(message, b'{"foo": "bar"}\0')

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


class TestSocketListener(unittest.TestCase):
    """ Tests suite for dewyatochka.core.plugin.subsystem.control.network.SocketListener """

    def setUp(self):
        """ Remove unused socket file before tests

        :return None:
        """
        socket_path = _get_test_socket_path()
        if os.path.isfile(socket_path):
            os.unlink(socket_path)
        self.socket_path = socket_path

    def assert_socket_state_is(self, path: str, type_: str, state: str):
        """ Assert socket state is the same as specified

        :param str path: Path to unix socket
        :param str type_: Socket type
        :param str state: Socket state
        :return None:
        """
        try:
            stats = {
                p[-1]: tuple(p[-4:-2])
                for p in map(lambda s: list(filter(None, s.split(' '))),
                             subprocess
                             .check_output(('netstat', '-lnx'))
                             .decode()
                             .split('\n'))
                if len(p) > 7
            }
            self.assertEqual(
                stats[path], (type_, state),
                'Socket %s expected to be in state %s, actual %s' % (path, stats[path], (type_, state))
            )
        except KeyError:
            self.fail('Socket %s does not exist' % path)

    def test_open_close(self):
        """ Test connection management """
        with SocketListener(self.socket_path):
            self.assert_socket_state_is(self.socket_path, 'STREAM', 'LISTENING')

        listener = SocketListener(self.socket_path)
        listener.close()  # Should be ignored

        listener.open()
        os.unlink(self.socket_path)
        listener.close()  # Should be ignored

    def test_commands(self):
        """ Test commands input stream """
        class _ListenerMock(SocketListener):
            """ Listener with socket mocked """

            # Socket mock
            client_connection_mock = Mock()
            socket_mock = _socket = Mock()

            @classmethod
            def set_messages(cls, *data: bytes):
                """ Set fake data to be sent by a client

                :param bytes data: Fake data
                :return None:
                """
                cls.socket_mock.reset_mock()
                cls.client_connection_mock.reset_mock()

                cls.client_connection_mock.recv.side_effect = data
                cls.socket_mock.accept.side_effect = [(cls.client_connection_mock, None)]

        # On valid message
        valid_command = b'{"name": "foo", "payload": "bar"}\0\x01\0'
        _ListenerMock.set_messages(valid_command)
        with _ListenerMock() as listener:
            commands = [c[0] for c in listener.commands]
        self.assertEqual(len(commands), 1)
        self.assertDictEqual(commands[0].data, {'name': 'foo', 'payload': 'bar'})
        _ListenerMock.client_connection_mock.send.assert_called_once_with(b'\x01\0')
        _ListenerMock.client_connection_mock.shutdown.assert_called_once_with(socket_.SHUT_RDWR)
        _ListenerMock.client_connection_mock.close.assert_called_once_with()

        # On unnamed message
        _ListenerMock.set_messages(b'{"payload": "bar"}\0\x01\0', valid_command)
        with _ListenerMock() as listener:
            self.assertRaises(StopIteration, next, listener.commands)
            _ListenerMock.client_connection_mock.send.assert_called_once_with(b'Message format unrecognized')

        # On client communication timeout
        _ListenerMock.set_messages(socket_.timeout)
        with _ListenerMock() as listener:
            self.assertRaises(StopIteration, next, listener.commands)

        # On broken connection
        _ListenerMock.set_messages(valid_command)
        _ListenerMock.client_connection_mock.send.side_effect = BrokenPipeError
        with _ListenerMock() as listener:
            commands = [c[0] for c in listener.commands]
        # Should yield one command with no errors
        self.assertEqual(len(commands), 1)

        # On closed state
        self.assertRaises(StopIteration, next, listener.commands)


class TestClient(unittest.TestCase):
    """ Tests suite for dewyatochka.core.plugin.subsystem.control.network.Client """

    def setUp(self):
        self.socket_path = _get_test_socket_path()
        self.socket = socket_.socket(socket_.AF_UNIX)
        self.socket.bind(self.socket_path)
        self.socket.listen(1)

    def tearDown(self):
        self.socket.close()
        os.unlink(self.socket_path)

    def test_client(self):
        """ Test client communication """
        with Client(self.socket_path) as client:
            client.send(Message(name='foo'))
            conn = self.socket.accept()[0]

            data = conn.recv(1024)
            self.assertEqual(data, b'{"name": "foo"}\0\x01\0')

            conn.send(b'{"foo": "bar"}\0{"bar": "baz"}\0\x01\0')
            conn.close()
            messages = list(client.input)
            self.assertDictEqual(messages[0].data, {'foo': 'bar'})
            self.assertDictEqual(messages[1].data, {'bar': 'baz'})

        self.assertFalse(os.path.isfile(self.socket_path))
