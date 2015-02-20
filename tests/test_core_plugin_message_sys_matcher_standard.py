# -*- coding=utf-8

""" Tests suite for dewyatochka.core.plugin.message_sys.matcher.standard """

import unittest

from dewyatochka.core.application import VoidApplication
from dewyatochka.core.config.container import ConferencesConfig
from dewyatochka.core.config.source.virtual import Predefined
from dewyatochka.core.plugin.message_sys.matcher.standard import *
from dewyatochka.core.network.xmpp.entity import *


class TestMatcher(unittest.TestCase):
    """ Covers dewyatochka.core.plugin.message_sys.matcher.standard.Matcher """

    def test_match(self):
        """ Test matching by conditions specified """
        jid_self = JID.from_string('self@example.com/nick')
        jid_other = JID.from_string('other@example.com/other')
        jid_other_sys = JID.from_string('other@example.com')
        conf_config = ConferencesConfig(VoidApplication())
        conf_config.load(Predefined({'c': {'room': 'self@example.com', 'nick': 'nick'}}))

        chat_message = ChatMessage(jid_other, jid_self, 'Normal chat message')
        own_message = ChatMessage(jid_self, jid_self, 'Own message')
        sys_message = ChatMessage(jid_other_sys, jid_self, 'Sys message')

        flag_matches = {'regular': chat_message, 'system': sys_message, 'own': own_message}

        for i in range(0, 7):
            flags = {'regular': bool(i & 1), 'system': bool(i & 2), 'own': bool(i & 4),
                     'conferences_config': conf_config}
            matcher = Matcher(**flags)

            for flag in flag_matches:
                self.assertEqual(flags[flag], matcher.match(flag_matches[flag]),
                                 'message: {}, matcher flags: {}'.format(flag, flags))


class TestCommandMatcher(unittest.TestCase):
    """ Covers dewyatochka.core.plugin.message_sys.matcher.standard.CommandMatcher """

    def test_match(self):
        """ Test matching by conditions specified """
        jid_self = JID.from_string('self@example.com/nick')
        jid_other = JID.from_string('other@example.com/other')
        jid_other_sys = JID.from_string('other@example.com')
        conf_config = ConferencesConfig(VoidApplication())
        conf_config.load(Predefined({'c': {'room': 'self@example.com', 'nick': 'nick'}}))

        chat_message1 = ChatMessage(jid_other, jid_self, '~cmd arg1 arg2')
        chat_message2 = ChatMessage(jid_other, jid_self, '\\cmd_arg1 arg2')
        own_message = ChatMessage(jid_self, jid_self, 'Own message')
        sys_message = ChatMessage(jid_other_sys, jid_self, 'Sys message')
        chat_command = ChatMessage(jid_other, jid_self, '\\cmd arg1 arg2')
        other_chat_command = ChatMessage(jid_other, jid_self, '\\cme arg1 arg2')

        matcher = CommandMatcher(conf_config, '\\', 'cmd')
        self.assertFalse(matcher.match(chat_message1))
        self.assertFalse(matcher.match(chat_message2))
        self.assertFalse(matcher.match(sys_message))
        self.assertFalse(matcher.match(own_message))
        self.assertTrue(matcher.match(chat_command))
        self.assertFalse(matcher.match(other_chat_command))
