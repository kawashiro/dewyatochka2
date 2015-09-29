# -*- coding: UTF-8

""" Subroutines to create and configure appropriate container instance

Attributes
==========
    COMMON_CONFIG_DEFAULT_PATH      -- Default path to a global config file
    CONFERENCES_CONFIG_DEFAULT_PATH -- Default path to a conferences config file
    EXTENSIONS_CONFIG_DEFAULT_PATH  -- Default path to a extensions directory location

Functions
=========
    get_common_config      -- Get common config container instance
    get_conferences_config -- Get conferences config container instance
    get_extensions_config  -- Get extensions config container instance
"""

from dewyatochka.core.application import Application
from dewyatochka.core.config.container import *
from dewyatochka.core.config.source.filesystem import INIFiles

__all__ = ['COMMON_CONFIG_DEFAULT_PATH', 'CONFERENCES_CONFIG_DEFAULT_PATH', 'EXTENSIONS_CONFIG_DEFAULT_PATH',
           'get_common_config', 'get_conferences_config', 'get_extensions_config']


# Filesystem configs default locations
COMMON_CONFIG_DEFAULT_PATH = '/etc/dewyatochka/dewyatochka.ini'
CONFERENCES_CONFIG_DEFAULT_PATH = '/etc/dewyatochka/conferences.ini'
EXTENSIONS_CONFIG_DEFAULT_PATH = '/etc/dewyatochka/ext/'


def _get_file_config_instance(cls: type, application: Application, path: str) -> ConfigContainer:
    """ Create filesystem-based config container instance by type

    :param type cls:
    :param Application application:
    :param str path:
    :return ConfigContainer:
    """
    config = cls(application)
    config.load(INIFiles(path))

    return config


def get_common_config(application: Application, path=None) -> CommonConfig:
    """ Get common config container instance

    :param Application application: Application instance
    :param str path: Path to config location, None to use default one
    :return CommonConfig:
    """
    return _get_file_config_instance(CommonConfig, application, path or COMMON_CONFIG_DEFAULT_PATH)


def get_conferences_config(application: Application) -> ConferencesConfig:
    """ Get conferences config container instance

    :param Application application: Application instance
    :return ConferencesConfig:
    """
    try:
        path = application.registry.config.global_section['conferences']
    except:
        path = CONFERENCES_CONFIG_DEFAULT_PATH

    return _get_file_config_instance(ConferencesConfig, application, path)


def get_extensions_config(application: Application) -> ExtensionsConfig:
    """ Get extensions config container instance

    :param Application application: Application instance
    :return ExtensionsConfig:
    """
    try:
        path = application.registry.config.global_section['extensions']
    except:
        path = EXTENSIONS_CONFIG_DEFAULT_PATH

    return _get_file_config_instance(ExtensionsConfig, application, path)
