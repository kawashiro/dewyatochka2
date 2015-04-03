# -*- coding: UTF-8

""" High-level applications implementation

Each module in this package MUST contain dewyatochka.core.application.Application
class implementation. Private sub-packages / sub-modules are also allowed if
certain application is too complicated.

Packages
========
    daemon -- Dewyatochka daemon app (dewyatochkad)

Modules
=======
    control -- dewyatochkactl utility implementation
"""

__all__ = ['daemon', 'control']
