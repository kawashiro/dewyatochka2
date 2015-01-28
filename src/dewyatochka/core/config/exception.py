# -*- coding: UTF-8

"""
Exception on config related operations
"""

__all__ = ['ConfigError', 'ReadError', 'SectionRetrievingError']


class ConfigError(Exception):
    """
    Error on invalid config
    """
    pass


class ReadError(ConfigError):
    """
    Error on config parsing
    """
    pass


class SectionRetrievingError(ConfigError):
    """
    Error on attempt to access to invalid section
    """
    pass
