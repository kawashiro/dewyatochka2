# -*- coding: UTF-8

""" Exceptions on config related operations

Classes
=======
    ConfigError            -- Base config exception class
    ReadError              -- Error on config parsing
    SectionRetrievingError -- Error on attempt to access to invalid section
"""

__all__ = ['ConfigError', 'ReadError', 'SectionRetrievingError']


class ConfigError(Exception):
    """ Base config exception class """
    pass


class ReadError(ConfigError):
    """ Error on config parsing """
    pass


class SectionRetrievingError(ConfigError):
    """ Error on attempt to access to invalid section """
    pass
