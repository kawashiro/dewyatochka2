# -*- coding: UTF-8

"""
Config module
"""

__all__ = ['ConferenceConfig', 'GlobalConfig', 'ConfigError']

from os import path
import configparser
from dewyatochka.core.application import Service


class ConfigError(Exception):
    """
    Exception on invalid config file content
    """
    pass


class _INIFIleConfig(Service):
    """
    Config stored in ini file
    """

    # INI parser instance
    _parser = None

    def __init__(self, application):
        """
        Create new file config
        :param application: Application
        """
        super().__init__(application)
        self._parser = configparser.ConfigParser()

    def reload(self, config_file):
        """
        Load config data from file
        :param config_file: Config file path
        :return: void
        """
        if not path.isfile(config_file):
            raise FileExistsError('Config file %s not found' % config_file)

        try:
            self._parser.read(config_file)
        except configparser.Error as e:
            raise ConfigError(e)

    def section(self, section):
        """
        Get config for service specified
        :param section: Section name
        :return: dict
        """
        try:
            return self._parser[section]
        except KeyError:
            return {}

    @property
    def global_section(self):
        """
        Get global section [global]
        :return: dict
        """
        return self.section('global')

    @property
    def sections(self):
        """
        Get sections available
        :return: list
        """
        return self._parser.sections()

    def __iter__(self):
        """
        Iterate through all the sections
        """
        for section in self._parser.sections():
            yield self.section(section)


class GlobalConfig(_INIFIleConfig):
    """
    Global app configuration
    """

    # Path to a global config file
    DEFAULT_FILE_PATH = '/etc/dewyatochka/dewyatochka.ini'

    # Default path to the lock-file
    DEFAULT_LOCK_FILE = '/var/run/dewyatochka2/dewyatochkad.pid'

    # Default path to the log-file
    DEFAULT_LOG_FILE = '/var/log/dewyatochkad.log'


class ConferenceConfig(_INIFIleConfig):
    """
    Conferences configurations container
    """

    # Path to a global config file
    DEFAULT_FILE_PATH = '/etc/dewyatochka/conferences.ini'
