# -*- coding: UTF-8

""" Entry decorators for python plugins

Functions
=========
    control -- Decorator for ctl-plugin

Classes
=======
    CtlInputError -- Error on invalid args in input data
"""

from dewyatochka.core.plugin.loader.internal import entry_point
from dewyatochka.core.plugin.exceptions import PluginRegistrationError, PluginError

from .service import PLUGIN_TYPE_CTL

__all__ = ['control', 'CtlInputError']


# Commands already in use
_used_commands = set()


class CtlInputError(PluginError):
    """ Error on invalid args in input data """
    pass


def control(name: str, description: str, *, services=None) -> callable:
    """ Register this function as a ctl command

    :param str name: Command name
    :param str description: Command short description
    :param list services: Dependencies
    :return callable:
    """
    from dewyatochka.core.plugin import builtins

    def _entry_point(fn):
        if fn.__module__ == builtins.__name__:
            full_name = name
        else:
            module_name = fn.__module__.split('.')[-1]
            full_name = '.'.join((module_name, name))

        if full_name in _used_commands:
            raise PluginRegistrationError('ctl command "%s" is already in use' % full_name)
        _used_commands.add(full_name)

        return entry_point(PLUGIN_TYPE_CTL, services=services, name=full_name, description=description)(fn)

    return _entry_point
