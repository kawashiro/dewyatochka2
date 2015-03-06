# -*- coding: UTF-8

""" Provides cool stories from zadolba.li for your chat

Modules
=======
    db_storage  -- zadolba.li local sqlite storage
    maintenance -- Functions for dewyatochkactl
    parser      -- zadolba.li html parser
"""

__all__ = ['db_storage', 'maintenance', 'parser']

import argparse

from dewyatochka.core import plugin

from . import maintenance


def _parse_args(argv: list):
    """ Parse own args

    :param list argv:
    :return argparse.Namespace:
    """
    args_parser = argparse.ArgumentParser()
    args_parser.add_argument('--db',
                             help='Path to database file',
                             default=None)
    return args_parser.parse_known_args(argv)[0]


@plugin.ctl('zl.recreate', 'Create a new empty zadolba.li db')
def recreate(registry, argv: list):
    """ Create a new empty zadolba.li db

    :param registry:
    :param argv:
    :return None:
    """
    db_path = _parse_args(argv).db or registry.config.get('db_path')
    maintenance.recreate(db_path, registry.log)


@plugin.ctl('zl.reindex', 'Populate stories table from scratch')
def reindex(registry, argv: list):
    """ Populate stories table from scratch

    :param registry:
    :param argv:
    :return None:
    """
    db_path = _parse_args(argv).db or registry.config.get('db_path')
    maintenance.recreate(db_path, registry.log)
    maintenance.reindex(db_path, registry.log)
