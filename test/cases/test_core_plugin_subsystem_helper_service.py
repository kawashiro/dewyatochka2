# -*- coding=utf-8

""" Tests suite for dewyatochka.core.plugin.subsystem.helper.service """

import threading

import unittest
from unittest.mock import Mock

from dewyatochka.core.plugin.subsystem.helper.service import *
from dewyatochka.core.application import Registry, VoidApplication
from dewyatochka.core.config.container import ExtensionsConfig
from dewyatochka.core.plugin.base import PluginEntry
from dewyatochka.core.plugin.base import Environment as BaseEnvironment
from dewyatochka.core.plugin.subsystem.helper.schedule import Schedule


class TestScheduleEnvironment(unittest.TestCase):
    """ Tests suite for dewyatochka.core.plugin.subsystem.helper.service.ScheduleEnvironment """

    def test_invoke(self):
        """ Test plugin invoke """
        assert_is_instance = self.assertIsInstance

        def _plugin(**kwargs):
            assert_is_instance(kwargs['registry'], Registry)
            barrier.wait()

        # Default
        barrier = threading.Barrier(2)
        environment = ScheduleEnvironment(_plugin, Registry(), Schedule.from_string('@minutely'))
        threading.Thread(target=environment).start()
        self.assertRaises(RuntimeError, environment)
        barrier.wait()

        # Not locked
        barrier = threading.Barrier(2)
        plugin_mock = Mock(side_effect=lambda **_: barrier.wait())
        environment = ScheduleEnvironment(plugin_mock, Registry(), Schedule.from_string('@minutely'), False)
        threading.Thread(target=environment).start()
        environment()
        self.assertEqual(plugin_mock.call_count, 2)

        # Check not in time
        plugin_mock = Mock()
        environment = ScheduleEnvironment(_plugin, Registry(), Schedule.from_string('* * 30 2 *'))
        environment()
        self.assertEqual(plugin_mock.call_count, 0)


class TestWrapper(unittest.TestCase):
    """ Tests suite for dewyatochka.core.plugin.subsystem.helper.service.Wrapper """

    def test_wrap(self):
        """ Test wrap method """
        application = VoidApplication()
        application.depend(ExtensionsConfig)
        application.depend(Mock(), 'log')

        wrapper = Wrapper(Service(application))
        schedule_env = wrapper.wrap(PluginEntry(lambda **_: None, dict(type='schedule', schedule='@annually')))
        bootstrap_env = wrapper.wrap(PluginEntry(lambda **_: None, dict(type='bootstrap')))

        self.assertIsInstance(schedule_env, ScheduleEnvironment)
        self.assertIsInstance(bootstrap_env, BaseEnvironment)


class TestService(unittest.TestCase):
    """ Tests suite for dewyatochka.core.plugin.subsystem.helper.service.Service """

    def test_loading(self):
        """ Test plugins loading """
        loader_mock = Mock()
        loader_mock.load.return_value = [
            PluginEntry(lambda **_: None, dict(type='schedule', schedule='@minutely')),
            PluginEntry(lambda **_: None, dict(type='bootstrap')),
            PluginEntry(lambda **_: None, dict(type='daemon')),
        ]
        loader_service_mock = Mock()
        loader_service_mock.loaders = [loader_mock]

        application = VoidApplication()
        application.depend(loader_service_mock, 'plugins_loader')
        application.depend(Mock(), 'extensions_config')
        application.depend(Mock(), 'log')

        service = Service(application)
        self.assertRaises(RuntimeError, lambda: service.schedule_plugins)

        service.load()
        self.assertEqual(len(service.plugins), 3)
        self.assertEqual(len(service.schedule_plugins), 1)
        self.assertEqual(len(service.daemon_plugins), 1)
        self.assertEqual(len(service.bootstrap_plugins), 1)

    def test_accepts(self):
        """ Test acceptable plugin types getter """
        self.assertEqual(set(Service(VoidApplication()).accepts), {'schedule', 'daemon', 'bootstrap'})

    def test_registration(self):
        """ Test service registration """
        application = VoidApplication()
        application.depend(Service)

        self.assertIsInstance(application.registry.helper_plugin_provider, Service)
