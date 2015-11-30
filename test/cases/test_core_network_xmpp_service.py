# -*- coding=utf-8

""" Tests suite for dewyatochka.core.network.xmpp.service """

import time
import threading

import unittest
from unittest.mock import Mock, patch, call, ANY

from dewyatochka.core.network.xmpp.service import *
from dewyatochka.core.application import VoidApplication
from dewyatochka.core.config.container import CommonConfig, ConferencesConfig
from dewyatochka.core.config.source.virtual import Predefined
from dewyatochka.core.network.xmpp.client import Client
from dewyatochka.core.network.xmpp.entity import TextMessage, JID, Conference
from dewyatochka.core.network.xmpp.exception import *
from dewyatochka.core.network.service import ChatManager, ConnectionManager
from dewyatochka.core.network.entity import Participant


class _ChatManagerImpl(ChatManager):
    """ Chat manager implementation stub """

    def alive_chats(self) -> frozenset:
        """ Get alive conferences

        :return frozenset:
        """
        return frozenset()

    def send(self, message: str, chat: Participant):
        """ Send a message to group chat

        :param str message: Message content
        :param GroupChat chat: Destination chat
        :return None:
        """
        pass

    def attach_connection_manager(self, connection: ConnectionManager):
        """ Attach a connection manager to take control on

        :param ConnectionManager connection: Connection manager
        :return None:
        """
        pass


class _Application(VoidApplication):
    """ Test app """

    # `sleep` method mock
    sleep = Mock()

    @classmethod
    def create(cls):
        """ Create app instance

        :return _Application:
        """
        log_mock = Mock()
        log_mock.name.return_value = 'log'

        application = cls()
        application.depend(CommonConfig)
        application.depend(_ChatManagerImpl)
        application.depend(log_mock)

        return application


