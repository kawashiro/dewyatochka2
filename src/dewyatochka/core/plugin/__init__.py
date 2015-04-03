# -*- coding: UTF-8

""" Plugins loading system

Contains plugins auto loading systems

Packages
========
    loader    -- Plugins loaders package
    subsystem -- Plugin subsystems implementations

Modules
=======
    base       -- Basic implementations for each plugin sub-system
    exceptions -- Plugin registration related exceptions

Functions
=========
    helper       -- Decorator for helper plugin
    chat_message -- Decorator for chat message plugin
    chat_command -- Decorator for chat command plugin
    ctl          -- dewyatochkactl command handler decorator
"""

__all__ = ['loader', 'subsystem', 'base', 'exceptions',
           'helper', 'chat_message', 'chat_command', 'ctl']

from .subsystem.helper.py_entry import *
from .subsystem.message.py_entry import *
from .subsystem.control.py_entry import *
