# -*- coding: UTF-8

""" Dewyatochka daemon implementation package

Contains all base daemon logic (detaching from console, etc)
and lock files management

Classes
=======
    ProcessLockedError    -- Exception on already locked process
    ProcessNotLockedError -- Exception process is not locked but should be

Functions
=========
    acquire_lock -- Create a lock-file
    release_lock -- Delete a lock-file
    detach       -- Detach a process from console
"""

from ._daemon import *

__all__ = ['detach', 'ProcessLockedError', 'ProcessNotLockedError', 'acquire_lock', 'release_lock']
