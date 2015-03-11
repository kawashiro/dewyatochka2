# -*- coding: UTF-8

""" Functions for dewyatochkactl

Functions
=========
    recreate -- Create a new empty local db
    reindex  -- Populate stories table from scratch
"""

__all__ = ['recreate', 'reindex']

import argparse
import threading
import queue

from .db_storage import Storage
from .parser import parsers, AbstractParser


# Stories amount to commit to db
_REINDEX_AUTO_COMMIT_COUNT = 1000


def _parse_args(argv: list):
    """ Parse own args

    :param list argv:
    :return argparse.Namespace:
    """
    args_parser = argparse.ArgumentParser()
    args_parser.add_argument('--db',
                             help='Path to database file',
                             default=None)
    return args_parser.parse_known_args(argv)[0]


def recreate(registry, argv: list):
    """ Create a new empty cool stories db

    :param registry:
    :param argv:
    :return None:
    """
    db_path = _parse_args(argv).db or registry.config.get('db_path')
    with Storage(db_path) as storage:
        storage.recreate()

    registry.log.info('Stories storage successfully recreated at %s' % storage.path)


def reindex(registry, argv: list):
    """ Populate stories table from scratch

    :param registry:
    :param argv:
    :return None:
    """
    def _parser_worker(parser: AbstractParser):
        """ Parser worker thread

        Collects remote stories and adds them into db insert queue

        :param AbstractParser parser:
        :return None:
        """
        for raw_story in parser:
            posts_queue.put(raw_story)

    # Starting process
    registry.log.info('Starting stories re-indexing')

    # Starting parsers in separate thread
    threads = []
    posts_queue = queue.Queue()
    for parser_class in parsers:
        parser_instance = parser_class()
        thread = threading.Thread(
            name='%s.reindex[%s]' % (__name__, parser_instance.name),
            target=_parser_worker,
            args=(parser_instance,),
            daemon=True
        )
        threads.append(thread)
        thread.start()
        registry.log.info('Initialized %s parser', parser_instance.name)

    # Saving stories from queue
    inserted = 0
    db_path = _parse_args(argv).db or registry.config.get('db_path')
    with Storage(db_path) as storage:
        while True:
            try:
                story = posts_queue.get(timeout=0.1)
                storage.add_post(story.source, story.id, story.title, story.text, story.tags, commit=False)
                inserted += 1
                if inserted % _REINDEX_AUTO_COMMIT_COUNT == 0:
                    # Commit changes only once per 1000 for performance
                    storage.db_session.commit()
                registry.log.progress('Indexed %d cool stories' % inserted)
            except queue.Empty:
                if all(map(lambda t: not t.is_alive(), threads)):
                    break
        else:
            storage.db_session.commit()

        registry.log.info('Completed')
