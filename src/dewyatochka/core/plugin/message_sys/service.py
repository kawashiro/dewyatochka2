# -*- coding: UTF-8

""" Message plugins container service implementation

Classes
=======
    Environment -- Message plugin environment
    Service     -- Message plugins container service
    Wrapper     -- Message plugin environment wrapper

Attributes
==========
    PLUGIN_TYPE_MESSAGE -- Simple message plugin type
    PLUGIN_TYPE_COMMAND -- Chat command plugin type
    PLUGIN_TYPES        -- All plugin types list
"""

__all__ = ['Environment', 'Service', 'Wrapper', 'PLUGIN_TYPE_COMMAND', 'PLUGIN_TYPE_MESSAGE', 'PLUGIN_TYPES']

from dewyatochka.core.application import Registry
from dewyatochka.core.network.xmpp.entity import Message
from dewyatochka.core.plugin.base import Environment as BaseEnvironment
from dewyatochka.core.plugin.base import Service as BaseService
from dewyatochka.core.plugin.base import Wrapper as BaseWrapper
from dewyatochka.core.plugin.base import PluginEntry
from dewyatochka.core.plugin.exceptions import PluginRegistrationError
from .matcher.standard import *


# Plugin types provided
PLUGIN_TYPE_MESSAGE = 'message'
PLUGIN_TYPE_COMMAND = 'chat_command'
PLUGIN_TYPES = [PLUGIN_TYPE_MESSAGE, PLUGIN_TYPE_COMMAND]


class Environment(BaseEnvironment):
    """ Environment for a message plugin

    Also contains a reference to a matcher instance
    to pass through only valid messages
    """

    def __init__(self, plugin: callable, registry: Registry, matcher):
        """ Initialize plugin environment

        :param callable plugin:
        :param Registry registry:
        :param .matcher._base.Matcher matcher:
        """
        super().__init__(plugin, registry)
        self._matcher = matcher

    def invoke(self, message: Message, **kwargs):
        """ Invoke plugin in environment registered

        :param Message message: Message to process
        :param dict kwargs: Other arguments
        :return None:
        """
        if self._matcher.match(message):
            super().invoke(message=message, **kwargs)


class Service(BaseService):
    """ Message plugins container service """

    @property
    def accepts(self) -> list:
        """ Get list of acceptable plugin types

        :return list:
        """
        return PLUGIN_TYPES

    @classmethod
    def name(cls) -> str:
        """ Get service unique name

        :return str:
        """
        return 'chat'


class Wrapper(BaseWrapper):
    """ Wraps a plugin into environment """

    def __init__(self, service: Service):
        """ Create plugin wrapper for plugin service

        :param Service service:
        :return:
        """
        self._service = service

    def _get_matcher(self, entry: PluginEntry) -> Matcher:
        """ Get matcher for plugin

        :param PluginEntry entry:
        :return Matcher:
        """
        e_type = entry.params.get('type')

        if e_type == PLUGIN_TYPE_MESSAGE:
            matcher = Matcher(
                **{param: entry.params[param] for param in entry.params if param in ['system', 'own', 'regular']}
            )
        elif e_type == PLUGIN_TYPE_COMMAND:
            try:
                matcher = CommandMatcher(self._service.config['command_prefix'], entry.params['command'])
            except KeyError:
                raise PluginRegistrationError('Failed to register chat command plugin: '
                                              'Chat command prefix is not configured')
        else:
            raise PluginRegistrationError(
                'Failed to determine matcher type for a plugin %s type of %s' % (repr(entry.plugin), repr(e_type))
            )

        return matcher

    def wrap(self, entry: PluginEntry) -> Environment:
        """ Wrap plugin into it's environment

        :param PluginEntry entry: Raw plugin entry
        :return Environment:
        """
        return Environment(entry.plugin, self._get_registry(entry), self._get_matcher(entry))
