# -*- coding: UTF-8

""" Entry decorators for python plugins

Functions
=========
    daemon    -- Register this function as a background helper
    bootstrap -- Register this function to be executed once on application start
    schedule  -- Register this function to be executed by a schedule
"""

from dewyatochka.core.plugin.loader.internal import entry_point

from .service import *

__all__ = ['daemon', 'bootstrap', 'schedule']


def daemon(fn=None, *, services=None) -> callable:
    """ Register this function as a background helper

    :param callable fn: Function if decorator is invoked directly
    :param list services: Function to register
    :return callable:
    """
    entry_point_fn = entry_point(PLUGIN_TYPE_DAEMON, services=services)
    return entry_point_fn(fn) if fn is not None else entry_point_fn


def bootstrap(fn=None, *, services=None) -> callable:
    """ Register this function to be executed once on application start

    :param callable fn: Function if decorator is invoked directly
    :param list services: Function to register
    :return callable:
    """
    entry_point_fn = entry_point(PLUGIN_TYPE_BOOTSTRAP, services=services)
    return entry_point_fn(fn) if fn is not None else entry_point_fn


def schedule(schedule_: str, *, services=None, lock=True) -> callable:
    """ Register this function to be executed by a schedule

    :param str schedule_: Schedule expression
    :param list services: Function to register
    :param bool lock: Forbid concurrent tasks run or not
    :return callable:
    """
    return entry_point(PLUGIN_TYPE_SCHEDULE, services=services, schedule=schedule_, lock=lock)
