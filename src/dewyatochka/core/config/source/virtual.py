# -*- coding: UTF-8

""" In-memory config data sources

Classes
=======
    Empty      -- Empty source, always returns {}
    Predefined -- Returns prepared data specified
"""

from dewyatochka.core.config.source import ConfigSource

__all__ = ['Empty', 'Predefined']


class Predefined(ConfigSource):
    """ Config source with already prepared data  """

    def __init__(self, data: dict):
        """ Create predefined source instance

        :param dict data:
        """
        self._data = data

    def read(self) -> dict:
        """ Read data and return dict-like object {'section': <...>}

        :return dict:
        """
        return self._data


class Empty(ConfigSource):
    """ Empty config implementation """

    def read(self) -> dict:
        """ Read data and return dict-like object {'section': <...>}

        :return dict:
        """
        return {}
