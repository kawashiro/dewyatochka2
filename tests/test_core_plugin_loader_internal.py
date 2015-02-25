# -*- coding=utf-8

""" Tests suite for dewyatochka.core.plugin.loader.internal """

from os import path
import imp

import unittest
from unittest.mock import patch, Mock, call

from dewyatochka.core.plugin.loader import internal
from dewyatochka.core.config.exception import SectionRetrievingError


class TestEntryPoint(unittest.TestCase):
    """ Covers dewyatochka.core.plugin.loader.internal.entry_point """

    def test_entry_point(self):
        """ Test common entry_point plugin decorator """
        fn = lambda: None
        plugin_type = 'foo'
        params = {'bar': 'baz'}

        self.assertEqual(fn, internal.entry_point(plugin_type, **params)(fn))
        self.assertEqual(fn, internal._entry_points['foo'][0].plugin)
        self.assertEqual({'type': 'foo', 'bar': 'baz'}, internal._entry_points['foo'][0].params)


class TestLoader(unittest.TestCase):
    """ Covers dewyatochka.core.plugin.loader.internal.Loader """

    @patch('importlib.import_module')
    @patch('dewyatochka.plugins')
    def test_load(self, plugins_pkg_mock, importlib_mock):
        """ Test internal plugins loading system """
        def _importlib_stub(name):
            if name.endswith('exception'):
                raise ImportError()

        importlib_mock.side_effect = _importlib_stub

        plugins_pkg_mock.__file__ = path.sep.join(
            (path.dirname(__file__), 'files', 'plugin', 'fake_package', '__init__.py')
        )
        plugins_pkg_mock.__name__ = 'dewyatochka.plugins'

        imp.reload(internal)  # Reload module after monkey patching. -_-

        service = Mock()
        no_conf_service = Mock()
        no_conf_service.application.registry.ext_config.section.side_effect = SectionRetrievingError

        internal.Loader().load(no_conf_service)
        self.assertEqual(0, importlib_mock.call_count)

        internal._ready = False
        internal.Loader().load(service)
        internal.Loader().load(service)

        self.assertEqual(2, importlib_mock.call_count)
        importlib_mock.assert_has_calls([call('dewyatochka.plugins.package'),
                                         call('dewyatochka.plugins.module')], any_order=True)

        internal._ready = False
        importlib_mock.side_effect = Exception
        plugins = internal.Loader().load(service)
        self.assertEqual(0, len(plugins))
