# -*- coding=utf-8

""" Tests suite for dewyatochka.core.plugin.message_sys.service """

import unittest
from unittest.mock import Mock, call, patch

from dewyatochka.core.plugin.message_sys.service import *
from dewyatochka.core.plugin.message_sys.matcher.standard import *
from dewyatochka.core.plugin.base import Wrapper as BaseWrapper
from dewyatochka.core.plugin.base import PluginEntry
from dewyatochka.core.plugin.exceptions import PluginRegistrationError
from dewyatochka.core.application import Registry, VoidApplication
from dewyatochka.core.network.xmpp.entity import JID, ChatMessage


class TestEnvironment(unittest.TestCase):
    """ Covers dewyatochka.core.plugin.message_sys.service.Environment """

    def test_invoke(self):
        """ Test message plugin call """
        plugin_fn = Mock()
        registry = Registry()
        matcher = Mock()
        matcher.match.side_effect = (True, False)
        message = ChatMessage(JID.from_string('jid1@example.com'), JID.from_string('jid1@example.com'), 'text')
        additional_args = {'foo': 'bar'}

        env = Environment(plugin_fn, registry, None, matcher)
        env._output_wrappers[str(message.sender.bare)] = Output(None, None)
        env.invoke(message=message, **additional_args)
        env.invoke(message=message, **additional_args)

        plugin_fn.assert_called_once_with(inp=message,
                                          outp=env._output_wrappers[str(message.sender.bare)],
                                          registry=registry,
                                          foo='bar')
        matcher.match.assert_has_calls([call(message), call(message)])


class TestService(unittest.TestCase):
    """ Covers dewyatochka.core.plugin.message_sys.service.Service """

    def test_accepts(self):
        """ Test acceptable plugins types list getter """
        self.assertEqual(['message', 'chat_command'], Service(VoidApplication()).accepts)

    def test_name(self):
        """ Test service name getter """
        self.assertEqual('chat', Service.name())


class TestWrapper(unittest.TestCase):
    """ Covers dewyatochka.core.plugin.message_sys.service.Wrapper """

    @patch.object(BaseWrapper, '_get_registry')
    def test_wrap(self, registry_getter_mock):
        """ Test message plugin wrapping """
        registry = Registry()
        registry_getter_mock.return_value = registry

        service = Mock()
        service.config = {'command_prefix': '!'}

        plugin_fn = lambda: None

        entry_message = PluginEntry(plugin_fn, {'type': 'message', 'regular': False, 'system': True, 'own': True})
        entry_command = PluginEntry(plugin_fn, {'type': 'chat_command', 'command': 'foo'})
        entry_unknown = PluginEntry(plugin_fn, {})
        entry_bad_cmd = PluginEntry(plugin_fn, {'type': 'chat_command'})

        wrapper = Wrapper(service)

        env_msg = wrapper.wrap(entry_message)
        env_cmd = wrapper.wrap(entry_command)
        self.assertRaises(PluginRegistrationError, wrapper.wrap, entry_unknown)
        self.assertRaises(PluginRegistrationError, wrapper.wrap, entry_bad_cmd)

        self.assertEqual(plugin_fn, env_msg._plugin)
        self.assertIsInstance(env_msg._matcher, Matcher)
        self.assertEqual(2, len(env_msg._matcher._conditions))

        self.assertEqual(plugin_fn, env_cmd._plugin)
        self.assertIsInstance(env_cmd._matcher, CommandMatcher)
        self.assertEqual('^\\!foo([\t\\s]+.*|$)', env_cmd._matcher._cmd_regexp.pattern)
