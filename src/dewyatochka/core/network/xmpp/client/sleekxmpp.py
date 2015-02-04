# -*- coding: UTF-8

"""
sleekxmpp lib based client
"""

__all__ = ['Client', 'MUCCommand', 'PingCommand']

import threading
import queue
import sleekxmpp
from sleekxmpp import exceptions as sleekexception
from . import _base
from dewyatochka.core.network.xmpp.entity import *
from dewyatochka.core.network.xmpp.exception import *


# Required sleekxmpp plugins names
_PLUGIN_PING = 'xep_0199'
_PLUGIN_MUC = 'xep_0045'

# Handled events names
_EVENT_MESSAGE = 'message'
_EVENT_PRESENCE_ERROR = 'presence_error'
_EVENT_DISCONNECTED = 'disconnected'


def _convert_message(raw_message: dict) -> ChatMessage:
    """
    Convert message to a Message instance
    :param raw_message: dict
    :return: ChatMessage
    """
    return ChatMessage(JID.from_string(raw_message['from'].bare),
                       JID.from_string(raw_message['to'].bare),
                       raw_message['body'])


class Client(_base.Client):
    """
    sleekxmpp lib based client
    """

    def __init__(self, host: str, login: str, password: str, port=5222, location=''):
        """
        Initialize xmpp connection instance
        :param host: str
        :param login: str
        :param password: str
        :param port: int
        :param location: str
        """
        super().__init__(host, login, password, port, location)

        self.__sleekxmpp = None
        self._connected = False
        self._connection_lock = threading.Lock()
        self._message_queue = queue.Queue()

    def disconnect(self, wait=True):
        """
        Close connection
        :param wait: bool - Wait until all received messages are processed
        :return: void
        """
        if not self._connected:
            raise ClientDisconnectedError('XMPP client is not connected to disconnect it')

        self._message_queue.put(ClientDisconnectedError('XMPP client is shutting down now'))
        if wait:
            self._message_queue.join()

        with self._connection_lock:
            self._connected = False
            self._sleekxmpp.disconnect()
            self._sleekxmpp.set_stop()

    def read(self) -> Message:
        """
        Read next message from stream
        :return: Message
        """
        try:
            message = self._message_queue.get()
            if isinstance(message, Exception):
                raise message
        finally:
            self._message_queue.task_done()

        return message

    def connect(self):
        """
        Establish connection to the server
        :return: void
        """
        with self._connection_lock:
            if self._connected:
                return

            self._connected = self._sleekxmpp.connect(self._server, reattempt=False)
            if not self._connected:
                raise C2SConnectionError('Failed to connect to %s:%s' % self._server)

            self._sleekxmpp.process()
            self._sleekxmpp.send_presence()

    @property
    def _sleekxmpp(self) -> sleekxmpp.ClientXMPP:
        """
        Get sleekxmpp client instance
        :return: sleekxmpp.ClientXMPP
        """
        if self.__sleekxmpp is None:
            self.__sleekxmpp = sleekxmpp.ClientXMPP(str(self._jid), self._password)
            self.__sleekxmpp.register_plugin(_PLUGIN_MUC)
            self.__sleekxmpp.register_plugin(_PLUGIN_PING)
            self.__sleekxmpp.add_event_handler(_EVENT_MESSAGE, self._queue_message)
            self.__sleekxmpp.add_event_handler(_EVENT_PRESENCE_ERROR, self._queue_presence_error)
            self.__sleekxmpp.add_event_handler(_EVENT_DISCONNECTED, self._queue_connection_error)

        return self.__sleekxmpp

    def _queue_message(self, message: dict):
        """
        Unify message format and put it into messages queue
        :param message: dict
        :return: void
        """
        if message['type'] == MessageError.MESSAGE_TYPE_ERROR:
            self._message_queue.put(
                MessageError(
                    MessageError.EXCEPTION_MESSAGE_TPL.format(message['error']['code'], message['error']['text'])
                )
            )
        else:
            self._message_queue.put(_convert_message(message))

    def _queue_presence_error(self, presence: dict):
        """
        Put presence error into messages queue
        :param presence: dict
        :return: void
        """
        self._message_queue.put(S2SConnectionError(presence['error']['text']))

    def _queue_connection_error(self):
        """
        Put connection error into messages queue
        :return: void
        """
        self._connection_lock.acquire()

        if self._connected:
            self._connected = False
            self._message_queue.put(C2SConnectionError('Connection broken'))

        self._connection_lock.release()

    @property
    def connection(self) -> sleekxmpp.ClientXMPP:
        """
        Get raw xmpp connection
        :return: sleekxmpp.ClientXMPP
        """
        if not self._connected:
            raise ClientDisconnectedError('XMPP connection is not established')

        return self._sleekxmpp


class MUCCommand(_base.Command):
    """
    Chat command
    """

    def send(self, message: str, receiver: JID):
        """
        Send message to a groupchat
        :param message: str
        :param receiver: JID
        :return: void
        """
        self._client.connection.send_message(receiver.jid, message, mtype='groupchat')

    def enter(self, conference: JID, nick=None):
        """
        Enter into a conference
        :param conference: JID
        :param nick: str
        :return: void
        """
        self._client.connection.plugin[_PLUGIN_MUC].joinMUC(conference.jid, nick or str(self._client.jid))

    def leave(self, conference: JID, nick=None, reason=''):
        """
        Leave a conference
        :param conference: JID
        :param nick: str
        :param reason: str
        :return: void
        """
        self._client.connection.plugin[_PLUGIN_MUC].leaveMUC(conference.jid, nick or str(self._client.jid), msg=reason)

    @property
    def name(self) -> str:
        """
        Command unique name
        :return: str
        """
        return 'chat'

    def __call__(self, message: str, receiver: JID):
        """
        Send chat message by default
        :param message: str
        :param receiver: JID
        :return: void
        """
        self.send(message, receiver)


class PingCommand(_base.Command):
    """
    c2s and s2s connections ping
    """

    @property
    def name(self) -> str:
        """
        Command unique name
        :return: str
        """
        return 'ping'

    def _do_ping(self, destination=None, timeout=None) -> int:
        """
        Ping destination by jid
        :param destination: JID or None
        :param timeout: int
        :return: int
        """
        try:
            destination_str = destination.jid if destination else None
            ping = self._client.connection.plugin[_PLUGIN_PING].ping(jid=destination_str,
                                                                     ifrom=str(self._client.jid),
                                                                     timeout=timeout)
        except sleekexception.IqError as e:
            if e.condition != MessageError.CONDITION_NOT_IMPLEMENTED:
                # feature-not-implemented error does not mean that connection is broken
                raise C2SConnectionError(e) if destination is None else S2SConnectionError(e)
            ping = -1
        except sleekexception.XMPPError as e:
            raise C2SConnectionError(e) if destination is None else S2SConnectionError(e)

        return ping

    def __call__(self, destination=None, timeout=None) -> int:
        """
        Ping something
        :param destination: JID or None to ping own server
        :param timeout: int
        :return int: int
        """
        return self._do_ping(destination, timeout)
