# -*- coding=utf-8

""" Tests suite for dewyatochka.core.config.source.virtual """

import unittest

from dewyatochka.core.config.source.virtual import *


class TestPredefined(unittest.TestCase):
    """ Tests suite for dewyatochka.core.config.source.filesystem.Predefined """

    def test_read(self):
        """ Test config reading """
        config = {'foo': {'bar': 'baz'}}
        self.assertEqual(Predefined(config).read(), config)


class TestEmpty(unittest.TestCase):
    """ Tests suite for dewyatochka.core.config.source.filesystem.Empty """

    def test_read(self):
        """ Test config reading """
        self.assertEqual(Empty().read(), {})
