# -*- coding=utf-8

""" Tests suite for dewyatochka.core.network.xmpp.client.sleekxmpp """

import threading
from collections import defaultdict

import unittest
from unittest.mock import patch, Mock, call, ANY, MagicMock

import sleekxmpp
from sleekxmpp import exceptions
from sleekxmpp.stanza import message, presence, error

from dewyatochka.core.network.xmpp.client.sleekxmpp import *
from dewyatochka.core.network.xmpp.exception import *
from dewyatochka.core.network.xmpp.entity import JID, ChatSubject, ChatPresence
from dewyatochka.core.network.entity import TextMessage


class _SleekMock(MagicMock):
    """ sleekxmpp mock """

    def __init__(self, *args, **kwargs):
        """ Init empty handlers list """
        super().__init__(*args, **kwargs)
        self._handlers = defaultdict(list)
        self._scheduled = {}

    def add_event_handler(self, event: str, handler: callable):
        """ Add event handler

        :param str event: Event name
        :param callable handler: Handler
        :return None:
        """
        self._handlers[event].append(handler)

    def schedule(self, name, seconds, callback, args=(), kwargs=None, repeat=False):
        """Schedule a callback function to execute after a given delay.

        :param name: A unique name for the scheduled callback.
        :param  seconds: The time in seconds to wait before executing.
        :param callback: A pointer to the function to execute.
        :param args: A tuple of arguments to pass to the function.
        :param kwargs: A dictionary of keyword arguments to pass to
                       the function.
        :param repeat: Flag indicating if the scheduled event should
                       be reset and repeat after executing.
        """
        self._scheduled[name] = dict(seconds=seconds, callback=callback, args=args,
                                     kwargs=(kwargs or {}), repeat=repeat)

    def yield_message(self, data: dict):
        """ Emulate message from xmpp stream

        :param dict data: Message params
        :return None:
        """
        self.__handle('message', data)

    def yield_s2s_error(self, data: dict):
        """ Emulate message from xmpp stream

        :param dict data: Message params
        :return None:
        """
        self.__handle('presence_error', data)

    def invoke_scheduled_task(self, name: str):
        """ Invoke scheduled task immediately

        :param str name: Task name
        :return any:
        """
        task = self._scheduled[name]
        return task['callback'](*task['args'], **task['kwargs'])

    def __handle(self, event: str, data: dict):
        """ Event name to be handled

        :param str event:
        :param dict data:
        :return None:
        """
        for handler in self._handlers[event]:
            handler(data)


class _FakeClient(Client):
    """ Client with overridden sleekxmpp property """

    def __init__(self, host: str, login: str, password: str, port=5222, location=''):
        """ Initialize XMPP client instance

        :param str host: XMPP server host
        :param str login: User login
        :param str password: User password
        :param int port: XMPP server port, default 5222
        :param str location: XMPP resource, default ''
        :return Client:
        """
        super().__init__(host, login, password, port, location)

        self.sleek_mock = _SleekMock()
        self.sleek_mock.connect.return_value = True

        self.sleek_mock.add_event_handler('message', self._queue_message)
        self.sleek_mock.add_event_handler('presence_error', self._queue_presence_error)

        self.sleek_mock.schedule('c2s_connection_check', 60, self._do_c2s_connection_check)

    @property
    def _sleekxmpp(self) -> Mock:
        """ Create new sleekxmpp instance or return an already instantiated one

        :return sleekxmpp.ClientXMPP:
        """
        return self.sleek_mock


class _RawJidStruct:
    """ Raw jid structure """

    def __init__(self, jid: JID):
        """ Create raw jid structure from parsed JID instance

        :param JID jid:
        """
        self.full = str(jid)
        self.bare = str(jid.bare)


def _client_factory(override_connection=True) -> Client:
    """ Client factory function

    :param
    :return Client:
    """
    return (_FakeClient if override_connection else Client)('host', 'user', 'pw', 5223, 'loc')


