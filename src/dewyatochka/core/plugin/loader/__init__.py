# -*- coding: UTF-8

""" Plugins loaders package

Contains plugins auto loading system and wrappers
over different types of plugin implementation

Modules
=======
    internal -- Internal python modules loader

Classes
=======
    LoaderService -- Simple loader service
"""

__all__ = ['internal', 'LoaderService']

from dewyatochka.core.application import Service

from . import internal


class LoaderService(Service):
    """ Simple loader service """

    @property
    def loaders(self) -> list:
        """ Get all loaders available

        :return list:
        """
        return [internal.Loader()]

    @classmethod
    def name(cls) -> str:
        """ Get service unique name

        :return str:
        """
        return 'plugins'
