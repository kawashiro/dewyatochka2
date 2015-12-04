# -*- coding=utf-8

""" Tests suite for dewyatochka.core.plugin.subsystem.message.matcher.standard """

import unittest

from dewyatochka.core.plugin.subsystem.message.matcher.standard import *
from dewyatochka.core.network.entity import Participant, TextMessage


class _Participant(Participant):
    """ Fake participant impl """

    def __init__(self, name: str):
        """ Set participant name """
        self.__name = name

    @property
    def public_name(self) -> str:
        """ Get public name displayed in chat """
        return self.__name

    def __str__(self) -> str:
        """ str() representation """
        return self.public_name

    @property
    def chat(self):
        """ Chat getter stub """
        return self


class TestSimpleMatcher(unittest.TestCase):
    """ Tests suite for dewyatochka.core.plugin.subsystem.message.matcher.standard.SimpleMatcher """

    def test_match(self):
        """ Test matcher """
        regular_msg = TextMessage(_Participant('sender'), _Participant('receiver'), text='Text message')
        system_msg = TextMessage(_Participant('sender'), _Participant('receiver'), text='System message', system=True)
        own_msg = TextMessage(_Participant('sender'), _Participant('sender'), text='Own message')

        messages = {'regular': regular_msg, 'system': system_msg, 'own': own_msg}
        variants = [{'regular': bool(i & 1), 'system': bool(i & 2), 'own': bool(i & 4)} for i in range(1, 8)]

        for variant in variants:
            matcher = SimpleMatcher(**variant)
            for type_ in variant:
                self.assertEqual(
                    matcher.match(messages[type_]), variant[type_],
                    '%s%s expected to be matched as %s' %
                    (messages[type_], ('' if variant[type_] else ' not'), type_)
                )


class TestCommandMatcher(unittest.TestCase):
    """ Tests suite for dewyatochka.core.plugin.subsystem.message.matcher.standard.CommandMatcher """

    def test_match(self):
        """ Test matcher """
        regular_msg = TextMessage(_Participant('sender'), _Participant('receiver'), text='Text message')
        command_msg_l = TextMessage(_Participant('sender'), _Participant('receiver'), text='$cmd arg1 arg2')
        command_msg_h = TextMessage(_Participant('sender'), _Participant('receiver'), text='$CMD arg1 arg2')
        system_msg = TextMessage(_Participant('sender'), _Participant('receiver'), text='System message', system=True)

        matcher = CommandMatcher('$', 'cmd')
        self.assertFalse(matcher.match(regular_msg))
        self.assertTrue(matcher.match(command_msg_l))
        self.assertTrue(matcher.match(command_msg_h))
        self.assertFalse(matcher.match(system_msg))


class TestAccostMatcher(unittest.TestCase):
    """ Tests suite for dewyatochka.core.plugin.subsystem.message.matcher.standard.AccostMatcher """

    def test_match(self):
        """ Test matcher """
        regular_msg = TextMessage(_Participant('sender'), _Participant('receiver'), text='Text message')
        accost_msg = TextMessage(_Participant('sender'), _Participant('receiver'), text='Hello, receiver')
        system_msg = TextMessage(_Participant('sender'), _Participant('receiver'), text='Hello, receiver', system=True)

        matcher = AccostMatcher()
        self.assertFalse(matcher.match(regular_msg))
        self.assertTrue(matcher.match(accost_msg))
        self.assertFalse(matcher.match(system_msg))
