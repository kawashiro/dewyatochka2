# -*- coding=utf-8

""" Tests suite for dewyatochka.core.plugin.helper_sys.py_entry """

import unittest

from dewyatochka.core.plugin.helper_sys.py_entry import *
from dewyatochka.core.plugin.loader import internal


class TestHelper(unittest.TestCase):
    """ Covers dewyatochka.core.plugin.helper_sys.py_entry.helper """

    def test_wrap(self):
        """ Test @helper decorator """
        helper_fn = lambda: None
        services = ['foo', 'bar']

        helper(helper_fn)
        helper(services=services)(helper_fn)

        entry_points = internal._entry_points['helper']
        self.assertEqual(helper_fn, entry_points[0].plugin)
        self.assertEqual({'services': None, 'type': 'helper'}, entry_points[0].params)
        self.assertEqual(helper_fn, entry_points[1].plugin)
        self.assertEqual({'services': services, 'type': 'helper'}, entry_points[1].params)
