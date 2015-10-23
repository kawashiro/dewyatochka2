# -*- coding=utf-8

""" Tests suite for dewyatochka.core.network.xmpp.client """

import unittest

from dewyatochka.core.network.xmpp.client import create, sleekxmpp


class TestCreate(unittest.TestCase):
    """ Covers dewyatochka.core.network.xmpp.client.create """

    def test_get_sleekxmpp_client(self):
        """ Test instantiating sleekxmpp based client """
        client = create('host', 'login', 'password', 1234, 'foo')

        self.assertIsInstance(client, sleekxmpp.Client)
        self.assertIsInstance(client.ping, sleekxmpp.PingCommand)
        self.assertIsInstance(client.chat, sleekxmpp.MUCCommand)

        self.assertEqual(('host', 1234), client._server)
        self.assertEqual('login@host/foo', str(client.jid))
        self.assertEqual('password', client._password)
