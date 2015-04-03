# -*- coding: UTF-8

""" Entry decorators for python plugins

Functions
=========
    chat_message -- Decorator for chat message plugin
    chat_command -- Decorator for chat command plugin
    chat_accost  -- Decorator for chat accost plugin
"""

__all__ = ['chat_command', 'chat_message', 'chat_accost']

from dewyatochka.core.plugin.loader.internal import entry_point
from dewyatochka.core.plugin.exceptions import PluginRegistrationError
from .service import PLUGIN_TYPE_COMMAND, PLUGIN_TYPE_MESSAGE, PLUGIN_TYPE_ACCOST


# Commands already in use
_reserved_commands = set()


def chat_message(fn=None, *, services=None, regular=False, system=False, own=False) -> callable:
    """ Decorator to mark function as message handler entry point

    :param callable fn: Function if decorator is invoked directly
    :param list services: Dependent services list
    :param bool regular: Register this handler for regular messages
    :param bool system: Register this handler for system messages
    :param bool own: Register this handler for own messages
    :return callable:
    """
    return entry_point(PLUGIN_TYPE_MESSAGE, services=services, regular=True, system=False, own=False)(fn) \
        if fn is not None else \
        entry_point(PLUGIN_TYPE_MESSAGE, services=services, regular=regular, system=system, own=own)


def chat_command(command, *, services=None) -> callable:
    """ Register handler for chat command

    :param list services: Dependent services list
    :param str command: Command name without prefix
    :return callable:
    """
    if command in _reserved_commands:
        raise PluginRegistrationError('Chat command %s is already in use' % command)

    _reserved_commands.add(command)
    return entry_point(PLUGIN_TYPE_COMMAND, services=services, command=command)


def chat_accost(fn, *, services=None) -> callable:
    """ Register handler for a chat personal accost

    :param callable fn: Function if decorator is invoked directly
    :param list services: Dependent services list
    :return callable:
    """
    entry_point_fn = entry_point(PLUGIN_TYPE_ACCOST, services=services)
    return entry_point_fn(fn) if fn is not None else entry_point_fn
