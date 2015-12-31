# -*- coding: UTF-8

""" Happy new year \^-^/ """

from dewyatochka.core import plugin
from dewyatochka.core.plugin import exceptions

__all__ = []


@plugin.schedule('@annually', services=['bot'])
def congratulation(registry):
    """ Congratulate a chat

    :param Registry registry:
    :return None:
    """
    congratulation_text = registry.config.get('message')
    if not congratulation_text:
        raise exceptions.PluginError('No congratulation message configured')

    for conference in registry.bot.alive_chats:
        registry.log.info('Congratulating chat %s', conference)
        registry.bot.send(congratulation_text, conference)
