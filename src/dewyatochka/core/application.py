
# -*- coding: UTF-8

"""
Application common module
"""

__all__ = ['Application', 'Registry', 'Service']

from abc import ABCMeta, abstractmethod
from threading import Event


class Application(metaclass=ABCMeta):
    """
    Dewyatochka application instance
    """

    def __init__(self, registry=None):
        """
        Init app
        """
        self._registry = registry or Registry()
        self._exit_code = 0
        self._stop_event = Event()

    @property
    def registry(self):
        """
        Get registry instance
        :return: Registry
        """
        return self._registry

    @abstractmethod
    def run(self, args: list):
        """
        Run application
        :param args: list Console arguments
        :return: void
        """
        pass

    def wait(self):
        """
        Sleep until application is stopped
        :return: void
        """
        self._stop_event.wait()

    def stop(self, exit_code=0):
        """
        Stop app
        :param exit_code: int
        :return: void
        """
        self._exit_code = exit_code
        self._stop_event.set()

    def fatal_error(self, module_name: str, exception: Exception):
        """
        Handle fatal error
        :param module_name: str
        :param exception: Exception
        :return: void
        """
        try:
            self.registry.log.fatal_error(module_name, exception)
        except:
            # Application is shutting down so continue anyway if error logging failed
            pass

        self.stop(1)

    @property
    def running(self) -> bool:
        """
        Check if application is not stopped
        :return: bool
        """
        return not self._stop_event.is_set()


class Service(metaclass=ABCMeta):
    """
    Abstract service class
    """

    def __init__(self, application: Application):
        """
        Initialize service & attach an application to it
        :param application: Application
        """
        self._application = application

    @property
    def application(self) -> Application:
        """
        Return application instance
        :return: Application
        """
        return self._application

    @property
    def config(self) -> dict:
        """
        Get related config section
        :return: dict
        """
        return self.application.registry.config.section(self.name())

    @classmethod
    def name(cls) -> str:
        """
        Get service unique name
        :return: str
        """
        return '.'.join((cls.__module__, cls.__name__))


class Registry():
    """
    Registry implementation
    """

    def __init__(self):
        """
        Initialize services storage
        """
        self._services = {}

    def add_service(self, service: Service):
        """
        Add a service to the registry
        :param service: Service instance
        :return: void
        """
        self._services[service.name()] = service

    def get_service(self, service) -> Service:
        """
        Get service by name
        :param service: Service class or name
        :return: Service
        """
        name = service if isinstance(service, str) else service.name()
        try:
            return self._services[name]
        except KeyError:
            raise RuntimeError('Service "%s" is not registered' % name)

    def __getattr__(self, item: str) -> Service:
        """
        Get registered service
        :param item: str
        :return: Service
        """
        return self.get_service(item)
