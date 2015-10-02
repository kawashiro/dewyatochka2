# -*- coding: UTF-8

""" Helper plugins container service implementation

Classes
=======
    Service             -- Helper plugins container service
    ScheduleEnvironment -- Environment for a schedule plugin
    Wrapper             -- Wraps a plugin into environment

Attributes
==========
    PLUGIN_TYPES          -- All plugin types list
    PLUGIN_TYPE_SCHEDULE  -- Executed by a schedule
    PLUGIN_TYPE_BOOTSTRAP -- Executed once on application start
    PLUGIN_TYPE_DAEMON    -- Runs all the time in background
"""

from threading import Event

from dewyatochka.core.application import Registry, Application
from dewyatochka.core.plugin.base import Environment, PluginEntry
from dewyatochka.core.plugin.base import Wrapper as BaseWrapper
from dewyatochka.core.plugin.base import Service as BaseService

from .schedule import Schedule

__all__ = ['Service', 'ScheduleEnvironment', 'Wrapper',
           'PLUGIN_TYPES', 'PLUGIN_TYPE_SCHEDULE', 'PLUGIN_TYPE_BOOTSTRAP', 'PLUGIN_TYPE_DAEMON']


# Plugin types provided
PLUGIN_TYPE_SCHEDULE = 'schedule'
PLUGIN_TYPE_BOOTSTRAP = 'bootstrap'
PLUGIN_TYPE_DAEMON = 'daemon'
PLUGIN_TYPES = [PLUGIN_TYPE_SCHEDULE, PLUGIN_TYPE_BOOTSTRAP, PLUGIN_TYPE_DAEMON]


class ScheduleEnvironment(Environment):
    """ Environment for a schedule plugin

    Also contains a reference to a matcher instance
    to pass through only valid messages
    """

    def __init__(self, plugin: callable, registry: Registry, schedule: Schedule, lock=True):
        """ Initialize plugin environment

        :param callable plugin:
        :param Registry registry:
        :param Schedule schedule:
        :param bool lock:
        """
        super().__init__(plugin, registry)

        self._schedule = schedule
        self._lock = Event() if lock else None

    def invoke(self, **kwargs):
        """ Invoke plugin in environment registered

        :param dict kwargs: Params to path to a plugin
        :return None:
        """
        if not self._schedule.in_time:
            return

        if self._lock:
            if self._lock.is_set():
                raise RuntimeError('The same task is still running')
            self._lock.set()

        try:
            super().invoke(**kwargs)
        finally:
            if self._lock:
                self._lock.clear()


class Wrapper(BaseWrapper):
    """ Wraps a plugin into environment """

    def wrap(self, entry: PluginEntry) -> Environment:
        """ Wrap plugin into it's environment

        :param PluginEntry entry: Raw plugin entry
        :return Environment:
        """
        registry = self._get_registry(entry)

        if entry.params['type'] == PLUGIN_TYPE_SCHEDULE:
            schedule = Schedule.from_string(entry.params['schedule'])
            lock_process = entry.params.get('lock', True)
            environment = ScheduleEnvironment(entry.plugin, registry, schedule, lock=lock_process)
        else:
            environment = Environment(entry.plugin, registry)

        return environment


class Service(BaseService):
    """ Helper plugins container service """

    # Plugin wrapper class
    _wrapper_class = Wrapper

    def __init__(self, application: Application):
        """ Create plugin container service

        :param Application application:
        """
        super().__init__(application)

        self.__plugins_by_type = {
            PLUGIN_TYPE_SCHEDULE: [],
            PLUGIN_TYPE_BOOTSTRAP: [],
            PLUGIN_TYPE_DAEMON: [],
        }

    def _register_plugin(self, entry: PluginEntry):
        """ Register a single plugin

        :param PluginEntry entry:
        :return None:
        """
        wrapped = self._wrapper.wrap(entry)

        self._plugins.append(wrapped)
        self.__plugins_by_type[entry.params['type']].append(wrapped)

    @property
    def accepts(self) -> list:
        """ Get list of acceptable plugin types

        :return list:
        """
        return PLUGIN_TYPES

    @property
    def _plugins_by_type(self) -> dict:
        """ Get plugins grouped by type

        :return dict:
        """
        if self._plugins is None:
            raise RuntimeError('Plugins are not loaded')

        return self.__plugins_by_type

    @property
    def schedule_plugins(self) -> list:
        """ Get schedule plugins list

        :return list:
        """
        return self._plugins_by_type[PLUGIN_TYPE_SCHEDULE]

    @property
    def daemon_plugins(self) -> list:
        """ Get daemon plugins list

        :return list:
        """
        return self._plugins_by_type[PLUGIN_TYPE_DAEMON]

    @property
    def bootstrap_plugins(self) -> list:
        """ Get bootstrap plugins list

        :return list:
        """
        return self._plugins_by_type[PLUGIN_TYPE_BOOTSTRAP]

    @classmethod
    def name(cls) -> str:
        """ Get service unique name

        :return str:
        """
        return 'helper_plugin_provider'
