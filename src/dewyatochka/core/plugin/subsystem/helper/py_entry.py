# -*- coding: UTF-8

""" Entry decorators for python plugins

Functions
=========
    helper -- Decorator for helper plugin
"""

__all__ = ['helper']

from dewyatochka.core.plugin.loader.internal import entry_point
from .service import PLUGIN_TYPE_HELPER


def helper(fn=None, *, services=None) -> callable:
    """ Register this function as a background helper

    :param callable fn: Function if decorator is invoked directly
    :param list services: Function to register
    :return callable:
    """
    entry_point_fn = entry_point(PLUGIN_TYPE_HELPER, services=services)
    return entry_point_fn(fn) if fn is not None else entry_point_fn
