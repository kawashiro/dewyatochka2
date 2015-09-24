# -*- coding: UTF-8

""" Logging app service implementation

Classes
=======
    LoggingService -- Logging app service
    LoggerWrapper  -- Extended logging.Logger

Attributes
==========
    LEVEL_PROGRESS      -- Special level no for progress messages
    LEVEL_NAME_PROGRESS -- Special level no for progress messages (text repr.)
"""

__all__ = ['LoggingService', 'LoggerWrapper', 'LEVEL_PROGRESS', 'LEVEL_NAME_PROGRESS']

import logging

from dewyatochka.core.application import Application, Service


# Special level no for progress messages
LEVEL_PROGRESS = 25
LEVEL_NAME_PROGRESS = 'PROGRESS'


class LoggerWrapper():
    """ Extended logging.Logger """

    # Already instantiated loggers by name
    __instances = {}

    def __init__(self, inner_logger: logging.Logger):
        """ Specify inner logger instance

        :param logging.Logger inner_logger:
        """
        self._logger = inner_logger

    def __getattr__(self, item: str):
        """ Get not overloaded attribute

        :param str item:
        :returns:
        """
        return getattr(self._logger, item)

    def error(self, msg, *args, **kwargs):
        """ Log 'msg % args' with severity 'ERROR'

        :param str msg: Message template
        :param tuple args: args
        :param dict kwargs: kwargs
        :return None:
        """
        if self._logger.isEnabledFor(logging.DEBUG):
            self._logger.exception(msg, *args, **kwargs)
        else:
            self._logger.error(msg, *args, **kwargs)

    def progress(self, template, *args, **kwargs):
        """ Echo some process progress info

        :param str template: Message format
        :param tuple args: Message args
        :param dict kwargs: Message kw args
        :return None:
        """
        self._logger.log(LEVEL_PROGRESS, template, *args, **kwargs)

    def __new__(cls, inner_logger: logging.Logger):
        """ Get new instance

        :param type cls:
        :param logging.Logger inner_logger:
        :return LoggerWrapper:
        """
        if inner_logger.name not in cls.__instances:
            cls.__instances[inner_logger.name] = super().__new__(cls)

        return cls.__instances[inner_logger.name]


class LoggingService(Service):
    """ Logging app service """

    def __init__(self, application: Application):
        """ Initialize service & attach an application to it

        :param Application application:
        """
        super().__init__(application)
        self._global_level = logging.NOTSET

    def register_handler(self, handler):
        """ Register global handler for compatibility with third-party libs

        :param handler: Instance of dewyatochka.core.log.output.Handler
        :return None:
        """
        logger = logging.getLogger()
        logger.setLevel(self.logging_level)
        self._global_level = logger.level

        logger.handlers = []
        logger.addHandler(handler)

    def fatal_error(self, module_name: str, exception: Exception):
        """ Log fatal error message

        :param str module_name: Module name to display in log
        :param Exception exception: Exception instance
        :return None:
        """
        logger = self(module_name)

        if self._global_level == logging.DEBUG:
            logger.exception(str(exception))
        else:
            logger.critical(str(exception))

    @property
    def logging_level(self) -> str:
        """ Get logging level

        :return str:
        """
        try:
            return self.config['level']
        except:
            pass
        return 'INFO'

    @classmethod
    def name(cls) -> str:
        """ Get service unique name

        :return str:
        """
        return 'log'

    def __call__(self, name=None) -> LoggerWrapper:
        """ Get global logger instance by name

        :param str name: Module name to display in log
        :return LoggerWrapper:
        """
        return LoggerWrapper(logging.getLogger(name))
