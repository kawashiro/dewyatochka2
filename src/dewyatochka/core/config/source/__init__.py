# -*- coding: UTF-8

"""
Config sources package
"""

__all__ = ['ConfigSource', 'filesystem']

from abc import ABCMeta, abstractmethod


class ConfigSource(metaclass=ABCMeta):
    """
    Config file parser
    """

    @abstractmethod
    def read(self) -> dict:  # pragma: no cover
        """
        Read file or directory and return dict-like object {'section': <...>}
        :return: dict
        """
        pass
