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

        ex_plugin = Mock(side_effect=Exception('Error'))
        logger = Mock()
        env = Environment(ex_plugin, registry)
        env()
        env(logger=logger)
        self.assertEqual(1, logger.error.call_count)

    def test_name(self):
        """ test name getter """
        plugin = Mock()
        plugin.__name__ = 'foo'
        self.assertEqual('dewyatochka.core.plugin.base[unittest.mock.foo]', str(Environment(plugin, Mock())))


class TestService(unittest.TestCase):
    """ Covers dewyatochka.core.plugin.base.Service """

    def test_init(self):
        """ Check defaults after __init__() """
        service = _DummyService(VoidApplication())
        self.assertIsNone(service._plugins)

    @patch.object(Service, 'log')
    def test_plugins_loading(self, logger_mock):
        """ Test loading plugins """
        def _cb(**_):
            pass

        entries = [PluginEntry(_cb, None), PluginEntry(_cb, None), PluginEntry(_cb, None), PluginEntry(_cb, None)]

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
        """ Test loading plugins (fail) """
        def _cb(**_):
            pass

        loader = Mock()
        loader.load.side_effect = [[PluginEntry(_cb, None)]]

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
            def section(self, _):
                return {}

        class _LogService(AppService):
            @classmethod
            def name(cls) -> str:
                return 'log'

        def _cb(**_):
            pass

        app = VoidApplication()
        app.registry.add_service(_FooService(app))
        app.registry.add_service(_BarService(app))
        app.registry.add_service(_ExtConfigService(app))
        app.registry.add_service(_LogService(app))

        service = _DummyService(app)
        entry = PluginEntry(_cb, {'services': ['foo', 'bar']})

        wrapper = Wrapper(service)
        env = wrapper.wrap(entry)

        self.assertEqual({'foo', 'config', 'log', 'bar'}, set(env._registry._services.keys()))
        self.assertIsInstance(env._registry.foo, _FooService)
        self.assertIsInstance(env._registry.bar, _BarService)
        self.assertIsInstance(env._registry.log, PluginLogService)

        entry_empty1 = PluginEntry(_cb, {'services': None})
        entry_empty2 = PluginEntry(_cb, {})

        env_empty1 = wrapper.wrap(entry_empty1)
        env_empty2 = wrapper.wrap(entry_empty2)
        self.assertEqual({'config', 'log'}, set(env_empty1._registry._services.keys()))
        self.assertEqual({'config', 'log'}, set(env_empty2._registry._services.keys()))

        entry_invalid = PluginEntry(_cb, {'services': ['foo', 'bar', 'baz']})
        self.assertRaises(RuntimeError, wrapper.wrap, entry_invalid)


class TestPluginLogService(unittest.TestCase):
    """ Covers dewyatochka.core.plugin.base.PluginLogService """

    def test_attr_get(self):
        """ Test inner logger getter """
        def _fn():
            pass
        log = Mock()
        app = Mock()
        app.registry.log.side_effect = (log,)

        logger = PluginLogService(app, _fn)
        logger.info('foo')

        app.registry.log.assert_called_once_with('test_core_plugin_base._fn')
        log.info.assert_called_once_with('foo')