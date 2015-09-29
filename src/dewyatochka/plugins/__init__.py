# -*- coding: UTF-8

""" Package used for plugins auto loading

Each python module in this package is loaded automatically
on application startup so any third-party plugin must create
an own module here and define all necessary entry points

Has no members by default

Modules
=======
    builtin -- Built-in chat / ctl commands accessible out of the box
"""

import importlib

__all__ = ['builtin']

# Mega hack for plugins loading
# to avoids random import errors on startup
__modules_preload = ('lxml', 'lxml.etree', 'sqlalchemy')

for module in __modules_preload:
    try:
        importlib.import_module(module)
    except ImportError as e:
        pass
