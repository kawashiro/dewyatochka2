# -*- coding=utf-8

""" Tests suite for dewyatochka.core.plugin.base """

import unittest
from unittest.mock import Mock, patch, call

from dewyatochka.core.plugin.base import *
from dewyatochka.core.application import Registry, VoidApplication
from dewyatochka.core.application import Service as AppService


class _DummyService(Service):
    """ Non-abstract service for test purposes """

    @property
    def accepts(self) -> list:
        """ Get list of acceptable plugin types

        :return list:
        """
        return []


class TestEnvironment(unittest.TestCase):
    """ Covers dewyatochka.core.plugin.base.Environment """

    def test_invoke(self):
        """ Test environment invoking (invoke() and __call__()) """
        kwargs = {'foo': 'bar', 'bar': 'baz'}
        plugin = Mock()
        registry = Registry()

        Environment(plugin, registry)(**kwargs)
        plugin.assert_called_once_with(registry=registry, **kwargs)


class TestService(unittest.TestCase):
    """ Covers dewyatochka.core.plugin.base.Service """

    def test_init(self):
        """ Check defaults after __init__() """
        service = _DummyService(VoidApplication())
        self.assertIsNone(service._plugins)

    @patch.object(Service, 'log')
    def test_plugins_loading(self, logger_mock):
        """ Test loading plugins """
        entries = [PluginEntry(None, None), PluginEntry(None, None), PluginEntry(None, None), PluginEntry(None, None)]

        loader1 = Mock()
        loader1.load.side_effect = [entries[:2]]

        loader2 = Mock()
        loader2.load.side_effect = [entries[2:]]

        wrapper = Mock()
        wrapper.wrap.side_effect = lambda e: e

        service = _DummyService(VoidApplication())
        service.load([loader1, loader2], wrapper)

        self.assertEqual(entries, service.plugins)
        loader1.load.assert_called_once_with(service)
        loader2.load.assert_called_once_with(service)
        wrapper.assert_has_calls([call.wrap(e) for e in entries])

        self.assertEqual(1, logger_mock.info.call_count)

    @patch.object(Service, 'log')
    def test_plugins_loading_fail(self, logger_mock):
        """ Test loading plugins """
        loader = Mock()
        loader.load.side_effect = [[PluginEntry(None, None)]]

        wrapper = Mock()
        wrapper.wrap.side_effect = RuntimeError()

        service = _DummyService(VoidApplication())
        service.load([loader], wrapper)

        self.assertEqual(1, logger_mock.error.call_count)

    def test_plugins_not_loaded(self):
        """ Test failing to get plugins if load() method has not been invoked """
        loader = Mock()
        loader.load.side_effect = [[PluginEntry(None, None)]]

        wrapper = Mock()
        wrapper.wrap.side_effect = RuntimeError()

        service = _DummyService(VoidApplication())
        self.assertRaises(RuntimeError, lambda: service.plugins)


class TestWrapper(unittest.TestCase):
    """ Covers dewyatochka.core.plugin.base.Wrapper """

    def test_wrap(self):
        """ Test default plugin wrapping and registry population """
        class _FooService(AppService):
            @classmethod
            def name(cls) -> str:
                return 'foo'

        class _BarService(AppService):
            @classmethod
            def name(cls) -> str:
                return 'bar'

        class _ExtConfigService(AppService):
            @classmethod
            def name(cls) -> str:
                return 'ext_config'

        class _LogService(AppService):
            @classmethod
            def name(cls) -> str:
                return 'log'

        app = VoidApplication()
        app.registry.add_service(_FooService(app))
        app.registry.add_service(_BarService(app))
        app.registry.add_service(_ExtConfigService(app))
        app.registry.add_service(_LogService(app))

        service = _DummyService(app)
        entry = PluginEntry(None, {'services': ['foo', 'bar']})

        wrapper = Wrapper(service)
        env = wrapper.wrap(entry)

        self.assertEqual({'foo', 'ext_config', 'config', 'log', 'bar'}, set(env._registry._services.keys()))
        self.assertIsInstance(env._registry.foo, _FooService)
        self.assertIsInstance(env._registry.bar, _BarService)
        self.assertIsInstance(env._registry.log, _LogService)
        self.assertIsInstance(env._registry.ext_config, _ExtConfigService)
        self.assertEqual(env._registry.ext_config, env._registry.config)

        entry_empty1 = PluginEntry(None, {'services': None})
        entry_empty2 = PluginEntry(None, {})

        env_empty1 = wrapper.wrap(entry_empty1)
        env_empty2 = wrapper.wrap(entry_empty2)
        self.assertEqual({'ext_config', 'config', 'log'}, set(env_empty1._registry._services.keys()))
        self.assertEqual({'ext_config', 'config', 'log'}, set(env_empty2._registry._services.keys()))

        entry_invalid = PluginEntry(None, {'services': ['foo', 'bar', 'baz']})
        self.assertRaises(RuntimeError, wrapper.wrap, entry_invalid)
