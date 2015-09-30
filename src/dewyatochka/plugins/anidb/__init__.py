# -*- coding: UTF-8

""" Suggests cartoons from anidb.net

Modules
=======
    entry    -- Plugin entry points
    model    -- SQLite storage, common logic
    importer -- AniDB import logic
"""

from dewyatochka.core import plugin

__all__ = ['entry', 'model', 'importer']


@plugin.ctl('import-file', 'Update cartoons database from xml file specified')
def import_file(**kwargs):
    """ Update cartoons database from xml file specified

    :param dict kwargs: Plugin args
    :return None:
    """
    from . import entry
    entry.update_db_from_file(**kwargs)


@plugin.ctl('recreate', 'Create a new empty cartoons db')
def recreate(**kwargs):
    """ Create a new empty db

    :param dict kwargs: Plugin args
    :return None:
    """
    from . import entry
    entry.recreate_storage(**kwargs)


@plugin.ctl('update', 'Update database')
def recreate(**kwargs):
    """ Create a new empty db

    :param dict kwargs: Plugin args
    :return None:
    """
    from . import entry
    entry.update_db_manual(**kwargs)


@plugin.daemon
def storage_helper(**kwargs):
    """ Daemon helper to check for updates

    :param dict kwargs: Plugin args
    :return None:
    """
    from .model import Storage, StorageHelper
    StorageHelper(Storage(kwargs['registry'].config.get('db_path')))()


@plugin.schedule('@daily')
def updates_helper(**kwargs):
    """ Daemon helper to check for updates

    :param dict kwargs: Plugin args
    :return None:
    """
    from . import entry
    entry.update_db_auto(**kwargs)


@plugin.chat_command('cartoon')
def cartoon_command_handler(**kwargs):
    """ Yield a random cartoon

    :param dict kwargs: Plugin args
    :return None:
    """
    from . import entry
    entry.cartoon_command_handler(**kwargs)
