# -*- coding: UTF-8

"""
Functions / classes to work with a single xmpp-connection
"""

__all__ = ['Client']

import sleekxmpp


class XMPPConnectionError(Exception):
    """
    Exception on failed connection attempt
    """
    pass


class Client():
    """
    XMPP client, handles a single connection to a jabber server
    """

    # XMPP connection instance
    _xmpp = None

    # True if connection is already established
    _connected = False

    # Server address (host, port)
    _server = ()

    # User jid
    _jid = ''

    def __init__(self, host, login, password, port=5222, location=''):
        """
        Initialize xmpp connection instance
        :param host: XMPP server host
        :param login: User login
        :param password: User password
        :param port: Server port, default 5222
        :return: void
        """
        full_jid = '{0}@{1}{2}'.format(login, host, location)
        self._server = host, port
        self._jid = full_jid

        self._xmpp = sleekxmpp.ClientXMPP(full_jid, password)
        self._xmpp.register_plugin('xep_0045')  # Enable MUC extension

    def _establish_connection(self):
        """
        Create a new connection
        :return: void
        """
        if self._connected:
            return

        self._connected = self._xmpp.connect(self._server)
        if not self._connected:
            raise XMPPConnectionError

        self._xmpp.send_presence()

    def enter_room(self, room, nick=None):
        """
        Enter the room specified
        :param room: Room
        :param nick:
        :return:
        """
        if nick is None:
            nick = self._jid

        self.connection.plugin['xep_0045'].joinMUC(room, nick)

    def set_message_handler(self, callback):
        """
        Set message handler
        :param callback: Callable
        :return:
        """
        self._xmpp.add_event_handler('message', callback)

    def send_chat_message(self, message, to):
        """
        Send a simple text message to a group chat
        :param message: Text message
        :param to: Reciever's JID
        :return:
        """
        self._xmpp.send_message(to, message, mtype='groupchat')

    @property
    def connection(self):
        """
        Get xmpp connection
        :return: sleekxmpp.ClientXMPP
        """
        self._establish_connection()
        return self._xmpp
