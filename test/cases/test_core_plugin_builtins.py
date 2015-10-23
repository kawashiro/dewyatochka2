# -*- coding=utf-8

""" Tests suite for dewyatochka.core.plugin.builtins """

import unittest

from dewyatochka.core.plugin.builtins import *
from dewyatochka.core.network.xmpp.entity import Conference
from dewyatochka.core.plugin.loader import internal


class TestActivityInfo(unittest.TestCase):
    """ Tests suite for dewyatochka.core.plugin.builtins.ActivityInfo/get_activity_info """

    def test_get_activity_info(self):
        """ Test activity info registration """
        chat = Conference.from_string('foo@bar/baz')
        activity_info = get_activity_info(chat)
        self.assertEqual(get_activity_info(chat), activity_info)
        self.assertEqual(activity_info.conference, chat.self)


class TestRegisterEntryPoints(unittest.TestCase):
    """ Tests suite for dewyatochka.core.plugin.builtins.register_entry_points """

    def assert_has_message_handler(self, entries, regular=True, own=False, system=False):
        """ Check if message type is handled

        :param dict entries:
        :param bool regular:
        :param bool own:
        :param bool system:
        :return None:
        """
        for entry in entries['message']:
            if entry.params.get('regular') == regular \
                    and entry.params.get('own') == own \
                    and entry.params.get('system') == system:
                break
        else:
            self.fail('Such message is not handled')

    def assert_has_chat_command_handler(self, entries, command):
        """ Check if chat command is handled

        :param dict entries:
        :param str command:
        :return None:
        """
        for entry in entries['chat_command']:
            if entry.params.get('command') == command:
                break
        else:
            self.fail('Chat command `%s` is not handled' % command)

    def assert_has_ctl_command_handler(self, entries, command):
        """ Check if ctl command is handled

        :param dict entries:
        :param str command:
        :return None:
        """
        for entry in entries['ctl']:
            if entry.params.get('name') == command:
                break
        else:
            self.fail('Ctl command `%s` is not handled' % command)

    def test_registration(self):
        """ Test entry points registration """
        register_entry_points()
        entries = internal._entry_points

        self.assert_has_message_handler(entries, regular=True, own=True, system=False)
        self.assert_has_message_handler(entries, regular=False, own=False, system=True)

        self.assert_has_chat_command_handler(entries, 'version')
        self.assert_has_chat_command_handler(entries, 'help')
        self.assert_has_chat_command_handler(entries, 'info')

        self.assert_has_ctl_command_handler(entries, 'list')
        self.assert_has_ctl_command_handler(entries, 'version')
