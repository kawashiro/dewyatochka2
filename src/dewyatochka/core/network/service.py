# -*- coding: UTF-8

""" Connections management service

Classes
=======
    ChatManager       -- Manages available conferences set
    ConnectionManager -- Serves multiple connections
"""

from abc import ABCMeta, abstractmethod, abstractproperty

from dewyatochka.core.application import Application, Service

from .entity import GroupChat

__all__ = ['ChatManager', 'ConnectionManager']


class ConnectionManager(Service, metaclass=ABCMeta):
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
    def connect(self):  # pragma: nocover
        """ Establish connection

        :return None:
        """
        pass

    @abstractproperty
    def input_stream(self):  # pragma: nocover
        """ Wrapper over xmpp client input stream

        Implements auto reconnection and conferences re-enter
        if something goes wrong

        :return Message:
        """
        pass

    @abstractmethod
    def disconnect(self):  # pragma: nocover
        """ Force disconnection

        :return None:
        """
        pass

    @abstractproperty
    def alive_chats(self) -> frozenset:  # pragma: nocover
        """ Get alive conferences

        :return frozenset:
        """
        pass

    @abstractmethod
    def send(self, message: str, chat: GroupChat):  # pragma: nocover
        """ Send a message to groupchat

        :param str message: Message content
        :param GroupChat chat: Destination chat
        :return None:
        """
        pass


class ChatManager(Service, metaclass=ABCMeta):
    """ Manages available conferences set """

    @abstractproperty
    def alive_chats(self) -> frozenset:  # pragma: nocover
        """ Get alive conferences

        :return frozenset:
        """
        pass

    @abstractmethod
    def send(self, message: str, chat: GroupChat):  # pragma: nocover
        """ Send a message to groupchat

        :param str message: Message content
        :param GroupChat chat: Destination chat
        :return None:
        """
        pass

    @abstractmethod
    def attach_connection_manager(self, connection: ConnectionManager):  # pragma: nocover
        """ Attach a connection manager to take control on

        :param ConnectionManager connection: Connection manager
        :return None:
        """
        pass

    @classmethod
    def name(cls) -> str:
        """ Get service unique name

        :return str:
        """
        return 'chat_manager'
