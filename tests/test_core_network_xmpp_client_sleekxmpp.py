# -*- coding=utf-8

""" Tests suite for dewyatochka.core.network.xmpp.client.sleekxmpp """

import _thread
import queue

import unittest
from unittest.mock import patch, Mock, MagicMock, ANY, call

from sleekxmpp import jid as sleekjid
from sleekxmpp import ClientXMPP
from sleekxmpp import exceptions

from dewyatochka.core.network.xmpp.client.sleekxmpp import *
from dewyatochka.core.network.xmpp.entity import *
from dewyatochka.core.network.xmpp.exception import *


class TestClient(unittest.TestCase):
    """ Covers dewyatochka.core.network.xmpp.client.sleekxmpp.Client """

    def test_init(self):
        """ Test __init__() """
        client = Client('', '', '')

        self.assertFalse(client._connected)
        self.assertIsInstance(client._connection_lock, _thread.LockType)
        self.assertIsInstance(client._message_queue, queue.Queue)

    @patch.object(Client, '_sleekxmpp')
    def test_disconnect(self, sleekxmpp_mock):
        """ Test disconnection """
        client = Client('', '', '')
        client._connected = True
        client._message_queue = MagicMock()
        client._connection_lock = MagicMock()

        client.disconnect()

        sleekxmpp_mock.disconnect.assert_called_once_with(send_close=True)

        client._connection_lock.__enter__.assert_called_once_with()
        client._connection_lock.__exit__.assert_called_once_with(None, None, None)

        client._message_queue.join.assert_called_once_with()
        client._message_queue.put.assert_called_once_with(ANY)
        self.assertIsInstance(client._message_queue.put.call_args[0][0], ClientDisconnectedError)

        sleekxmpp_mock.disconnect.assert_called_once_with(send_close=True)

    @patch.object(Client, '_sleekxmpp')
    def test_disconnect_no_wait(self, sleekxmpp_mock):
        """ Test disconnection """
        client = Client('', '', '')
        client._connected = True
        client._message_queue = MagicMock()

        client.disconnect(wait=False)
        self.assertEqual(0, client._message_queue.join.call_count)

        sleekxmpp_mock.disconnect.assert_called_once_with(send_close=False)

    def test_disconnect_disconnected(self):
        """ Test exception on disconnecting disconnected client """
        self.assertRaises(ClientDisconnectedError, Client('', '', '').disconnect)

    def test_read(self):
        """ Test reading from queue """
        client = Client('', '', '')
        client._message_queue.put({'hello': 'world'})
        client._message_queue.put(Exception('Something wrong'))

        self.assertEqual({'hello': 'world'}, client.read())
        self.assertRaises(Exception, client.read)

        self.assertEqual(0, client._message_queue.unfinished_tasks)

    @patch.object(Client, '_sleekxmpp')
    def test_connect(self, sleekxmpp_mock):
        """ Test connection establishing """
        client = Client('host', '', '')

        client.connect()
        client.connect()

        sleekxmpp_mock.connect.assert_called_once_with(('host', 5222), reattempt=False)
        sleekxmpp_mock.process.assert_called_once_with()
        sleekxmpp_mock.send_presence.assert_called_once_with()

    @patch.object(Client, '_sleekxmpp')
    def test_connect_fail(self, sleekxmpp_mock):
        """ Test exception on connection failed """
        client = Client('', '', '')
        sleekxmpp_mock.connect.side_effect = (False,)

        self.assertRaises(C2SConnectionError, client.connect)

    def test_sleekxmpp_instantiation(self):
        """ Test creating sleekxmpp instance """
        client = Client('host', 'login', 'password')

        sleekxmpp = client._sleekxmpp
        self.assertTrue(sleekxmpp.plugin.enabled('xep_0045'))
        self.assertTrue(sleekxmpp.plugin.enabled('xep_0199'))
        self.assertTrue(sleekxmpp.event_handled('message'))
        self.assertTrue(sleekxmpp.event_handled('presence_error'))
        self.assertEqual('password', sleekxmpp.password)
        self.assertEqual(str(client.jid), sleekxmpp.boundjid.full)

        self.assertEqual(sleekxmpp, client._sleekxmpp)

    def test_queue_presence_error(self):
        """ Test queueing presence error """
        client = Client('', '', '')
        jid = Mock()
        jid.bare = 'foo@example.com'

        client._queue_presence_error({'error': {'text': 'Something wrong'}, 'from': jid})
        self.assertRaises(S2SConnectionError, client.read)

    @patch.object(Client, '_sleekxmpp')
    def test_queue_connection_error(self, sleekxmpp_mock):
        """ Test on slekxmpp client self-disconnect """
        client = Client('', '', '')
        client._connected = True

        client._queue_connection_error()
        self.assertRaises(C2SConnectionError, client.read)
        self.assertFalse(client._connected)
        sleekxmpp_mock.disconnect.assert_called_once_with(send_close=False)

    def test_queue_connection_error_not_connected(self):
        """ Test abnormal _queue_connection_error call """
        client = Client('', '', '')

        client._queue_connection_error()
        self.assertEqual(0, client._message_queue.unfinished_tasks)

    def test_connection(self):
        """ Test connection property """
        client = Client('host', 'login', 'password')
        self.assertRaises(ClientDisconnectedError, lambda: client.connection)

        client._connected = True
        self.assertIsInstance(client.connection, ClientXMPP)

    def test_exit(self):
        """ Test _connected flag affection on behaviour on __exit__() """
        def _error(client_):
            with client_:
                raise ClientDisconnectedError()

        client = Client('host', 'login', 'password')
        self.assertRaises(ClientDisconnectedError, _error, client)

        client._connected = True
        with client:
            # Suppress error
            raise ClientDisconnectedError()

    def test_do_c2s_connection_check(self):
        """ Test internal ping check """
        ping_cmd = Mock(side_effect=(0, C2SConnectionError()))
        ping_cmd.name = 'ping'

        client = Client('host', 'login', 'password')

        client._do_c2s_connection_check()  # Disconnected, nothing
        self.assertTrue(client._message_queue.empty())
        client._connected = True
        client._do_c2s_connection_check()  # No cmd registered, still nothing
        self.assertTrue(client._message_queue.empty())
        client.add_command(ping_cmd)
        client._do_c2s_connection_check()  # No exception, queue empty
        self.assertTrue(client._message_queue.empty())
        client._do_c2s_connection_check()  # Exception, read() raises
        self.assertRaises(C2SConnectionError, client.read)



