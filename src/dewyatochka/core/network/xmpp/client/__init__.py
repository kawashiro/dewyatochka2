# -*- coding: UTF-8

"""
Blocking xmpp-client
"""

__all__ = ['get_client', 'sleekxmpp']

from ._base import Client


def get_client(host: str, login: str, password: str, port=5222, location='') -> Client:
    """
    Get xmpp client instance
    :param host: str
    :param login: str
    :param password: str
    :param port: str
    :param location: str
    :return:
    """
    from . import sleekxmpp  # Only sleekxmpp-based client is supported now

    client = sleekxmpp.Client(host, login, password, port, location)
    client.add_command(sleekxmpp.MUCCommand(client))
    client.add_command(sleekxmpp.PingCommand(client))

    return client
