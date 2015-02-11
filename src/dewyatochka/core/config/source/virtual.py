# -*- coding: UTF-8

""" In-memory config data sources

Classes
=======
    Empty      -- Empty source, always returns {}
    Predefined -- Returns prepared data specified
"""

__all__ = ['Empty', 'Predefined']

from dewyatochka.core.config.source import ConfigSource


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


class Empty(Predefined):
    """ Empty config implementation """

    def __init__(self):
        """ Create an empty predefined config """
        super().__init__({})