class TestMUCCommand(unittest.TestCase):
    """ Covers dewyatochka.core.network.xmpp.client.sleekxmpp.MUCCommand """

    @patch.object(Client, 'connection')
    def test_send(self, connection_mock):
        """ Test MUC message send """
        command = MUCCommand(Client('host', 'login', 'password'))
        receiver = JID.from_string('receiver@example.com')

        command('message', receiver)
        connection_mock.send_message.assert_called_once_with('receiver@example.com', 'message', mtype='groupchat')

    @patch.object(Client, 'connection')
    def test_enter(self, connection_mock):
        """ Test MUC message send """
        command = MUCCommand(Client('host', 'login', 'password'))
        conference = JID.from_string('chat@conference.example.com')

        command.enter(conference)
        command.enter(conference, 'nick')

        connection_mock.plugin['xep_0045'].joinMUC.assert_has_calls([
            call('chat@conference.example.com', 'login@host'),
            call('chat@conference.example.com', 'nick')
        ])

    @patch.object(Client, 'connection')
    def test_leave(self, connection_mock):
        """ Test MUC message send """
        command = MUCCommand(Client('host', 'login', 'password'))
        conference = JID.from_string('chat@conference.example.com')

        command.leave(conference, reason='foo')
        command.leave(conference, 'nick', 'foo')
        command.leave(conference, 'nick')

        connection_mock.plugin['xep_0045'].leaveMUC.assert_has_calls([
            call('chat@conference.example.com', 'login@host', msg='foo'),
            call('chat@conference.example.com', 'nick', msg='foo'),
            call('chat@conference.example.com', 'nick', msg='')
        ])

    def test_name(self):
        """ Test name property """
        self.assertEqual('chat', MUCCommand(Client('', '', '')).name)


class TestPingCommand(unittest.TestCase):
    """ Covers dewyatochka.core.network.xmpp.client.sleekxmpp.PingCommand """

    @patch.object(Client, 'connection')
    def test_ping(self, connection_mock):
        """ Test ping """
        command = PingCommand(Client('host', 'login', 'password'))
        destination = JID.from_string('chat@conference.example.com')
        connection_mock.plugin['xep_0199'].ping.side_effect = (1, 2, 3)

        result = (command(), command(destination), command(destination, timeout=9000))
        self.assertEqual((1, 2, 3), result)
        connection_mock.plugin['xep_0199'].ping.assert_has_calls([
            call(jid=None, ifrom='login@host', timeout=None),
            call(jid='chat@conference.example.com', ifrom='login@host', timeout=None),
            call(jid='chat@conference.example.com', ifrom='login@host', timeout=9000)
        ])

    @patch.object(Client, 'connection')
    def test_ping_not_supported(self, connection_mock):
        """ Behaviour if remote service does not support ping """
        command = PingCommand(Client('host', 'login', 'password'))
        connection_mock.plugin['xep_0199'].ping.side_effect = exceptions.IqError(
            {'error': {'condition': 'feature-not-implemented', 'text': '', 'type': ''}}
        )

        self.assertEqual(-1, command())

    @patch.object(Client, 'connection')
    def test_ping_iq_error(self, connection_mock):
        """ Behaviour on any iq error """
        command = PingCommand(Client('host', 'login', 'password'))
        destination = JID.from_string('chat@conference.example.com')
        connection_mock.plugin['xep_0199'].ping.side_effect = exceptions.IqError(
            {'error': {'condition': 'foo', 'text': '', 'type': ''}}
        )

        self.assertRaises(S2SConnectionError, command, destination)
        self.assertRaises(C2SConnectionError, command)

    @patch.object(Client, 'connection')
    def test_ping_xmpp_error(self, connection_mock):
        """ Behaviour on any xmpp error """
        command = PingCommand(Client('host', 'login', 'password'))
        destination = JID.from_string('chat@conference.example.com')
        connection_mock.plugin['xep_0199'].ping.side_effect = exceptions.XMPPError()

        self.assertRaises(S2SConnectionError, command, destination)
        self.assertRaises(C2SConnectionError, command)

    def test_name(self):
        """ Test name property """
        self.assertEqual('ping', PingCommand(Client('', '', '')).name)
