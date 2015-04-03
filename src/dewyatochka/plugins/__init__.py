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

__all__ = ['builtin']

import importlib

try:
    importlib.import_module('lxml')  # FIXME: Remove this dirty hack
    importlib.import_module('lxml.etree')
except ImportError:
    pass
