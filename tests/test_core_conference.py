# coding=utf-8

"""
Tests suite for dewyatochka.core.conference
"""

import unittest
#from unittest.mock import patch
from dewyatochka.core import conference


class TestConference(unittest.TestCase):
    """
    dewyatochka.core.conference.Conference
    """

    def test_properties(self):
        """
        Test all properties
        """
        conf = conference.Conference('conference@jabber.example.com', 'Nobody')

        self.assertEqual('conference', conf.name)
        self.assertEqual('jabber.example.com', conf.host)
        self.assertEqual('conference@jabber.example.com', conf.jid)
        self.assertEqual('Nobody', conf.member)
        self.assertEqual('conference@jabber.example.com/Nobody', conf.resource)
