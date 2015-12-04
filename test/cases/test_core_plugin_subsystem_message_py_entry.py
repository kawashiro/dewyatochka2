# -*- coding=utf-8

""" Tests suite for dewyatochka.core.plugin.subsystem.message.py_entry """

import unittest
from unittest.mock import call, patch

from dewyatochka.core.plugin.subsystem.message.py_entry import *
from dewyatochka.core.plugin.exceptions import PluginRegistrationError


def _entry(**_):
    """ Dummy entry point fn """
    pass


class TestChatMessage(unittest.TestCase):
    """ Tests suite for dewyatochka.core.plugin.subsystem.message.py_entry.chat_message """

    @patch('dewyatochka.core.plugin.subsystem.message.py_entry.entry_point')
    def test_decorator(self, entry_point_mock):
        """ Test @chat_message decorator """
        chat_message(services=['service1', 'service2'], own=True)(_entry)
        chat_message(_entry)

        entry_point_mock.assert_has_calls([
            call('message', own=True, services=['service1', 'service2'], system=False, regular=False),
            call()(_entry),
            call('message', own=False, services=None, system=False, regular=True),
            call()(_entry)
        ])


class TestChatCommand(unittest.TestCase):
    """ Tests suite for dewyatochka.core.plugin.subsystem.message.py_entry.chat_command """

    @patch('dewyatochka.core.plugin.subsystem.message.py_entry.entry_point')
    def test_decorator(self, entry_point_mock):
        """ Test @chat_command decorator """
        chat_command('name1', services=['service1', 'service2'])(_entry)
        chat_command('name2')(_entry)

        self.assertRaises(PluginRegistrationError, chat_command, 'name2')
        entry_point_mock.assert_has_calls([
            call('chat_command', services=['service1', 'service2'], command='name1'),
            call()(_entry),
            call('chat_command', services=None, command='name2'),
            call()(_entry)
        ])


class TestChatAccost(unittest.TestCase):
    """ Tests suite for dewyatochka.core.plugin.subsystem.message.py_entry.chat_accost """

    @patch('dewyatochka.core.plugin.subsystem.message.py_entry.entry_point')
    def test_decorator(self, entry_point_mock):
        """ Test @chat_accost decorator """
        chat_accost(services=['service1', 'service2'])(_entry)
        chat_accost(_entry)

        entry_point_mock.assert_has_calls([
            call('accost', services=['service1', 'service2']),
            call()(_entry),
            call('accost', services=None),
            call()(_entry)
        ])
