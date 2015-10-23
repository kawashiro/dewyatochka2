# -*- coding=utf-8

""" Tests suite for dewyatochka.core.daemon """

from os import path
import time
import subprocess

import unittest


class TestDaemon(unittest.TestCase):
    """ Covers dewyatochka.core.daemon """

    def test_run(self):
        """ Test whole daemon functionality """
        script = path.dirname(__file__) + '/files/daemon/script.py'
        script_lock = script + '.lock'

        subprocess.call(script, shell=True)
        time.sleep(0.5)
        self.assertTrue(path.isfile(script_lock), 'Lock file %s was not created' % script_lock)

        with open(script_lock) as pid_f:
            pid = int(pid_f.readline())
            self.assertGreater(pid, 0)

            proc_f_name = '/proc/%d/cmdline' % pid
            self.assertTrue(path.isfile(proc_f_name), 'Process %d does not seem to be running' % pid)
            with open(proc_f_name) as proc_f:
                command = proc_f.readline().split('\0')[1]
                self.assertEqual(script, command, 'Process %d exist but it is not a test script' % pid)

        time.sleep(0.6)
        self.assertFalse(path.isfile(script_lock), 'Lock file %s was not removed' % script_lock)
