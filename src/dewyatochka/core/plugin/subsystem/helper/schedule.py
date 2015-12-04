# -*- coding: UTF-8

""" Crontab-like schedule implementation

Classes
=======
    Schedule            -- Task schedule
    ScheduleFormatError -- Error on invalid schedule format
    Component           -- Schedule rule component
    DayOfMonth          -- Day of month component
    DayOfWeek           -- Day of week component
    Hour                -- Hour component
    Minute              -- Minute component
    Month               -- Month component
    Matcher             -- Component value matcher
    AbbreviationMatcher -- Matcher supporting simple abbreviations
    DayOfWeekMatcher    -- Day ow week abbreviations matcher
    MonthMatcher        -- Month abbreviations matcher
    RangeMatcher        -- Matcher for a single values range
    SequenceMatcher     -- Matcher for a sequence of ranges
"""

import time
from collections import namedtuple
from abc import ABCMeta, abstractproperty, abstractmethod

__all__ = ['Schedule', 'ScheduleFormatError', 'Component', 'DayOfMonth', 'DayOfWeek', 'Hour', 'Minute', 'Month',
           'Matcher', 'AbbreviationMatcher', 'DayOfWeekMatcher', 'MonthMatcher', 'RangeMatcher', 'SequenceMatcher']


class Component(metaclass=ABCMeta):
    """ Schedule rule component """

    def __init__(self, timestamp=None):
        """ Init component

        :param int timestamp:
        """
        self._now = timestamp

    @abstractproperty
    def min(self) -> int:  # pragma: nocover
        """ Minimal numeric value

        :return int:
        """
        pass

    @abstractproperty
    def max(self) -> int:  # pragma: nocover
        """ Maximal numeric value

        :return int:
        """
        pass

    @abstractproperty
    def current(self) -> int:  # pragma: nocover
        """ Current value

        :return int:
        """
        pass


class Minute(Component):
    """ Minute component """

    # Minimal numeric value
    min = 0

    # Maximal numeric value
    max = 59

    @property
    def current(self) -> int:
        """ Current value

        :return int:
        """
        return time.localtime(self._now).tm_min


class Hour(Component):
    """ Hour component """

    # Minimal numeric value
    min = 0

    # Maximal numeric value
    max = 23

    @property
    def current(self) -> int:
        """ Current value

        :return int:
        """
        return time.localtime(self._now).tm_hour


class DayOfMonth(Component):
    """ Day of month component """

    # Minimal numeric value
    min = 1

    # Maximal numeric value
    max = 31

    @property
    def current(self) -> int:
        """ Current value

        :return int:
        """
        return time.localtime(self._now).tm_mday


class Month(Component):
    """ Month component """

    # Minimal numeric value
    min = 1

    # Maximal numeric value
    max = 12

    @property
    def current(self) -> int:
        """ Current value

        :return int:
        """
        return time.localtime(self._now).tm_mon


class DayOfWeek(Component):
    """ Day of week component """

    # Minimal numeric value
    min = 0

    # Maximal numeric value
    max = 7

    @property
    def current(self) -> int:
        """ Current value

        :return int:
        """
        return time.localtime(self._now).tm_wday + 1


class Matcher(metaclass=ABCMeta):
    """ Component value matcher """

    def __init__(self, format_: str, component: Component):
        """ Init matcher

        :param str format_:
        :param Component component:
        """
        self._component = component
        self._values = self._parse_format(format_)

    @property
    def valid(self) -> bool:
        """ Check component value, return True if value is valid now

        :return bool:
        """
        return self._component.current in self._values

    @abstractmethod
    def _parse_format(self, format_: str) -> set:  # pragma: nocover
        """ Parse string

        :param str format_:
        :return set:
        """
        pass


class RangeMatcher(Matcher):
    """ Matcher for a single values range """

    def _parse_format(self, format_: str) -> set:
        """ Parse string

        :param str format_:
        :return set:
        """
        value_step = format_.split('/')
        if len(value_step) > 2:
            raise ValueError('Invalid range step specification "%s"' % format_)
        value = value_step[0]
        step = int(value_step[1]) if len(value_step) == 2 else None
        if step == 0:
            raise ValueError('Range step must not be zero: "%s"' % format_)

        if value == '*':
            # Any value
            value_from = self._component.min
            value_to = self._component.max
        else:
            # Values range or a single value
            value_limits = value.split('-')
            if len(value_limits) > 2:
                raise ValueError('Invalid range limits specification: "%s"' % value)
            value_from = int(value_limits[0])
            value_to = int(value_limits[1]) if len(value_limits) == 2 else None

        if value_to is None and step is not None:
            raise ValueError('Step can not be used for a single value: "%s"' % format_)

        values = set(range(value_from, value_to + 1, step or 1)) if value_to is not None else {value_from}
        if not values:
            raise ValueError('Expression "%s" produces empty launch schedule' % format_)
        if max(values) > self._component.max or min(values) < self._component.min:
            # noinspection PyStringFormat
            raise ValueError('Value is out of bounds [%d-%d]: %s' % (self._component.min, self._component.max, value))

        return values


