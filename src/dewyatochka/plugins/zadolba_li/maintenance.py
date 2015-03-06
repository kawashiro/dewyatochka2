# -*- coding: UTF-8

""" Functions for dewyatochkactl

Functions
=========
    recreate -- Create a new empty zadolba.li db
    reindex  -- Populate stories table from scratch
"""

__all__ = ['recreate', 'reindex']

from .db_storage import Storage
from .parser import site_iterator


# Stories amount to commit to db
_REINDEX_AUTO_COMMIT_COUNT = 1000


def recreate(db_path: str, log):
    """ Create a new empty zadolba.li db

    :param str db_path: Path to database file
    :param log:
    :return None:
    """
    with Storage(db_path) as storage:
        storage.recreate()

    log.info('Stories storage successfully recreated at %s' % storage.path)


def reindex(db_path: str, log):
    """ Populate stories table from scratch

    :param str db_path: Path to database file
    :param log:
    :return None:
    """
    inserted = 0
    with Storage(db_path) as storage:
        log.info('Starting stories re-indexing')

        for raw_story in site_iterator():
            storage.add_post(raw_story.id, raw_story.title, raw_story.text, raw_story.tags, commit=False)
            inserted += 1
            if inserted % _REINDEX_AUTO_COMMIT_COUNT == 0:
                # Commit changes only once per 1000 for performance
                storage.db_session.commit()
            log.progress('Indexed %d cool stories from zadolba.li' % inserted)
        else:
            storage.db_session.commit()

        log.info('Completed')
