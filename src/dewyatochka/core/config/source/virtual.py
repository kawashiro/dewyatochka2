# -*- coding: UTF-8

"""
In-memory config sources
"""

__all__ = ['Empty', 'Predefined']

from dewyatochka.core.config.source import ConfigSource


class Predefined(ConfigSource):
    """
    Config source with already prepared data
    """

    def __init__(self, data: dict):
        """
        Create predefined source instance
        :param data: dict
        """
        self._data = data

    def read(self) -> dict:
        """
        Read file or directory and return dict-like object {'section': <...>}
        :return: dict
        """
        return self._data


class Empty(Predefined):
    """
    Empty config implementation
    """

    def __init__(self):
        """
        Create empty predefined config
        """
        super().__init__({})
