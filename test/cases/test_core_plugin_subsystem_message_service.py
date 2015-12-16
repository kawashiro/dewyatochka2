# -*- coding=utf-8

""" Tests suite for dewyatochka.core.plugin.subsystem.message.service """

import unittest
from unittest.mock import Mock, call

from dewyatochka.core.plugin.subsystem.message.service import *

from dewyatochka.core.application import Registry, VoidApplication
from dewyatochka.core.config.container import CommonConfig
from dewyatochka.core.config.source.virtual import Predefined
from dewyatochka.core.config.container import ExtensionsConfig
from dewyatochka.core.plugin.base import PluginEntry
from dewyatochka.core.plugin.exceptions import PluginRegistrationError
from dewyatochka.core.plugin.subsystem.message.matcher.standard import AbstractMatcher
from dewyatochka.core.network.entity import Message, TextMessage, Participant
from dewyatochka.core.network.service import ChatManager, ConnectionManager


class _ChatManagerImpl(ChatManager):
    """ Chat manager implementation stub """

    # Send a message to group chat
    send = Mock()

    def alive_chats(self) -> frozenset:
        """ Get alive conferences

        :return frozenset:
        """
        return frozenset()

    def attach_connection_manager(self, connection: ConnectionManager):
        """ Attach a connection manager to take control on

        :param ConnectionManager connection: Connection manager
        :return None:
        """
        pass


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

    @property
    def chat(self):
        """ Chat getter stub """
        return self


class _TrueMatcher(AbstractMatcher):
    """ Always true """

    def match(self, message: Message) -> bool:
        """ Check message

        :param Message message: Chat message
        :return bool:
        """
        return True


class _FalseMatcher(AbstractMatcher):
    """ Always false """

    def match(self, message: Message) -> bool:
        """ Check message

        :param Message message: Chat message
        :return bool:
        """
        return False


class TestEnvironment(unittest.TestCase):
    """ Tests suite for dewyatochka.core.plugin.subsystem.message.service.Environment """

    def test_invoke(self):
        """ Test plugin invoke """
        assert_is_instance = self.assertIsInstance
        callable_mock = Mock()

        def _plugin(**kwargs):
            assert_is_instance(kwargs['registry'], Registry)
            assert_is_instance(kwargs['inp'], Message)
            assert_is_instance(kwargs['outp'], Output)
            callable_mock()

        text_message = TextMessage(_Participant('1'), _Participant('2'), text='text')

        Environment(_plugin, Registry(), _ChatManagerImpl(VoidApplication()), _TrueMatcher())(message=text_message)
        Environment(_plugin, Registry(), _ChatManagerImpl(VoidApplication()), _FalseMatcher())(message=text_message)
        callable_mock.assert_called_once_with()


class TestWrapper(unittest.TestCase):
    """ Tests suite for dewyatochka.core.plugin.subsystem.message.service.Wrapper """

    def test_wrap(self):
        """ Test wrapping """
        callable_mock = Mock()

        application = VoidApplication()
        application.depend(CommonConfig)
        application.depend(ExtensionsConfig)
        application.depend(_ChatManagerImpl)
        application.depend(Service)

        application.registry.config.load(Predefined(
            {'message': {'command_prefix': '$'}}
        ))

        wrapper = Wrapper(application.registry.message_plugin_provider)
        environment = wrapper.wrap(PluginEntry(lambda **_: callable_mock(), dict(type='chat_command', command='foo')))
        environment.invoke(message=TextMessage(_Participant('1'), _Participant('2'), text='$foo text'))
        callable_mock.assert_called_once_with()

        self.assertRaises(PluginRegistrationError, wrapper.wrap,
                          PluginEntry(lambda **_: callable_mock(), dict(type='foo')))


class TestOutput(unittest.TestCase):
    """ Tests suite for dewyatochka.core.plugin.subsystem.message.service.Output """

    def test_output(self):
        """ Test output wrapper """
        conference = _Participant('conference')
        _ChatManagerImpl.send.reset_mock()

        output = Output(_ChatManagerImpl(VoidApplication()), conference)
        output.say('say(%s, %s)', 'arg1', 'arg2')
        output.say('say(%s, %s)')

        _ChatManagerImpl.send.assert_has_calls([
            call('say(arg1, arg2)', conference),
            call('say(%s, %s)', conference)
        ])


class TestService(unittest.TestCase):
    """ Tests suite for dewyatochka.core.plugin.subsystem.message.service.Service """

    def test_accepts(self):
        """ Test acceptable plugin types getter """
        self.assertEqual(set(Service(VoidApplication()).accepts), {'message', 'chat_command', 'accost'})

    def test_registration(self):
        """ Test service registration """
        application = VoidApplication()
        application.depend(Service)

        self.assertIsInstance(application.registry.message_plugin_provider, Service)
