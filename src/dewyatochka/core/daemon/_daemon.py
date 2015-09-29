# -*- coding: UTF-8

""" Daemon detach implementation

Functions
=========
    detach -- Detach a process from console
"""

import os
import signal

from . import _utils

__all__ = ['detach']


def detach(sigterm_handler=None):
    """ Detach a process from console

    :param callable sigterm_handler: SIGTERM handler
    :return None:
    """
    pid = os.fork()
    if pid != 0:
        _utils.exit(0)

    os.setsid()
    pid = os.fork()
    if pid != 0:
        _utils.exit(0)

    if sigterm_handler is not None:
        signal.signal(signal.SIGTERM, sigterm_handler)

    _utils.close_io(os.devnull)
