# -*- coding: UTF-8

""" Something like "framework" to build all dewyatochka apps on

Classes
=======
    Application     -- Abstract application class
    Registry        -- Registry pattern implementation
    Service         -- Abstract registrable service
    VoidApplication -- Empty application, generally for test purposes
"""

__all__ = ['Application', 'Registry', 'Service', 'VoidApplication']

from abc import ABCMeta, abstractmethod
from threading import Event
from logging import Logger


class Application(metaclass=ABCMeta):
    """ Abstract application class

    Implements methods common for any application
    """

    def __init__(self, registry=None):
        """ Init app

        :param Registry registry: External registry instance or create internal one
        """
        self._registry = registry or Registry()
        self._exit_code = 0
        self._stop_event = Event()

    @property
    def registry(self):
        """ Get registry instance

        :return Registry:
        """
        return self._registry

    def depend(self, dependent_service):
        """ Add a dependent service to a registry

        :param type dependent_service: Subclass of Service
        :return None:
        """
        if isinstance(dependent_service, type):
            dependent_service = dependent_service(self)
        self.registry.add_service(dependent_service)

    @abstractmethod
    def run(self, args: list):  # pragma: no cover
        """ Run application

        :param list args: Console arguments
        :return None:
        """
        pass

    def wait(self):
        """ Sleep until application is stopped

        :return None:
        """
        self._stop_event.wait()

    def sleep(self, time: int):
        """ Sleep `time` sec. or until application is stopped

        :param in time: Seconds to sleep
        :return None:
        """
        self._stop_event.wait(time)

    def stop(self, exit_code=0):
        """ Stop app

        :param int exit_code: Exit code
        :return None:
        """
        self._exit_code = exit_code
        self._stop_event.set()

    def fatal_error(self, module_name: str, exception: Exception):
        """ Handle fatal error

        :param  str module_name: Module where error has occurred
        :param Exception exception: Exception instance
        :return None:
        """
        try:
            self.registry.log.fatal_error(module_name, exception)
        except:
            # Application is shutting down so continue anyway if error logging failed
            pass

        self.stop(1)

    @property
    def running(self) -> bool:
        """ Check if application is not stopped

        :return bool:
        """
        return not self._stop_event.is_set()


class VoidApplication(Application):  # pragma: no cover
    """ Empty application

    Application with empty run() method
    generally for test purposes or as a stub
    """

    def run(self, args: list):
        """ Do nothing

        :param list args: Ignored
        :return None:
        """
        pass


class Service():
    """ Abstract registrable service """

    def __init__(self, application: Application):
        """ Initialize service & attach an application to it

        :param Application application:
        """
        self._application = application

    @property
    def application(self) -> Application:
        """ Return an application instance

        :return Application:
        """
        return self._application

    @property
    def config(self) -> dict:
        """ Get related config section

        :return dict:
        """
        return self.application.registry.config.section(self.name())

    @property
    def log(self) -> Logger:
        """ Get related logger instance

        :return Logger:
        """
        return self.application.registry.log(self.__module__)

    @classmethod
    def name(cls) -> str:
        """ Get service unique name

        :return str:
        """
        return '.'.join((cls.__module__, cls.__name__))


class Registry():
    """ Registry pattern implementation """

    def __init__(self):
        """ Initialize services storage """
        self._services = {}

    def __add_service(self, name: str, service: Service):
        """ Assign a service to name

        :param str name:
        :param Service service:
        :return None:
        """
        if name in self._services.keys():
            raise RuntimeError('Service "%s" is already registered' % name)

        self._services[name] = service

    def add_service(self, service: Service):
        """ Add a service to the registry

        :param Service service: Service instance
        :return None:
        """
        self.__add_service(service.name(), service)

    def add_service_alias(self, original: str, alias: str):
        """ Add an alias to the service

        Service may be accessible by two different attributes after that.

        :param str original: Original name of the registered service
        :param str alias: Alias to be added
        :return None:
        """
        self.__add_service(alias, self.get_service(original))

    def get_service(self, service) -> Service:
        """ Get service by name

        :param service: Service class or name
        :return Service:
        """
        name = service if isinstance(service, str) else service.name()
        try:
            return self._services[name]
        except KeyError:
            raise RuntimeError('Service "%s" is not registered' % name)

    def __getattr__(self, item: str) -> Service:
        """ Get registered service

        :param str item:
        :return Service:
        """
        return self.get_service(item)
