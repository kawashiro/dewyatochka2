# -*- coding: UTF-8

""" Configuration containers used in application globally

Classes
=======
    ConfigContainer   -- Superclass for all the containers
    CommonConfig      -- Container for common application configuration options
    ConferencesConfig -- Contains list of conferences configured
    ExtensionsConfig  -- Container with options accessible to extensions
"""

from dewyatochka.core.application import Application, Service
from dewyatochka.core.config.source import ConfigSource
from dewyatochka.core.config.exception import SectionRetrievingError

__all__ = ['ConfigContainer', 'CommonConfig', 'ConferencesConfig', 'ExtensionsConfig']


class ConfigContainer(Service):
    """ Superclass for all the containers

    Implements access to config sections
    and registration as an app service
    """

    def __init__(self, application: Application):
        """ Register an application and initialize empty data storage

        :param Application application:
        """
        super().__init__(application)
        self._data = {}

    def load(self, config_parser: ConfigSource):
        """ Load config data from source

        :param ConfigParser config_parser: Parser instance
        :return ConfigContainer:
        """
        self._data = config_parser.read()
        return self

    def section(self, section: str, require=False) -> dict:
        """ Get config section

        :param str section: Section name
        :param bool require: Raise an exception if section is not found
        :return dict:
        """
        try:
            return self._data[section]
        except KeyError:
            if require:
                raise SectionRetrievingError('Config section %s is not defined' % section)
            return {}

    @classmethod
    def name(cls) -> str:
        """ Get service unique name

        :return str:
        """
        return 'config'

    def __iter__(self):
        """ Return sections iterator

        :return iterator:
        """
        return iter(self._data)


class CommonConfig(ConfigContainer):
    """ Container for common application configuration options """

    @property
    def global_section(self) -> dict:
        """
        Get global section [global]
        :return dict:
        """
        return self.section('global')


class ConferencesConfig(ConfigContainer):
    """ Contains list of conferences configured """

    @classmethod
    def name(cls) -> str:
        """ Get service unique name

        :return str:
        """
        return 'conferences_config'


class ExtensionsConfig(ConfigContainer):
    """ Container with options accessible to extensions """

    @classmethod
    def name(cls) -> str:
        """ Get service unique name

        :return str:
        """
        return 'extensions_config'
