# -*- coding: UTF-8

""" Config data sources

Sources are separated by modules to group them
by a kind of data storage but most of all by dependencies required

Modules
=======
    filesystem -- File based config data sources
    virtual    -- In-memory config data sources

Classes
=======
    ConfigSource -- Abstract config data source
"""

from abc import ABCMeta, abstractmethod

__all__ = ['ConfigSource', 'filesystem', 'virtual']


class ConfigSource(metaclass=ABCMeta):
    """ Abstract config data source

        For internal use and third-party implementations
    """

    @abstractmethod
    def read(self) -> dict:  # pragma: no cover
        """ Read data and return dict-like object {'section': <...>}

        :return dict:
        """
        pass
