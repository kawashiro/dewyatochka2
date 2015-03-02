# -*- coding: UTF-8

""" Plugins loading system

Contains plugins auto loading systems

Packages
========
    loader      -- Plugins loaders package
    message_sys -- Message plugins sub-system
    helper_sys  -- Helper plugins sub-system
    ctl_sys     -- Plugins for dewyatochkactl utility

Modules
=======
    base       -- Basic implementations for each plugin sub-system
    exceptions -- Plugin registration related exceptions

Functions
=========
    helper       -- Decorator for helper plugin
    chat_message -- Decorator for chat message plugin
    chat_command -- Decorator for chat command plugin
"""

__all__ = ['loader', 'message_sys', 'helper_sys', 'ctl_sys', 'base', 'exceptions',
           'helper', 'chat_message', 'chat_command', 'ctl']

from .helper_sys.py_entry import *
from .message_sys.py_entry import *
from .ctl_sys.py_entry import *