class TestClient(unittest.TestCase):
    """ Tests suite for dewyatochka.core.network.xmpp.client.sleekxmpp.Client """

    def assert_event_handled(self, sleek_client: sleekxmpp.ClientXMPP, event: str):
        """ Check if event handler is registered in sleekxmpp client

        :param sleekxmpp.ClientXMPP sleek_client:
        :param str event:
        :return None:
        """
        self.assertTrue(sleek_client.event_handled(event), 'Event %s is not handled by SleekXMPP client')

    @patch.object(sleekxmpp.ClientXMPP, 'schedule')
    @patch.object(sleekxmpp.ClientXMPP, 'process')
    @patch.object(sleekxmpp.ClientXMPP, 'send_presence')
    @patch.object(sleekxmpp.ClientXMPP, 'connect', return_value=True)
    def test_connect_success(self, sleek_connect_mock, sleek_send_presence_mock,
                             sleek_process_mock, sleek_schedule_mock):
        """ Test connection establishing """
        client = _client_factory(override_connection=False)

        client.connect()
        client.connect()  # Repeated intentionally

        self.assertIsInstance(client.connection, sleekxmpp.ClientXMPP)

        enabled_plugins = set(client.connection.plugin.__keys__())
        self.assertIn('xep_0045', enabled_plugins)
        self.assertIn('xep_0199', enabled_plugins)

        self.assert_event_handled(client.connection, 'message')
        self.assert_event_handled(client.connection, 'presence_error')
        self.assert_event_handled(client.connection, 'disconnected')
        self.assert_event_handled(client.connection, 'groupchat_subject')
        self.assert_event_handled(client.connection, 'groupchat_presence')

        sleek_schedule_mock.assert_called_once_with('c2s_connection_check', 60, ANY, repeat=True)

        self.assertEqual(client.connection.requested_jid.full, 'user@host/loc')
        sleek_connect_mock.assert_called_once_with(('host', 5223), reattempt=False)
        sleek_send_presence_mock.assert_called_once_with()
        sleek_process_mock.assert_called_once_with()

        self.assertRaises(ClientDisconnectedError, lambda: Client('host', 'user', 'pw', 5223, 'loc').connection)

    def test_connect_error(self):
        """ Test error on connecting """
        client = _client_factory()
        client.sleek_mock.connect.return_value = False

        self.assertRaises(C2SConnectionError, client.connect)
        client.sleek_mock.connect.assert_called_once_with(('host', 5223), reattempt=False)

    def test_disconnect_disconnected(self):
        """ Test attempt to disconnect already disconnected client """
        client = _client_factory()
        self.assertRaises(ClientDisconnectedError, client.disconnect)

    def test_disconnect_common(self):
        """ Test common disconnection logic """
        client = _client_factory()
        client.connect()

        client.disconnect(wait=False, notify=False)
        client.sleek_mock.disconnect.assert_called_once_with(send_close=False)

    def test_disconnect_notify(self):
        """ Test reader notification on client disconnect """
        client = _client_factory()

        client.connect()
        client.disconnect(wait=False)

        self.assertRaises(ClientDisconnectedError, client.read)

    def test_disconnect_wait(self):
        """ Test reader wait on disconnect """
        def _do_test(wait, expected_calls):
            """ Run test for a specific flag value """
            def _reader(client_, accumulator_, barrier_):
                """ Input stream reader thread """
                try:
                    client_.read()
                except ClientDisconnectedError:
                    accumulator_('read')
                finally:
                    barrier_.wait()

            client = _client_factory()
            barrier = threading.Barrier(2)
            accumulator = Mock()

            client.connect()
            threading.Thread(target=_reader, args=(client, accumulator, barrier)).start()

            client.disconnect(wait=wait)
            accumulator('disconnected')
            barrier.wait()

            accumulator.assert_has_calls(expected_calls)
            client.sleek_mock.disconnect.assert_called_once_with(send_close=wait)

        _do_test(True, [call('read'), call('disconnected')])
        _do_test(False, [call('disconnected'), call('read')])

    def test_context_management(self):
        """ Test using client as a context manager """
        def _normal_disconnect(client_):
            """ Normally such error should be suppressed... """
            with client_:
                client_.connect()
                raise ClientDisconnectedError()
            return True

        def _logic_error(client_):
            """ ... but not on possible logic error """
            with client_:
                raise ClientDisconnectedError()

        self.assertTrue(_normal_disconnect(_client_factory()))
        self.assertRaises(ClientDisconnectedError, _logic_error, _client_factory())

    def test_c2s_ping(self):
        """ Check if client-to-server ping """
        cmd = Mock()
        cmd.name = 'ping'

        client = _client_factory()
        client.connect()

        # Command is not registered, just do nothing
        client.sleek_mock.invoke_scheduled_task('c2s_connection_check')

        # Register command, succeed ping
        client.add_command(cmd)
        client.sleek_mock.invoke_scheduled_task('c2s_connection_check')
        cmd.assert_called_once_with()

        # Ping error, exception in reader thread
        cmd.side_effect = C2SConnectionError()
        client.sleek_mock.invoke_scheduled_task('c2s_connection_check')
        self.assertRaises(C2SConnectionError, client.read)

    def test_presence_error(self):
        """ Check presence error handling """
        client = _client_factory()
        client.connect()

        client.sleek_mock.yield_s2s_error({
            'from': _RawJidStruct(JID.from_string('some@conference.example.com')),
            'error': {'text': 'S2S connection error'},
        })

        remote_jid = None
        try:
            client.read()
        except S2SConnectionError as e:
            remote_jid = e.remote

        self.assertEqual(remote_jid, 'some@conference.example.com')

    def test_regular_message(self):
        """ Test regular message receiving """
        raw_message = message.Message(sfrom='some@conference.example.com/sender',
                                      sto='some@conference.example.com/receiver')
        raw_message['body'] = 'Hello, world!'
        raw_message['type'] = 'groupchat'

        client = _client_factory()
        client.connect()

        client.sleek_mock.yield_message(raw_message)
        text_message = client.read()

        self.assertIsInstance(text_message, TextMessage)
        self.assertEqual(text_message.sender, 'some@conference.example.com/sender')
        self.assertEqual(text_message.receiver, 'some@conference.example.com/receiver')
        self.assertEqual(text_message.text, 'Hello, world!')
        self.assertFalse(text_message.is_system)

    def test_system_message(self):
        """ Test system message receiving """
        raw_message = message.Message(sfrom='some@conference.example.com',
                                      sto='some@conference.example.com/receiver')
        raw_message['body'] = 'Hello, world!'
        raw_message['type'] = 'groupchat'

        client = _client_factory()
        client.connect()

        client.sleek_mock.yield_message(raw_message)
        text_message = client.read()

        self.assertIsInstance(text_message, TextMessage)
        self.assertEqual(text_message.sender, 'some@conference.example.com')
        self.assertEqual(text_message.receiver, 'some@conference.example.com/receiver')
        self.assertEqual(text_message.text, 'Hello, world!')
        self.assertTrue(text_message.is_system)

    def test_subject_message(self):
        """ Test chat subject change notification """
        raw_message = message.Message(sfrom='some@conference.example.com',
                                      sto='some@conference.example.com/receiver')
        raw_message['subject'] = 'Hello, world!'
        raw_message['type'] = 'groupchat'

        client = _client_factory()
        client.connect()

        client.sleek_mock.yield_message(raw_message)
        subj_message = client.read()

        self.assertIsInstance(subj_message, ChatSubject)
        self.assertEqual(subj_message.sender, 'some@conference.example.com')
        self.assertEqual(subj_message.receiver, 'some@conference.example.com/receiver')
        self.assertEqual(subj_message.subject, 'Hello, world!')

    def test_presence_message(self):
        """ Test chat presence change message receiving """
        raw_message = presence.Presence(sfrom='some@conference.example.com',
                                        sto='some@conference.example.com/receiver')
        raw_message['type'] = 'available'
        raw_message['status'] = 'Hello, world!'
        raw_message['muc']['role'] = 'participant'

        client = _client_factory()
        client.connect()

        client.sleek_mock.yield_message(raw_message)
        subj_message = client.read()

        self.assertIsInstance(subj_message, ChatPresence)
        self.assertEqual(subj_message.sender, 'some@conference.example.com')
        self.assertEqual(subj_message.receiver, 'some@conference.example.com/receiver')
        self.assertEqual(subj_message.type, 'available')
        self.assertEqual(subj_message.status, 'Hello, world!')
        self.assertEqual(subj_message.role, 'participant')

    def test_error_message(self):
        """ Test error message receiving """
        client = _client_factory()
        client.connect()

        err = error.Error()
        err['code'] = 42
        err['text'] = 'Something wrong'
        raw_message = message.Message()
        raw_message['type'] = 'error'
        raw_message['error'] = err

        client.sleek_mock.yield_message(raw_message)
        self.assertRaises(MessageError, client.read)

    def test_unaccepted_message(self):
        """ Test invalid or unrecognized message receiving """
        client = _client_factory()
        client.connect()

        client.sleek_mock.yield_message(message.Message())
        self.assertRaises(MessageError, client.read)


