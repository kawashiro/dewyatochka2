# -*- coding: UTF-8

""" Basic implementations for each plugin sub-system

Classes
=======
    Environment         -- Minimal plugin environment
    Service             -- Plugins container service
    Loader              -- Abstract plugins loader
    Wrapper             -- Wraps a plugin into environment
    PluginLogService    -- Named logger for plugin
    PluginConfigService -- Dict-like config container for plugin

Attributes
==========
    PluginEntry -- Namedtuple, contains loaded & wrapped plugin callback
        and attributes which plugin has been registered with
"""

from collections import namedtuple
from abc import ABCMeta, abstractmethod, abstractproperty

from dewyatochka.core.application import Registry, Application
from dewyatochka.core.application import Service as AppService

from .exceptions import PluginRegistrationError

__all__ = ['Environment', 'Service', 'Loader', 'Wrapper', 'PluginEntry', 'PluginLogService', 'PluginConfigService']


# Registered plugin structure
PluginEntry = namedtuple('PluginEntry', ['plugin', 'params'])


class Environment:
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

    @property
    def name(self) -> str:
        """ Get unique name

        :return str:
        """
        return '.'.join((self._plugin.__module__, self._plugin.__name__))

    def __str__(self) -> str:
        """ Convert to string (=name)

        :return str:
        """
        return self.name

    def __call__(self, *, logger=None, **kwargs):
        """ Let it be invokable too (as a plugin is)

        :param logging.Logger logger:
        :param dict kwargs:
        :return None:
        """
        try:
            self.invoke(**kwargs)
        except Exception as e:
            if logger is not None:
                logger.error('Plugin %s failed: %s', self, e)


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

    def load(self):
        """ Load plugins

        :return None:
        """
        self._plugins = []
        wrapper = self._wrapper

        for loader in self.application.registry.plugins.loaders:
            for entry in loader.load(self):
                try:
                    self._plugins.append(wrapper.wrap(entry))
                except Exception as e:
                    self.log.error('Failed to register plugin %s.%s: %s',
                                   entry.plugin.__module__,
                                   entry.plugin.__name__,
                                   e)

        self.log.debug('Loaded %d %s plugins', len(self._plugins), self.name())

    @abstractproperty
    def accepts(self) -> list:  # pragma: no cover
        """ Get list of acceptable plugin types

        :return list:
        """
        pass

    @property
    def _wrapper(self):
        """ Get wrapper instance

        :return Wrapper:
        """
        return Wrapper(self)

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


class Wrapper:
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

        plugin_conf_section = entry.plugin.__module__.split('.')[-1]
        plugin_conf_data = self._service.application.registry.extensions_config.section(plugin_conf_section)
        config_container = PluginConfigService(self._service.application, plugin_conf_data)
        plugin_registry.add_service(config_container)

        plugin_registry.add_service(PluginLogService(self._service.application, entry.plugin))

        return plugin_registry

    def wrap(self, entry: PluginEntry) -> Environment:
        """ Wrap plugin into it's environment

        :param PluginEntry entry: Raw plugin entry
        :return Environment:
        """
        return Environment(entry.plugin, self._get_registry(entry))


class PluginLogService(AppService):
    """ Named logger for plugin """

    def __init__(self, application: Application, owner: callable):
        """ Initialize service & attach an application to it

        :param Application application:
        :param callable owner:
        """
        super().__init__(application)
        self._logger_name = '.'.join((owner.__module__, owner.__name__))

    def __getattr__(self, item):
        """ Get inner logger attribute

        :param str item:
        :returns: Depending on value
        """
        return getattr(self.application.registry.log(self._logger_name), item)

    @classmethod
    def name(cls) -> str:
        """ Get service unique name

        :return str:
        """
        return 'log'


class PluginConfigService(AppService):
    """ Dict-like config container for plugin """

    def __init__(self, application: Application, data: dict):
        """ Init service

        :param Application application:
        :param dict data:
        """
        super().__init__(application)
        self._data = data

    def __getitem__(self, item):
        """ Get dict item

        :param hashable item:
        :returns: Various
        """
        return self._data[item]

    def __getattr__(self, item: str):
        """ Get dict attribute

        :param str item:
        :returns: Various
        """
        return getattr(self._data, item)

    @classmethod
    def name(cls) -> str:
        """ Get service unique name

        :return str:
        """
        return 'config'
