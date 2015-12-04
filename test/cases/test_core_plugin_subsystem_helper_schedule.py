# -*- coding=utf-8

""" Tests suite for dewyatochka.core.plugin.subsystem.helper.schedule """

import time

import unittest

from dewyatochka.core.plugin.subsystem.helper.schedule import *


class _MatcherTestTrait:
    """ Matcher values getter """

    @property
    def values(self) -> set:
        """ Get valid values set

        :return set:
        """
        return getattr(self, '_values')


class _Component(Component):
    """ Simple component with hardcoded values """

    # Min value
    min = 1

    # Max value
    max = 5

    @property
    def current(self) -> int:
        """ Current value

        :return int:
        """
        return self._now


class TestMinute(unittest.TestCase):
    """ Tests suite for dewyatochka.core.plugin.subsystem.helper.schedule.Minute """

    def test_current(self):
        """ Test current value getter """
        self.assertEqual(Minute(42 * 60).current, 42)


class TestHour(unittest.TestCase):
    """ Tests suite for dewyatochka.core.plugin.subsystem.helper.schedule.Hour """

    def test_current(self):
        """ Test current value getter """
        self.assertEqual(Hour(9 * 3600).current, 9 + time.localtime(0).tm_hour)


class TestDayOfMonth(unittest.TestCase):
    """ Tests suite for dewyatochka.core.plugin.subsystem.helper.schedule.DayOfMonth """

    def test_current(self):
        """ Test current value getter """
        self.assertEqual(DayOfMonth(42 * 86400).current, 11 + time.localtime(0).tm_mday)


class TestDayOfWeek(unittest.TestCase):
    """ Tests suite for dewyatochka.core.plugin.subsystem.helper.schedule.DayOfWeek """

    def test_current(self):
        """ Test current value getter """
        self.assertEqual(DayOfWeek(3 * 86400).current, 4 + time.localtime(0).tm_wday)


class TestMonth(unittest.TestCase):
    """ Tests suite for dewyatochka.core.plugin.subsystem.helper.schedule.Month """

    def test_current(self):
        """ Test current value getter """
        self.assertEqual(Month(42 * 86400).current, 2)


class TestMatcher(unittest.TestCase):
    """ Tests suite for dewyatochka.core.plugin.subsystem.helper.schedule.Matcher """

    def test_valid(self):
        """ Test input value validation """
        class _MatcherImpl(Matcher):
            """ Matcher implementation """
            def _parse_format(self, format_: str) -> set:
                """ Parse string

                :param str format_:
                :return set:
                """
                return {int(format_)}

        self.assertTrue(_MatcherImpl('42', Minute(42 * 60)).valid)
        self.assertFalse(_MatcherImpl('42', Minute(43 * 60)).valid)


class TestRangeMatcher(unittest.TestCase):
    """ Tests suite for dewyatochka.core.plugin.subsystem.helper.schedule.RangeMatcher """

    def test_parse(self):
        """ Test range format parsing """
        class _MatcherImpl(RangeMatcher, _MatcherTestTrait):
            pass

        self.assertRaises(ValueError, _MatcherImpl, '1/2/3', _Component())
        self.assertRaises(ValueError, _MatcherImpl, '*/0', _Component())
        self.assertRaises(ValueError, _MatcherImpl, '1-2-3', _Component())
        self.assertRaises(ValueError, _MatcherImpl, '7/10', _Component())
        self.assertRaises(ValueError, _MatcherImpl, '1-10', _Component())
        self.assertRaises(ValueError, _MatcherImpl, '0-4', _Component())
        self.assertRaises(ValueError, _MatcherImpl, '*/-42', _Component())

        self.assertEqual(_MatcherImpl('*', _Component()).values, {1, 2, 3, 4, 5})
        self.assertEqual(_MatcherImpl('*/2', _Component()).values, {1, 3, 5})
        self.assertEqual(_MatcherImpl('2-5', _Component()).values, {2, 3, 4, 5})
        self.assertEqual(_MatcherImpl('2-5/2', _Component()).values, {2, 4})


class TestSequenceMatcher(unittest.TestCase):
    """ Tests suite for dewyatochka.core.plugin.subsystem.helper.schedule.SequenceMatcher """

    def test_parse(self):
        """ Test sequence format parsing """
        class _MatcherImpl(SequenceMatcher, _MatcherTestTrait):
            pass

        self.assertEqual(_MatcherImpl('1-3/2,5', _Component()).values, {1, 3, 5})


class TestAbbreviationMatcher(unittest.TestCase):
    """ Tests suite for dewyatochka.core.plugin.subsystem.helper.schedule.AbbreviationMatcher """

    def test_parse(self):
        """ Test abbreviations parsing """
        class _MatcherImpl(AbbreviationMatcher, _MatcherTestTrait):
            _abbreviations = {'foo': 5}

        self.assertEqual(_MatcherImpl('1-3', _Component()).values, {1, 2, 3})
        self.assertEqual(_MatcherImpl('foo', _Component()).values, {5})


