# -*- coding: UTF-8

""" Ask a question from mail.ru """

import time
import logging
import random
import threading
from collections import defaultdict

from dewyatochka.core import plugin
from dewyatochka.core.plugin.builtins import get_activity_info

__all__ = []


# Cached questions lists by categories
_mail_ru_questions_cache = defaultdict(lambda: [])

# Lock for _get_question function
_get_question_lock = threading.Lock()

# otvet.mail.ru API domain
_QUESTIONS_DOMAIN = 'otvet.mail.ru'

# URI to fetch questions from
_QUESTIONS_REQUEST_URI = '/api/v2/questlist'

# Questions limit in one query, using 100 (max)
_QUESTIONS_PER_QUERY = 100

# Default questions category
_DEFAULT_CATEGORY = 'adult'

# Max silence allowed by default
_DEFAULT_SILENCE_INTERVAL = 10800  # 3 hours


def _get_question(category: str, log) -> str:
    """ Get question by category

    :param str category: Category label
    :param logging.Logger log: Logger instance
    :return str:
    """
    from dewyatochka.core.utils.http import WebClient

    try:
        _get_question_lock.acquire()
        category_questions = _mail_ru_questions_cache[category]
        if not category_questions:
            log.info('No questions left, loading new')

            response = WebClient(_QUESTIONS_DOMAIN, https=True) \
                .get(_QUESTIONS_REQUEST_URI, {'n': _QUESTIONS_PER_QUERY, 'cat': category}) \
                .get('qst', [])
            questions = [question['qtext'] for question in response]

            if questions:
                category_questions.extend(questions)
                log.info('Loaded %d new questions for category "%s"', len(questions), category)
            else:
                log.warning('Failed to load new questions, server response: %s', response)
                return None

        return category_questions.pop(random.randint(0, len(category_questions) - 1))
    finally:
        _get_question_lock.release()


@plugin.chat_accost
@plugin.chat_command('talk')
def talk_command_handler(outp, registry, **_):
    """ Echo to the conference a question

    :param outp:
    :param registry:
    :param _:
    :return None:
    """
    category = registry.config.get('category', _DEFAULT_CATEGORY)
    outp.say(_get_question(category, registry.log))


@plugin.schedule('@minutely', services=['bot'])
def occasional_question(registry):
    """ Ask a question if conference is too silent

    :param registry:
    :return None:
    """
    category = registry.config.get('category', _DEFAULT_CATEGORY)
    silence_interval = int(registry.config.get('silence_interval', _DEFAULT_SILENCE_INTERVAL))
    log = registry.log

    log.debug('Checking conferences state')
    for conference in registry.bot.alive_chats:
        last_message_ts = get_activity_info(conference).last_message

        if last_message_ts and last_message_ts + silence_interval < time.time():
            log.info('Conference %s is too silent (last msg.: %d), waking up', conference, last_message_ts)
            registry.bot.send_muc(_get_question(category, log), conference)
        else:
            log.debug('Conference %s postponed (last msg.: %d)', conference, last_message_ts)
