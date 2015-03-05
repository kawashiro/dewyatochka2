# -*- coding: UTF-8

""" Provides cool stories from zadolba.li for your chat

Modules
=======
    db_storage  -- zadolba.li local sqlite storage
    maintenance -- Functions for dewyatochkactl
    parser      -- zadolba.li html parser
"""

__all__ = ['db_storage', 'maintenance', 'parser']

from dewyatochka.core import plugin

from . import maintenance


@plugin.ctl('zl.recreate', 'Create a new empty zadolba.li db')
def recreate(registry, **_):
    """ Create a new empty zadolba.li db

    :param registry:
    :param _:
    :return None:
    """
    maintenance.recreate(registry.config, registry.log)


@plugin.ctl('zl.reindex', 'Populate stories table from scratch')
def reindex(registry, **_):
    """ Populate stories table from scratch

    :param registry:
    :param _:
    :return None:
    """
    maintenance.recreate(registry.config, registry.log)
    maintenance.reindex(registry.config, registry.log)
