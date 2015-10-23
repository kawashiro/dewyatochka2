# -*- coding=utf-8

""" Tests suite for dewyatochka.core.config.container """

import unittest
from unittest.mock import Mock

from dewyatochka.core.config.container import *
from dewyatochka.core.config.exception import SectionRetrievingError
from dewyatochka.core.config import source
from dewyatochka.core.application import VoidApplication


class TestConfigContainer(unittest.TestCase):
    """ Tests suite for dewyatochka.core.config.container.ConfigContainer """

    def test_loading(self):
        """ Test loading data from external data source """
        class _TestSource(source.ConfigSource):
            sections = {'foo': object(), 'bar': object()}
            read = Mock(return_value=sections)

        container = ConfigContainer(VoidApplication())
        container.load(_TestSource())

        _TestSource.read.assert_called_once_with()

        self.assertEqual(container.section('foo'), _TestSource.sections['foo'])
        self.assertEqual(container.section('bar'), _TestSource.sections['bar'])
        self.assertEqual(container.section('baz'), {})
        self.assertRaises(SectionRetrievingError, container.section, 'baz', require=True)

        self.assertEqual(list(container), list(_TestSource.sections.keys()))

    def test_registration(self):
        """ Test service registration """
        app = VoidApplication()
        app.depend(ConfigContainer)

        self.assertIsInstance(app.registry.config, ConfigContainer)


class TestCommonConfig(unittest.TestCase):
    """ Tests suite for dewyatochka.core.config.container.CommonConfig """

    def test_global_section(self):
        """ Test global section retrieving """
        class _TestSource(source.ConfigSource):
            sections = {'global': object()}
            read = Mock(return_value=sections)

        container = CommonConfig(VoidApplication())
        container.load(_TestSource())

        self.assertEqual(container.global_section, _TestSource.sections['global'])


class TestConferencesConfig(unittest.TestCase):
    """ Tests suite for dewyatochka.core.config.container.ConferencesConfig """

    def test_registration(self):
        """ Test service registration """
        app = VoidApplication()
        app.depend(ConferencesConfig)

        self.assertIsInstance(app.registry.conferences_config, ConferencesConfig)


class TestExtensionsConfig(unittest.TestCase):
    """ Tests suite for dewyatochka.core.config.container.ExtensionsConfig """

    def test_registration(self):
        """ Test service registration """
        app = VoidApplication()
        app.depend(ExtensionsConfig)

        self.assertIsInstance(app.registry.extensions_config, ExtensionsConfig)
