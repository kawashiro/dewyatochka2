# coding=utf-8

"""
Tests suite for dewyatochka.core.application
"""

import unittest
from unittest.mock import patch, Mock, PropertyMock, MagicMock
from threading import Event
from dewyatochka.core.application import *
from testlib.application import VoidApplication, EmptyService, EmptyNamedService


class TestApplication(unittest.TestCase):
    """
    dewyatochka.core.application.Application
    """

    def test_init(self):
        """
        Test __init__()
        """
        app = VoidApplication()

        self.assertIsInstance(app._registry, Registry)
        self.assertIsInstance(app._stop_event, Event)
        self.assertFalse(app._stop_event.is_set())
        self.assertEqual(0, app._exit_code)

        test_registry = Registry()
        app = VoidApplication(test_registry)
        self.assertEqual(test_registry, app._registry)

    def test_registry(self):
        """
        Test registry getter
        """
        app = VoidApplication()
        self.assertEqual(app._registry, app.registry)

    @patch.object(Event, 'wait')
    def test_wait(self, wait_method):
        """
        Test wait method
        """
        app = VoidApplication()
        app._stop_event = Event()
        app.wait()
        wait_method.assert_called_once_with()

    @patch.object(Event, 'set')
    def test_stop(self, wait_method):
        """
        Test application stop event
        """
        exit_code = 9000

        app = VoidApplication()
        app._stop_event = Event()
        app.stop(exit_code)

        wait_method.assert_called_once_with()
        self.assertEqual(exit_code, app._exit_code)

    @patch.object(VoidApplication, 'stop')
    def test_fatal_error(self, stop_method):
        """
        Test app fatal error
        """
        registry = PropertyMock()
        registry.log.fatal_error = Mock()

        app = VoidApplication(registry)
        module = 'foo_module'
        exception = Exception()
        app.fatal_error(module, exception)

        stop_method.assert_called_once_with(1)
        registry.log.fatal_error.assert_called_once_with(module, exception)

    @patch.object(VoidApplication, 'stop')
    def test_fatal_error_log_fail(self, stop_method):
        """
        Test app fatal error handling on logging failed
        """
        registry = PropertyMock()
        registry.log.fatal_error = Mock(side_effect=Exception)

        app = VoidApplication(registry)
        module = 'foo_module'
        exception = Exception()
        app.fatal_error(module, exception)

        stop_method.assert_called_once_with(1)
        registry.log.fatal_error.assert_called_once_with(module, exception)

    @patch.object(Event, 'is_set')
    def test_running(self, is_set_method):
        """
        Test `running` property
        """
        is_set_method.side_effect = True, False

        app = VoidApplication()
        app._stop_event = Event()

        self.assertFalse(app.running)
        self.assertTrue(app.running)
        self.assertEqual(2, is_set_method.call_count)


class TestService(unittest.TestCase):
    """
    dewyatochka.core.application.Service
    """

    def test_init(self):
        """
        Test __init__ method
        """
        app = VoidApplication()
        service = EmptyService(app)

        self.assertEqual(app, service.application)

    def test_application(self):
        """
        Test application property
        """
        app = VoidApplication()
        service = EmptyService(app)

        self.assertEqual(app, service.application)

    @patch.object(EmptyService, 'name')
    def test_config(self, name_method):
        """
        Test service config getter
        """
        service_name = 'foo_service'
        service_config = {'foo': 'bar'}

        name_method.side_effect = (service_name,)
        registry_mock = PropertyMock()
        registry_mock.config.section = Mock(side_effect=(service_config,))

        service = EmptyService(VoidApplication(registry_mock))
        self.assertEqual(service_config, service.config)
        registry_mock.config.section.assert_called_once_with(service_name)

    @patch.object(EmptyService, 'name')
    def test_log(self, name_method):
        """
        Test service config getter
        """
        service_name = 'foo_service'

        name_method.side_effect = (service_name,)
        registry_mock = PropertyMock()

        self.assertIsInstance(EmptyService(VoidApplication(registry_mock)).log, MagicMock)
        registry_mock.log.assert_called_once_with(service_name)

    def test_name(self):
        """
        Test default name property
        """
        self.assertEqual('testlib.application.EmptyService', EmptyService.name())


class TestRegistry(unittest.TestCase):
    """
    dewyatochka.core.application.Registry
    """

    def test_init(self):
        """
        Test __init__ method
        """
        registry = Registry()
        self.assertEqual({}, registry._services)

    def test_service_registration(self):
        """
        Test add_service() / get_service()
        """
        service = EmptyNamedService(VoidApplication())

        registry = Registry()
        registry.add_service(service)

        self.assertEqual(service, registry.get_service('test_service'))
        self.assertEqual(service, registry.get_service(EmptyNamedService))
        self.assertEqual(service, registry.test_service)

    def test_unregistered_service(self):
        """
        Test that RuntimeError is thrown if service is not registered
        """
        registry = Registry()
        self.assertRaises(RuntimeError, registry.get_service, 'foo')
