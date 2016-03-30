# -*- coding: UTF-8

""" Something like "framework" to build all dewyatochka apps on

Classes
=======
    Application           -- Abstract application class
    Registry              -- Registry pattern implementation
    Service               -- Abstract registrable service
    StandaloneService     -- Service which can be launched in separate thread
    VoidApplication       -- Empty application, generally for test purposes
    UndefinedServiceError -- Error on unknown service

Attributes
==========
    EXIT_CODE_OK    -- Normal exit
    EXIT_CODE_ERROR -- Exit on error
    EXIT_CODE_TERM  -- Exit on user terminate
"""

import sys
import threading
from abc import ABCMeta, abstractmethod
from threading import Event
from logging import Logger

from dewyatochka import __name__ as app_name

__all__ = ['Application', 'Registry', 'Service', 'StandaloneService', 'VoidApplication', 'UndefinedServiceError',
           'EXIT_CODE_OK', 'EXIT_CODE_ERROR', 'EXIT_CODE_TERM']


# App exit codes
EXIT_CODE_OK = 0
EXIT_CODE_ERROR = 1
EXIT_CODE_TERM = 2


class UndefinedServiceError(RuntimeError):
    """ Error on unknown service """
    pass


class Application(metaclass=ABCMeta):
    """ Abstract application class

    Implements methods common for any application
    """

    def __init__(self, registry=None):
        """ Init app

        :param Registry registry: External registry instance or create internal one
        """
        self._registry = registry or Registry()
        self._exit_code = EXIT_CODE_OK
        self._stop_event = Event()

    @property
    def registry(self):
        """ Get registry instance

        :return Registry:
        """
        return self._registry

    def depend(self, dependent_service, *aliases):
        """ Add a dependent service to a registry

        :param dependent_service: Subclass of Service
        :param tuple aliases: Alternative service names
        :return None:
        """
        if isinstance(dependent_service, type):
            dependent_service = dependent_service(self)

        self.registry.add_service(dependent_service)

        for alias in aliases:
            self.registry.add_service_alias(dependent_service, alias)

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

    def stop(self, exit_code=EXIT_CODE_OK):
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
            # and try at least to echo what really happened
            print('Error at %s: %s' % (module_name, exception), file=sys.stderr)

        self.stop(EXIT_CODE_ERROR)

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


class Service:
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

    @classmethod
    def _log_name(cls):
        """ Format name to be displayed in log messages

        :return str:
        """
        svc_name = cls.name()
        return svc_name if svc_name.startswith(app_name) else 'dewyatochka.%s' % svc_name

    @property
    def log(self) -> Logger:
        """ Get related logger instance

        :return Logger:
        """
        return self.application.registry.log(self._log_name())

    @classmethod
    def name(cls) -> str:
        """ Get service unique name

        :return str:
        """
        return '.'.join((cls.__module__, cls.__name__))


class StandaloneService(Service, metaclass=ABCMeta):
    """ Service which can be launched in separate thread """

    def __init__(self, application: Application):
        """ Initialize service & attach an application to it

        :param Application application:
        """
        super().__init__(application)

        self._thread = threading.Thread(name=self.name() + '[Main]', target=self.run)

    def start(self):
        """ Start service

        :return None:
        """
        self._thread.start()

    @abstractmethod
    def run(self):  # pragma: no cover
        """ Do job

        :return None:
        """
        pass

    # noinspection PyMethodMayBeStatic
    def stop(self):  # pragma: no cover
        """ Stop simultaneously

        Normally service should monitor Application.running event
        but sometimes it's impossible due to 3rd-party libs usage,
        service hang up or other issues

        :return None:
        """
        pass

    def wait(self):
        """ Wait until stopped

        :return None:
        """
        self._thread_wait(self._thread)

    def _thread_wait(self, thread: threading.Thread):
        """ Waiting for thread to complete

        :param threading.Thread thread: Running thread instance
        :return None:
        """
        if thread.is_alive():
            self.log.debug('Waiting for thread "%s"', thread.name)
            thread.join()


class Registry:
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

    def add_service_alias(self, original, alias: str):
        """ Add an alias to the service

        Service may be accessible by two different attributes after that.

        :param original: Original registered service name or class
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
            raise UndefinedServiceError('Service "%s" is not registered' % name)

    @property
    def all(self) -> list:
        """ Get all unique services

        :return list:
        """
        res = []
        for service in self._services.values():
            if service not in res:
                res.append(service)
        return res

    def __getattr__(self, item: str) -> Service:
        """ Get registered service

        :param str item:
        :return Service:
        """
        # noinspection PyTypeChecker
        return self.get_service(item)
