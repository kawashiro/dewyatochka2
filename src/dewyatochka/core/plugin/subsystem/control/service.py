# -*- coding: UTF-8

""" Helper plugins container service implementation

Classes
=======
    Service       -- Ctl plugins container service
    ClientService -- Control client service impl
    Output        -- Output wrapper
    Wrapper       -- Wraps a plugin into environment
    Environment   -- Environment for a ctl plugin

Attributes
==========
    PLUGIN_TYPE_CTL  -- Ctl plugin type
    PLUGIN_TYPES     -- All plugin types list
"""

from dewyatochka.core.application import Application
from dewyatochka.core.application import Service as BaseService
from dewyatochka.core.plugin.base import Service as BasePluginService
from dewyatochka.core.plugin.base import Wrapper as BaseWrapper
from dewyatochka.core.plugin.base import Environment as BaseEnvironment
from dewyatochka.core.plugin.base import PluginEntry
from dewyatochka.core.plugin.exceptions import PluginRegistrationError

from .network import Message, Client

__all__ = ['Service', 'Output', 'Wrapper', 'Environment', 'PLUGIN_TYPE_CTL', 'PLUGIN_TYPES', 'Cli']


# Plugin types provided
PLUGIN_TYPE_CTL = 'ctl'
PLUGIN_TYPES = [PLUGIN_TYPE_CTL]


class Output:
    """ Output wrapper

    Passed to each plugin to allow communication to client
    """

    def __init__(self, connection, logger):
        """ Bind output wrapper to xmpp-client and a conference

        :param socket connection:
        :param logger:
        """
        self._connection = connection
        self._log = logger

    def __send(self, message: Message):
        """ Send a message

        :param Message message:
        :return None:
        """
        try:
            self._connection.send(message.encode())
        except BrokenPipeError:
            raise RuntimeError('Control client disconnected before operation has completed')

    def info(self, text: str, *args):
        """ Send something

        :param str text: Message content
        :param tuple args: Args for message format
        :return None:
        """
        self.__send(Message(self._connection, text=(text % args)))
        self._log.info(text, *args)

    def error(self, text: str, *args):
        """ Send error message

        :param str text: Message content
        :param tuple args: Args for message format
        :return None:
        """
        self.__send(Message(error=(text % args)))

    def debug(self, text: str, *args):
        """ Debug message

        :param str text: Message content
        :param tuple args: Args for message format
        :return None:
        """
        self._log.debug(text, *args)

    # Some useful aliases
    log = say = info


class Wrapper(BaseWrapper):
    """ Wraps a plugin into environment """

    def wrap(self, entry: PluginEntry):
        """ Wrap plugin into it's environment

        :param PluginEntry entry: Raw plugin entry
        :return Environment:
        """
        return Environment(entry.plugin, self._get_registry(entry))


class Environment(BaseEnvironment):
    """ Environment for a ctl plugin """

    def invoke(self, *, command=None, source=None, **kwargs):
        """ Invoke plugin in environment registered

        :param .network.Message command: Message to process
        :param socket.socket source: Message source
        :param dict kwargs: Params to path to a plugin
        :return None:
        """
        if command is None:
            raise TypeError('`command` keyword argument is required')
        if source is None:
            raise TypeError('`source` keyword argument is required')

        output = Output(source, self._registry.log)

        try:
            super().invoke(inp=command, outp=output, **kwargs)
        except Exception as e:
            output.error('%s', e)
            raise


class Service(BasePluginService):
    """ Ctl plugins container service """

    # Plugin wrapper class
    _wrapper_class = Wrapper

    def __init__(self, application: Application):
        """ Create plugin container service

        :param Application application:
        """
        super().__init__(application)

        self._commands = {}

    @property
    def accepts(self) -> list:
        """ Get list of acceptable plugin types

        :return list:
        """
        return PLUGIN_TYPES

    def _register_plugin(self, entry: PluginEntry):
        """ Register a single plugin

        :param PluginEntry entry:
        :return None:
        """
        wrapped = self._wrapper.wrap(entry)

        if entry.params['name'] in self._commands:
            raise PluginRegistrationError('ctl command "%s" is already in use' % entry.params['name'])

        self._commands[entry.params['name']] = wrapped
        self._plugins.append(wrapped)

    def get_command(self, name: str):
        """ Get command to use

        :param str name: Registered command name
        :return Environment:
        """
        if self._plugins is None:
            raise RuntimeError('Plugins are not loaded')

        if name not in self._commands:
            raise RuntimeError('Command %s is not registered' % name)

        return self._commands[name]

    @classmethod
    def name(cls) -> str:
        """ Get service unique name

        :return str:
        """
        return 'control_plugin_provider'


class ClientService(BaseService):
    """ Control client service impl """

    def __init__(self, application: Application):
        """ Initialize service & attach an application to it

        :param Application application:
        """
        super().__init__(application)

        self.socket = None

    def communicate(self, command: str, optional: dict):
        """ Communicate with daemon

        :param str command: Command name
        :param dict optional: Optional command args
        :return None:
        """
        with Client(self.socket) as ctl_client:
            ctl_client.send(Message(name=command, args=optional or {}))
            for msg in ctl_client.input:
                if msg.error:
                    self.log.error('Server error: %s', msg.error)

                elif msg.text:
                    self.log.info(msg.text)

                else:
                    self.log.error('Unhandled message: %s', str(msg.data))

    @classmethod
    def name(cls) -> str:
        """ Get service unique name

        :return str:
        """
        return 'control_client'
