# -*- coding: UTF-8

""" Dewyatochka daemon app (dewyatochkad)

Serves conferences and takes a talk with other people

Classes
=======
    Application -- dewyatochkad application

Functions
=========
    main -- Main routine
"""

from .application import DaemonApp as Application

__all__ = ['Application', 'main']


def main():
    """ Main routine

    :return None:
    """
    import sys

    app = Application()
    app.run(sys.argv)
