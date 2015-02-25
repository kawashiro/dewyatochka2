# -*- coding=utf-8

""" Tests suite for dewyatochka.core.application """

import time
from threading import Event

import unittest
from unittest.mock import patch, Mock, PropertyMock, MagicMock

from dewyatochka.core.application import *


class _EmptyService(Service):
    """ Empty service for tests """
    pass


class _EmptyNamedService(_EmptyService):
    """ Service with own name """

    @classmethod
    def name(cls) -> str:
        """ Get service unique name

        :return str:
        """
        return 'test_service'


class TestApplication(unittest.TestCase):
    """ Covers dewyatochka.core.application.Application """

    def test_init(self):
        """ Test __init__() """
        app = VoidApplication()

        self.assertIsInstance(app._registry, Registry)
        self.assertIsInstance(app._stop_event, Event)
        self.assertFalse(app._stop_event.is_set())
        self.assertEqual(0, app._exit_code)

        test_registry = Registry()
        app = VoidApplication(test_registry)
        self.assertEqual(test_registry, app._registry)

    def test_registry(self):
        """ Test registry getter """
        app = VoidApplication()
        self.assertEqual(app._registry, app.registry)

    @patch.object(Event, 'wait')
    def test_wait(self, wait_method):
        """ Test wait method """
        app = VoidApplication()
        app._stop_event = Event()
        app.wait()
        wait_method.assert_called_once_with()

    @patch.object(Event, 'set')
    def test_stop(self, wait_method):
        """ Test application stop event """
        exit_code = 9000

        app = VoidApplication()
        app._stop_event = Event()
        app.stop(exit_code)

        wait_method.assert_called_once_with()
        self.assertEqual(exit_code, app._exit_code)

    @patch.object(VoidApplication, 'stop')
    def test_fatal_error(self, stop_method):
        """ Test app fatal error """
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
        """ Test app fatal error handling on logging failed """
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
        """ Test `running` property """
        is_set_method.side_effect = True, False

        app = VoidApplication()
        app._stop_event = Event()

        self.assertFalse(app.running)
        self.assertTrue(app.running)
        self.assertEqual(2, is_set_method.call_count)

    def test_sleep(self):
        """ Test stop waiting with timeout """
        app = VoidApplication()

        start = int(time.time())
        app.sleep(1)
        self.assertEqual(start + 1, int(time.time()))

        app.stop()
        start = int(time.time())
        app.sleep(1)
        self.assertEqual(start, int(time.time()))

    def test_depend(self):
        """ Test depend() method """
        app = VoidApplication()
        app.depend(_EmptyNamedService)
        self.assertIsInstance(app.registry.test_service, _EmptyNamedService)

        app = VoidApplication()
        app.depend(_EmptyNamedService(app))
        self.assertIsInstance(app.registry.test_service, _EmptyNamedService)


class TestService(unittest.TestCase):
    """ Covers dewyatochka.core.application.Service """

    def test_init(self):
        """ Test __init__ method """
        app = VoidApplication()
        service = _EmptyService(app)

        self.assertEqual(app, service.application)

    def test_application(self):
        """ Test application property """
        app = VoidApplication()
        service = _EmptyService(app)

        self.assertEqual(app, service.application)

    @patch.object(_EmptyService, 'name')
    def test_config(self, name_method):
        """ Test service config getter """
        service_name = 'foo_service'
        service_config = {'foo': 'bar'}

        name_method.side_effect = (service_name,)
        registry_mock = PropertyMock()
        registry_mock.config.section = Mock(side_effect=(service_config,))

        service = _EmptyService(VoidApplication(registry_mock))
        self.assertEqual(service_config, service.config)
        registry_mock.config.section.assert_called_once_with(service_name)

    @patch.object(_EmptyService, 'name')
    def test_log(self, name_method):
        """ Test service config getter """
        service_name = 'foo_service'

        name_method.side_effect = (service_name,)
        registry_mock = PropertyMock()

        self.assertIsInstance(_EmptyService(VoidApplication(registry_mock)).log, MagicMock)
        registry_mock.log.assert_called_once_with(__name__)

    def test_name(self):
        """ Test default name property """
        self.assertEqual('test_core_application._EmptyService', _EmptyService.name())


class TestRegistry(unittest.TestCase):
    """ Covers dewyatochka.core.application.Registry """

    def test_init(self):
        """ Test __init__ method """
        registry = Registry()
        self.assertEqual({}, registry._services)

    def test_service_registration(self):
        """ Test add_service() / get_service() / add_service_alias() """
        service = _EmptyNamedService(VoidApplication())

        registry = Registry()
        registry.add_service(service)

        self.assertEqual(service, registry.get_service('test_service'))
        self.assertEqual(service, registry.get_service(_EmptyNamedService))
        self.assertEqual(service, registry.test_service)

        registry.add_service_alias('test_service', 'test_service2')
        self.assertEqual(registry.test_service, registry.test_service2)

        self.assertRaises(RuntimeError, registry.add_service, _EmptyNamedService(VoidApplication()))

    def test_unregistered_service(self):
        """ Test that RuntimeError is thrown if service is not registered """
        registry = Registry()
        self.assertRaises(RuntimeError, registry.get_service, 'foo')
