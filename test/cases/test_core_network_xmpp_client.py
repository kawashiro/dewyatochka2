# -*- coding=utf-8

""" Tests suite for dewyatochka.core.network.xmpp.client """

import unittest
from unittest.mock import Mock, call

from dewyatochka.core.network.xmpp import client
from dewyatochka.core.network.entity import Message, TextMessage
from dewyatochka.core.network.xmpp.exception import *
from dewyatochka.core.network.xmpp.entity import JID
from dewyatochka.core.network.xmpp.client import sleekxmpp


class _ClientImpl(client.Client):
    """ Abstract client impl """

    def disconnect(self, wait=True, notify=True):
        """ Close connection

        :param bool wait: Wait until all received messages are processed
        :param bool notify: Notify reader about disconnection
        :return None:
        """
        pass

    def connect(self):
        """ Establish connection to the server

        :return None:
        """
        pass

    def read(self) -> Message:
        """ Read next message from stream

        :return Message:
        """
        return TextMessage(
            JID.from_string('some@conference.example.com/sender'),
            JID.from_string('some@conference.example.com/receiver'),
            text='<< Fake text message >>'
        )


class TestClient(unittest.TestCase):
    """ Tests suite for dewyatochka.core.network.xmpp.client._base.Client """

    def test_jid(self):
        """ Test self JID assigning """
        client_ = _ClientImpl('host', 'login', '', location='foo')
        self.assertEqual(str(client_.jid), 'login@host/foo')

    def test_command_reg(self):
        """ Test external command registration """
        class _Command(Mock):
            """ Fake command """
            name = 'foo'

        client_ = _ClientImpl('host', 'login', 'password')
        command = _Command()
        client_.add_command(command)

        self.assertEqual(client_.get_command('foo'), command)
        self.assertEqual(client_.foo, command)

    def test_context_management(self):
        """ Test using client as a context manager """
        class _ClientImpl2(_ClientImpl):
            """ Mocked disconnect() method """
            disconnect = Mock()

        def _disconnection(client__):
            """ Forced disconnection in other thread, exit normally """
            with client__:
                raise ClientDisconnectedError()
            return True

        def _broken_connection(client__):
            """ Connection broken, raise """
            with client__:
                raise C2SConnectionError()

        def _any_error(client__):
            """ Any other error, disconnect immediately """
            with client__:
                raise Exception()

        def _self_exit(client__):
            """ End of reading input, disconnect & exit """
            with client__:
                pass

        def _do_test(fn_, exc_, calls_):
            """ Run test """
            client_ = _ClientImpl2('host', 'login', 'password')
            if (exc_):
                self.assertRaises(exc_, fn_, client_)
            else:
                fn_(client_)
            client_.disconnect.assert_has_calls(calls_ or [])

        _do_test(_disconnection, None, None)
        _do_test(_broken_connection, C2SConnectionError, None)
        _do_test(_any_error, Exception, [call(wait=False)])
        _do_test(_self_exit, None, [call(wait=True)])


class TestCreate(unittest.TestCase):
    """ Tests suite for dewyatochka.core.network.xmpp.client.create """

    def test_fn(self):
        """ Test factory function """
        client_ = client.create('host', 'user', 'pw', 5223, 'loc')

        self.assertIsInstance(client_, sleekxmpp.Client)
        self.assertIsInstance(client_.ping, sleekxmpp.PingCommand)
        self.assertIsInstance(client_.chat, sleekxmpp.MUCCommand)
