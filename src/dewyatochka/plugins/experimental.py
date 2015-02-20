# -*- coding: UTF-8

""" Experimental plugin

Temporary, for functional tests only!
"""

__all__ = ['test_fn', 'helper_fn']

from dewyatochka.core.plugin import chat_command, helper


@chat_command('say')
def test_fn(inp, outp, **_):
    """ Say nyan~

    :param inp:
    :param outp:
    :param _:
    :return None:
    """
    outp.say('Nyan~ %s~' % inp.sender.resource)


@helper
def helper_fn(registry):
    """ Dummy helper

    :param registry:
    :return None:
    """
    import time

    while True:
        registry.log.info('I\'m running...')
        time.sleep(10)
