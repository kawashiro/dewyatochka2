# -*- coding: UTF-8

"""
Common client implementation
"""

__all__ = ['Client', 'Command']

from abc import ABCMeta, abstractmethod, abstractproperty
from dewyatochka.core.network.xmpp.entity import *
from dewyatochka.core.network.xmpp.exception import C2SConnectionError


class Command(metaclass=ABCMeta):
    """
    XMPP client command
    """

    def __init__(self, client):
        """
        Create command attached to a client instance
        :param client: Client
        """
        self._client = client

    @abstractmethod
    def __call__(self, *args, **kwargs):  # pragma: no cover
        """
        Command is invokable
        :param args:
        :param kwargs:
        :return:
        """
        pass

    @abstractproperty
    def name(self) -> str:  # pragma: no cover
        """
        Command unique name
        :return: str
        """
        pass


class Client(metaclass=ABCMeta):
    """
    Abstract xmpp client
    """

    def __init__(self, host: str, login: str, password: str, port=5222, location=''):
        """
        Initialize xmpp connection instance
        :param host: str
        :param login: str
        :param password: str
        :param port: int
        :param location: str
        """
        self._jid = JID(login, host, location)
        self._server = host, port
        self._password = password
        self._commands = {}

    def add_command(self, command: Command):
        """
        Add command instance
        :param command: Command
        :return: void
        """
        self._commands[command.name] = command

    def get_command(self, command: str) -> Command:
        """
        Get command
        :param command: str
        :return: Command
        """
        try:
            return self._commands[command]
        except KeyError:
            raise RuntimeError('Command {} is not implemented in xmpp-client {}'.format(command, self.__class__))

    @abstractmethod
    def connect(self):  # pragma: no cover
        """
        Establish connection to the server
        :return: void
        """
        pass

    @abstractmethod
    def disconnect(self, wait=True):  # pragma: no cover
        """
        Close connection
        :param wait: bool - Wait until all received messages are processed
        :return: void
        """
        pass

    @abstractmethod
    def read(self) -> Message:  # pragma: no cover
        """
        Read next message from stream
        :return: Message
        """
        pass

    @property
    def jid(self) -> JID:
        """
        Authorized as JID
        :return: JID
        """
        return self._jid

    def __getattr__(self, item):
        """
        Get command as an attribute
        :param item: str
        :return: Command
        """
        return self.get_command(item)

    def __enter__(self):
        """
        Enter in with statement
        :return: Client
        """
        self.connect()
        return self

    def __exit__(self, *args) -> bool:
        """
        Cleanup
        :param args: tuple
        :return: bool
        """
        if not isinstance(args[1], C2SConnectionError):
            self.disconnect()

        return False