class SequenceMatcher(RangeMatcher):
    """ Matcher for a sequence of ranges """

    def _parse_format(self, format_: str) -> set:
        """ Parse string

        :param str format_:
        :return set:
        """
        values = set()

        for range_str in format_.split(','):
            values.update(super()._parse_format(range_str))

        return values


class AbbreviationMatcher(SequenceMatcher, metaclass=ABCMeta):
    """ Matcher supporting simple abbreviations """

    @abstractproperty
    def _abbreviations(self) -> dict:  # pragma: nocover
        """ Abbreviations to numeric values (dict of int)

        :return dict:
        """
        pass

    def _parse_format(self, format_: str) -> set:
        """ Parse string

        :param str format_:
        :return set:
        """
        format_ = format_.lower()
        if format_ in self._abbreviations:
            return {self._abbreviations[format_]}

        return super()._parse_format(format_)


class DayOfWeekMatcher(AbbreviationMatcher):
    """ Day ow week abbreviations matcher """

    # Abbreviations to numeric values
    _abbreviations = {
        'sun': 0,
        'mon': 1,
        'tue': 2,
        'wed': 3,
        'thu': 4,
        'fri': 5,
        'sat': 6,
    }

    def _parse_format(self, format_: str) -> set:
        """ Parse string

        :param str format_:
        :return set:
        """
        values = super()._parse_format(format_)

        if 7 in values:
            values.add(0)  # Sunday juggling
        elif 0 in values:
            values.add(7)

        return values


class MonthMatcher(AbbreviationMatcher):
    """ Month abbreviations matcher """

    # Abbreviations to numeric values
    _abbreviations = {
        'jan': 1,
        'feb': 2,
        'mar': 3,
        'apr': 4,
        'may': 5,
        'jun': 6,
        'jul': 7,
        'aug': 8,
        'sep': 9,
        'oct': 10,
        'nov': 11,
        'dec': 12,
    }


class ScheduleFormatError(ValueError):
    """ Error on invalid schedule format """

    pass


class Schedule:
    """ Task schedule """

    # Format sequence namedtuple
    _ScheduleSequence = namedtuple(
        'Schedule__ScheduleSequence', ('min', 'hour', 'mday', 'mon', 'wday')
    )

    # Schedules shortcuts
    _aliases = {
        'yearly':   '0 0 1 1 *',
        'annually': '0 0 1 1 *',
        'monthly':  '0 0 1 * *',
        'weekly':   '0 0 * * 0',
        'daily':    '0 0 * * *',
        'midnight': '0 0 * * *',
        'hourly':   '0 * * * *',
        'minutely': '* * * * *',
    }

    def __init__(self, matchers: list):
        """ Init schedule

        :param matchers list:
        """
        self._matchers = matchers

    @property
    def in_time(self) -> bool:
        """ Check if should be evaluated now

        :return bool:
        """
        return all([m.valid for m in self._matchers])

    @classmethod
    def from_string(cls, string: str, now=None):
        """ Create a schedule from string

        :param str string: Schedule specification
        :param int now: Current timestamp override
        :return Schedule:
        """
        try:
            if string.startswith('@'):
                alias = string[1:]
                if alias not in cls._aliases:
                    raise ValueError('Unknown alias "%s"' % alias)
                string = cls._aliases[alias]

            try:
                schedule = cls._ScheduleSequence(*string.split(' '))
            except TypeError:
                raise ValueError('Schedule should contain exactly 5 components')

            return cls([
                SequenceMatcher(schedule.min, Minute(now)),
                SequenceMatcher(schedule.hour, Hour(now)),
                SequenceMatcher(schedule.mday, DayOfMonth(now)),
                MonthMatcher(schedule.mon, Month(now)),
                DayOfWeekMatcher(schedule.wday, DayOfWeek(now)),
            ])

        except ValueError as e:
            raise ScheduleFormatError('Failed to parse schedule string "%s": %s' % (string, str(e)))