class TestMUCCommand(unittest.TestCase):
    """ Tests suite for dewyatochka.core.network.xmpp.client.sleekxmpp.MUCCommand """

    def test_enter(self):
        """ Test conference enter """
        client = _client_factory()
        client.add_command(MUCCommand(client))
        client.connect()

        client.chat.enter(JID.from_string('some@conference.example.com'), 'MyNick')
        client.chat.enter(JID.from_string('some@conference.example.com'))

        client.sleek_mock.plugin['xep_0045'].joinMUC.assert_has_calls([
            call('some@conference.example.com', 'MyNick'),
            call('some@conference.example.com', 'user@host/loc'),
        ])

    def test_leave(self):
        """ Test conference leave """
        client = _client_factory()
        client.add_command(MUCCommand(client))
        client.connect()

        client.chat.leave(JID.from_string('some@conference.example.com'), 'MyNick', reason='you suck')
        client.chat.leave(JID.from_string('some@conference.example.com'))

        client.sleek_mock.plugin['xep_0045'].leaveMUC.assert_has_calls([
            call('some@conference.example.com', 'MyNick', msg='you suck'),
            call('some@conference.example.com', 'user@host/loc', msg=''),
        ])

    def test_send(self):
        """ Test sending MUC message """
        client = _client_factory()
        client.add_command(MUCCommand(client))
        client.connect()

        client.chat('Hello, guys', JID.from_string('some@conference.example.com'))

        client.sleek_mock.send_message.assert_called_once_with(
            'some@conference.example.com', 'Hello, guys', mtype='groupchat'
        )


