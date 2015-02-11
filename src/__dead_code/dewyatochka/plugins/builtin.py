# -*- coding: UTF-8

"""
Standard plugins plugins to provide a basic functionality
"""

__all__ = ['silence_checker', 'get_conference_last_activity']

import time
from dewyatochka.core import plugin
from collections import defaultdict


# Conference jid -> last activity timestamp
_conference_last_activity = defaultdict(lambda: time.time())


@plugin.chat_message(regular=True, own=True)
def silence_checker(**kwargs):
    """
    Checks where occasional question can be yield
    :param kwargs:
    :return: None
    """
    _conference_last_activity[kwargs['conference'].jid] = time.time()


def get_conference_last_activity(conference_jid):
    """
    Get conferences last not system message time
    :param conference_jid: str
    :return: int
    """
    return _conference_last_activity[conference_jid]
