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


class TestService(unittest.TestCase):
    """ Covers dewyatochka.core.plugin.base.Service """

    def test_init(self):
        """ Check defaults after __init__() """
        service = _DummyService(VoidApplication())
        self.assertIsNone(service._plugins)

    def test_plugins_not_loaded(self):
        """ Test failing to get plugins if load() method has not been invoked """
        loader = Mock()
        loader.load.side_effect = [[PluginEntry(None, None)]]

        wrapper = Mock()
        wrapper.wrap.side_effect = RuntimeError()

        service = _DummyService(VoidApplication())
        self.assertRaises(RuntimeError, lambda: service.plugins)


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