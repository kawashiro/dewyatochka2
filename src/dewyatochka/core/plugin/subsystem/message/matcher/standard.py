# -*- coding: UTF-8

""" Simple message matchers: chat message + chat command

Classes
=======
    AbstractMatcher -- Abstract matcher
    SimpleMatcher   -- Matches any chat message
    CommandMatcher  -- Matches chat message that seems to be a bot command
    AccostMatcher   -- If someone is trying to talk to Dewyatochka
"""

__all__ = ['AbstractMatcher', 'SimpleMatcher', 'CommandMatcher', 'AccostMatcher']

import re
from abc import ABCMeta, abstractmethod

from dewyatochka.core.network.entity import Message, TextMessage


class AbstractMatcher(metaclass=ABCMeta):
    """ Abstract matcher """

    @abstractmethod
    def match(self, message: Message):
        """ Check message

        Return True if message matches this matcher

        :param Message message: Chat message
        :return bool:
        """
        pass


class SimpleMatcher(AbstractMatcher):
    """ Matches any chat message for allowed type"""

    def __init__(self, regular=True, system=False, own=False):
        """ Create a matcher for message types specified

        :param bool regular: Allow regular messages (not own)
        :param bool system: Allow system messages (persistence change, etc)
        :param bool own: Allow own messages
        """
        self._match_regular = regular
        self._match_system = system
        self._match_own = own

    def match(self, message: Message) -> bool:
        """ Check message

        Return True if message matches this matcher

        :param Message message: Chat message
        :return bool:
        """
        return self._match_regular and message.is_regular \
            or self._match_system and message.is_system   \
            or self._match_own and message.is_own


class CommandMatcher(AbstractMatcher):
    """ Matches chat message that seems to be a bot command """

    def __init__(self, prefix, command):
        """ Create a matcher for message types specified

        :param str prefix:
        :param str command:
        """
        self._cmd_regexp = re.compile('^%s([\t\s]+.*|$)' % re.escape(prefix + command), re.I)

    def match(self, message: TextMessage) -> bool:
        """ Check message

        Return True if message matches this matcher

        :param Message message: Chat message
        :return bool:
        """
        return self._cmd_regexp.match(str(message)) is not None


class AccostMatcher(AbstractMatcher):
    """ If someone is trying to talk to Dewyatochka """

    def match(self, message: TextMessage) -> bool:
        """ Check message

        Return True if message matches this matcher

        :param Message message: Chat message
        :return bool:
        """
        return message.receiver.public_name in str(message)
