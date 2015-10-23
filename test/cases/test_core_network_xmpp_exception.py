# -*- coding=utf-8

""" Tests suite for dewyatochka.core.network.xmpp.exception """

import unittest

from dewyatochka.core.network.xmpp.exception import *
from dewyatochka.core.network.xmpp.entity import Conference


class TestS2SConnectionError(unittest.TestCase):
    """ Tests suite for dewyatochka.core.network.xmpp.exception.S2SConnectionError """

    def test_remote(self):
        """ Test remote svc property store """
        exc = S2SConnectionError('Some message', 9000, remote=Conference.from_config('r@c.s.c', 'nick'))

        self.assertEqual(exc.args, ('Some message', 9000))
        self.assertEqual(str(exc.remote), 'r@c.s.c/nick')
