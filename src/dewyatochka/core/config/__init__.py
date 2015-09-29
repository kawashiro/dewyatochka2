# -*- coding: UTF-8

""" Config options containers implementation

Packages
========
    source -- Config data sources (files, databases, etc)

Modules
=======
    container -- Configuration containers used in application globally
    exception -- Related exception classes
    factory   -- Subroutines to create and configure appropriate container instance

Functions
=========
    get_common_config      -- Import from dewyatochka.core.config.factory
    get_conferences_config -- Import from dewyatochka.core.config.factory
    get_extensions_config  -- Import from dewyatochka.core.config.factory
"""

from .factory import get_common_config, get_conferences_config, get_extensions_config

__all__ = ['container', 'exception', 'factory', 'source',
           'get_common_config', 'get_conferences_config', 'get_extensions_config']
