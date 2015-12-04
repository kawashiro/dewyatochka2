# -*- coding: UTF-8

""" Package used for plugins auto loading

Each python module in this package is loaded automatically
on application startup so any third-party plugin must create
an own module here and define all necessary entry points

Has no members by default
"""

import importlib

__all__ = []

# Mega hack for plugins loading
# to avoids random import errors on startup
__modules_preload = ('lxml', 'lxml.etree', 'sqlalchemy')

for module in __modules_preload:  # pragma: nocover
    try:
        importlib.import_module(module)
    except ImportError as e:
        pass
