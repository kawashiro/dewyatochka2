# -*- coding: UTF-8

""" Entry decorators for python plugins

Functions
=========
    ctl -- Decorator for ctl-plugin
"""

from dewyatochka.core.plugin.loader.internal import entry_point
from .service import PLUGIN_TYPE_CTL


def ctl(name: str, description: str, *, services=None) -> callable:
    """ Register this function as a ctl command

    :param str name: Command name
    :param str description: Command short description
    :param list services: Dependencies
    :return callable:
    """
    return entry_point(PLUGIN_TYPE_CTL, services=services, name=name, description=description)
