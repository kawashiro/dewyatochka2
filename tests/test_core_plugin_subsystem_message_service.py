# -*- coding=utf-8

""" Tests suite for dewyatochka.core.plugin.subsystem.message.service """

import unittest
from unittest.mock import Mock, call, patch

from dewyatochka.core.plugin.subsystem.message.service import *
from dewyatochka.core.plugin.subsystem.message.matcher.standard import *
from dewyatochka.core.plugin.base import Wrapper as BaseWrapper
from dewyatochka.core.plugin.base import PluginEntry
from dewyatochka.core.plugin.exceptions import PluginRegistrationError
from dewyatochka.core.application import Registry, VoidApplication
from dewyatochka.core.network.xmpp.entity import JID
from dewyatochka.core.network.entity import TextMessage


class TestEnvironment(unittest.TestCase):
    """ Covers dewyatochka.core.plugin.subsystem.message.service.Environment """

    def test_invoke(self):
        """ Test message plugin call """
        plugin_fn = Mock()
        registry = Registry()
        matcher = Mock()
        matcher.match.side_effect = (True, False)
        message = TextMessage(JID.from_string('jid1@example.com'), JID.from_string('jid1@example.com'), text='text')
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

        self.assertRaises(TypeError, env.invoke)


class TestService(unittest.TestCase):
    """ Covers dewyatochka.core.plugin.subsystem.message.service.Service """

    def test_accepts(self):
        """ Test acceptable plugins types list getter """
        self.assertEqual(['message', 'chat_command', 'accost'], Service(VoidApplication()).accepts)
