# -*- coding: UTF-8

""" Miscellaneous xmpp clients

Intended to have more than one implementation

Modules
=======
    sleekxmpp -- sleekxmpp lib based client

Functions
=========
    create -- Get configured client instance
"""

__all__ = ['create', 'sleekxmpp']

from ._base import Client


def create(host: str, login: str, password: str, port=5222, location='') -> Client:
    """ Get configured client instance

    Try to instantiate client that is satisfied with libs installed

    :param str host: XMPP server host
    :param str login: User login
    :param str password: User password
    :param int port: XMPP server port, default 5222
    :param str location: XMPP resource, default ''
    :return Client:
    """
    from . import sleekxmpp  # Only sleekxmpp-based client is supported now

    client = sleekxmpp.Client(host, login, password, port, location)
    client.add_command(sleekxmpp.MUCCommand(client))
    client.add_command(sleekxmpp.PingCommand(client))

    return client
