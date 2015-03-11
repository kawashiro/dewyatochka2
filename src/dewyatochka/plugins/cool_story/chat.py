# -*- coding: UTF-8

""" Chat functions

Functions
=========
    get_random_cool_story -- Say a random cool story
"""

__all__ = ['cool_story_command_handler']

from .db_storage import Storage


def cool_story_command_handler(outp, registry, **_):
    """ Say a cool story

    :param outp:
    :param registry:
    :param _:
    :return None:
    """
    with Storage(registry.config.get('db_path')) as storage:
        outp.say(storage.random_post.text)
