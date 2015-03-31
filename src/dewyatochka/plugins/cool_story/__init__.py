# -*- coding: UTF-8

""" Provides cool stories for your chat

Packages
========
    parser -- External stories sources parsers

Modules
=======
    model       -- Plugin logic impl
    maintenance -- Functions for dewyatochkactl
    chat        -- Chat functions
    helper      -- Chat helpers
"""

__all__ = ['model', 'maintenance', 'parser', 'chat', 'helper']

from dewyatochka.core import plugin


@plugin.chat_command('coolstory')
def cool_story_command_handler(**kwargs):
    """ Say a cool story

    :param dict kwargs: Plugin args
    :return None:
    """
    from . import chat
    chat.cool_story_command_handler(**kwargs)


@plugin.chat_command('azaza')
def cool_joke_command_handler(**kwargs):
    """ Say a cool joke

    :param dict kwargs: Plugin args
    :return None:
    """
    from . import chat
    chat.cool_joke_command_handler(**kwargs)


@plugin.chat_message
def keyword_story_selector(**kwargs):
    """ Find a story by keyword and yield it

    :param dict kwargs: Plugin args
    :return None:
    """
    from . import chat
    chat.keyword_story_selector(**kwargs)


@plugin.helper
def storage_helper(**kwargs):
    """ Storage helper thread

    :param dict kwargs: Plugin args
    :return None:
    """
    from . import helper
    helper.StorageHelper()(**kwargs)


@plugin.helper
def stories_indexer(**kwargs):
    """ Live stories incremental indexer

    :param dict kwargs: Plugin args
    :return None:
    """
    from . import helper
    helper.stories_indexer(**kwargs)


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
