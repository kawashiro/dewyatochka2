# -*- coding: UTF-8

""" Helper plugins container service implementation

Classes
=======
    Environment -- Helper plugin environment (using basic implementation)
    Service     -- Helper plugins container service

Attributes
==========
    PLUGIN_TYPE_HELPER  -- Helper plugin
    PLUGIN_TYPES        -- All plugin types list
"""

from dewyatochka.core.plugin.base import Environment
from dewyatochka.core.plugin.base import Service as BaseService

__all__ = ['Environment', 'Service', 'PLUGIN_TYPE_HELPER', 'PLUGIN_TYPES']


# Plugin types provided
PLUGIN_TYPE_HELPER = 'helper'
PLUGIN_TYPES = [PLUGIN_TYPE_HELPER]


class Service(BaseService):
    """ Helper plugins container service """

    @property
    def accepts(self) -> list:
        """ Get list of acceptable plugin types

        :return list:
        """
        return PLUGIN_TYPES
