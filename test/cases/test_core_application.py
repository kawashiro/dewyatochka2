# -*- coding=utf-8

""" Tests suite for dewyatochka.core.application """

from threading import Event

import unittest
from unittest.mock import patch, call, Mock

from dewyatochka.core.application import *


class TestApplication(unittest.TestCase):
    """ Tests suite for dewyatochka.core.application.Application """

    def test_init(self):
        """ Test app instantiation """
        registry = Registry()

        app = VoidApplication(registry)
        self.assertEqual(app.registry, registry)
        self.assertTrue(app.running)

        app2 = VoidApplication()
        self.assertIsInstance(app2.registry, Registry)
        self.assertNotEqual(app2.registry, app.registry)

    @patch.object(Event, 'wait')
    def test_event_handling(self, wait_method):
        """ Test application stop event behaviour (wait / sleep / stop) """
        fake_exit_code = 900
        fake_sleep_time = 42

        app = VoidApplication()
        self.assertTrue(app.running)
        app.stop(fake_exit_code)
        self.assertFalse(app.running)
        self.assertEqual(getattr(app, '_exit_code'), fake_exit_code)

        VoidApplication().wait()
        VoidApplication().sleep(fake_sleep_time)
        wait_method.assert_has_calls([call(), call(fake_sleep_time)])

    def test_registry(self):
        """ Test registry manipulations """
        class _TestServiceClass(Service):
            pass

        class _TestServiceInstance(Service):
            pass

        registry = Registry()

        app = VoidApplication(registry)
        self.assertEqual(app.registry, registry)

        app2 = VoidApplication()
        self.assertIsInstance(app2.registry, Registry)
        self.assertNotEqual(app2.registry, app.registry)

        app.depend(_TestServiceClass, 'foo', 'bar')
        app.depend(_TestServiceInstance(app))

        self.assertIsInstance(app.registry.get_service(_TestServiceInstance), _TestServiceInstance)
        self.assertIsInstance(app.registry.get_service(_TestServiceClass), _TestServiceClass)
        self.assertEqual(app.registry.get_service(_TestServiceClass), app.registry.get_service('foo'))
        self.assertEqual(app.registry.get_service(_TestServiceClass), app.registry.get_service('bar'))

    @patch('sys.stderr')
    def test_fatal_error(self, stderr_mock):
        """ Test app fatal error """
        class _FakeLogService(Service):
            fatal_error = Mock()

        module = 'foo_module'
        exception = Exception()

        app = VoidApplication()
        app.depend(_FakeLogService, 'log')
        app.fatal_error(module, exception)

        self.assertEqual(getattr(app, '_exit_code'), EXIT_CODE_ERROR)
        _FakeLogService.fatal_error.assert_called_once_with(module, exception)

        # Just should not fail if logger is not registered
        VoidApplication().fatal_error(module, exception)
        self.assertGreater(stderr_mock.write.call_count, 0)


class TestRegistry(unittest.TestCase):
    """ Tests suite for dewyatochka.core.application.Registry """

    class _TestService(Service):
        @classmethod
        def name(cls):
            """ To check named service registration """
            return 'test_service'

    def test_service_registration(self):
        """ Test service registration logic """
        registry = Registry()
        service = self._TestService(VoidApplication())

        registry.add_service(service)
        self.assertRaises(RuntimeError, registry.add_service, service)

        registry.add_service_alias(self._TestService, 'foo')
        self.assertRaises(UndefinedServiceError, registry.add_service_alias, 'unknown', 'bar')

        self.assertEqual(registry.get_service('test_service'), service)
        self.assertEqual(registry.get_service(self._TestService), service)
        self.assertEqual(registry.get_service('foo'), service)
        self.assertEqual(registry.test_service, service)
        self.assertEqual(registry.foo, service)
        self.assertRaises(UndefinedServiceError, registry.get_service, 'bar')

        self.assertEqual(registry.all, [service])


class TestService(unittest.TestCase):
    """ Tests suite for dewyatochka.core.application.Service """

    def test_init(self):
        """ Test service instantiation """
        app = VoidApplication()
        svc = Service(app)

        self.assertEqual(svc.application, app)

    def test_config(self):
        """ Test config retrieving """
        class _FakeConfigService(Service):
            fake_section = object()
            section = Mock(return_value=fake_section)

        app = VoidApplication()
        app.depend(_FakeConfigService, 'config')

        svc = Service(app)
        cfg = svc.config

        _FakeConfigService.section.assert_called_once_with(svc.name())
        self.assertEqual(cfg, _FakeConfigService.fake_section)

    def test_log(self):
        """ Test logger retrieving """
        class _FakeLogService(Service):
            fake_logger = object()
            __call__ = mock = Mock(return_value=fake_logger)

        app = VoidApplication()
        app.depend(_FakeLogService, 'log')

        log = Service(app).log

        _FakeLogService.mock.assert_called_once_with('dewyatochka.core.application.Service')
        self.assertEqual(log, _FakeLogService.fake_logger)
