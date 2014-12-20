# -*- coding: UTF-8

"""
Common API for external plugins
"""

__all__ = ['chat_entry', 'get_helpers', 'get_message_handlers', 'helper', 'MessageHandler']

import os
from types import FunctionType
from abc import abstractmethod, ABCMeta
import importlib
import logging

# Registered message handlers list
_message_handlers = []


# Registered helpers to run in background
_helpers = []


class MessageHandler(metaclass=ABCMeta):
    """
    Abstract message handler
    """
    @abstractmethod
    def handle(self, message: dict, **kwargs) -> str:
        """
        Get XMPP message and return test response to be sent
        :param message: dict XMPP message structure
        :param kwargs: {conference: Conference where message came from, application: Current app environment}
        :return:
        """
        pass


class FunctionWrapper(MessageHandler):
    """
    Wraps simple function provided as a message handler
    """

    # Associated function to call
    _function = None

    def __init__(self, callback):
        """
        Wrap callable object
        :param callback:
        :return:
        """
        self._function = callback

    def handle(self, message: dict, **kwargs) -> str:
        """
        Get XMPP message and return test response to be sent
        :param message: dict XMPP message structure
        :param kwargs: {conference: Conference where message came from, application: Current app environment}
        :return:
        """
        return self._function(message, **kwargs)

    @property
    def __name__(self):
        """
        Function name emulation
        :return: string
        """
        return '%s[%s.%s]' % (__name__, self._function.__module__, self._function.__name__)


class PluginError(Exception):
    """
    Common exception related to plugins
    """
    pass


class PluginRegistrationError(PluginError):
    """
    Error on plugin loading
    """
    pass


def chat_entry(handler):
    """
    Decorator to mark function as message handler entry point
    :param handler: Function to register
    :return: Function
    """
    if isinstance(handler, FunctionType):
        _message_handlers.append(FunctionWrapper(handler))

    elif issubclass(handler, MessageHandler):
        _message_handlers.append(handler())

    else:
        raise PluginRegistrationError('Handler %s is not callable nor instance of MessageHandler' % repr(handler))

    return handler


def helper(fn):
    """
    Register this function as a background helper
    :param fn: Function to register
    :return: Function
    """
    _helpers.append(fn)
    return fn


def get_message_handlers():
    """
    Get message processing plugins list copy
    :return: list
    """
    return _message_handlers[:]


def get_helpers():
    """
    Get message processing helpers list copy
    :return: list
    """
    return _helpers[:]


def load_plugins():
    """
    Dynamically load message processing plugins
    :return: void
    """
    importlib.import_module('dewyatochka.plugins')

    dewyatochka_plugins_home = os.sep.join(__file__.split(os.sep)[:-2] + ['plugins'])
    for file in os.listdir(dewyatochka_plugins_home):
        file_path = dewyatochka_plugins_home + os.sep + file
        if os.path.isfile(file_path) and file != '__init__.py' and file.endswith('.py'):
            module_name = 'dewyatochka.plugins.' + file[:-3]
            importlib.import_module(module_name)
            logging.getLogger(__name__).info('Loaded plugin: %s', module_name)
