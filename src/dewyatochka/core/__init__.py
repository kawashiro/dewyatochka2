# -*- coding: UTF-8

""" Dewyatochka core package

Contains all the packages needed dewyatochka to just work.
"Just work" means a simple xmpp-client that holds connection to a
xmpp-server configured, enter to some conference and that's all

Sub-packages
============
    config  -- Config options containers implementation
    log     -- Logging implementation
    network -- Implementation of application-level network protocols
    plugin  -- Plugins loading system

Modules
=======
    application -- Something like "framework" to build all dewyatochka apps on
"""

__all__ = ['application', 'config', 'log', 'network', 'plugin']