class TestPingCommand(unittest.TestCase):
    """ Tests suite for dewyatochka.core.network.xmpp.client.sleekxmpp.PingCommand """

    def test_connection_ping_ok(self):
        """ Test succeeded connection ping """
        client = _client_factory()
        client.add_command(PingCommand(client))
        client.connect()

        remote = JID.from_string('some@conference.example.com')
        sleek_ping_mock = client.sleek_mock.plugin['xep_0199'].ping
        sleek_ping_mock.side_effect = [0.42, 0.43]

        res1 = client.ping(timeout=42)
        res2 = client.ping(remote, timeout=43)

        sleek_ping_mock.assert_has_calls([
            call(jid=None, ifrom='user@host/loc', timeout=42),
            call(jid='some@conference.example.com', ifrom='user@host/loc', timeout=43),
        ])
        self.assertEqual(res1, 0.42)
        self.assertEqual(res2, 0.43)

    def test_unimplemented_ping(self):
        """ Test on unimplemented ping on remote side """
        client = _client_factory()
        client.add_command(PingCommand(client))
        client.connect()

        sleek_ping_mock = client.sleek_mock.plugin['xep_0199'].ping
        sleek_ping_mock.side_effect = exceptions.IqError(
            {'error': {'condition': 'feature-not-implemented', 'text': '', 'type': ''}}
        )

        self.assertEqual(client.ping(), -1)

    def test_any_error(self):
        """ Test on any other error """
        client = _client_factory()
        client.add_command(PingCommand(client))
        client.connect()

        remote = JID.from_string('some@conference.example.com')
        sleek_ping_mock = client.sleek_mock.plugin['xep_0199'].ping

        sleek_ping_mock.side_effect = exceptions.IqError({'error': {'condition': '', 'text': '', 'type': ''}})
        self.assertRaises(C2SConnectionError, client.ping)
        self.assertRaises(S2SConnectionError, client.ping, remote)

        sleek_ping_mock.side_effect = exceptions.XMPPError()
        self.assertRaises(C2SConnectionError, client.ping)
        self.assertRaises(S2SConnectionError, client.ping, remote)
