# -*- coding: UTF-8

""" Provides some utils for conferences

Classes
=======
    ActivityInfo -- Conference activity info structure

Functions
=========
    get_activity_info -- Get conference activity info by JID
"""

from collections import defaultdict

from dewyatochka.core.network.entity import GroupChat

__all__ = ['ActivityInfo', 'get_activity_info']


# Conference jid -> last activity
_conference_last_activity = defaultdict(lambda key: ActivityInfo(key))


class ActivityInfo(object):
    """ Conference activity info structure """

    def __init__(self, conference: GroupChat):
        """ Create new activity info object with default values

        :param JID conference:
        """
        self._conference = conference
        self.last_message = 0
        self.last_activity = 0

    @property
    def conference(self) -> GroupChat:
        """ Conference getter

        :return JID:
        """
        return self._conference


def get_activity_info(conference: GroupChat) -> ActivityInfo:
    """ Get conference activity info

    :param JID conference: Conference JID
    :return ActivityInfo:
    """
    bare = str(conference.bare)
    if bare not in _conference_last_activity:
        _conference_last_activity[bare] = ActivityInfo(conference.bare)

    return _conference_last_activity[bare]
