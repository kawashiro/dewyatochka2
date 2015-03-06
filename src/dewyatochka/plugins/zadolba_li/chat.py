# -*- coding: UTF-8

""" Chat functions

Functions
=========
    get_random_cool_story -- Yields a random cool story
"""

__all__ = ['get_random_cool_story']

from .db_storage import Storage


def get_random_cool_story(db_path: str) -> str:
    """ Yields a random cool story

    :param str db_path: Path to database file
    :return str:
    """
    with Storage(db_path) as storage:
        return storage.random_post.text
