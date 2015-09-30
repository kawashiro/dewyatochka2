# -*- coding: UTF-8

""" Plugin entry points

Functions
=========
    recreate_storage    -- Create a new empty cartoons db
    update_db_manual    -- Update cartoons database if needed from ctl utility
    update_db_from_file -- Update cartoons database from xml file specified
"""

import time
import argparse
import threading

from dewyatochka.core.config.exception import SectionRetrievingError

from .model import Storage, StorageHelper
from .importer import *

__all__ = ['recreate_storage', 'update_db_manual', 'update_db_from_file']


def _parse_ctl_args(argv: list, require_xml_param=False):
    """ Parse control utility cmd args

    :param list argv:
    :param bool require_xml_param:
    :return argparse.Namespace:
    """
    args_parser = argparse.ArgumentParser()
    args_parser.add_argument('--db',
                             help='Path to database file',
                             default=None)
    xml_param_kwargs = {'help': 'Path to XML AniDB file'}
    if not require_xml_param:
        xml_param_kwargs['default'] = None
    args_parser.add_argument('--xml', **xml_param_kwargs)

    return args_parser.parse_known_args(argv)[0]


def _start_ctl_storage_helper(registry, argv: list):
    """ Start storage helper for ctl utility

    :param registry:
    :param argv:
    :return None:
    """
    threading.Thread(
        name='%s.update_db_manual[StorageHelper]' % __name__,
        target=StorageHelper(Storage(_parse_ctl_args(argv).db or registry.config.get('db_path'))),
        daemon=True
    ).start()


def _wait_ctl_storage_helper(log):
    """ Wait until storage helper completes it's work

    :param log:
    :return None:
    """
    log.info('Waiting until all changes are committed ...')
    StorageHelper.wait()
    log.info('Completed successfully')


def recreate_storage(registry, argv: list):
    """ Create a new empty cartoons db

    :param registry:
    :param argv:
    :return None:
    """
    db_path = _parse_ctl_args(argv).db or registry.config.get('db_path')
    with Storage(db_path) as storage:
        storage.recreate()

    registry.log.info('Cartoons storage successfully recreated at %s' % storage.path)


def update_db_manual(registry, argv: list):
    """ Update cartoons database if needed from ctl utility

    :param registry:
    :param argv:
    :return None:
    """
    _start_ctl_storage_helper(registry, argv)
    update_database(registry.log)
    _wait_ctl_storage_helper(registry.log)


def update_db_auto(registry):
    """ Automatic updates checker. Runs as daemon helper

    :param registry:
    :return None:
    """
    update_database(registry.log)


def update_db_from_file(registry, argv: list):
    """ Update cartoons database from xml file specified

    :param registry:
    :param argv:
    :return None:
    """
    _start_ctl_storage_helper(registry, argv)
    xml_file = _parse_ctl_args(argv, require_xml_param=True).xml
    import_xml_file(xml_file, registry.log)
    _wait_ctl_storage_helper(registry.log)


def cartoon_command_handler(inp, outp, registry, **_):
    """ Yield a random cartoon

    :param inp:
    :param outp:
    :param registry:
    :param _:
    :return None:
    """
    template = registry.config.get('message')
    if not template:
        raise SectionRetrievingError('`message` config param is required for AniDB plugin')

    cartoon = StorageHelper.run_task(lambda s: s.random_cartoon)
    msg_params = {'user': inp.sender.resource, 'title': cartoon.primary_title, 'url': cartoon.url}

    outp.say(template.format(**msg_params))
