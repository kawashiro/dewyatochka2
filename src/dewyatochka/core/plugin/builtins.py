# -*- coding: UTF-8

""" Some chat / ctl commands accessible by default

Classes
=======
    ActivityInfo -- Conference activity info structure

Functions
=========
    get_activity_info     -- Get conference activity info
    register_entry_points -- Register plugins entry points
"""

import time

from dewyatochka import __version__
from dewyatochka.core.application import Registry
from dewyatochka.core.plugin import chat_message, chat_command, control
from dewyatochka.core.plugin.loader import LoaderService
from dewyatochka.core.plugin.subsystem.control.service import Service as CtlService
from dewyatochka.core.plugin.subsystem.message.service import Service as MSysService
from dewyatochka.core.network.entity import GroupChat

__all__ = ['ActivityInfo', 'get_activity_info', 'register_entry_points']


class ActivityInfo(object):
    """ Conference activity info structure """

    def __init__(self, conference):
        """ Create new activity info object with default values

        :param GroupChat conference:
        """
        self._conference = conference
        self.last_message = 0
        self.last_activity = 0

    @property
    def conference(self) -> GroupChat:
        """ Conference getter

        :return JID:
        """
        return self._conference


# Conference jid -> last activity
_conference_last_activity = {}


def get_activity_info(conference: GroupChat) -> ActivityInfo:
    """ Get conference activity info

    :param GroupChat conference: Conference identity
    :return ActivityInfo:
    """
    if conference.self not in _conference_last_activity:
        _conference_last_activity[conference.self] = ActivityInfo(conference.self)

    return _conference_last_activity[conference.self]


def register_entry_points():
    """ Register plugins entry points

    :return None:
    """
    chat_message(regular=True, own=True)(_chat_on_message_input)
    chat_message(system=True)(_chat_on_activity_input)

    chat_command('version')(_version_info)
    chat_command('help', services=[LoaderService, MSysService])(_ChatHelpMessage)
    chat_command('info', services=[LoaderService, MSysService])(_ChatHelpMessage)

    control('list', _CtlCommandsList.DESCRIPTION, services=[LoaderService, CtlService])(_CtlCommandsList)
    control('version', _version_info.DESCRIPTION)(_version_info)


def _chat_on_message_input(inp, **_):
    """ Collect messages stat

    :param inp:
    :param _:
    :return None:
    """
    activity = get_activity_info(inp.sender.bare)
    activity.last_message = time.time()
    activity.last_activity = time.time()


def _chat_on_activity_input(inp, **_):
    """ Collect activity stat

    :param inp:
    :param _:
    :return None:
    """
    get_activity_info(inp.sender.bare).last_activity = time.time()


def _version_info(outp, **_):
    """ Show version

    :param outp:
    :param _:
    :return None:
    """
    outp.say('dewyatochkad v.%s', __version__)

_version_info.DESCRIPTION = 'Show version'


class _ChatHelpMessage:
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
            prefix = registry.message_plugin_provider.config['command_prefix']
            for loader in registry.plugins_loader.loaders:
                commands += [prefix + entry.params['command']
                             for entry in loader.load(registry.message_plugin_provider)
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
        msg_format = registry.message_plugin_provider.config.get('help_message')
        if msg_format:
            message = msg_format.format(user=inp.sender.public_name,
                                        version=__version__,
                                        commands=', '.join(self._get_commands(registry)))
            outp.say(message)
        else:
            registry.log.warning('Help message is not configured, command ignored')


class _CtlCommandsList:
    """ Show help message """

    # Command description
    DESCRIPTION = 'List all the commands available'

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
            for loader in registry.plugins_loader.loaders:
                self.__commands.update({entry.params['name']: entry.params['description']
                                        for entry in loader.load(registry.control_plugin_provider)})
        return self.__commands

    def __call__(self, outp, registry, **_):
        """ Invoke command

        :param outp:
        :param registry:
        :return None:
        """
        commands = self._get_commands(registry)
        cmd_len = max(map(len, commands.keys())) + 1

        outp.log('Accessible commands:')
        for command in sorted(commands.keys()):
            outp.log('    %s: %s' % (command.ljust(cmd_len), commands[command]))
