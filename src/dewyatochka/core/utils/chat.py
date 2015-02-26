# -*- coding: UTF-8

""" Provides some utils for conferences

Classes
=======
    ActivityInfo -- Conference activity info structure

Functions
=========
    get_activity_info -- Get conference activity info by JID
"""

__all__ = ['ActivityInfo', 'get_activity_info']

import time
from collections import defaultdict

from dewyatochka import __version__
from dewyatochka.core.application import Registry
from dewyatochka.core.plugin import chat_message, chat_command
from dewyatochka.core.network.xmpp.entity import JID
from dewyatochka.core.plugin.loader import LoaderService
from dewyatochka.core.plugin.message_sys.service import Service as MSysService


# Conference jid -> last activity
_conference_last_activity = defaultdict(lambda key: ActivityInfo(key))


class ActivityInfo(object):
    """ Conference activity info structure """

    def __init__(self, conference: JID):
        """ Create new activity info object with default values

        :param JID conference:
        """
        self._conference = conference
        self.last_message = 0
        self.last_activity = 0

    @property
    def conference(self) -> JID:
        """ Conference getter

        :return JID:
        """
        return self._conference


def get_activity_info(conference: JID) -> ActivityInfo:
    """ Get conference activity info

    :param JID conference: Conference JID
    :return ActivityInfo:
    """
    bare = str(conference.bare)
    if bare not in _conference_last_activity:
        _conference_last_activity[bare] = ActivityInfo(conference.bare)

    return _conference_last_activity[bare]


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
