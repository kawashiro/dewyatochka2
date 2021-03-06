# -*- coding: UTF-8

""" Message plugins container service implementation

Classes
=======
    Environment -- Message plugin environment
    Service     -- Message plugins container service
    Wrapper     -- Message plugin environment wrapper
    Output      -- Output wrapper

Attributes
==========
    PLUGIN_TYPES        -- All plugin types list
"""

from dewyatochka.core.application import Registry
from dewyatochka.core.network.entity import Participant
from dewyatochka.core.network.service import ChatManager
from dewyatochka.core.plugin.base import Environment as BaseEnvironment
from dewyatochka.core.plugin.base import Service as BaseService
from dewyatochka.core.plugin.base import Wrapper as BaseWrapper
from dewyatochka.core.plugin.base import PluginEntry
from dewyatochka.core.plugin.exceptions import PluginRegistrationError

from . import matcher

__all__ = ['Environment', 'Service', 'Wrapper', 'Output', 'PLUGIN_TYPES']


# Plugin types provided
PLUGIN_TYPES = [matcher.PLUGIN_TYPE_MESSAGE,
                matcher.PLUGIN_TYPE_COMMAND,
                matcher.PLUGIN_TYPE_ACCOST]


class Environment(BaseEnvironment):
    """ Environment for a message plugin

    Also contains a reference to a matcher instance
    to pass through only valid messages
    """

    def __init__(self, plugin: callable, registry: Registry,
                 chat_manager: ChatManager, matcher_: matcher.AbstractMatcher):
        """ Initialize plugin environment

        :param callable plugin:
        :param Registry registry:
        :param ChatManager chat_manager:
        :param AbstractMatcher matcher_:
        """
        super().__init__(plugin, registry)

        self._matcher = matcher_
        self._chat_manager = chat_manager
        self._output_wrappers = {}

    def invoke(self, *, message, **kwargs):
        """ Invoke plugin in environment registered

        :param Message message: Message to process
        :param dict kwargs: Params to path to a plugin
        :return None:
        """
        if self._matcher.match(message):
            super().invoke(inp=message, outp=self._get_output_wrapper(message.sender), **kwargs)

    def _get_output_wrapper(self, destination: Participant):
        """ Get output wrapper for a conference

        :param JID destination:
        :return None:
        """
        try:
            output = self._output_wrappers[str(destination.chat)]
        except KeyError:
            output = Output(self._chat_manager, destination.chat)
            self._output_wrappers[str(destination)] = output

        return output


class Wrapper(BaseWrapper):
    """ Wraps a plugin into environment """

    def _get_matcher(self, entry: PluginEntry) -> matcher.AbstractMatcher:
        """ Get matcher for plugin

        :param PluginEntry entry:
        :return Matcher:
        """
        try:
            entry_type = entry.params.get('type')
            cmd_prefix = self._service.config.get('command_prefix')

            return matcher.factory(entry_type, command_prefix=cmd_prefix, **entry.params)

        except matcher.UnknownMatcherError as e:
            raise PluginRegistrationError(e)

    def wrap(self, entry: PluginEntry) -> Environment:
        """ Wrap plugin into it's environment

        :param PluginEntry entry: Raw plugin entry
        :return Environment:
        """
        registry = self._get_registry(entry)
        c_manager = self._service.application.registry.chat_manager
        matcher_ = self._get_matcher(entry)

        return Environment(entry.plugin, registry, c_manager, matcher_)


class Service(BaseService):
    """ Message plugins container service """

    # Plugin wrapper class
    _wrapper_class = Wrapper

    @property
    def accepts(self) -> list:
        """ Get list of acceptable plugin types

        :return list:
        """
        return PLUGIN_TYPES

    @property
    def config(self) -> dict:
        """ Get related config section

        Overridden for a prettier config format

        :return dict:
        """
        return self.application.registry.config.section('message')

    @classmethod
    def name(cls) -> str:
        """ Get service unique name

        :return str:
        """
        return 'message_plugin_provider'


class Output:
    """ Output wrapper

    Output wrapper is passed to each message plugin
    to allow plugin to communicate through xmpp
    """

    def __init__(self, chat_manager: ChatManager, conference: Participant):
        """ Bind output wrapper to xmpp-client and a conference

        :param ChatManager chat_manager:
        :param JID conference:
        """
        self._chat_manager = chat_manager
        self._conference = conference

    def say(self, text: str, *args):
        """ Say something

        :param str text: Message content
        :param tuple args: Args for message format
        :return None:
        """
        formatted_text = (text % args) if args else text
        self._chat_manager.send(formatted_text, self._conference)
