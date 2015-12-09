#!/usr/bin/env python3
# -*- coding: UTF-8

""" Run dewyatochka tests """

import sys
import os
import unittest

if __name__ == '__main__':
    # Test, Dewyatochka, test! ^-^
    home_dir = os.path.realpath(os.path.dirname(__file__))

    # Some dirty hack to run it such shortened way
    sys.path.insert(0, home_dir + '/src')
    unittest_args = [__file__, 'discover', '-s', home_dir + '/test/cases'] + sys.argv[1:]

    unittest.main(argv=unittest_args, module=None)
