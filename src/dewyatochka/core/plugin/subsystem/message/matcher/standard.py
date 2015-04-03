# -*- coding: UTF-8

""" Simple message matchers: chat message + chat command

Classes
=======
    Matcher        -- Matches any chat message
    CommandMatcher -- Matches chat message that seems to be a bot command
    AccostMatcher  -- If someone is trying to talk to Dewyatochka
"""

__all__ = ['Matcher', 'CommandMatcher', 'AccostMatcher']

import re

from dewyatochka.core.network.xmpp.entity import Message, ChatMessage, JID
from dewyatochka.core.config.container import ConferencesConfig


class Matcher():
    """ Matches any chat message for allowed type"""

    def __init__(self, conferences_config: ConferencesConfig, regular=True, system=False, own=False):
        """ Create a matcher for message types specified

        :param ConferencesConfig conferences_config:
        :param bool regular: Allow regular messages (not own)
        :param bool system: Allow system messages (persistence change, etc)
        :param bool own: Allow own messages
        """
        self._conferences = conferences_config

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
        return not isinstance(message, ChatMessage) or not message.sender.resource

    def __is_own(self, message: Message) -> bool:
        """ Check if message is an own one

        :param Message message:
        :return bool:
        """
        for name in self._conferences:
            try:
                params = self._conferences.section(name)
                room, server = params['room'].split('@')
                # FIXME: Detection on empty nick in the config
                conf_receiver_jid = JID(room, server, params.get('nick', message.receiver))
                if conf_receiver_jid == message.sender:
                    return True
            except:
                # Malformed config, just skip it
                pass

        return False

    def __is_regular(self, message: Message) -> bool:
        """ Check if this is a regular chat message

        :param Message message:
        :return bool:
        """
        return not self.__is_own(message) and not self.__is_system(message)


class CommandMatcher(Matcher):
    """ Matches chat message that seems to be a bot command """

    def __init__(self, conferences_config: ConferencesConfig, prefix, command):
        """ Create a matcher for message types specified

        :param ConferencesConfig conferences_config:
        :param str prefix:
        :param str command:
        """
        super().__init__(conferences_config, regular=True, system=False, own=False)

        self._cmd_regexp = re.compile('^%s([\t\s]+.*|$)' % re.escape(prefix + command), re.I)

    def match(self, message: ChatMessage) -> bool:
        """ Check message

        Return True if message matches this matcher

        :param Message message: Chat message
        :return bool:
        """
        return super().match(message) and self._cmd_regexp.match(message.text) is not None


class AccostMatcher(Matcher):
    """ If someone is trying to talk to Dewyatochka """

    def __init__(self, conferences_config: ConferencesConfig):
        """ Create a matcher for message types specified

        :param ConferencesConfig conferences_config:
        """
        super().__init__(conferences_config)

    def match(self, message: ChatMessage) -> bool:
        """ Check message

        Return True if message matches this matcher

        :param Message message: Chat message
        :return bool:
        """
        nick = None
        msg_conference = str(message.sender.bare)
        for name in self._conferences:
            try:
                conference_cfg = self._conferences.section(name)
                if conference_cfg['room'] == msg_conference:
                    # TODO: Use fulltext analyzer when it is implemented
                    nick = conference_cfg.get('nick')
            except:
                # Malformed config, just skip it
                pass

        return super().match(message) and nick and nick in message.text
