# -*- coding: UTF-8

""" Provides cool stories for your chat

Packages
========
    parser -- External stories sources parsers

Modules
=======
    model -- Plugin logic impl
"""

import random
import threading

from dewyatochka.core import plugin
from dewyatochka.core.plugin.exceptions import PluginError

from . import model
from .parser import parsers
from .parser.chattyfish import ZADOLBA_LI_SOURCE_NAME, ITHAPPENS_SOURCE_NAME
from .parser.nya_sh import NYA_SH_SOURCE_NAME

__all__ = ['model', 'parser']


# Indexation lock to avoid concurrent processes run
__indexation_running = threading.Event()


@plugin.bootstrap
def init_storage(registry):
    """ Set storage params

    :param registry:
    :return None:
    """
    db_path = registry.config.get('db_path')
    if db_path:
        model.Storage().path = db_path

    model.Storage().create()


@plugin.chat_command('coolstory')
def cool_story_command_handler(outp, **_):
    """ Say a cool story

    :param outp:
    :param _:
    :return None:
    """
    source = ZADOLBA_LI_SOURCE_NAME if random.getrandbits(1) else ITHAPPENS_SOURCE_NAME
    post = model.Storage().get_random_post_by_source(source)
    outp.say(post.text)


@plugin.chat_command('azaza')
def cool_joke_command_handler(outp, **_):
    """ Say a cool joke

    :param outp:
    :param _:
    :return None:
    """
    post = model.Storage().get_random_post_by_source(NYA_SH_SOURCE_NAME)
    outp.say(post.text)


@plugin.schedule('0 */12 * * *')
@plugin.control('update', 'Check for updates')
def index(**kwargs):
    """ Live stories incremental indexer

    :param kwargs:
    :return None:
    """
    if __indexation_running.is_set():
        raise PluginError('Cool stories indexation is already running')

    try:
        __indexation_running.set()

        log = kwargs.get('outp') or kwargs.get('registry').log
        log.info('Checking stories services for updates')

        for parser_cls in parsers:
            parser_ = parser_cls()
            log.debug('Initialized %s parser', parser_.name)

            last_id = model.Storage().get_last_indexed_post(parser_.name).ext_id or 0
            log.debug('Story last ID : %s => %d', parser_.name, last_id)

            new_stories = 0
            for story in parser_:
                if story.id <= last_id:
                    log.debug('Story #%d from %s is already indexed, completed', story.id, story.source)
                    break
                model.Storage().add_post(story.source, story.id, story.title, story.text, story.tags)
                new_stories += 1

            if new_stories:
                log.info('Indexed %d new stories from %s', new_stories, parser_.name)
            else:
                log.info('Stories source %s is already up to date', parser_.name)

        log.info('Completed checking for updates')

    finally:
        __indexation_running.clear()


@plugin.control('recreate', 'Create a new empty cartoons db')
def recreate(outp, **_):
    """ Create a new empty db

    :param outp:
    :param _:
    :return None:
    """
    model.Storage().recreate()
    outp.say('Cool stories storage successfully recreated at %s', model.Storage().path)


@plugin.control('reindex', 'Populate stories table from scratch')
def reindex(outp, **_):
    """ Populate stories table from scratch

    :param outp:
    :param _:
    :return None:
    """
    recreate(outp)
    index(outp=outp)
