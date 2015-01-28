# -*- coding: UTF-8

"""
Factory functions for config instances creation
"""

__all__ = ['COMMON_CONFIG_DEFAULT_PATH', 'CONFERENCES_CONFIG_DEFAULT_PATH', 'EXTENSIONS_CONFIG_DEFAULT_PATH',
           'get_common_config', 'get_conferences_config', 'get_extensions_config']

from dewyatochka.core.application import Application
from dewyatochka.core.config.container import *
from dewyatochka.core.config.source.filesystem import INIFiles


# Default path to a global config file
COMMON_CONFIG_DEFAULT_PATH = '/etc/dewyatochka/dewyatochka.ini'

# Default path to a conferences config file
CONFERENCES_CONFIG_DEFAULT_PATH = '/etc/dewyatochka/conferences.ini'

# Default path to a extensions directory location
EXTENSIONS_CONFIG_DEFAULT_PATH = '/etc/dewyatochka/ext/'


def _get_file_config_instance(cls: type, application: Application, path: str) -> ConfigContainer:
    """
    Create filesystem-based config container instance by type
    :param cls: type
    :param application: Application
    :param path: str
    :return: ConfigContainer
    """
    config = cls(application)
    config.load(INIFiles(path))

    return config


def get_common_config(application: Application, path=None) -> CommonConfig:
    """
    Get common config container instance
    :param application: Application
    :param path: str
    :return: CommonConfig
    """
    return _get_file_config_instance(CommonConfig, application, path or COMMON_CONFIG_DEFAULT_PATH)


def get_conferences_config(application: Application, path=None) -> ConferencesConfig:
    """
    Get conferences config container instance
    :param application: Application
    :param path: str
    :return: CommonConfig
    """
    return _get_file_config_instance(ConferencesConfig, application, path or CONFERENCES_CONFIG_DEFAULT_PATH)


def get_extensions_config(application: Application, path=None) -> ExtensionsConfig:
    """
    Get conferences config container instance
    :param application: Application
    :param path: str
    :return: CommonConfig
    """
    return _get_file_config_instance(ExtensionsConfig, application, path or EXTENSIONS_CONFIG_DEFAULT_PATH)
