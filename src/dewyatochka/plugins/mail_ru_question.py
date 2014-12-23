# -*- coding: UTF-8

"""
Ask a question from mail.ru
"""

__all__ = ['get_question', 'talk_command_handler', 'silence_checker', 'occasional_question']

import json
import random
import logging
import threading
import time
from urllib import parse as urlparse
from collections import defaultdict
from dewyatochka.core import plugin
from dewyatochka.utils import http
from dewyatochka.plugins.builtin import get_conference_last_activity


# Cached questions lists by categories
_mail_ru_questions_cache = defaultdict(lambda: [])

# Logger instance
_log = logging.getLogger(__name__)

# Lock for _get_question function
_get_question_lock = threading.Lock()

# Default questions category
_DEFAULT_CATEGORY = 'adult'  # TODO: Get random category if possible

# Max silence allowed by default
_DEFAULT_SILENCE_INTERVAL = 10800  # 3 hours

# Global config section
_CONFIG_SECTION = 'mail_ru'


def get_question(category):
    """
    Get question by category
    :param category:
    :return: str
    """
    try:
        _get_question_lock.acquire()
        category_questions = _mail_ru_questions_cache[category]
        if not category_questions:
            _log.info('No questions left, loading new')

            request_uri = '/api/v2/questlist?n=100&state=A&cat=%s' % urlparse.quote_plus(category)
            response = http.Client('otvet.mail.rus').get(request_uri)
            questions = [question['qtext'] for question in json.loads(response).get('qst', [])]

            if questions:
                category_questions.extend(questions)
                _log.info('Loaded %d new questions for category "%s"', len(questions), category)
            else:
                _log.warn('Failed to load new questions, server response: %s', response)
                return None

        return category_questions.pop(random.randint(0, len(category_questions) - 1))
    finally:
        _get_question_lock.release()


@plugin.chat_command('talk')
def talk_command_handler(**kwargs) -> str:
    """
    Echo to the conference with question
    :param kwargs: dict
    :return: str
    """
    category = kwargs['application'].config.section(_CONFIG_SECTION).get('category', _DEFAULT_CATEGORY)
    return get_question(category)


@plugin.helper
def occasional_question(application):
    """
    Occasionally generates questions to each conference
    :param application:
    :return: void
    """
    timeout = int(application.config.section(_CONFIG_SECTION).get('silence_interval', _DEFAULT_SILENCE_INTERVAL))
    conferences = application.conference_manager.conferences
    question_category = application.config.section(_CONFIG_SECTION).get('category', _DEFAULT_CATEGORY)

    while application.running:
        for conference_jid in conferences:
            last_activity = get_conference_last_activity(conference_jid)
            if last_activity + timeout < time.time():
                application.conference_manager.xmpp.send_chat_message(get_question(question_category), conference_jid)
        time.sleep(1)