class TestXMPPConnectionManager(unittest.TestCase):
    """ Tests suite for dewyatochka.core.network.xmpp.service.XMPPConnectionManager """

    def assert_connection_params_equal(self, client: Client, host: str, login: str,
                                       password: str, port: int, location: str):
        """ Check if client instance has correct connection params

        :param Client client:
        :param str host:
        :param str login:
        :param str password:
        :param int port:
        :param str location:
        :return None:
        """
        self.assertEqual(getattr(client, '_jid').server, host)
        self.assertEqual(getattr(client, '_jid').login, login)
        self.assertEqual(getattr(client, '_jid').resource, location)
        self.assertEqual(getattr(client, '_password'), password)
        self.assertEqual(getattr(client, '_server'), (host, port))

    def test_client(self):
        """ Test XMPP client instantiation """
        app = _Application.create()

        # Complete config
        cfg = {'host': 'example.com', 'port': '9000', 'login': 'foo', 'password': 'bar', 'location': 'baz'}
        app.registry.config.load(Predefined({'xmpp': cfg}))
        self.assert_connection_params_equal(
            XMPPConnectionManager(app).client, 'example.com', 'foo', 'bar', 9000, 'baz'
        )

        # Default values
        cfg = {'host': 'example.com', 'login': 'foo', 'password': 'bar'}
        app.registry.config.load(Predefined({'xmpp': cfg}))
        self.assert_connection_params_equal(
            XMPPConnectionManager(app).client, 'example.com', 'foo', 'bar', 5222, ''
        )

        # Missing required params
        for field in 'host', 'login', 'password':
            cfg_ = cfg.copy()
            del cfg_[field]
            app.registry.config.load(Predefined({'xmpp': cfg_}))
            self.assertRaises(ConnectionConfigError, lambda: XMPPConnectionManager(app).client)

        # Bad port number
        cfg = {'host': 'example.com', 'login': 'foo', 'password': 'bar', 'port': 'baz'}
        app.registry.config.load(Predefined({'xmpp': cfg}))
        self.assertRaises(ConnectionConfigError, lambda: XMPPConnectionManager(app).client)

    def test_connect(self):
        """ Test connecting """
        presence_helper_mock = Mock()
        xmpp_client_mock = Mock()
        app = _Application.create()

        cm = XMPPConnectionManager(app, presence_helper_mock, xmpp_client_mock)
        cm.connect()

        xmpp_client_mock.connect.assert_called_once_with()
        presence_helper_mock.start.assert_called_once_with()
        presence_helper_mock.enter_all.assert_called_once_with()

    def test_input_stream_common(self):
        """ Test input stream generator common use cases """
        fake_conference_jid = Conference.from_string('receiver@server/1')

        xmpp_client_mock = Mock()
        xmpp_client_mock.jid = JID.from_string('receiver@server2/2')

        stream_message = TextMessage(JID.from_string('sender@server/1'), xmpp_client_mock.jid, text='')
        xmpp_client_mock.read.side_effect = [
            stream_message,
            MessageError,
            S2SConnectionError(remote=fake_conference_jid),
            ClientDisconnectedError,
        ]

        presence_helper_mock = Mock()
        presence_helper_mock.get_presence_jid.return_value = fake_conference_jid

        app = _Application.create()

        cm = XMPPConnectionManager(app, presence_helper_mock, xmpp_client_mock)

        message = next(cm.input_stream)
        self.assertEqual(message, stream_message)
        self.assertEqual(message.receiver, fake_conference_jid)

        self.assertRaises(StopIteration, next, cm.input_stream)
        self.assertIsInstance(cm.log.debug.mock_calls[0][1][0], MessageError)  # Fuck!
        presence_helper_mock.schedule_reenter.assert_called_once_with(fake_conference_jid)

    @patch('dewyatochka.core.network.xmpp.service._XMPP_OFFLINE_TIME_LIMIT', 0.1)
    def test_input_stream_reconnect(self, *_):
        """ Test reconnection on input stream reading errors """
        def _init_new_cm(client_mock_):
            presence_helper = Mock()
            return XMPPConnectionManager(_Application.create(), presence_helper, client_mock_), presence_helper

        stream_message = TextMessage(JID.from_string('sender@server/s'), JID.from_string('receiver@server/s'), text='')

        client = Mock()
        client.read.side_effect = [C2SConnectionError, stream_message]
        cm_ok, ph_ok = _init_new_cm(client)

        self.assertEqual(stream_message, next(cm_ok.input_stream))
        cm_ok.log.error.assert_called_once_with(ANY)
        cm_ok.client.connect.assert_called_once_with()
        ph_ok.clear_state.assert_called_once_with()
        ph_ok.enter_all.assert_called_once_with()

        client = Mock()
        client.read.side_effect = C2SConnectionError
        client.connect.side_effect = C2SConnectionError
        cm_bad, ph_bad = _init_new_cm(client)

        self.assertRaises(C2SConnectionError, next, cm_bad.input_stream)
        self.assertGreater(cm_bad.client.connect.call_count, 1)

    def test_disconnect(self):
        """ Test disconnection """
        app = _Application.create()
        presence_helper_mock = Mock()
        xmpp_client_mock = Mock()

        cm = XMPPConnectionManager(app, presence_helper_mock, xmpp_client_mock)

        cm.disconnect()
        presence_helper_mock.leave_all.assert_called_once_with()
        presence_helper_mock.stop.assert_called_once_with()
        xmpp_client_mock.disconnect.assert_called_once_with()

        xmpp_client_mock.reset_mock()
        presence_helper_mock.leave_all.side_effect = RuntimeError
        cm.disconnect()
        xmpp_client_mock.disconnect.assert_called_once_with()

        xmpp_client_mock.disconnect.side_effect = ClientDisconnectedError
        cm.disconnect()

    def test_alive_chats(self):
        """ Test alive chats getter """
        app = _Application.create()
        presence_helper_mock = Mock()
        xmpp_client_mock = Mock()

        cm = XMPPConnectionManager(app, presence_helper_mock, xmpp_client_mock)
        self.assertEqual(cm.alive_chats, presence_helper_mock.alive_conferences)

    def test_send(self):
        """ Test messages sending """
        app = _Application.create()
        xmpp_client_mock = Mock()

        presence_helper_mock = Mock()
        presence_helper_mock.is_alive.side_effect = [True, False]

        chats = [Conference.from_string('chat1@server/1'), Conference.from_string('chat2@server/2')]
        message = 'Hello, chat!'

        cm = XMPPConnectionManager(app, presence_helper_mock, xmpp_client_mock)

        cm.send(message, chats[0])
        self.assertRaises(S2SConnectionError, cm.send, message, chats[1])
        xmpp_client_mock.chat.assert_called_once_with(message, chats[0].bare)

    def test_registration(self):
        """ Test service registration """
        app = _Application.create()
        app.depend(XMPPConnectionManager)

        self.assertIsInstance(app.registry.xmpp, XMPPConnectionManager)


