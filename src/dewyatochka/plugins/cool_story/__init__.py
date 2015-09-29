# -*- coding: UTF-8

""" Provides cool stories for your chat

Packages
========
    parser -- External stories sources parsers
    entry  -- Plugin entry points

Modules
=======
    model -- Plugin logic impl
"""

from dewyatochka.core import plugin

__all__ = ['model', 'parser', 'entry']


@plugin.chat_command('coolstory')
def cool_story_command_handler(**kwargs):
    """ Say a cool story

    :param dict kwargs: Plugin args
    :return None:
    """
    from .entry import chat
    chat.cool_story_command_handler(**kwargs)


@plugin.chat_command('azaza')
def cool_joke_command_handler(**kwargs):
    """ Say a cool joke

    :param dict kwargs: Plugin args
    :return None:
    """
    from .entry import chat
    chat.cool_joke_command_handler(**kwargs)


@plugin.chat_message
def keyword_story_selector(**kwargs):
    """ Find a story by keyword and yield it

    :param dict kwargs: Plugin args
    :return None:
    """
    from .entry import chat
    chat.keyword_story_selector(**kwargs)


@plugin.helper
def storage_helper(registry):
    """ Storage helper thread

    :param registry: Plugin registry
    :return None:
    """
    from .model import Storage, StorageHelper
    StorageHelper(Storage(registry.config.get('db_path')))()


@plugin.helper
def stories_indexer(**kwargs):
    """ Live stories incremental indexer

    :param dict kwargs: Plugin args
    :return None:
    """
    from .entry import helper
    helper.stories_indexer(**kwargs)


@plugin.ctl('recreate', 'Create a new empty cool stories db')
def recreate(**kwargs):
    """ Create a new empty cool stories db

    :param dict kwargs: Plugin args
    :return None:
    """
    from .entry import maintenance
    maintenance.recreate(**kwargs)


@plugin.ctl('reindex', 'Populate stories table from scratch')
def reindex(**kwargs):
    """ Populate stories table from scratch

    :param dict kwargs: Plugin args
    :return None:
    """
    from .entry import maintenance
    maintenance.recreate(**kwargs)
    maintenance.reindex(**kwargs)
