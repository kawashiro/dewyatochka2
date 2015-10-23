# -*- coding=utf-8

""" Tests suite for dewyatochka.core.network.xmpp.exception """

import unittest

from dewyatochka.core.network.xmpp.exception import S2SConnectionError
from dewyatochka.core.network.xmpp.entity import JID


class TestJID(unittest.TestCase):
    """ Covers dewyatochka.core.network.xmpp.exception.S2SConnectionError """

    def test_remote(self):
        """ Test remote JID property """
        jid = JID.from_string('remote@example.com')
        e = S2SConnectionError(remote=jid)

        self.assertEqual(jid, e.remote)
