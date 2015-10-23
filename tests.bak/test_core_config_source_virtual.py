# -*- coding=utf-8

""" Tests suite for dewyatochka.core.log.get_logger """

import unittest

from dewyatochka.core.config.source.virtual import *


class TestPredefined(unittest.TestCase):
    """ Covers dewyatochka.core.config.source.virtual.Predefined """

    def test_read(self):
        """ Test config reading """
        config = {'foo': {'bar': 'baz'}}
        self.assertEqual(config, Predefined(config).read())


class TestEmpty(unittest.TestCase):
    """ Covers dewyatochka.core.config.source.virtual.Empty """

    def test_read(self):
        """ Test config reading """
        self.assertEqual({}, Empty().read())
