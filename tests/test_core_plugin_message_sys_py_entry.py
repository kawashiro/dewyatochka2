# -*- coding=utf-8

""" Tests suite for dewyatochka.core.plugin.message_sys.py_entry """

import unittest

from dewyatochka.core.plugin.message_sys.py_entry import *
from dewyatochka.core.plugin.loader import internal
from dewyatochka.core.plugin.exceptions import PluginRegistrationError


class TestChatMessage(unittest.TestCase):
    """ Covers dewyatochka.core.plugin.message_sys.py_entry.chat_message """

    def test_wrap(self):
        """ Test @chat_message decorator """
        plugin_fn = lambda: None
        services = ['foo', 'bar']

        chat_message(plugin_fn)
        chat_message(services=services, regular=False, system=True, own=True)(plugin_fn)

        entry_points = internal._entry_points['message']
        self.assertEqual(plugin_fn, entry_points[0].plugin)
        self.assertEqual({
            'services': None,
            'type': 'message',
            'regular': True,
            'system': False,
            'own': False
        }, entry_points[0].params)
        self.assertEqual(plugin_fn, entry_points[1].plugin)
        self.assertEqual({
            'services': services,
            'type': 'message',
            'regular': False,
            'system': True,
            'own': True
        }, entry_points[1].params)


class TestChatCommand(unittest.TestCase):
    """ Covers dewyatochka.core.plugin.message_sys.py_entry.chat_command """

    def test_wrap(self):
        """ Test @chat_command decorator """
        plugin_fn = lambda: None
        services = ['foo', 'bar']

        chat_command('cmd1')(plugin_fn)
        chat_command('cmd2', services=services)(plugin_fn)

        entry_points = internal._entry_points['chat_command']
        self.assertEqual(plugin_fn, entry_points[0].plugin)
        self.assertEqual({'command': 'cmd1', 'type': 'chat_command', 'services': None},
                         entry_points[0].params)
        self.assertEqual(plugin_fn, entry_points[1].plugin)
        self.assertEqual({'command': 'cmd2', 'services': ['foo', 'bar'], 'type': 'chat_command'},
                         entry_points[1].params)

        self.assertRaises(PluginRegistrationError, chat_command, 'cmd1')
