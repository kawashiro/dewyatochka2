# -*- coding=utf-8

""" Tests suite for dewyatochka.core.log.get_logger """

from os import path

import unittest
from unittest.mock import Mock, patch, call

from dewyatochka.core.config.factory import *
from dewyatochka.core.config.container import *
from dewyatochka.core.application import VoidApplication


class TestFactoryFunctions(unittest.TestCase):
    """ Covers dewyatochka.core.config.factory """

    def setUp(self):
        """ Initialize test cases """
        self._expected_types = (
            (get_conferences_config, ConferencesConfig),
            (get_extensions_config, ExtensionsConfig)
        )

    def test_factory_functions(self):
        """ Test factories """
        custom_path = path.dirname(__file__) + '/files/config/ini_file.ini'
        application = Mock()
        application.registry.config.global_section = {
            'conferences': custom_path,
            'extensions': custom_path
        }

        for factory, container_class in self._expected_types:
            self.assertIsInstance(factory(application), container_class)

        self.assertIsInstance(get_common_config(application, custom_path), CommonConfig)

    @patch('dewyatochka.core.config.factory._get_file_config_instance')
    def test_default_paths(self, factory_mock):
        """ Test assigning default config paths """
        app = VoidApplication()

        get_common_config(app)
        get_conferences_config(app)
        get_extensions_config(app)

        factory_mock.assert_has_calls([call(CommonConfig, app, COMMON_CONFIG_DEFAULT_PATH),
                                       call(ConferencesConfig, app, CONFERENCES_CONFIG_DEFAULT_PATH),
                                       call(ExtensionsConfig, app, EXTENSIONS_CONFIG_DEFAULT_PATH)])
