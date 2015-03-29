# -*- coding: UTF-8

""" Chat functions

Functions
=========
    get_random_cool_story     -- Say a random cool story
    cool_joke_command_handler -- Say a cool joke
"""

__all__ = ['cool_story_command_handler', 'cool_joke_command_handler']

import random

from .helper import StorageHelper
from .parser.chattyfish import ZADOLBA_LI_SOURCE_NAME, ITHAPPENS_SOURCE_NAME
from .parser.nya_sh import NYA_SH_SOURCE_NAME


def cool_story_command_handler(outp, **_):
    """ Say a cool story

    :param outp:
    :param _:
    :return None:
    """
    source = ZADOLBA_LI_SOURCE_NAME if random.getrandbits(1) else ITHAPPENS_SOURCE_NAME
    post = StorageHelper.run_task(lambda s: s.get_random_post(source))
    outp.say(post.text)


def cool_joke_command_handler(outp, **_):
    """ Say a cool joke

    :param outp:
    :param _:
    :return None:
    """
    post = StorageHelper.run_task(lambda s: s.get_random_post(NYA_SH_SOURCE_NAME))
    outp.say(post.text)
