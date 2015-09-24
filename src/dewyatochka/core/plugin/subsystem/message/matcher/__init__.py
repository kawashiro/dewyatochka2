# -*- coding: UTF-8

""" Message matchers package

Each matcher checks if the message corresponds all preconditions

Modules
=======
    standard -- Simple message matchers: chat message + chat command

Classes
=======
    UnknownMatcherError -- Unknown matcher error

Functions
=========
    factory -- Get matcher instance

Attributes
==========
    PLUGIN_TYPE_MESSAGE -- Simple message plugin type
    PLUGIN_TYPE_COMMAND -- Chat command plugin type
    PLUGIN_TYPE_ACCOST  -- Chat accost plugin type
"""

__all__ = ['standard', 'factory', 'UnknownMatcherError',
           'PLUGIN_TYPE_COMMAND', 'PLUGIN_TYPE_MESSAGE', 'PLUGIN_TYPE_ACCOST']

from .standard import *


# Plugins types
PLUGIN_TYPE_MESSAGE = 'message'
PLUGIN_TYPE_COMMAND = 'chat_command'
PLUGIN_TYPE_ACCOST = 'accost'


class UnknownMatcherError(ValueError):
    """ Unknown matcher error

    Error if matcher can not be instantiated for params specified
    """
    pass


def factory(e_type: str, **params) -> AbstractMatcher:
    """ Get matcher instance

    :param str e_type: Plugin entry type
    :param dict params: Other params (type dependent)
    :return Matcher:
    """
    if e_type == PLUGIN_TYPE_MESSAGE:
        e_params = {param: params[param] for param in params if param in ['system', 'own', 'regular']}
        matcher = SimpleMatcher(**e_params)

    elif e_type == PLUGIN_TYPE_COMMAND:
        if not params.get('command_prefix') or not params.get('command'):
            raise UnknownMatcherError('Command name or command prefix is not configured for command matcher')
        matcher = CommandMatcher(params['command_prefix'], params['command'])

    elif e_type == PLUGIN_TYPE_ACCOST:
        matcher = AccostMatcher()

    else:
        raise UnknownMatcherError('Unrecognized entry type: %s' % e_type)

    return matcher
