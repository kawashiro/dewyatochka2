# -*- coding: UTF-8

""" Provides some utils for ctl utility

Classes
=======
    ActivityInfo -- Conference activity info structure

Functions
=========
    get_activity_info -- Get conference activity info by JID
"""

__all__ = ['ActivityInfo', 'get_activity_info']

from dewyatochka.core.application import Registry
from dewyatochka.core.plugin import ctl
from dewyatochka.core.plugin.loader import LoaderService
from dewyatochka.core.plugin.ctl_sys.service import Service as CtlService


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

        print('Accessible commands:')
        print('====================')
        for command in commands:
            print('%s: %s' % (command.ljust(cmd_len), commands[command]))
