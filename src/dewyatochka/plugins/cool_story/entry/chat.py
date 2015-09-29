# -*- coding: UTF-8

""" Chat functions

Functions
=========
    get_random_cool_story     -- Say a random cool story
    cool_joke_command_handler -- Say a cool joke
    keyword_story_selector    -- Find a story by keyword and yield it
"""

import random

from ..parser.chattyfish import ZADOLBA_LI_SOURCE_NAME, ITHAPPENS_SOURCE_NAME
from ..parser.nya_sh import NYA_SH_SOURCE_NAME

from .helper import StorageHelper

__all__ = ['cool_story_command_handler', 'cool_joke_command_handler', 'keyword_story_selector']


def cool_story_command_handler(outp, **_):
    """ Say a cool story

    :param outp:
    :param _:
    :return None:
    """
    source = ZADOLBA_LI_SOURCE_NAME if random.getrandbits(1) else ITHAPPENS_SOURCE_NAME
    post = StorageHelper.run_task(lambda s: s.get_random_post_by_source(source))
    outp.say(post.text)


def cool_joke_command_handler(outp, **_):
    """ Say a cool joke

    :param outp:
    :param _:
    :return None:
    """
    post = StorageHelper.run_task(lambda s: s.get_random_post_by_source(NYA_SH_SOURCE_NAME))
    outp.say(post.text)


def keyword_story_selector(inp, outp, **_):
    """ Find a story by keyword and yield it

    :param inp:
    :param outp:
    :param _:
    :return None:
    """
    for tag in StorageHelper.run_task(lambda s: s.tags).keys():
        if tag in inp.text.lower():  # TODO: Implement tokenizer
            post = StorageHelper.run_task(lambda s: s.get_random_post_by_tag(tag))
            outp.say(post.text)
            break
