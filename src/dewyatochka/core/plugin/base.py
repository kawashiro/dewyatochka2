# -*- coding: UTF-8

""" Basic implementations for each plugin sub-system

Classes
=======
    Environment -- Minimal plugin environment
    Service     -- Plugins container service
    Loader      -- Abstract plugins loader
    Wrapper     -- Wraps a plugin into environment

Attributes
==========
    PluginEntry -- Namedtuple, contains loaded & wrapped plugin callback
        and attributes which plugin has been registered with
"""

__all__ = ['Environment', 'Service', 'Loader', 'Wrapper', 'PluginEntry']

from collections import namedtuple
from abc import ABCMeta, abstractmethod, abstractproperty

from dewyatochka.core.application import Registry, Application
from dewyatochka.core.application import Service as AppService
from dewyatochka.core.plugin.exceptions import PluginRegistrationError


# Registered plugin structure
PluginEntry = namedtuple('PluginEntry', ['plugin', 'params'])


class Environment():
    """ Minimal plugin environment

    Contains only a references to a plugin
    and it's dependencies registry
    """

    def __init__(self, plugin: callable, registry: Registry):
        """ Initialize plugin environment

        :param callable plugin:
        :param Registry registry:
        """
        self._plugin = plugin
        self._registry = registry

    def invoke(self, **kwargs):
        """ Invoke plugin in environment registered

        :param dict kwargs: Params to path to a plugin
        :return None:
        """
        self._plugin(registry=self._registry, **kwargs)

    def __call__(self, **kwargs):
        """ Let it be invokable too (as a plugin is)

        :param dict kwargs:
        :return None:
        """
        self.invoke(**kwargs)


class Service(AppService, metaclass=ABCMeta):
    """ Plugins container service

    Provides access to plugins collections loaded
    """

    def __init__(self, application: Application):
        """ Create plugin container service

        :param Application application:
        """
        super().__init__(application)
        self._plugins = None

    def load(self, loaders, wrapper):
        """ Load plugins

        :param iterable loaders: Loaders collection
        :param Wrapper wrapper: Wrapper instance
        :return None:
        """
        self._plugins = []
        for loader in loaders:
            for entry in loader.load(self):
                try:
                    self._plugins.append(wrapper.wrap(entry))
                except Exception as e:
                    self.log.error('Failed to register plugin %s: %s', repr(entry.plugin), e)

        self.log.info('Loaded %d plugins', len(self._plugins))

    @abstractproperty
    def accepts(self) -> list:  # pragma: no cover
        """ Get list of acceptable plugin types

        :return list:
        """
        pass

    @property
    def plugins(self) -> list:
        """ Get plugins list

        :return list:
        """
        if self._plugins is None:
            raise RuntimeError('Plugins are not loaded')

        return self._plugins


class Loader(metaclass=ABCMeta):
    """ Abstract plugins loader """

    @abstractmethod
    def load(self, service: Service) -> list:  # pragma: no cover
        """ Load and return plugins

        :param Service service: Reference to a service initiated load
        :return list: List of PluginEntry
        """
        pass


class Wrapper():
    """ Wraps a plugin into environment """

    def __init__(self, service: Service):
        """ Create plugin wrapper for plugin service

        :param Service service:
        :return:
        """
        self._service = service

    def _get_registry(self, entry: PluginEntry) -> Registry:
        """ Create a registry for plugin

        :param list dependencies:
        :return registry:
        """
        plugin_registry = Registry()
        services = entry.params.get('services')

        if services is not None:
            for service in services:
                try:
                    service_obj = self._service.application.registry.get_service(service)
                    plugin_registry.add_service(service_obj)
                except Exception as e:
                    raise PluginRegistrationError(
                        'Failed to get add dependency %s for plugin %s: %s' % (repr(service), repr(entry.plugin), e)
                    )

        plugin_registry.add_service(self._service.application.registry.ext_config)
        plugin_registry.add_service_alias('ext_config', 'config')

        plugin_registry.add_service(self._service.application.registry.log)

        return plugin_registry

    def wrap(self, entry: PluginEntry) -> Environment:
        """ Wrap plugin into it's environment

        :param PluginEntry entry: Raw plugin entry
        :return Environment:
        """
        return Environment(entry.plugin, self._get_registry(entry))
