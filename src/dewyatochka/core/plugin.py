# -*- coding: UTF-8

"""
Common API for external plugins
"""

__all__ = ['chat_entry', 'get_helpers', 'get_message_handlers', 'helper', 'MessageHandler', 'load_plugins',
           'chat_command', 'get_command_handler']

import os
from types import FunctionType
from abc import abstractmethod, ABCMeta
import importlib
import logging
import traceback

# Registered message handlers list for regular messages
_regular_message_handlers = []

# Handlers for system message (e.g. topic, presence, etc)
_system_message_handlers = []

# Handlers for own messages
_own_message_handlers = []

# Handlers for chat commands
_command_handlers = {}


# Registered helpers to run in background
_helpers = []


class MessageHandler(metaclass=ABCMeta):
    """
    Abstract message handler
    """
    @abstractmethod
    def handle(self, **kwargs) -> str:
        """
        Get XMPP message and return test response to be sent
        :param kwargs: {message, conference, application, command, command_args}
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

    def handle(self, **kwargs) -> str:
        """
        Get XMPP message and return test response to be sent
        :param kwargs: {message, conference, application, command, command_args}
        :return:
        """
        return self._function(**kwargs)

    @property
    def __name__(self):
        """
        Function name emulation
        :return: string
        """
        return 'FunctionWrapper[%s.%s]' % (self._function.__module__, self._function.__name__)


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


def _create_handler(fn):
    """
    Create handler instance
    :param fn: callable
    :return: MessageHandler
    """
    if isinstance(fn, FunctionType):
        handler_instance = FunctionWrapper(fn)
    elif issubclass(fn, MessageHandler):
        handler_instance = fn()
    else:
        raise PluginRegistrationError('Handler %s is not callable nor instance of MessageHandler' % repr(fn))

    return handler_instance


def chat_message(*, regular=True, system=False, own=False):
    """
    Decorator to mark function as message handler entry point
    :param regular: Register this handler for regular messages
    :param system: Register this handler for system messages
    :param own: Register this handler for own messages
    :return: Function
    """
    def _register(handler):
        """
        Actually register handler
        :param handler: Function to register
        :return: callable
        """
        handler_instance = _create_handler(handler)

        if regular:
            _regular_message_handlers.append(handler_instance)
        if system:
            _system_message_handlers.append(handler_instance)
        if own:
            _own_message_handlers.append(handler_instance)

        return handler

    return _register


def chat_command(command):
    """
    Register handler for chat command
    :param command: str
    :return:
    """
    def _register(handler):
        """
        Actually register handler
        :param handler: Function to register
        :return: callable
        """
        if _command_handlers.get(command):
            raise PluginRegistrationError('Command %s is already defined' % command)

        _command_handlers[command] = _create_handler(handler)
        return handler

    return _register


def helper(fn):
    """
    Register this function as a background helper
    :param fn: Function to register
    :return: Function
    """
    _helpers.append(fn)
    return fn


def get_message_handlers(regular, system, own):
    """
    Get message processing plugins list
    :param regular: Get handlers for regular messages
    :param system: Get handlers for system messages
    :param own: Get handlers for own messages
    :return: list
    """
    result = []

    if regular:
        result += _regular_message_handlers
    if system:
        result += _system_message_handlers
    if own:
        result += _own_message_handlers

    return result


def get_command_handler(command):
    """
    Get handler for command
    :param command: str
    :return: callable|None
    """
    return _command_handlers.get(command)


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
            try:
                importlib.import_module(module_name)
                logging.getLogger(__name__).info('Loaded plugin: %s', module_name)
            except Exception as e:
                logging.getLogger(__name__).error(
                    'Failed to load module %s: %s\n%s',
                    module_name,
                    e,
                    ''.join(traceback.format_tb(e.__traceback__)).strip()
                )