class TestPresenceHelper(unittest.TestCase):
    """ Tests suite for dewyatochka.core.network.xmpp.service.PresenceHelper """

    @staticmethod
    def create_connection_manager() -> XMPPConnectionManager:
        """ Create test helper instance

        :return XMPPConnectionManager:
        """
        connection_manager_mock = Mock()
        connection_manager_mock.name.return_value = 'xmpp'

        return connection_manager_mock

    def test_start_stop(self):
        """ Test start/stop methods """
        def _threads() -> list:
            return {t.name for t in threading.enumerate()
                    if t.name.startswith(XMPPConnectionManager.name()) and t.is_alive()}

        connection_manager = self.create_connection_manager()
        presence_helper = PresenceHelper(connection_manager)

        try:
            presence_helper.start()
            self.assertEqual(_threads(), {'xmpp[PresenceHelper][Ping]', 'xmpp[PresenceHelper][Reenter]'})
        finally:
            presence_helper.stop()
            self.assertEqual(_threads(), set())

        self.assertRaises(RuntimeError, presence_helper.stop)

    def test_enter_leave(self):
        """ Test conference entering / leaving """
        connection_manager = self.create_connection_manager()

        with PresenceHelper(connection_manager) as presence_helper:
            conference1 = Conference.from_string('conference1@server.com')
            conference2 = Conference.from_string('conference2@server.com')
            conference3 = Conference.from_string('conference2@server.com/foo')

            presence_helper.enter(conference1)
            presence_helper.enter(conference2)
            presence_helper.enter(conference3)
            presence_helper.enter(conference1)
            connection_manager.client.chat.enter.assert_has_calls([
                call(conference1.bare, conference1.resource),
                call(conference2.bare, conference2.resource),
            ])
            self.assertTrue(presence_helper.is_alive(conference1))
            self.assertTrue(presence_helper.is_alive(conference2))
            self.assertEqual(
                presence_helper.alive_conferences,
                {conference1, conference2}
            )

            presence_helper.leave(conference1)
            presence_helper.leave(conference1)
            connection_manager.client.chat.leave.assert_called_once_with(conference1, conference1.resource)
            self.assertFalse(presence_helper.is_alive(conference1))
            self.assertTrue(presence_helper.is_alive(conference2))

    def test_enter_leave_all(self):
        """ Test entering / leaving all the configured conferences """
        raw_config = Predefined({
            'regular_conference': {
                'room': 'regular@conference.com',
                'nick': 'username',
            },
            'invalid_room': {
                'room': 'foo',
                'nick': 'username',
            },
            'empty_room': {
                'nick': 'username',
            },
            'empty_nick': {
                'room': 'regular@conference2.com',
            },
        })

        xmpp_client_mock = Mock()

        application = _Application.create()
        application.depend(ConferencesConfig)
        application.registry.conferences_config.load(raw_config)

        with PresenceHelper(XMPPConnectionManager(application, xmpp_client=xmpp_client_mock)) as presence_helper:
            presence_helper.enter_all()
            self.assertEqual(
                set(presence_helper.alive_conferences),
                {Conference.from_string('regular@conference.com')}
            )
            presence_helper.leave_all()
            self.assertEqual(presence_helper.alive_conferences, frozenset())

    def test_clear_state(self):
        """ Test clearing state """
        with PresenceHelper(self.create_connection_manager()) as presence_helper:
            conference = Conference.from_string('conference@server.com/foo')
            presence_helper.enter(conference)
            presence_helper.clear_state()
            self.assertEqual(presence_helper.alive_conferences, frozenset())

    def test_get_presence_jid(self):
        """ Test full jid determination """
        with PresenceHelper(self.create_connection_manager()) as presence_helper:
            conference = Conference.from_string('conference@server.com/username')
            presence_helper.enter(conference)
            self.assertEqual(presence_helper.get_presence_jid(conference.bare), conference)
            self.assertRaises(RuntimeError, presence_helper.get_presence_jid, Conference.from_string('foo@bar'))

    @patch('dewyatochka.core.network.xmpp.service._XMPP_RECONNECT_INTERVAL', 0.02)
    def test_schedule_reenter(self):
        """ Test conference re-enter scheduling """
        connection_manager = self.create_connection_manager()
        with PresenceHelper(connection_manager) as presence_helper:
            conference = Conference.from_string('conference@server.com/username')

            # Normal re-enter
            presence_helper.enter(conference)
            presence_helper.schedule_reenter(conference)
            time.sleep(0.02)
            connection_manager.client.chat.enter.assert_has_calls([
                call(conference.bare, conference.resource)
            ])
            time.sleep(0.02)
            connection_manager.client.chat.enter.assert_has_calls([
                call(conference.bare, conference.resource), call(conference.bare, conference.resource)
            ])

            # Re-enter task enqueue on fail
            connection_manager.client.chat.enter.reset_mock()
            connection_manager.client.chat.enter.side_effect = XMPPError
            presence_helper.schedule_reenter(conference)
            time.sleep(0.05)
            connection_manager.client.chat.enter.assert_has_calls([
                call(conference.bare, conference.resource), call(conference.bare, conference.resource)
            ])

            # Test behaviour on duplicate re-enter attempt
            connection_manager.client.chat.enter.reset_mock()
            connection_manager.client.chat.enter.side_effect = None
            presence_helper.schedule_reenter(conference)
            time.sleep(0.02)
            presence_helper.schedule_reenter(conference)
            time.sleep(0.02)
            connection_manager.client.chat.enter.assert_has_calls([
                call(conference.bare, conference.resource)
            ])

            # On unknown error
            connection_manager.client.chat.enter.side_effect = Exception
            presence_helper.schedule_reenter(conference)
            time.sleep(0.2)
            self.assertEqual(connection_manager.application.fatal_error.call_count, 1)

    @patch('dewyatochka.core.network.xmpp.service._XMPP_RECONNECT_INTERVAL', 0.01)
    @patch('dewyatochka.core.network.xmpp.service._XMPP_CHECK_INTERVAL', 0.02)
    def test_ping(self):
        """ Test conferences pinging """
        connection_manager = self.create_connection_manager()
        with PresenceHelper(connection_manager) as presence_helper:
            conference1 = Conference.from_string('conference@server1.com/username')
            conference2 = Conference.from_string('conference@server2.com/username')
            conference3 = Conference.from_string('conference@server3.com/username')

            connection_manager.client.ping.side_effect = [
                42, S2SConnectionError(remote=Conference.from_string('conference@server.com')), Exception, 43
            ]

            presence_helper.enter(conference1)
            presence_helper.enter(conference2)
            presence_helper.enter(conference3)

            time.sleep(0.06)
            connection_manager.client.chat.enter.assert_has_calls([
                call(conference1.bare, conference1.resource),
                call(conference2.bare, conference2.resource),
                call(conference3.bare, conference3.resource),
                ANY,
            ], any_order=True)

    @patch('dewyatochka.core.network.xmpp.service._XMPP_CHECK_INTERVAL', 0.01)
    def test_ping_fatal_error(self):
        """ Test fatal errors handling in ping thread """
        connection_manager = self.create_connection_manager()
        connection_manager.application.sleep.side_effect = Exception
        with PresenceHelper(connection_manager) as presence_helper:
            presence_helper.enter(Conference.from_string('conference@server.com/username'))
        self.assertEqual(connection_manager.application.fatal_error.call_count, 2)
