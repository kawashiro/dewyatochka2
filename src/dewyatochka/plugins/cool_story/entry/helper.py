# -*- coding: UTF-8

""" Chat helpers

Classes:
========
    StorageHelper -- Storage helper thread

Functions
=========
    stories_indexer -- Live stories incremental indexer
"""

from ..model import StorageHelper
from ..parser import parsers

__all__ = ['StorageHelper', 'stories_indexer']


def stories_indexer(registry):
    """ Live stories incremental indexer

    :param registry:
    :return None:
    """
    log = registry.log

    log.info('Checking stories services for updates')
    for parser_cls in parsers:
        parser = parser_cls()
        log.debug('Initialized %s parser', parser.name)

        last_id = StorageHelper.run_task(lambda s: s.get_last_indexed_post(parser.name)).ext_id or 0
        log.debug('Story last ID : %s => %d', parser.name, last_id)

        new_stories = 0
        for story in parser:
            if story.id <= last_id:
                log.debug('Story #%d from %s is already indexed, completed', story.id, story.source)
                break
            StorageHelper.run_task(
                lambda s: s.add_post(story.source, story.id, story.title, story.text, story.tags)
            )
            new_stories += 1
            log.debug('Indexed new story #%d from %s', story.id, story.source)
        if new_stories:
            log.info('Indexed %d new stories from %s', new_stories, parser.name)
        else:
            log.info('Stories source %s is already up to date', parser.name)

    log.info('Completed checking for updates')
