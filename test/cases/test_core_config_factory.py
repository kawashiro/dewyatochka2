# -*- coding=utf-8

""" Tests suite for dewyatochka.core.config.factory """

import unittest
from unittest.mock import patch

from dewyatochka.core.config.factory import *
from dewyatochka.core.config.container import *
from dewyatochka.core.config.source import virtual
from dewyatochka.core.application import VoidApplication


class TestFactoryFunctions(unittest.TestCase):
    """ Tests suite for dewyatochka.core.config.factory.* """

    def _assert_config_initialized(self, container, application, source_mock, source_path):
        """ Check if config initialized properly

        :param ConfigContainer container:
        :param Application application:
        :param MagicMock source_mock:
        :param str source_path:
        :return None:
        """
        self.assertEqual(container.application, application)

        source_mock.assert_called_once_with(source_path)
        source_mock.return_value.read.assert_called_once_with()

        source_mock.reset_mock()

    @patch('dewyatochka.core.config.factory.INIFiles')
    def test_get_common_config(self, source_class_mock):
        """ Test get_common_config() function """
        application = VoidApplication()

        self._assert_config_initialized(
            get_common_config(application), application,
            source_class_mock, COMMON_CONFIG_DEFAULT_PATH)

        self._assert_config_initialized(
            get_common_config(application, '/foo'),
            application, source_class_mock, '/foo')

    @patch('dewyatochka.core.config.factory.INIFiles')
    def test_get_conferences_config(self, source_class_mock):
        """ Test get_conferences_config() function """
        configured_app = VoidApplication()
        configured_app.depend(
            CommonConfig(configured_app).load(
                virtual.Predefined({'global': {'conferences': '/foo'}})))

        empty_app = VoidApplication()

        self._assert_config_initialized(
            get_conferences_config(empty_app), empty_app,
            source_class_mock, CONFERENCES_CONFIG_DEFAULT_PATH)

        self._assert_config_initialized(
            get_conferences_config(configured_app), configured_app,
            source_class_mock, '/foo')

    @patch('dewyatochka.core.config.factory.INIFiles')
    def test_get_extensions_config(self, source_class_mock):
        """ Test get_extensions_config() function """
        configured_app = VoidApplication()
        configured_app.depend(
            CommonConfig(configured_app).load(
                virtual.Predefined({'global': {'extensions': '/foo'}})))

        empty_app = VoidApplication()

        self._assert_config_initialized(
            get_extensions_config(empty_app), empty_app,
            source_class_mock, EXTENSIONS_CONFIG_DEFAULT_PATH)

        self._assert_config_initialized(
            get_extensions_config(configured_app), configured_app,
            source_class_mock, '/foo')
