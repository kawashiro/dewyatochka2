# -*- coding: UTF-8

""" Connections management service

Classes
=======
    ChatManager       -- Manages available conferences set
    ConnectionManager -- Serves multiple connections
"""

__all__ = ['ChatManager', 'ConnectionManager']

from abc import ABCMeta, abstractmethod, abstractproperty

from dewyatochka.core.application import Application, Service

from .entity import Message, GroupChat


class ChatManager(Service, metaclass=ABCMeta):
    """ Manages available conferences set """

    @abstractproperty
    def alive_chats(self) -> frozenset:
        """ Get alive conferences

        :return frozenset:
        """
        pass

    @abstractmethod
    def send(self, message: str, chat: GroupChat):
        """ Send a message to groupchat

        :param str message: Message content
        :param GroupChat chat: Destination chat
        :return None:
        """
        pass

    @classmethod
    def name(cls) -> str:
        """ Get service unique name

        :return str:
        """
        return 'chat_manager'


class ConnectionManager(ChatManager, metaclass=ABCMeta):
    """ Server connection

    Check connections state and provides
    a single stable input stream to work with
    """

    def __init__(self, application: Application):
        """ Initialize service & attach an application to it

        :param Application application:
        """
        super().__init__(application)

        self.application  \
            .registry     \
            .chat_manager \
            .attach_connection_manager(self)

    @abstractmethod
    def connect(self):
        """ Establish connection

        :return None:
        """
        pass

    @abstractproperty
    def input_stream(self) -> Message:
        """ Wrapper over xmpp client input stream

        Implements auto reconnection and conferences re-enter
        if something goes wrong

        :return Message:
        """
        pass

    @abstractmethod
    def disconnect(self):
        """ Force disconnection

        :return None:
        """
        pass
