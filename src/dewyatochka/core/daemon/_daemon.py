# -*- coding: UTF-8

""" Daemon detach implementation

Classes
=======
    ProcessLockedError    -- Exception on already locked process
    ProcessNotLockedError -- Exception process is not locked but should be

Functions
=========
    detach       -- Detach a process from console
    acquire_lock -- Create a lock-file
    release_lock -- Delete a lock-file
"""

import os
import signal
import fcntl

from . import _utils

__all__ = ['ProcessLockedError', 'ProcessNotLockedError', 'acquire_lock', 'release_lock', 'detach']


# Path to the lock-file if none is specified
_DEFAULT_LOCK_FILE_PATH = '/var/run/dewyatochka/dewyatochkad.pid'

# Global lock file handler
_lock_file_obj = None


class ProcessLockedError(RuntimeError):
    """ Exception on already locked process """
    pass


class ProcessNotLockedError(RuntimeError):
    """ Exception process is not locked but should be """
    pass


def acquire_lock(lock_file=None):
    """ Create a lock-file

    :param str lock_file: Path to a lock-file
    :return None:
    """
    global _lock_file_obj

    if _lock_file_obj is not None:
        raise ProcessLockedError('Current process is already locked')

    if os.path.isfile(lock_file):
        raise ProcessLockedError('Another process is already running')

    if lock_file is None:
        lock_file = _DEFAULT_LOCK_FILE_PATH  # pragma: nocover

    _lock_file_obj = open(lock_file, 'w')
    fcntl.flock(_lock_file_obj.fileno(), fcntl.LOCK_EX)
    _lock_file_obj.write(str(os.getpid()))
    _lock_file_obj.flush()


def release_lock():
    """ Delete a lock-file

    :return None:
    """
    global _lock_file_obj

    if _lock_file_obj is None or _lock_file_obj.closed:
        raise ProcessNotLockedError('Process is not locked to unlock it')

    fcntl.flock(_lock_file_obj, fcntl.LOCK_UN)
    _lock_file_obj.close()
    os.unlink(_lock_file_obj.name)

    _lock_file_obj = None


def detach(sigterm_handler=None):  # pragma: nocover
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
