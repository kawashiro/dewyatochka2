# -*- coding: UTF-8

""" Logging implementation

Modules
=======
    output  -- Log output handlers implementation
    service -- Logging app service implementation
    factory -- Subroutines to create and configure appropriate logger instance

Functions
=========
    get_daemon_logger  -- Get configured logger instance for daemonizeable apps
    get_console_logger -- Get console app logger
"""

from .factory import get_console_logger, get_daemon_logger

__all__ = ['service', 'output', 'factory', 'get_daemon_logger', 'get_console_logger']
