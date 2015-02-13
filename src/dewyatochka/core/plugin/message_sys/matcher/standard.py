# -*- coding: UTF-8

""" Simple message matchers: chat message + chat command

Classes
=======
    Matcher        -- Matches any chat message
    CommandMatcher -- Matches chat message that seems to be a bot command
"""

__all__ = ['Matcher', 'CommandMatcher']

import re

from dewyatochka.core.network.xmpp.entity import Message, ChatMessage


class Matcher():
    """ Matches any chat message for allowed type"""

    def __init__(self, *, regular=True, system=False, own=False):
        """ Create a matcher for message types specified

        :param bool regular: Allow regular messages (not own)
        :param bool system: Allow system messages (persistence change, etc)
        :param bool own: Allow own messages
        """
        self._conditions = []
        if system:
            self._conditions.append(self.__is_system)
        if own:
            self._conditions.append(self.__is_own)
        if regular:
            self._conditions.append(self.__is_regular)

    def match(self, message: Message) -> bool:
        """ Check message

        Return True if message matches this matcher

        :param Message message: Chat message
        :return bool:
        """
        for condition in self._conditions:
            if condition(message):
                return True

        return False

    @staticmethod
    def __is_system(message: Message) -> bool:
        """ Check if message is a system one

        :param Message message:
        :return bool:
        """
        return not isinstance(message, ChatMessage)

    @staticmethod
    def __is_own(message: Message) -> bool:
        """ Check if message is an own one

        :param Message message:
        :return bool:
        """
        return message.sender == message.receiver

    @classmethod
    def __is_regular(cls, message: Message) -> bool:
        """ Check if this is a regular chat message

        :param Message message:
        :return bool:
        """
        return not cls.__is_own(message) and not cls.__is_system(message)


class CommandMatcher(Matcher):
    """ Matches chat message that seems to be a bot command """

    def __init__(self, prefix, command):
        """ Create a matcher for message types specified

        :param str prefix:
        """
        super().__init__(regular=True, system=False, own=False)

        self._cmd_regexp = re.compile('^%s([\t\s]+.*|$)' % re.escape(prefix + command), re.I)

    def match(self, message: ChatMessage) -> bool:
        """ Check message

        Return True if message matches this matcher

        :param Message message: Chat message
        :return bool:
        """
        return super().match(message) and self._cmd_regexp.match(message.text) is not None
