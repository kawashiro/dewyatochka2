# -*- coding: UTF-8

"""
XMPP messages
"""

__all__ = ['JID', 'Message', 'ChatMessage']


class JID():
    """
    JID params container
    """

    def __init__(self, login: str, server: str, resource=''):
        """
        Create new JID params container
        :param login: str
        :param server: str
        :param resource: str
        """
        self._login = login
        self._server = server
        self._resource = resource
        self._jid = '{}@{}{}'.format(login, server, ('/%s' % resource) if resource else '')

    @property
    def login(self) -> str:
        """
        Get login
        :return: str
        """
        return self._login

    @property
    def server(self) -> str:
        """
        Get server
        :return: str
        """
        return self._server

    @property
    def resource(self) -> str:
        """
        Get resource
        :return: str
        """
        return self._resource

    @property
    def jid(self) -> str:
        """
        Get JID
        :return: str
        """
        return self._jid

    def __str__(self) -> str:
        """
        Convert JID to string
        :return: str
        """
        return self.jid

    def __eq__(self, other):
        """
        Check if JIDs are equal
        :param JID other:
        :return: bool
        """
        return str(self) == str(other)

    @classmethod
    def from_string(cls, jid: str):
        """
        Convert from string
        :param jid: str
        :return: JID
        """
        parts = jid.split('/')
        login, server = parts[0].split('@')

        return cls(login, server, parts[1] if len(parts) > 1 else '')


class Message():
    """
    Common message
    """

    def __init__(self, sender: JID, receiver: JID):
        """
        Create message instance
        """
        self._sender = sender
        self._receiver = receiver

    @property
    def sender(self) -> JID:
        """
        Get sender
        :return: JID
        """
        return self._sender

    @property
    def receiver(self) -> JID:
        """
        Get receiver
        :return: JID
        """
        return self._receiver


class ChatMessage(Message):
    """
    Chat text message
    """

    def __init__(self, sender: JID, receiver: JID, text: str):
        """
        Initialize general chat message container
        :param sender: JID
        :param receiver: JID
        :param text: str
        """
        super().__init__(sender, receiver)
        self._text = text

    @property
    def text(self) -> str:
        """
        Get message text
        :return: str
        """
        return self._text

    def __str__(self) -> str:
        """
        Convert to string
        :return: str
        """
        return self.text
