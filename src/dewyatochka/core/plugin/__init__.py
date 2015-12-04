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
    builtins   -- Some chat / ctl commands accessible by default

Functions
=========
    control      -- dewyatochkactl command handler decorator
    daemon       -- Register this function as a background helper
    bootstrap    -- Register this function to be executed once on application start
    schedule     -- Register this function to be executed by a schedule
    chat_message -- Decorator for chat message plugin
    chat_command -- Decorator for chat command plugin
    chat_accost  -- Decorator for chat accost plugin
"""

from .subsystem.helper.py_entry import *
from .subsystem.message.py_entry import *
from .subsystem.control.py_entry import *

__all__ = ['loader', 'subsystem', 'base', 'builtins', 'exceptions',
           'control', 'daemon', 'bootstrap', 'schedule',
           'chat_message', 'chat_command', 'chat_accost']
