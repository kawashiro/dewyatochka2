# coding=utf-8

"""
Test
"""

import sys
sys.path.append('/home/erashkevich/projects/dewyatochka2/src')

import unittest
from dewyatochka.core import application, log


class TestApplication(unittest.TestCase):
    """
    Application
    """

    class TestApp(application.Application):
        """
        Test application with empty run() method
        """
        def run(self, args: list):
            """
            Run application
            :param args: list Console arguments
            :return:
            """
            pass

    def test_logger_registration(self):
        """
        Test get / set logger
        """
        app = self.TestApp()

        logger = log.Console(app)
        app.set_logger(logger)

        self.assertEqual(logger, app.log)


if __name__ == '__main__':
    unittest.main(argv=['discover'])