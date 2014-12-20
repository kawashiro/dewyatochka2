# coding=utf-8

"""
Tests suite for dewyatochka.core.application
"""

import unittest
from dewyatochka.core import application


class _TestAppClass(application.Application):
    """
    Test application with empty run() method
    """
    def run(self, args: list):
        """
        Run application
        :param args: list Console arguments
        :return:
        """
        pass


class _TestServiceClass(application.Service):
    """
    Empty service for tests
    """
    pass


class TestApplication(unittest.TestCase):
    """
    dewyatochka.core.application.Application
    """

    def test_config_registration(self):
        """
        Test get / set config
        """
        app = _TestAppClass()

        config = _TestServiceClass(app)
        app.set_config(config)

        self.assertEqual(config, app.config)

    def test_conference_config_registration(self):
        """
        Test get / set conferences config
        """
        app = _TestAppClass()

        config = _TestServiceClass(app)
        app.set_conferences_config(config)

        self.assertEqual(config, app.conferences_config)

    def test_conference_manager_registration(self):
        """
        Test get / set conference_manager
        """
        app = _TestAppClass()

        conference_manager = _TestServiceClass(app)
        app.set_conference_manager(conference_manager)

        self.assertEqual(conference_manager, app.conference_manager)


class TestService(unittest.TestCase):
    """
    dewyatochka.core.application.Service
    """

    def test_init(self):
        """
        Test __init__ method
        """
        app = _TestAppClass()
        service = _TestServiceClass(app)

        self.assertEqual(app, service.application)
