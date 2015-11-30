# -*- coding=utf-8

""" Tests suite for dewyatochka.core.network.service """

import unittest

from dewyatochka.core.network.service import *
from dewyatochka.core.network.entity import Participant
from dewyatochka.core.application import Application, VoidApplication


class _ChatManagerImpl(ChatManager):
    """ Chat manager implementation stub """

    def __init__(self, application: Application):
        """ Initialize service & attach an application to it

        :param Application application:
        """
        super().__init__(application)
        self.connection_managers = []

    def alive_chats(self) -> frozenset:
        """ Get alive conferences

        :return frozenset:
        """
        return frozenset()

    def send(self, message: str, chat: Participant):
        """ Send a message to groupchat

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
        self.connection_managers.append(connection)


class _ConnectionManagerImpl(ConnectionManager):
    """ Connection manager implementation stub """

    def connect(self):
        """ Establish connection

        :return None:
        """
        pass

    def disconnect(self):
        """ Force disconnection

        :return None:
        """
        pass

    def alive_chats(self) -> frozenset:
        """ Get alive conferences

        :return frozenset:
        """
        return frozenset()

    def send(self, message: str, chat: Participant):
        """ Send a message to groupchat

        :param str message: Message content
        :param GroupChat chat: Destination chat
        :return None:
        """
        pass

    def input_stream(self):
        """ Wrapper over xmpp client input stream

        Implements auto reconnection and conferences re-enter
        if something goes wrong

        :return Message:
        """
        raise StopIteration()


class TestChatManager(unittest.TestCase):
    """ Tests suite for dewyatochka.core.network.ChatManager """

    def test_registration(self):
        """ Test service registration """
        app = VoidApplication()
        app.depend(_ChatManagerImpl)

        self.assertIsInstance(app.registry.chat_manager, _ChatManagerImpl)


class TestConnectionManager(unittest.TestCase):
    """ Tests suite for dewyatochka.core.network.ChatManager """

    def test_registration(self):
        """ Test service registration """
        app = VoidApplication()
        app.depend(_ChatManagerImpl)
        app.depend(_ConnectionManagerImpl)

        self.assertEqual(app.registry.chat_manager.connection_managers,
                         [app.registry.get_service(_ConnectionManagerImpl)])
