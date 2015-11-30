# -*- coding=utf-8

""" Tests suite for dewyatochka.core.network.xmpp.entity """

import unittest

from dewyatochka.core.network.xmpp.entity import *


class TestJID(unittest.TestCase):
    """ Tests suite for dewyatochka.core.network.xmpp.entity.JID """

    def test_properties(self):
        """ Test JID properties """
        jid = JID('login', 'server.com', 'resource')

        self.assertEqual(jid.login, 'login')
        self.assertEqual(jid.server, 'server.com')
        self.assertEqual(jid.resource, 'resource')
        self.assertEqual(jid.bare, JID('login', 'server.com'))
        self.assertEqual(jid.jid, 'login@server.com/resource')
        self.assertEqual(jid.public_name, 'resource')
        self.assertEqual(str(jid), 'login@server.com/resource')
        self.assertEqual(jid.chat, Conference.from_string('login@server.com'))

    def test_empty_resource(self):
        """ Test properties for JID with no resource """
        jid = JID('login', 'server.com')

        self.assertEqual(str(jid), 'login@server.com')
        self.assertEqual(jid.bare, jid)

    def test_from_string(self):
        """ Test string parsing """
        self.assertEqual(JID.from_string('login@server.com/resource'), JID('login', 'server.com', 'resource'))
        self.assertEqual(JID.from_string('login@server.com'), JID('login', 'server.com'))
        self.assertEqual(JID.from_string('login@server.com'), JID('login', 'server.com'))

        self.assertRaises(ValueError, JID.from_string, 'foo')
        self.assertRaises(ValueError, JID.from_string, 'foo@bar/baz/')
        self.assertRaises(ValueError, JID.from_string, 'foo@bar@baz')


class TestConference(unittest.TestCase):
    """ Tests suite for dewyatochka.core.network.xmpp.entity.Conference """

    def test_properties(self):
        """ Test conference properties """
        conf = Conference.from_string('room@conference.example.com/nickname')
        self.assertEqual(conf.public_name, 'room@conference.example.com')
        self.assertEqual(conf.chat, conf.bare)

    def test_from_config(self):
        """ Test instantiating from separated room & nick values """
        self.assertEqual(
            Conference.from_config('room@conference.example.com', 'nickname'),
            Conference.from_string('room@conference.example.com/nickname')
        )


class TestChatSubject(unittest.TestCase):
    """ Tests suite for dewyatochka.core.network.xmpp.entity.ChatSubject """

    def test_properties(self):
        """ Test chat subject sys message properties """
        subj = ChatSubject(JID('sender', 'server'), JID('receiver', 'server'), text='Chat subj. text')

        self.assertEqual(subj.subject, 'Chat subj. text')
        self.assertTrue(subj.is_system)


class TestChatPresence(unittest.TestCase):
    """ Tests suite for dewyatochka.core.network.xmpp.entity.ChatPresence """

    def test_properties(self):
        """ Test chat presence properties """
        presence = ChatPresence(
            sender=JID.from_string('room@conference.example.com/somebody'),
            receiver=JID.from_string('room@conference.example.com/me'),
            role='participant',
            type='available',
            status='foo'
        )

        self.assertEqual(presence.type, 'available')
        self.assertEqual(presence.status, 'foo')
        self.assertEqual(presence.role, 'participant')
        self.assertTrue(presence.is_system)

        self.assertEqual(str(presence), 'Participant somebody is now available (foo)')
