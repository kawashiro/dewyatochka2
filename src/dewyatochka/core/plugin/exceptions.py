# -*- coding: UTF-8

""" Plugin registration related exceptions

Classes
=======
    PluginError             -- Common exception related to plugins
    PluginRegistrationError -- Error on plugin loading
"""

__all__ = ['PluginError', 'PluginRegistrationError']


class PluginError(RuntimeError):
    """ Common exception related to plugins """
    pass


class PluginRegistrationError(PluginError):
    """ Error on plugin loading """
    pass
