# -*- coding=utf-8

""" Tests suite for dewyatochka.core.plugin.builtins """

import importlib
import time

import unittest
from unittest.mock import call, Mock

from dewyatochka.core.plugin import builtins

from dewyatochka import __version__
from dewyatochka.core.application import VoidApplication
from dewyatochka.core.config.container import CommonConfig, ExtensionsConfig
from dewyatochka.core.config.source.virtual import Predefined
from dewyatochka.core.network.entity import Participant, TextMessage
from dewyatochka.core.plugin.loader import internal, LoaderService
from dewyatochka.core.plugin.subsystem.control import py_entry as ctl_py_entry
from dewyatochka.core.plugin.subsystem.control import service as ctl_subsystem
from dewyatochka.core.plugin.subsystem.control import network as ctl_network
from dewyatochka.core.plugin.subsystem.message import py_entry as message_py_entry
from dewyatochka.core.plugin.subsystem.message import service as message_subsystem


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


class TestActivityInfo(unittest.TestCase):
    """ Tests suite for dewyatochka.core.plugin.builtins.ActivityInfo/get_activity_info """

    def test_get_activity_info(self):
        """ Test activity info registration """
        participant = _Participant('foo@bar/baz')
        activity_info = builtins.get_activity_info(participant)
        self.assertEqual(builtins.get_activity_info(participant), activity_info)
        self.assertEqual(activity_info.conference, participant.chat)


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
        importlib.reload(internal)
        importlib.reload(ctl_py_entry)
        importlib.reload(message_py_entry)

        builtins.register_entry_points()
        entries = internal._entry_points

        self.assert_has_message_handler(entries, regular=True, own=True, system=False)
        self.assert_has_message_handler(entries, regular=False, own=False, system=True)

        self.assert_has_chat_command_handler(entries, 'version')
        self.assert_has_chat_command_handler(entries, 'help')
        self.assert_has_chat_command_handler(entries, 'info')

        self.assert_has_ctl_command_handler(entries, 'list')
        self.assert_has_ctl_command_handler(entries, 'version')


class TestBuiltins(unittest.TestCase):
    """ Tests suite for dewyatochka.core.plugin.builtins._* """

    @classmethod
    def setUpClass(cls):
        """ Reload builtin plugins before tests & register builtins only

        :return None:
        """
        cls.tearDownClass()
        internal.Loader.lock_state()
        builtins.register_entry_points()

    @classmethod
    def tearDownClass(cls):
        """ Reload modules to reset state after tests

        :return None:
        """
        importlib.reload(internal)
        importlib.reload(ctl_py_entry)
        importlib.reload(message_py_entry)
        importlib.reload(builtins)

    @staticmethod
    def _get_application() -> VoidApplication:
        """ Get initialized app instance

        :return VoidApplication:
        """
        application = VoidApplication()

        application.depend(Mock(), 'log')
        application.depend(Mock(), 'chat_manager')
        application.depend(CommonConfig)
        application.depend(ExtensionsConfig)
        application.depend(LoaderService)
        application.depend(message_subsystem.Service)
        application.depend(ctl_subsystem.Service)

        application.registry.config.load(Predefined({
            'message': {
                'command_prefix': '$',
                'help_message': '{user} :: {version} :: {commands}',
            },
        }))

        return application

    def _get_plugins_svc(self, service: type):
        """ Get registered plugins service

        :param type service:
        :return Service:
        """
        service_obj = self._get_application().registry.get_service(service)
        service_obj.load()

        return service_obj

    @staticmethod
    def _invoke_all(service, **kwargs):
        """ Invoke all plugins with args

        :param Service service:
        :param dict kwargs:
        :return None:
        """
        for plugin in service.plugins:
            plugin(**kwargs)

    def test_version_info(self):
        """ Test version info message """
        sender = _Participant('1')
        message = TextMessage(sender, _Participant('2'), text='$version')
        service = self._get_plugins_svc(message_subsystem.Service)

        self._invoke_all(service, message=message)

        expected_massage = 'dewyatochkad v.%s' % __version__
        service.application.registry.chat_manager.send.assert_called_once_with(expected_massage, sender)

        ctl_service = self._get_plugins_svc(ctl_subsystem.Service)
        connection = Mock()
        ctl_service.get_command('version')(command=ctl_network.Message(name='version', args={}), source=connection)
        connection.send.assert_has_calls([call(b'{"text": "dewyatochkad v.' + __version__.encode() + b'"}\x00')])
        ctl_service.application.registry.log().info.assert_has_calls([call('dewyatochkad v.%s', __version__)])

    def test_help_message(self):
        """ Test help message """
        sender = _Participant('sender')
        message = TextMessage(sender, _Participant('receiver'), text='$help')
        service = self._get_plugins_svc(message_subsystem.Service)

        self._invoke_all(service, message=message)
        service.application.registry.chat_manager.send.assert_called_once_with(
            'sender :: %s :: $help, $info, $version' % __version__, sender
        )

        service.application.registry.config.load(Predefined(
            {'message': {'command_prefix': '$', 'help_message': ''}}
        ))
        self._invoke_all(service, message=message)
        service.application.registry.log().warning.assert_called_once_with(
            'Help message is not configured, command ignored'
        )

    def test_ctl_list(self):
        """ Test control commands listing """
        ctl_py_entry.control('test', 'Test command')(lambda **_: None)

        connection = Mock()
        service = self._get_plugins_svc(ctl_subsystem.Service)
        service.get_command('list')(command=ctl_network.Message(name='list', args={}), source=connection)

        connection.send.assert_has_calls([
            call(b'{"text": "Accessible commands:"}\x00'),
            call(b'{"text": "    list                           : List all the commands available"}\x00'),
            call(b'{"text": "    test_core_plugin_builtins.test : Test command"}\x00'),
            call(b'{"text": "    version                        : Show version"}\x00')
        ])
        service.application.registry.log().info.assert_has_calls([
            call('Accessible commands:'),
            call('    list                           : List all the commands available'),
            call('    test_core_plugin_builtins.test : Test command'),
            call('    version                        : Show version')
        ])

    def test_activity_info(self):
        """ Test chat activity info registration """
        importlib.reload(builtins)  # Statistics reset

        sender = _Participant('1')
        regular_message = TextMessage(sender, _Participant('2'), text='Any message')
        system_message = TextMessage(sender, _Participant('2'), text='System message', system=True)
        service = self._get_plugins_svc(message_subsystem.Service)

        activity_info = builtins.get_activity_info(sender)
        self.assertEqual(activity_info.last_activity, 0.0)
        self.assertEqual(activity_info.last_message, 0.0)

        now = time.time()
        self._invoke_all(service, message=system_message)
        activity_info = builtins.get_activity_info(sender)
        self.assertAlmostEqual(activity_info.last_activity, now, places=1)
        self.assertAlmostEqual(activity_info.last_message, 0.0, places=1)

        self._invoke_all(service, message=regular_message)
        activity_info = builtins.get_activity_info(sender)
        self.assertAlmostEqual(activity_info.last_activity, now, places=1)
        self.assertAlmostEqual(activity_info.last_message, now, places=1)
