# -*- coding=utf-8

""" Tests suite for dewyatochka.core.plugin.loader.internal """

import importlib
from os import path

import unittest
from unittest.mock import patch, Mock, call

from dewyatochka.core.plugin.loader import internal

from dewyatochka.core.application import VoidApplication
from dewyatochka.core.config.exception import SectionRetrievingError
from dewyatochka.core.plugin.base import Service


class TestEntryPoint(unittest.TestCase):
    """ Tests suite for dewyatochka.core.plugin.loader.internal.entry_point """

    def test_entry_point(self):
        """ Test common entry_point plugin decorator """
        def _fn():
            pass

        plugin_type = 'foo'
        params = {'bar': 'baz'}

        self.assertEqual(internal.entry_point(plugin_type, **params)(_fn), _fn)
        self.assertEqual(internal._entry_points['foo'][0].plugin, _fn)
        self.assertEqual(internal._entry_points['foo'][0].params, {'type': 'foo', 'bar': 'baz'})


class TestLoader(unittest.TestCase):
    """ Covers dewyatochka.core.plugin.loader.internal.Loader """

    @patch('importlib.import_module')
    @patch('dewyatochka.plugins')
    @patch('dewyatochka.core.plugin.builtins.register_entry_points')
    def test_load(self, _, plugins_pkg_mock, importlib_mock):
        """ Test internal plugins loading system """
        class _PluginService(Service):
            accepts = ['foo']

        # Mocking importlib
        def _importlib_stub(name):
            if name.endswith('exception'):
                raise ImportError
        importlib_mock.side_effect = _importlib_stub

        # Mocking plugins root package
        plugins_pkg_mock.__file__ = path.realpath(path.sep.join(
            (path.dirname(__file__), '..', 'files', 'plugin', 'fake_package', '__init__.py')
        ))
        plugins_pkg_mock.__name__ = 'dewyatochka.plugins'
        plugins_pkg_mock.__all__ = []

        # Initializing app instance
        application = VoidApplication()
        application.depend(Mock(), 'extensions_config')
        application.depend(Mock(), 'log')
        application.depend(_PluginService)
        plugins_service = application.registry.get_service(_PluginService)

        # Reload module after monkey patching. -_-
        importlib.reload(internal)

        # Normal import
        internal.Loader().load(plugins_service)
        internal.Loader().load(plugins_service)
        importlib_mock.assert_has_calls([call('dewyatochka.plugins.package'),
                                         call('dewyatochka.plugins.module')], any_order=True)
        self.assertEqual(application.registry.log().warning.call_count, 0)

        # Reset state one more time ...
        importlib.reload(internal)

        # Import with disabled modules
        application.registry.extensions_config.section.side_effect = SectionRetrievingError
        internal.Loader().load(plugins_service)
        self.assertEqual(application.registry.log().warning.call_count, 2)

        # And once more ...
        importlib.reload(internal)

        # Test on import-time error
        application.registry.extensions_config.section.side_effect = None
        importlib_mock.side_effect = Exception
        internal.Loader().load(plugins_service)
        self.assertEqual(application.registry.log().error.call_count, 2)
