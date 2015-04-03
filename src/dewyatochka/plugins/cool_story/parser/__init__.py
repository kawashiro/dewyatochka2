# -*- coding: UTF-8

""" External stories sources parsers

Modules
=======
    chattyfish -- ChattyFish Ltd. projects
    nya_sh --     nya.sh html parser

Classes
=======
    AbstractParser -- Abstract parser

Attributes
==========
    RawPost -- Raw post immutable structure
    parsers -- All parsers declared
"""

__all__ = ['AbstractParser', 'RawPost', 'chattyfish', 'nya_sh', 'parsers']

from ._base import AbstractParser, RawPost  # Public for notations in external modules
from . import chattyfish, nya_sh

# All parsers tuple
parsers = (chattyfish.ItHappensParser,
           chattyfish.ZadolbaLiParser,
           nya_sh.Parser)
