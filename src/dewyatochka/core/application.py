
# -*- coding: UTF-8

"""
Application common module
"""

__all__ = ['Application', 'Service']

from abc import ABCMeta, abstractmethod
import logging
import threading


class Application(metaclass=ABCMeta):
    """
    Dewyatochka application instance
    """

    # Registered services
    _services = {}

    # Stop event instance
    _stop_event = None

    # Code to exit with
    _exit_code = 0

    def __init__(self):
        """
        Init app
        """
        self._stop_event = threading.Event()

    def _add_service(self, name, service):
        """
        Add a service to the registry
        :param service: Service instance
        :param name: Service name
        :return: void
        """
        self._services[name] = service

    def _get_service(self, name):
        """
        Get service by name
        :param name:
        :return: service instance
        """
        try:
            return self._services[name]
        except KeyError:
            raise RuntimeError('Service "%s" is not registered' % name)

    def set_config(self, config):
        """
        Set config service
        :param config:
        :return: void
        """
        self._add_service('config', config)

    def set_conferences_config(self, config):
        """
        Set config service
        :param config:
        :return: void
        """
        self._add_service('conferences_config', config)

    def set_conference_manager(self, manager):
        """
        Get conferences manager
        :param manager:
        :return: config
        """
        return self._add_service('conference_manager', manager)

    def set_helper_manager(self, manager):
        """
        Get helpers manager
        :param manager:
        :return: config
        """
        return self._add_service('helper_manager', manager)

    def set_log_handler(self, log_handler):
        """
        Set logger
        :param log_handler:
        :return: void
        """
        logger = logging.getLogger()
        logger.setLevel(self.config.global_section.get('log_level', logging.INFO))

        logger.handlers = []
        logger.addHandler(log_handler)

    @property
    def config(self):
        """
        Get config instance
        :return: config
        """
        return self._get_service('config')

    @staticmethod
    def log(module):
        """
        Get loger for module
        :param module: str
        :return: config
        """
        return logging.getLogger(module)

    @property
    def conferences_config(self):
        """
        Get config instance
        :return: config
        """
        return self._get_service('conferences_config')

    @property
    def conference_manager(self):
        """
        Get conferences manager
        :return: config
        """
        return self._get_service('conference_manager')

    @property
    def helper_manager(self):
        """
        Get helpers manager
        :return: config
        """
        return self._get_service('helper_manager')

    @abstractmethod
    def run(self, args: list):
        """
        Run application
        :param args: list Console arguments
        :return:
        """
        pass

    def stop(self, exit_code=0):
        """
        Stop app
        :param exit_code: int
        :return: void
        """
        self._exit_code = exit_code
        self._stop_event.set()

    def error(self, module_name, exception):
        """
        Handle fatal error
        :param module_name: str
        :param exception: Exception
        :return: void
        """
        message = '%s failed: %s'
        if logging.getLogger().level < logging.INFO:
            self.log(module_name).exception(message, module_name, exception)
        else:
            self.log(module_name).error(message, module_name, exception)

        self.stop(1)

    @property
    def running(self):
        """
        Check if application is not stopped
        :return: bool
        """
        return not self._stop_event.is_set()


class Service():
    """
    Abstract service class
    """

    # Application instance
    _application = None

    def __init__(self, application: Application):
        """
        Initialize service & attach an application to it
        :param application: Application
        :return:
        """
        self._application = application

    @property
    def application(self):
        """
        Return application instance
        :return: Application
        """
        return self._application
