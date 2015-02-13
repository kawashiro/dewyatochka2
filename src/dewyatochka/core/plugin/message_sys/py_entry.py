# -*- coding: UTF-8

""" Entry decorators for python plugins

Functions
=========
    chat_message -- Decorator for chat message plugin
    chat_command -- Decorator for chat command plugin
"""

from dewyatochka.core.plugin.loader.internal import entry_point
from dewyatochka.core.plugin.exceptions import PluginRegistrationError
from .service import PLUGIN_TYPE_COMMAND, PLUGIN_TYPE_MESSAGE


# Commands already in use
_reserved_commands = set()


def chat_message(fn=None, *, services=None, regular=True, system=False, own=False) -> callable:
    """ Decorator to mark function as message handler entry point

    :param callable fn: Function if decorator is invoked directly
    :param list services: Dependent services list
    :param bool regular: Register this handler for regular messages
    :param bool system: Register this handler for system messages
    :param bool own: Register this handler for own messages
    :return callable:
    """
    entry_point_fn = entry_point(PLUGIN_TYPE_MESSAGE, services=services, regular=regular, system=system, own=own)
    return entry_point_fn(fn) if fn is not None else entry_point_fn


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
