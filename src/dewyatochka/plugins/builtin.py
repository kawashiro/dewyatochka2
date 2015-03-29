# -*- coding: UTF-8

""" Some chat / ctl commands accessible by default """

__all__ = []

import time

from dewyatochka import __version__
from dewyatochka.core.application import Registry
from dewyatochka.core.plugin import chat_message, chat_command, ctl
from dewyatochka.core.plugin.loader import LoaderService
from dewyatochka.core.plugin.ctl_sys.service import Service as CtlService
from dewyatochka.core.plugin.message_sys.service import Service as MSysService
from dewyatochka.core.utils.chat import get_activity_info


@chat_message(regular=True, own=True)
def message_input(inp, **_):
    """ Collect messages stat

    :param inp:
    :param _:
    :return None:
    """
    activity = get_activity_info(inp.sender.bare)
    activity.last_message = time.time()
    activity.last_activity = time.time()


@chat_message(system=True)
def activity_input(inp, **_):
    """ Collect activity stat

    :param inp:
    :param _:
    :return None:
    """
    get_activity_info(inp.sender.bare).last_activity = time.time()


@chat_command('help', services=(LoaderService, MSysService))
@chat_command('info', services=(LoaderService, MSysService))
class HelpMessage():
    """ Show help message """

    def __init__(self):
        """ Init object """
        self.__commands = None

    def _get_commands(self, registry: Registry) -> frozenset:
        """ Get available commands

        :param Registry registry:
        :return frozenset:
        """
        if self.__commands is None:
            commands = []
            prefix = registry.chat.config['command_prefix']
            for loader in registry.plugins.loaders:
                commands += [prefix + entry.params['command']
                             for entry in loader.load(registry.chat)
                             if 'command' in entry.params]
            self.__commands = frozenset(commands)

        return self.__commands

    def __call__(self, inp, outp, registry, **_):
        """ Invoke command

        :param inp:
        :param outp:
        :param _:
        :return None:
        """
        msg_format = registry.chat.config.get('help_message')
        if msg_format:
            message = msg_format.format(user=inp.sender.resource,
                                        version=__version__,
                                        commands=', '.join(self._get_commands(registry)))
            outp.say(message)
        else:
            registry.log.warning('Help message is not configured, command ignored')


@chat_command('version')
def version(outp, **_):
    """ Show version

    :param outp:
    :param _:
    :return None:
    """
    outp.say('dewyatochkad v.%s', __version__)


@ctl('list', 'List all the commands available', services=(LoaderService, CtlService))
class CommandsList():
    """ Show help message """

    def __init__(self):
        """ Init object """
        self.__commands = None

    def _get_commands(self, registry: Registry) -> dict:
        """ Get available commands

        :param Registry registry:
        :return dict:
        """
        if self.__commands is None:
            self.__commands = {}
            for loader in registry.plugins.loaders:
                self.__commands.update({entry.params['name']: entry.params['description']
                                        for entry in loader.load(registry.ctl)})
        return self.__commands

    def __call__(self, registry, **_):
        """ Invoke command

        :param registry:
        :param _:
        :return None:
        """
        commands = self._get_commands(registry)
        cmd_len = max(map(lambda s: len(s), commands.keys())) + 1

        registry.log.info('Accessible commands:')
        for command in sorted(commands.keys()):
            registry.log.info('    %s: %s' % (command.ljust(cmd_len), commands[command]))
