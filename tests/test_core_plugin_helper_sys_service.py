# -*- coding=utf-8

""" Tests suite for dewyatochka.core.plugin.helper_sys.service """

import unittest

from dewyatochka.core.plugin.helper_sys.service import *
from dewyatochka.core.application import VoidApplication


class TestService(unittest.TestCase):
    """ Covers dewyatochka.core.plugin.helper_sys.service.Service """

    def test_accepts(self):
        """ Test acceptable plugins types list getter """
        self.assertEqual(['helper'], Service(VoidApplication()).accepts)

    def test_name(self):
        """ Test service name getter """
        self.assertEqual('helper', Service.name())
