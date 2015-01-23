# -*- coding: UTF-8

"""
Test loggers
"""

__all__ = ['NullHandler']

import logging
from dewyatochka.core.log import Handler


class NullHandler(Handler):
    """
    NULL handler wrapper
    """

    def _create_handler(self) -> logging.Handler:
        """
        Create new handler instance
        :return: logging.Handler
        """
        return logging.NullHandler()
