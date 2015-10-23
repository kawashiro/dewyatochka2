# -*- coding=utf-8

""" Tests suite for dewyatochka.core.daemon """

import os

import unittest

from dewyatochka.core.daemon import *


# Root path to test files directory
_FILES_ROOT = os.path.realpath(os.path.dirname(__file__) + '/../files/daemon')


class TestLock(unittest.TestCase):
    """ Tests suite for dewyatochka.core.daemon.acquire_lock / release_lock """

    # Lock file path
    _lock_path = _FILES_ROOT + os.sep + __file__.replace(os.sep, '_') + '.lock'

    def test_acquire(self):
        """ Test lock acquiring """
        with open(self._lock_path, 'w+'):
            pass
        self.assertRaises(ProcessLockedError, acquire_lock, self._lock_path)
        os.unlink(self._lock_path)

        acquire_lock(self._lock_path)
        self.assertTrue(os.path.isfile(self._lock_path),
                        'Lock file %s was not created' % self._lock_path)
        with open(self._lock_path) as f:
            lock_pid = int(f.readline())
        self.assertEqual(lock_pid, os.getpid())

        self.assertRaises(ProcessLockedError, acquire_lock, self._lock_path)

    def test_release(self):
        """ Test lock releasing """
        release_lock()
        self.assertRaises(ProcessNotLockedError, release_lock)
