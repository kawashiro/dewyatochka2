# coding=utf-8

"""
Tests suite for dewyatochka.core.log.get_logger
"""

from os import path
import unittest
from dewyatochka.core.config.factory import *
from dewyatochka.core.config.container import *
from dewyatochka.core.application import VoidApplication


class TestFactoryFunctions(unittest.TestCase):
    """
    dewyatochka.core.config.factory
    """

    def setUp(self):
        """
        Initialize test cases
        :return: void
        """
        self._expected_types = (
            (get_common_config, CommonConfig),
            (get_conferences_config, ConferencesConfig),
            (get_extensions_config, ExtensionsConfig)
        )

    def test_factory_functions(self):
        """
        Test factories
        """
        application = VoidApplication()
        custom_path = path.dirname(__file__) + '/files/config/ini_file.ini'

        for factory, container_class in self._expected_types:
            self.assertIsInstance(factory(application, path=custom_path), container_class)
