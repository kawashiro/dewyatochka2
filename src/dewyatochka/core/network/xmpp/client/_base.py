# -*- coding: UTF-8

""" Common client implementation

Private module, for internal use only

Classes
=======
    Client  -- Abstract XMPP client
    Command -- Abstract command to extend client functionality
"""

from abc import ABCMeta, abstractmethod, abstractproperty

from dewyatochka.core.network.entity import Message
from dewyatochka.core.network.xmpp.entity import JID
from dewyatochka.core.network.xmpp.exception import C2SConnectionError, ClientDisconnectedError

__all__ = ['Client', 'Command']


class Command(metaclass=ABCMeta):
    """ Abstract command to extend client functionality

    Commands are intended to be attached to a XMPP client
    and invoked on provided attribute call on client
    """

    def __init__(self, client):
        """ Create command attached to a client instance

        :param Client client:
        """
        self._client = client

    @abstractmethod
    def __call__(self, *args, **kwargs):  # pragma: no cover
        """ Command is invokable

        :param tuple args:
        :param dict kwargs:
        :returns: Depends on command implementation
        """
        pass

    @abstractproperty
    def name(self) -> str:  # pragma: no cover
        """ Command unique name

        Command is to be attached as client's attribute
        named as the command is.

        :return str:
        """
        pass


class Client(metaclass=ABCMeta):
    """ Abstract XMPP client """

    def __init__(self, host: str, login: str, password: str, port=5222, location=''):
        """ Initialize XMPP client instance

        :param str host: XMPP server host
        :param str login: User login
        :param str password: User password
        :param int port: XMPP server port, default 5222
        :param str location: XMPP resource, default ''
        :return Client:
        """
        self._jid = JID(login, host, location)
        self._server = host, port
        self._password = password
        self._commands = {}

    def add_command(self, command: Command):
        """ Attach a command to client

        :param Command command: Command instance
        :return None:
        """
        self._commands[command.name] = command

    def get_command(self, command: str) -> Command:
        """ Get command by name

        :param str command: Command name as .Command.name provides
        :return Command:
        """
        try:
            return self._commands[command]
        except KeyError:
            raise RuntimeError('Command {} is not implemented in xmpp-client {}'.format(command, self.__class__))

    @abstractmethod
    def connect(self):  # pragma: no cover
        """ Establish connection to the server

        :return None:
        """
        pass

    @abstractmethod
    def disconnect(self, wait=True, notify=True):  # pragma: no cover
        """ Close connection

        :param bool wait: Wait until all received messages are processed
        :param bool notify: Notify reader about disconnection
        :return None:
        """
        pass

    @abstractmethod
    def read(self) -> Message:  # pragma: no cover
        """ Read next message from stream

        :return Message:
        """
        pass

    @property
    def jid(self) -> JID:
        """ Authorized as JID

        :return JID:
        """
        return self._jid

    def __getattr__(self, item) -> Command:
        """ Get command as an attribute

        :param str item:
        :return Command:
        """
        return self.get_command(item)

    def __enter__(self):
        """ Entering in with statement

        :return Client:
        """
        return self

    def __exit__(self, *args) -> bool:
        """ Close connection on exit if needed

        :param tuple args:
        :return bool:
        """
        exc_instance = args[1]

        if isinstance(exc_instance, ClientDisconnectedError):
            return True

        if not isinstance(args[1], C2SConnectionError):
            self.disconnect(wait=args[1] is None)

        return False
