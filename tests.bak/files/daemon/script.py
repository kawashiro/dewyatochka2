#!/usr/bin/env python3
# -*- coding: UTF-8

""" Test daemon script

Simply starts as a daemon, creates a lock-file and exit after 2 sec
"""

import sys
import os
import time


if __name__ == '__main__':
    # Some dirty hack to import dewyatochka pkg
    sys.path.insert(0, os.path.realpath(os.path.dirname(__file__) + '/../../../src'))
    from dewyatochka.core import daemon

    daemon.detach()

    daemon.acquire_lock(__file__ + '.lock')
    time.sleep(1)
    daemon.release_lock()
