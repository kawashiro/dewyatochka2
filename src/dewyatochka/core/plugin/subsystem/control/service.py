# -*- coding: UTF-8

""" Helper plugins container service implementation

Classes
=======
    Environment -- Ctl plugin environment
    Service     -- Ctl plugins container service
    Wrapper     -- Wraps a plugin into environment

Attributes
==========
    PLUGIN_TYPE_CTL  -- Ctl plugin type
    PLUGIN_TYPES     -- All plugin types list
"""

__all__ = ['Environment', 'Service', 'Wrapper', 'PLUGIN_TYPE_CTL', 'PLUGIN_TYPES']

from dewyatochka.core.plugin.base import PluginEntry
from dewyatochka.core.plugin.base import Environment as BaseEnvironment
from dewyatochka.core.plugin.base import Service as BaseService
from dewyatochka.core.plugin.base import Wrapper as BaseWrapper


# Plugin types provided
PLUGIN_TYPE_CTL = 'ctl'
PLUGIN_TYPES = [PLUGIN_TYPE_CTL]


class Environment(BaseEnvironment):
    """ ctl plugin environment """

    def __call__(self, **kwargs):
        """ Let it be invokable too (as a plugin is)

        :param dict kwargs:
        :return None:
        """
        self.invoke(**kwargs)


class Service(BaseService):
    """ Ctl plugins container service """

    @property
    def accepts(self) -> list:
        """ Get list of acceptable plugin types

        :return list:
        """
        return PLUGIN_TYPES

    def load(self):
        """ Load plugins

        :return None:
        """
        self._plugins = {}
        wrapper = self._wrapper

        for loader in self.application.registry.plugins.loaders:
            for entry in loader.load(self):
                try:
                    self._plugins[entry.params['name']] = wrapper.wrap(entry)
                except Exception as e:
                    self.log.error('Failed to register command %s (%s.%s): %s',
                                   entry.params['name'], entry.plugin.__module__,
                                   entry.plugin.__name__, e)

        self.log.debug('Loaded %d %s plugins', len(self._plugins), self.name())

    def get_command(self, name: str) -> Environment:
        """ Get command to use

        :param str name: Registered command name
        :return Environment:
        """
        if self._plugins and name in self._plugins:
            return self._plugins[name]

        raise RuntimeError('Command %s is not registered' % name)

    @property
    def plugins(self) -> list:
        """ Get plugins list

        :return list:
        """
        # noinspection PyUnresolvedReferences
        return super().plugins.values()

    @property
    def _wrapper(self):
        """ Get wrapper instance

        :return Wrapper:
        """
        return Wrapper(self)


class Wrapper(BaseWrapper):
    """ Wraps a plugin into environment """

    def wrap(self, entry: PluginEntry) -> Environment:
        """ Wrap plugin into it's environment

        :param PluginEntry entry: Raw plugin entry
        :return Environment:
        """
        return Environment(entry.plugin, self._get_registry(entry))
