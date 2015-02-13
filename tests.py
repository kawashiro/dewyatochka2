#!/usr/bin/env python3
# -*- coding: UTF-8

""" Run dewyatochka tests """

import sys
import os
import unittest

if __name__ == '__main__':
    home_dir = os.path.realpath(os.path.dirname(__file__))

    # Some dirty hack to run it such shortened way
    sys.path.append(home_dir + '/src')
    unittest_args = [__file__, 'discover', '-s', home_dir + '/tests'] + sys.argv[1:]

    unittest.main(argv=unittest_args)
