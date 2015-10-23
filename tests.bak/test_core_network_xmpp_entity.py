# -*- coding=utf-8

""" Tests suite for dewyatochka.core.network.xmpp.entity """

import itertools

import unittest

from dewyatochka.core.network.xmpp.entity import *


class TestJID(unittest.TestCase):
    """ Covers dewyatochka.core.network.xmpp.entity.JID """

    def test_properties(self):
        """ Test JID instance properties """
        login = 'user'
        server = 'example.com'
        resource = 'foo'
        jid_str = 'user@example.com/foo'

        jid = JID(login, server, resource)
        self.assertEqual(login, jid.login)
        self.assertEqual(server, jid.server)
        self.assertEqual(resource, jid.resource)
        self.assertEqual(jid_str, jid.jid)
        self.assertEqual(jid_str, str(jid))
        self.assertIsInstance(hash(jid), int)

        jid_without_resource = JID(login, server)
        self.assertEqual(jid_str.split('/')[0], jid_without_resource.jid)
        self.assertEqual('', jid_without_resource.resource)
        self.assertEqual(jid_without_resource, jid_without_resource.bare)
        self.assertEqual(jid_without_resource, jid.bare)
        self.assertNotEqual(hash(jid), hash(jid_without_resource))

    def test_eq(self):
        """ Test two JIDs comparison """
        for jid_params_1 in itertools.combinations('abc ', 3):
            for jid_params_2 in itertools.combinations('abc ', 3):
                jid1 = JID(*jid_params_1)
                jid2 = JID(*jid_params_2)
                self.assertEqual(str(jid1) == str(jid2), jid1 == jid2)

    def test_from_string(self):
        """ Test parsing JID from string """
        jid_str = 'user@example.com/foo'

        jid = JID.from_string(jid_str)
        self.assertEqual(jid_str, str(jid))

        self.assertRaises(ValueError, JID.from_string, '@@@')
        self.assertRaises(ValueError, JID.from_string, 'foo@bar/b/a/z')


# class TestMessage(unittest.TestCase):
#     """ Covers dewyatochka.core.network.xmpp.entity.Message """
#
#     def test_properties(self):
#         """ Test Message instance properties """
#         sender = JID.from_string('user1@example.com')
#         receiver = JID.from_string('user2@example.com')
#
#         message = Message(sender, receiver)
#         self.assertEqual(sender, message.sender)
#         self.assertEqual(receiver, message.receiver)


# class TestChatMessage(unittest.TestCase):
#     """ Covers dewyatochka.core.network.xmpp.entity.ChatMessage """
#
#     def test_properties(self):
#         """ Test Message instance properties """
#         text = 'Hello, world'
#
#         message = ChatMessage(JID.from_string('user1@example.com'), JID.from_string('user2@example.com'), text=text)
#         self.assertEqual(text, message.text)
#         self.assertEqual(text, str(message))
