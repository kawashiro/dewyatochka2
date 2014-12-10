
# -*- coding: UTF-8

"""
Application common module
"""

__all__ = ['Application', 'Service']

from abc import ABCMeta, abstractmethod


class Application(metaclass=ABCMeta):
    """
    Dewyatochka application instance
    """

    # Registered services
    _services = {}

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

    def set_xmpp_worker(self, xmpp_worker):
        """
        Set XMPP-connection worker instance
        :param xmpp_worker:
        :return: void
        """
        self._add_service('xmpp', xmpp_worker)

    def set_logger(self, logger):
        """
        Set logger
        :param logger:
        :return: void
        """
        self._add_service('logger', logger)

    @property
    def config(self):
        """
        Get config instance
        :return: config
        """
        return self._get_service('config')

    @property
    def log(self):
        """
        Get logger
        :return: config
        """
        return self._get_service('logger')

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
    def xmpp_worker(self):
        """
        Get xmpp-worker
        :return: config
        """
        return self._get_service('xmpp')

    @abstractmethod
    def run(self, args: list):
        """
        Run application
        :param args: list Console arguments
        :return:
        """
        pass


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
