# -*- coding=utf-8

""" Tests suite for dewyatochka.core.plugin.subsystem.helper.py_entry """

import unittest
from unittest.mock import patch, call

from dewyatochka.core.plugin.subsystem.helper.py_entry import *


def _entry(**_):
    """ Dummy entry point fn """
    pass


class TestControl(unittest.TestCase):
    """ Tests suite for dewyatochka.core.plugin.subsystem.helper.py_entry.daemon """

    @patch('dewyatochka.core.plugin.subsystem.helper.py_entry.entry_point')
    def test_decorator(self, entry_point_mock):
        """ Test @daemon decorator """
        daemon(services=['service1', 'service2'])(_entry)
        daemon(_entry)

        entry_point_mock.assert_has_calls([
            call('daemon', services=['service1', 'service2']),
            call()(_entry),
            call('daemon', services=None),
            call()(_entry)
        ])


class TestBootstrap(unittest.TestCase):
    """ Tests suite for dewyatochka.core.plugin.subsystem.helper.py_entry.bootstrap """

    @patch('dewyatochka.core.plugin.subsystem.helper.py_entry.entry_point')
    def test_decorator(self, entry_point_mock):
        """ Test @bootstrap decorator """
        bootstrap(services=['service1', 'service2'])(_entry)
        bootstrap(_entry)

        entry_point_mock.assert_has_calls([
            call('bootstrap', services=['service1', 'service2']),
            call()(_entry),
            call('bootstrap', services=None),
            call()(_entry)
        ])


class TestSchedule(unittest.TestCase):
    """ Tests suite for dewyatochka.core.plugin.subsystem.helper.py_entry.schedule """

    @patch('dewyatochka.core.plugin.subsystem.helper.py_entry.entry_point')
    def test_decorator(self, entry_point_mock):
        """ Test @schedule decorator """
        schedule('@daily', services=['service1', 'service2'], lock=False)(_entry)

        entry_point_mock.assert_has_calls([
            call('schedule', schedule='@daily', lock=False, services=['service1', 'service2']),
            call()(_entry),
        ])
