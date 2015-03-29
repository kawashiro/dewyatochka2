# -*- coding: UTF-8

""" Provides cool stories for your chat

Packages
========
    parser -- External stories sources parsers

Modules
=======
    db_storage  -- Local SQLite storage
    maintenance -- Functions for dewyatochkactl
    chat        -- Chat functions
"""

__all__ = ['db_storage', 'maintenance', 'parser', 'chat']

from dewyatochka.core import plugin


@plugin.chat_command('coolstory')
def cool_story_command_handler(**kwargs):
    """ Say a cool story

    :param dict kwargs: Plugin args
    :return None:
    """
    from . import chat
    chat.cool_story_command_handler(**kwargs)


@plugin.ctl('recreate', 'Create a new empty cool stories db')
def recreate(**kwargs):
    """ Create a new empty cool stories db

    :param dict kwargs: Plugin args
    :return None:
    """
    from . import maintenance
    maintenance.recreate(**kwargs)


@plugin.ctl('reindex', 'Populate stories table from scratch')
def reindex(**kwargs):
    """ Populate stories table from scratch

    :param dict kwargs: Plugin args
    :return None:
    """
    from . import maintenance
    maintenance.recreate(**kwargs)
    maintenance.reindex(**kwargs)
