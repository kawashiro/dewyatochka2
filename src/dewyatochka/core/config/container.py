# -*- coding: UTF-8

"""
Different containers for different configs filesystem hierarchy
"""

__all__ = ['ConfigContainer', 'CommonConfig', 'ConferencesConfig', 'ExtensionsConfig']

from dewyatochka.core.application import Application, Service
from dewyatochka.core.config.source import ConfigSource


class ConfigContainer(Service):
    """
    Config container service
    """

    def __init__(self, application: Application):
        """
        Create new file config
        :param application: Application
        """
        super().__init__(application)
        self._data = {}

    def load(self, config_parser: ConfigSource):
        """
        Load config data from parser
        :param config_parser: ConfigParser
        :return: ConfigContainer
        """
        self._data = config_parser.read()
        return self

    def section(self, section: str) -> dict:
        """
        Get config for service specified
        :param section: Section name
        :return: dict
        """
        try:
            return self._data[section]
        except KeyError:
            return {}

    @classmethod
    def name(cls) -> str:
        """
        Get service unique name
        :return: str
        """
        return 'config'

    def __iter__(self) -> dict:
        """
        Return sections iterator
        :return: dict
        """
        return self._data


class CommonConfig(ConfigContainer):
    """
    Common file config
    """

    @property
    def global_section(self) -> dict:
        """
        Get global section [global]
        :return: dict
        """
        return self.section('global')


class ConferencesConfig(ConfigContainer):
    """
    Config for conferences list
    """

    @classmethod
    def name(cls) -> str:
        """
        Get service unique name
        :return: str
        """
        return 'conferences_config'


class ExtensionsConfig(ConfigContainer):
    """
    Config for conferences list
    """

    @classmethod
    def name(cls) -> str:
        """
        Get service unique name
        :return: str
        """
        return 'ext_config'
