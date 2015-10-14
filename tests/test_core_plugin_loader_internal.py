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
