# -*- coding=utf-8

""" Tests suite for dewyatochka.core.plugin.subsystem.message.matcher """

import unittest

from dewyatochka.core.plugin.subsystem.message import matcher


class TestFactory(unittest.TestCase):
    """ Tests suite for dewyatochka.core.plugin.subsystem.message.matcher.factory """

    def test_factory(self):
        """ Test factory function """
        self.assertIsInstance(matcher.factory('message'), matcher.standard.SimpleMatcher)
        self.assertIsInstance(matcher.factory('chat_command', command_prefix='$', command='foo'),
                              matcher.standard.CommandMatcher)
        self.assertIsInstance(matcher.factory('accost'), matcher.standard.AccostMatcher)

        self.assertRaises(matcher.UnknownMatcherError, matcher.factory, 'chat_command', command_prefix='$')
        self.assertRaises(matcher.UnknownMatcherError, matcher.factory, 'chat_command', command='foo')
        self.assertRaises(matcher.UnknownMatcherError, matcher.factory, 'unknown_type')
