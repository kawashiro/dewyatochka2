# -*- coding: UTF-8

""" XMPP entities; mostly simple container classes

Classes
=======
    JID          -- JID params container
    ChatPresence -- Groupchat member presence change notification
    ChatSubject  -- Groupchat subject change notification
    Conference   -- XMPP conference
"""

__all__ = ['JID', 'ChatPresence', 'ChatSubject', 'Conference']

from ..entity import *


class JID(Participant):
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

    @property
    def public_name(self) -> str:
        """ Get public name displayed in chat

        :return str:
        """
        return self.resource

    def __str__(self) -> str:
        """ Convert JID object to string

        :return str:
        """
        return self.jid

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


class Conference(JID, GroupChat):
    """ XMPP conference """

    @property
    def self(self) -> JID:
        """ Get self identification

        :return Participant:
        """
        return self.bare

    @property
    def public_name(self) -> str:
        """ Get public name displayed in chat

        :return str:
        """
        return str(self.bare)

    @classmethod
    def from_config(cls, room: str, nick: str):
        """ Factory function

        :param str room: conference@server.org
        :param str nick: Participant's nick
        :return Conference:
        """
        room, server = room.split('@')
        return cls(room, server, nick)


class ChatSubject(TextMessage):
    """ Groupchat subject change notification """

    @property
    def subject(self) -> str:
        """ Get new subject

        :return str:
        """
        return self.text

    @property
    def is_system(self) -> bool:
        """ Check if message is a system one

        :return bool:
        """
        return True


class ChatPresence(Message):
    """ Groupchat member presence change notification """

    @property
    def type(self) -> str:
        """ Get presence type (online / offline / etc)

        :return str:
        """
        return self._content['type']

    @property
    def status(self) -> str:
        """ Get user status

        :return str:
        """
        return self._content['status']

    @property
    def role(self) -> str:
        """ Get user role

        :return str:
        """
        return self._content['role']

    @property
    def is_system(self) -> bool:
        """ Check if message is a system one

        :return bool:
        """
        return True

    def __str__(self) -> str:
        """ Convert to str

        :return str:
        """
        return '{} {} is now {} ({})'.format(
            self.role.capitalize(),
            self.sender.resource,
            self.type,
            self.status
        )
