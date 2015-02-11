# -*- coding=utf-8

""" Tests suite for dewyatochka.core.log.get_logger """

import unittest

from dewyatochka.core.config.container import *
from dewyatochka.core.config.source.virtual import Predefined
from dewyatochka.core.application import VoidApplication


class TestConfigContainer(unittest.TestCase):
    """ Covers dewyatochka.core.config.container.ConfigContainer """

    def test_init(self):
        """ Test __init__() """
        self.assertEqual({}, ConfigContainer(VoidApplication()).__iter__())

    def test_load_section(self):
        """ Test loading data from config source and fetching one section """
        config = {'foo': {'bar': 'baz'}}
        container = ConfigContainer(VoidApplication()).load(Predefined(config))

        self.assertEqual(config, container.__iter__())
        self.assertEqual(config['foo'], container.section('foo'))
        self.assertEqual({}, container.section('null'))

    def test_get_name(self):
        """ Test service name getter """
        self.assertEqual('config', ConfigContainer.name())


class TestCommonConfig(unittest.TestCase):
    """ Covers dewyatochka.core.config.container.CommonConfig """

    def test_global_section(self):
        """ Test global section getter """
        config = {'global': {'foo': 'bar'}}

        self.assertEqual(config['global'], CommonConfig(VoidApplication()).load(Predefined(config)).global_section)


class TestConferencesConfig(unittest.TestCase):
    """ Covers dewyatochka.core.config.container.ConferencesConfig """

    def test_get_name(self):
        """ Test service name getter """
        self.assertEqual('conferences_config', ConferencesConfig.name())


class TestExtensionsConfig(unittest.TestCase):
    """ Covers dewyatochka.core.config.container.ConferencesConfig """

    def test_get_name(self):
        """ Test service name getter """
        self.assertEqual('ext_config', ExtensionsConfig.name())
