# -*- coding=utf-8

""" Tests suite for dewyatochka.core.plugin.loader """

import unittest

from dewyatochka.core.plugin.loader import *
from dewyatochka.core.application import VoidApplication


class TestLoaderService(unittest.TestCase):
    """ Tests suite for dewyatochka.core.plugin.loader.LoaderService """

    def test_loaders_list(self):
        """ Test loaders list getter """
        service = LoaderService(VoidApplication())
        self.assertEqual([internal.Loader], list(map(type, service.loaders)))

    def test_registration(self):
        """ Test service registration """
        application = VoidApplication()
        application.depend(LoaderService)

        self.assertIsInstance(application.registry.plugins_loader, LoaderService)
