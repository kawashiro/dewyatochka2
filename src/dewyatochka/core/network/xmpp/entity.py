# -*- coding: UTF-8

""" XMPP entities; mostly simple container classes

Classes
=======
    JID          -- JID params container
    Message      -- Common message params container
    ChatMessage  -- Chat text message params container
    ChatPresence -- Groupchat member presence change notification
    ChatSubject  -- Groupchat subject change notification
"""

__all__ = ['JID', 'Message', 'ChatMessage', 'ChatPresence', 'ChatSubject']


class JID():
    """ JID params container """

    def __init__(self, login: str, server: str, resource=''):
        """ Create new JID params container

        :param str login:
        :param str server:
        :param str resource:
        """
        self._login = login
        self._server = server
        self._resource = resource
        self._jid = '{}@{}{}'.format(login, server, ('/%s' % resource) if resource else '')
        self._bare = JID(login, server) if resource else self

    @property
    def login(self) -> str:
        """ Get login

        :return str:
        """
        return self._login

    @property
    def server(self) -> str:
        """ Get server

        :return str:
        """
        return self._server

    @property
    def resource(self) -> str:
        """ Get resource

        :return str:
        """
        return self._resource

    @property
    def bare(self):
        """ Get bare JID instance

        :return JID:
        """
        return self._bare

    @property
    def jid(self) -> str:
        """ Get full JID

        :return str:
        """
        return self._jid

    def __str__(self) -> str:
        """ Convert JID object to string

        :return str:
        """
        return self.jid

    def __eq__(self, other) -> bool:
        """ Check if JIDs are equal

        :param JID other:
        :return bool:
        """
        return str(self) == str(other)

    def __hash__(self) -> int:
        """ Calculate unique hash

        :return int:
        """
        return hash('jid:///%s' % self)

    @classmethod
    def from_string(cls, jid: str):
        """ Convert from string

        :param str jid: str('somebody@example.com/resource')
        :return JID:
        """
        try:
            parts = jid.split('/')
            login, server = parts[0].split('@')
            if len(parts) > 2:
                raise ValueError()

            return cls(login, server, parts[1] if len(parts) > 1 else '')
        except (ValueError, AttributeError):
            raise ValueError('Invalid JID (%s)' % repr(jid))


class Message():
    """ Common message params container """

    def __init__(self, sender: JID, receiver: JID):
        """ Create message instance

        :param JID sender:
        :param JID receiver:
        """
        self._sender = sender
        self._receiver = receiver

    @property
    def sender(self) -> JID:
        """ Get sender

        :return JID:
        """
        return self._sender

    @property
    def receiver(self) -> JID:
        """ Get receiver

        :return JID:
        """
        return self._receiver


class ChatMessage(Message):
    """ Chat text message params container """

    def __init__(self, sender: JID, receiver: JID, text: str):
        """ Create message instance

        :param JID sender:
        :param JID receiver:
        :param str text:
        """
        super().__init__(sender, receiver)
        self._text = text

    @property
    def text(self) -> str:
        """ Get message text

        :return str:
        """
        return self._text

    def __str__(self) -> str:
        """ Convert to string

        :return str:
        """
        return self.text


class ChatSubject(ChatMessage):
    """ Groupchat subject change notification """

    @property
    def subject(self) -> str:
        """ Get new subject

        :return str:
        """
        return self.text


class ChatPresence(Message):
    """ Groupchat member presence change notification """

    def __init__(self, sender: JID, receiver: JID, p_type: str, status: str, role: str):
        """ Create message instance

        :param JID sender:
        :param JID receiver:
        :param str p_type:
        :param str status:
        :param str role:
        """
        super().__init__(sender, receiver)
        self._type = p_type
        self._status = status
        self._role = role

    @property
    def type(self) -> str:
        """ Get presence type (online / offline / etc)

        :return str:
        """
        return self._type

    @property
    def status(self) -> str:
        """ Get user status

        :return str:
        """
        return self._status

    @property
    def role(self) -> str:
        """ Get user role

        :return str:
        """
        return self._role

    def __str__(self) -> str:
        """ Convert to str

        :return str:
        """
        return '{} {} is now {} ({})'.format(self.role.capitalize(), self.sender.resource, self.type, self.status)