class TestDayOfWeekMatcher(unittest.TestCase):
    """ Tests suite for dewyatochka.core.plugin.subsystem.helper.schedule.DayOfWeekMatcher """

    def test_parse(self):
        """ Test abbreviations parsing """
        class _MatcherImpl(DayOfWeekMatcher, _MatcherTestTrait):
            pass

        self.assertEqual(_MatcherImpl('0', DayOfWeek()).values, {0, 7})
        self.assertEqual(_MatcherImpl('7', DayOfWeek()).values, {0, 7})
        self.assertEqual(_MatcherImpl('sun', DayOfWeek()).values, {0, 7})
        self.assertEqual(_MatcherImpl('mon', DayOfWeek()).values, {1})
        self.assertEqual(_MatcherImpl('tue', DayOfWeek()).values, {2})
        self.assertEqual(_MatcherImpl('wed', DayOfWeek()).values, {3})
        self.assertEqual(_MatcherImpl('thu', DayOfWeek()).values, {4})
        self.assertEqual(_MatcherImpl('fri', DayOfWeek()).values, {5})
        self.assertEqual(_MatcherImpl('sat', DayOfWeek()).values, {6})


class TestMonthMatcher(unittest.TestCase):
    """ Tests suite for dewyatochka.core.plugin.subsystem.helper.schedule.MonthMatcher """

    def test_parse(self):
        """ Test abbreviations parsing """
        class _MatcherImpl(MonthMatcher, _MatcherTestTrait):
            pass

        self.assertEqual(_MatcherImpl('jan', Month()).values, {1})
        self.assertEqual(_MatcherImpl('feb', Month()).values, {2})
        self.assertEqual(_MatcherImpl('mar', Month()).values, {3})
        self.assertEqual(_MatcherImpl('apr', Month()).values, {4})
        self.assertEqual(_MatcherImpl('may', Month()).values, {5})
        self.assertEqual(_MatcherImpl('jun', Month()).values, {6})
        self.assertEqual(_MatcherImpl('jul', Month()).values, {7})
        self.assertEqual(_MatcherImpl('aug', Month()).values, {8})
        self.assertEqual(_MatcherImpl('sep', Month()).values, {9})
        self.assertEqual(_MatcherImpl('oct', Month()).values, {10})
        self.assertEqual(_MatcherImpl('nov', Month()).values, {11})
        self.assertEqual(_MatcherImpl('dec', Month()).values, {12})


class TestSchedule(unittest.TestCase):
    """ Tests suite for dewyatochka.core.plugin.subsystem.helper.schedule.Schedule """

    @staticmethod
    def _in_time(schedule: str, date: str):
        """ Check if time matches schedule

        :param schedule:
        :param date:
        :return:
        """
        ts = time.mktime(time.strptime(date, '%Y-%m-%d %H:%M:%S %Z'))
        return Schedule.from_string(schedule, ts).in_time

    def assert_in_time(self, schedule: str, date: str):
        """ Assert schedule is in time

        :return None:
        """
        self.assertTrue(
            self._in_time(schedule, date), 'Schedule "%s" expected to match date "%s"' % (schedule, date)
        )

    def assert_not_in_time(self, schedule: str, date: str):
        """ Assert schedule is not in time

        :return None:
        """
        self.assertFalse(
            self._in_time(schedule, date), 'Schedule "%s" expected not to match date "%s"' % (schedule, date)
        )

    def test_invalid_schedule_format(self):
        """ Test handling schedule format errors """
        self.assertRaises(ScheduleFormatError, Schedule.from_string, '@foo')
        self.assertRaises(ScheduleFormatError, Schedule.from_string, '1 2 3')

    def test_aliases(self):
        """ Test aliases support """
        self.assert_in_time('@yearly', '2015-01-01 00:00:00 UTC')
        self.assert_not_in_time('@yearly', '2015-03-01 00:00:00 UTC')
        self.assert_in_time('@annually', '2015-01-01 00:00:00 UTC')
        self.assert_not_in_time('@annually', '2015-01-02 00:00:00 UTC')
        self.assert_in_time('@monthly', '2013-07-01 00:00:00 UTC')
        self.assert_not_in_time('@monthly', '2013-07-05 00:00:00 UTC')
        self.assert_in_time('@weekly', '2015-12-06 00:00:00 UTC')
        self.assert_not_in_time('@weekly', '2015-12-07 00:00:00 UTC')
        self.assert_in_time('@daily', '2015-12-06 00:00:00 UTC')
        self.assert_not_in_time('@daily', '2015-12-06 08:00:00 UTC')
        self.assert_in_time('@midnight', '2015-12-06 00:00:00 UTC')
        self.assert_not_in_time('@midnight', '2015-12-06 08:00:00 UTC')
        self.assert_in_time('@hourly', '2015-12-06 08:00:00 UTC')
        self.assert_not_in_time('@hourly', '2015-12-06 08:01:00 UTC')
        self.assert_in_time('@minutely', '2015-12-06 08:42:00 UTC')

    def test_value(self):
        """ Test some value """
        self.assert_in_time('12 7 25 12 5-7', '2015-12-25 07:12:42 UTC')
        self.assert_in_time('12 7 25 12 5-7', '2016-12-25 07:12:42 UTC')
        self.assert_not_in_time('12 7 25 12 5-7', '2014-12-25 07:12:42 UTC')
