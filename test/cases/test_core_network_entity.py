# -*- coding=utf-8

""" Tests suite for dewyatochka.core.network.entity """

import unittest

from dewyatochka.core.network.entity import *


class _Participant(Participant):
    """ Fake participant impl """

    def __init__(self, name: str):
        """ Set participant name """
        self.__name = name

    @property
    def public_name(self) -> str:
        """ Get public name displayed in chat """
        return self.__name

    def __str__(self) -> str:
        """ str() representation """
        return self.public_name


class TestEntity(unittest.TestCase):
    """ Tests suite for dewyatochka.core.network.entity._Entity """

    class _Class(GroupChat):
        """ Entity child class mock """

        def __init__(self, uid: str):
            """ Set unique ID for hashing """
            self.__uid = uid

        def __str__(self) -> str:
            """ str() representation """
            return self.__uid

        @property
        def self(self) -> Participant:
            """ Just a mock """
            raise NotImplemented()

    def test_eq(self):
        """ Test '==' operator """
        v1 = self._Class('foo')
        v2 = self._Class('bar')
        v3 = self._Class('foo')

        self.assertEqual(v1, v3)
        self.assertNotEqual(v1, v2)
        self.assertNotEqual(v2, v3)

    def test_hashing(self):
        """ Check if equal objects are the same """
        set_ = {self._Class('foo'), self._Class('bar'), self._Class('foo')}

        self.assertEqual(len(set_), 2)

    def test_repr(self):
        """ Test entity representative form """
        self.assertEqual(repr(self._Class('foo')), '_Class(foo)')


class TestMessage(unittest.TestCase):
    """ Tests suite for dewyatochka.core.network.entity.Message """

    class _Message(Message):
        """ Fake message impl """

        def __str__(self) -> str:
            """ str() representation """
            return ''

    def test_properties(self):
        """ Test common message properties """
        part1 = _Participant('Participant #1')
        part2 = _Participant('Participant #2')
        part3 = _Participant('Participant #3')

        message = self._Message(part1, part2)
        self.assertEqual(message.sender, part1)
        self.assertEqual(message.receiver, part2)

        message.receiver = part3
        self.assertEqual(message.receiver, part3)

        reg_message = self._Message(part1, part2)
        own_message = self._Message(part3, part3)
        sys_message = self._Message(part2, part3, system=True)

        self.assertTrue(reg_message.is_regular)
        self.assertFalse(reg_message.is_system)
        self.assertFalse(reg_message.is_own)

        self.assertFalse(sys_message.is_regular)
        self.assertTrue(sys_message.is_system)
        self.assertFalse(sys_message.is_own)

        self.assertFalse(own_message.is_regular)
        self.assertFalse(own_message.is_system)
        self.assertTrue(own_message.is_own)


class TestTextMessage(unittest.TestCase):
    """ Tests suite for dewyatochka.core.network.entity.TextMessage """

    def test_properties(self):
        """ Test text property """
        message_text = 'Message text'

        message = TextMessage(_Participant('Sender'), _Participant('Receiver'), text=message_text)
        self.assertEqual(message.text, message_text)
        self.assertEqual(str(message), message_text)
