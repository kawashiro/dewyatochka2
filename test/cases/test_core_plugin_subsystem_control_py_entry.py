# -*- coding=utf-8

""" Tests suite for dewyatochka.core.plugin.subsystem.control.py_entry """

import unittest
from unittest.mock import patch, call

from dewyatochka.core.plugin.subsystem.control.py_entry import *
from dewyatochka.core.plugin.exceptions import PluginRegistrationError


class TestControl(unittest.TestCase):
    """ Tests suite for dewyatochka.core.plugin.subsystem.control.py_entry.control """

    @patch('dewyatochka.core.plugin.subsystem.control.py_entry.entry_point')
    def test_decorator(self, entry_point_mock):
        """ Test @control decorator """
        def _entry():
            pass

        control('name1', 'description1', services=['service1', 'service2'])(_entry)
        control('name2', 'description2')(_entry)

        self.assertRaises(PluginRegistrationError, control('name2', 'description2'), _entry)
        entry_point_mock.assert_has_calls([
            call('ctl', services=['service1', 'service2'],
                 name='test_core_plugin_subsystem_control_py_entry.name1',
                 description='description1'),
            call()(_entry),
            call('ctl', services=None,
                 name='test_core_plugin_subsystem_control_py_entry.name2',
                 description='description2'),
            call()(_entry)
        ])
