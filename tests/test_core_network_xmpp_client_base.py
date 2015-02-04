# coding=utf-8

"""
Tests suite for dewyatochka.core.network.xmpp.client._base
"""

import unittest
from unittest.mock import patch
from dewyatochka.core.network.xmpp.client._base import *
from dewyatochka.core.network.xmpp.entity import *
from dewyatochka.core.network.xmpp.exception import C2SConnectionError


class _ClientStub(Client):
    """
    xmpp client stub for abstract client testing
    """

    def connect(self):
        """
        Establish connection to the server
        :return: void
        """
        pass

    def disconnect(self, wait=True):
        """
        Close connection
        :param wait: bool - Wait until all received messages are processed
        :return: void
        """
        pass

    def read(self) -> Message:
        """
        Read next message from stream
        :return: Message
        """
        pass


class _CommandStub(Command):
    """
    Empty command for testing purposes
    """

    def __call__(self, *args, **kwargs):
        """
        Command is invokable
        :param args:
        :param kwargs:
        :return:
        """
        pass

    @property
    def name(self) -> str:
        """
        Command unique name
        :return: str
        """
        return 'foo'


class TestCommand(unittest.TestCase):
    """
    dewyatochka.core.network.xmpp.client._base.Command
    """

    def test_init(self):
        """
        Test __init__()
        """
        client = _ClientStub('', '', '')
        command = _CommandStub(client)

        self.assertEqual(client, command._client)


class TestClient(unittest.TestCase):
    """
    dewyatochka.core.network.xmpp.client._base.Client
    """

    def test_init(self):
        """
        Test __init__()
        """
        login = 'user'
        password = 'pass'
        host = 'example.com'
        port = 1234
        location = 'location'

        client = _ClientStub(host, login, password, port, location)
        self.assertEqual(JID(login, host, location), client._jid)
        self.assertEqual((host, port), client._server)
        self.assertEqual(password, client._password)
        self.assertEqual({}, client._commands)

    def test_command_registration(self):
        """
        Test add_command / get_command / __getattr__
        """
        client = _ClientStub('', '', '')
        command = _CommandStub(client)

        client.add_command(command)
        self.assertEqual(command, client.get_command('foo'))
        self.assertEqual(command, client.foo)
        self.assertRaises(RuntimeError, client.get_command, 'not_registered')

    def test_jid_property(self):
        """
        Test JID property
        """
        self.assertEqual(JID.from_string('user@example.com'), _ClientStub('example.com', 'user', '').jid)

    @patch.object(_ClientStub, 'connect')
    @patch.object(_ClientStub, 'disconnect')
    def test_context_normal(self, disconnect_method, connect_method):
        """
        Test __enter__ / __exit__ without exceptions
        """
        with _ClientStub('', '', ''):
            connect_method.assert_called_once_with()

        disconnect_method.assert_called_once_with()

    @patch.object(_ClientStub, 'disconnect')
    def test_context_connection_error(self, disconnect_method):
        """
        Test __enter__ / __exit__ on client to server connection error
        """
        try:
            with _ClientStub('', '', ''):
                raise C2SConnectionError()
        except C2SConnectionError:
            pass

        self.assertEqual(0, disconnect_method.call_count)

    @patch.object(_ClientStub, 'disconnect')
    def test_context_other_error(self, disconnect_method):
        """
        Test __enter__ / __exit__ on any other error
        """
        try:
            with _ClientStub('', '', ''):
                raise Exception()
        except Exception:
            pass

        disconnect_method.assert_called_once_with()
