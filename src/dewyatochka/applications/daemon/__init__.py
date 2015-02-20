# -*- coding: UTF-8

""" Dewyatochka daemon app (dewyatochkad)

Serves conferences and takes a talk with other people

Classes
=======
    Application -- dewyatochkad application
"""

__all__ = ['Application']

from ._application import DaemonApp as Application  # Alias for a common interface
