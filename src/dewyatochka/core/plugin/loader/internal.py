# -*- coding: UTF-8

""" Internal python modules loader

Classes
=======
    Loader -- Python plugins loader

Functions
=========
    entry_point -- Plugin entry point decorator
"""

import os
from collections import defaultdict
import importlib
from functools import reduce

from dewyatochka import plugins  # Be careful to remove this import
from dewyatochka.core.plugin.base import Loader as BaseLoader
from dewyatochka.core.plugin.base import PluginEntry
from dewyatochka.core.plugin.base import Service
from dewyatochka.core.config.exception import SectionRetrievingError

__all__ = ['Loader', 'entry_point']


# Entry points dict grouped by entry point type
_entry_points = defaultdict(lambda: [])

# Flag if modules loading is completed
_ready = False


def entry_point(entry_point_type, **kwargs) -> callable:
    """ Plugin entry point decorator

    :param str entry_point_type: Entry point type (depends on sub-system implementation)
    :param dict kwargs: Other arguments to pass to a decorator
    :return callable:
    """
    def _decorator(fn):
        fn_obj = fn() if isinstance(fn, type) else fn
        fn_obj.__name__ = fn.__name__ if hasattr(fn, '__name__') else fn_obj.__class__
        params = kwargs.copy()
        params['type'] = entry_point_type
        _entry_points[entry_point_type].append(PluginEntry(fn_obj, params))
        return fn

    return _decorator


class Loader(BaseLoader):
    """ Python plugins loader

    Loads plugins located into dewyatochka.plugins package
    """

    # Package init file
    __PKG_INIT = '__init__.py'

    # Separator between packages / modules
    __PKG_SEP = '.'

    # Python file extension
    __MODULE_EXT = '.py'

    # Python plugins auto loading path
    __PLUGINS_PATH = os.path.dirname(plugins.__file__)

    def _get_modules(self, service: Service) -> list:
        """ Load optional plugin modules

        :param Service service: Reference to a service initiated load
        :return list:
        """
        modules = []
        for file in os.listdir(self.__PLUGINS_PATH):
            file_path = os.sep.join([self.__PLUGINS_PATH, file])

            if self.__is_module(file_path):
                load_name = self.__PKG_SEP.join([plugins.__name__, file[:-len(self.__MODULE_EXT)]])
            elif self.__is_package(file_path):
                load_name = self.__PKG_SEP.join([plugins.__name__, file])
            else:
                continue  # pragma: no cover

            try:
                conf_name = load_name.split(self.__PKG_SEP)[-1]
                if conf_name not in plugins.__all__:
                    service.application.registry.extensions_config.section(conf_name, require=True)
            except SectionRetrievingError:
                service.application.registry.log(__name__).warning('Plugin %s is disabled', load_name)
                continue

            modules.append(load_name)

        return modules

    def load(self, service: Service) -> list:
        """ Load and return plugins

        :param Service service: Reference to a service initiated load
        :return list: List of PluginEntry
        """
        global _ready

        if not _ready:
            for load_name in self._get_modules(service):
                try:
                    importlib.import_module(load_name)
                    service.application.registry.log(__name__).debug('Loaded plugins from %s', load_name)
                except Exception as e:
                    service.application.registry.log(__name__).error('Failed to load module %s: %s', load_name, e)

            _ready = True

        return reduce(lambda res, p_type: res + (_entry_points[p_type] if p_type in service.accepts else []),
                      _entry_points, [])

    @classmethod
    def __is_module(cls, path) -> bool:
        """ Check if file is a python module

        :param str path:
        :return bool:
        """
        return os.path.isfile(path) and path.endswith(cls.__MODULE_EXT) \
            and not (os.path.basename(path) == cls.__PKG_INIT)

    @classmethod
    def __is_package(cls, path) -> bool:
        """ Check if dir is a python package

        :param str path:
        :return bool:
        """
        return os.path.isdir(path) and os.path.isfile(os.sep.join([path, cls.__PKG_INIT]))
