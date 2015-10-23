# -*- coding=utf-8

""" Tests suite for dewyatochka.core.plugin.base """

import unittest
from unittest.mock import Mock

from dewyatochka.core.plugin.base import *
from dewyatochka.core.plugin.exceptions import PluginRegistrationError
from dewyatochka.core.application import VoidApplication, Registry
from dewyatochka.core.application import Service as BaseService
from dewyatochka.core.config.container import ExtensionsConfig
from dewyatochka.core.config.source.virtual import Predefined


class _PluginService(Service):
    """ Non-abstract service for test purposes """

    @property
    def accepts(self) -> list:
        """ Get list of acceptable plugin types

        :return list:
        """
        return []


class TestEnvironment(unittest.TestCase):
    """ Tests suite for dewyatochka.core.plugin.base.Environment """

    def test_name(self):
        """ Test name getter  """
        def _invokable():
            pass

        registry = Registry()

        environment = Environment(_invokable, registry)
        self.assertEqual(environment.name, 'test_core_plugin_base._invokable')
        self.assertEqual(str(environment), 'test_core_plugin_base._invokable')

    def test_invoke(self):
        """ test plugin invoking """
        invokable = Mock()
        registry = Registry()
        logger = Mock()

        environment = Environment(invokable, registry)
        environment(foo='bar')
        invokable.assert_called_once_with(foo='bar', registry=registry)

        plugin_exc = Exception('error')
        invokable.side_effect = plugin_exc
        environment()
        environment(logger=logger)
        logger.error.assert_called_once_with('Plugin %s failed: %s', environment, plugin_exc)


class TestWrapper(unittest.TestCase):
    """ Tests suite for dewyatochka.core.plugin.base.Wrapper """

    def test_wrap(self):
        """ Test wrapping & registry population """
        _assert_equal = self.assertEqual

        class _Service1(BaseService):
            pass

        class _Service2(BaseService):
            pass

        class _Service3(BaseService):
            pass

        def _assert_has_service(service, registry):
            try:
                registry.get_service(service)
            except Exception as e:
                self.fail(str(e))

        def _plugin_callable(registry):
            _assert_has_service(PluginLogService, registry)
            _assert_has_service(PluginConfigService, registry)
            _assert_has_service(_Service1, registry)
            _assert_has_service(_Service2, registry)
            _assert_has_service('foo', registry)

            log_err_method = registry.log.error
            application.registry.log.assert_called_once_with('test_core_plugin_base._plugin_callable')
            _assert_equal(log_err_method, application.registry.log('test_core_plugin_base._plugin_callable').error)

            _assert_equal(registry.config.get('foo'), 'bar')
            _assert_equal(registry.config['foo'], 'bar')

        application = VoidApplication()
        application.depend(_Service1)
        application.depend(_Service2, 'foo')
        application.depend(_PluginService)
        application.depend(ExtensionsConfig)
        application.depend(Mock(), 'log')
        application.registry.extensions_config.load(
            Predefined({'test_core_plugin_base': {'foo': 'bar'}})
        )

        wrapper = Wrapper(application.registry.get_service(_PluginService))

        valid_entry = PluginEntry(_plugin_callable, dict(services=[_Service1, 'foo']))
        unsatisfied_entry = PluginEntry(_plugin_callable, dict(services=[_Service1, _Service2, _Service3]))

        wrapper.wrap(valid_entry).invoke()  # Assertions in _plugin_callable()
        self.assertRaises(PluginRegistrationError, wrapper.wrap, unsatisfied_entry)


class TestService(unittest.TestCase):
    """ Covers dewyatochka.core.plugin.base.Service """

    def test_plugins_loading(self):
        """ Test loading plugins """
        entries = [PluginEntry(lambda **_: None, {}), PluginEntry(lambda **_: None, {}),
                   PluginEntry(lambda **_: None, {}), PluginEntry(lambda **_: None, {'services': ['foo']})]

        loader1 = Mock()
        loader1.load.return_value = entries[:2]
        loader2 = Mock()
        loader2.load.return_value = entries[2:]

        loader_service = Mock()
        loader_service.name.return_value = 'plugins_loader'
        loader_service.loaders = [loader1, loader2]

        application = VoidApplication()
        application.depend(_PluginService)
        application.depend(ExtensionsConfig)
        application.depend(Mock(), 'log')
        application.depend(loader_service)

        plugin_service = application.registry.get_service(_PluginService)
        plugin_service.load()
        self.assertEqual(len(plugin_service.plugins), 3)

    def test_plugins_not_loaded(self):
        """ Test failing to get plugins if load() method has not been invoked """
        application = VoidApplication()
        application.depend(Mock(), 'log')
        application.depend(_PluginService)

        self.assertRaises(RuntimeError, lambda: application.registry.get_service(_PluginService).plugins)


class TestPluginLogService(unittest.TestCase):
    """ Covers dewyatochka.core.plugin.base.PluginConfigService """

    # Covered in test.cases.test_core_plugin_base.TestWrapper#test_wrap
    # No additional tests required
    pass


class TestPluginConfigService(unittest.TestCase):
    """ Covers dewyatochka.core.plugin.base.PluginConfigService """

    # Covered in test.cases.test_core_plugin_base.TestWrapper#test_wrap
    # No additional tests required
    pass
