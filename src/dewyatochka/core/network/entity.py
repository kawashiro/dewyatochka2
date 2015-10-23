# -*- coding: UTF-8

""" Common chat entities

Classes
=======
    Participant -- Chat participant info container
    Message     -- Common chat message params container
    TextMessage -- Chat text message params container
    GroupChat   -- Group chat params container
"""

from abc import ABCMeta, abstractmethod, abstractproperty

__all__ = ['Participant', 'Message', 'TextMessage', 'GroupChat']


class _Entity(metaclass=ABCMeta):
    """ Abstract entity class

    Should not be inherited anywhere except this module
    """

    @abstractmethod
    def __str__(self) -> str:  # pragma: nocover
        """ Convert participant object to string

        :return str:
        """
        pass

    def __eq__(self, other) -> bool:
        """ Check if participants are equal

        :param _Entity other:
        :return bool:
        """
        return str(self) == str(other)

    def __hash__(self) -> int:
        """ Calculate unique hash

        :return int:
        """
        module = self.__class__.__module__
        class_ = self.__class__.__name__

        return hash('%s.%s::%s' % (module, class_, self))

    def __repr__(self) -> str:
        """ Representative form

        :return str:
        """
        return '%s(%s)' % (self.__class__.__name__, str(self))


class Participant(_Entity, metaclass=ABCMeta):
    """ Chat participant info container """

    @abstractproperty
    def public_name(self) -> str:  # pragma: nocover
        """ Get public name displayed in chat

        :return str:
        """
        pass


class GroupChat(_Entity, metaclass=ABCMeta):
    """ Group chat params container """

    @abstractproperty
    def self(self) -> Participant:  # pragma: nocover
        """ Get self identification

        :return Participant:
        """
        pass


class Message(_Entity, metaclass=ABCMeta):
    """ Common chat message params container """

    def __init__(self, sender: Participant, receiver: Participant, **content):
        """ Create message instance

        :param Participant sender:
        :param Participant receiver:
        :param dict content:
        """
        self._sender = sender
        self._receiver = receiver
        self._content = content

    @property
    def sender(self):
        """ Get sender

        :return Participant:
        """
        return self._sender

    @property
    def receiver(self):
        """ Get receiver

        :return Participant:
        """
        return self._receiver

    @receiver.setter
    def receiver(self, new_receiver: Participant):
        """ Change message receiver

        :param Participant new_receiver: New receiver
        :return None:
        """
        self._receiver = new_receiver

    @property
    def is_own(self) -> bool:
        """ Check if message is an own one

        :param Message message:
        :return bool:
        """
        return self.sender == self.receiver

    @property
    def is_system(self) -> bool:
        """ Check if message is a system one

        :return bool:
        """
        return self._content.get('system', False)

    @property
    def is_regular(self) -> bool:
        """ Check if this is a regular chat message

        :return bool:
        """
        return not self.is_own and not self.is_system


class TextMessage(Message):
    """ Chat text message params container """

    @property
    def text(self) -> str:
        """ Get message text

        :return str:
        """
        return self._content['text']

    def __str__(self) -> str:
        """ Convert to string

        :return str:
        """
        return self.text
