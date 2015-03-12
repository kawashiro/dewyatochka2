# -*- coding: UTF-8

""" sleekxmpp lib based client

Classes
=======
    Client      -- Client basic implementation
    MUCCommand  -- Multi-user chat commands
    PingCommand -- XMPP ping
"""

__all__ = ['Client', 'MUCCommand', 'PingCommand']

import threading
import queue

import sleekxmpp
from sleekxmpp import exceptions as sleekexception
from sleekxmpp.xmlstream.stanzabase import ElementBase
from sleekxmpp.stanza.message import Message as SMessage
from sleekxmpp.stanza.presence import Presence

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
_EVENT_GC_SUBJECT = 'groupchat_subject'
_EVENT_GC_PRESENCE = 'groupchat_presence'


# C2S connection check params
_TASK_C2S_CHECK_NAME = 'c2s_connection_check'
_TASK_C2S_CHECK_INTERVAL = 60


def _convert_message(raw_message: ElementBase) -> ChatMessage:
    """ Convert message to a Message instance

    :param ElementBase raw_message:
    :return ChatMessage:
    """
    if isinstance(raw_message, SMessage) and raw_message['type'] == 'groupchat':
        if raw_message['body']:
            return ChatMessage(JID.from_string(raw_message['from'].full),
                               JID.from_string(raw_message['to'].full),
                               raw_message['body'])
        elif raw_message['subject']:
            return ChatSubject(JID.from_string(raw_message['from'].full),
                               JID.from_string(raw_message['to'].full),
                               raw_message['subject'])
    elif isinstance(raw_message, Presence):
        return ChatPresence(JID.from_string(raw_message['from'].full),
                            JID.from_string(raw_message['to'].full),
                            raw_message['type'],
                            raw_message['status'],
                            raw_message['muc']['role'])
    raise ValueError('Not acceptable message: %s' % raw_message)


class Client(_base.Client):
    """ Client basic implementation """

    def __init__(self, host: str, login: str, password: str, port=5222, location=''):
        """ Initialize XMPP client instance

        :param str host: XMPP server host
        :param str login: User login
        :param str password: User password
        :param int port: XMPP server port, default 5222
        :param str location: XMPP resource, default ''
        :return Client:
        """
        super().__init__(host, login, password, port, location)

        self.__sleekxmpp = None
        self._connected = False
        self._connection_lock = threading.Lock()
        self._message_queue = queue.Queue()

    def disconnect(self, wait=True, notify=True):
        """ Close connection

        :param bool wait: Wait until all received messages are processed
        :param bool notify: Notify reader about disconnection
        :return None:
        """
        if not self._connected:
            raise ClientDisconnectedError()

        if notify:
            self._message_queue.put(ClientDisconnectedError())

        if wait:
            self._message_queue.join()

        with self._connection_lock:
            self._connected = False
            self._sleekxmpp.disconnect(send_close=wait)

    def read(self) -> Message:
        """ Read next message from stream

        :return Message:
        """
        message = self._message_queue.get()
        self._message_queue.task_done()

        if isinstance(message, Exception):
            raise message

        return message

    def connect(self):
        """ Establish connection to the server

        :return None:
        """
        with self._connection_lock:
            if self._connected:
                return

            self._connected = self._sleekxmpp.connect(self._server, reattempt=False)
            if not self._connected:
                raise C2SConnectionError('Failed to connect to %s:%s' % self._server)

            self._sleekxmpp.send_presence()
            self._sleekxmpp.process()

    @property
    def _sleekxmpp(self) -> sleekxmpp.ClientXMPP:
        """ Create new sleekxmpp instance or return an already instantiated one

        :return sleekxmpp.ClientXMPP:
        """
        if self.__sleekxmpp is None:
            self.__sleekxmpp = sleekxmpp.ClientXMPP(str(self._jid), self._password)
            self.__sleekxmpp.register_plugin(_PLUGIN_MUC)
            self.__sleekxmpp.register_plugin(_PLUGIN_PING)
            self.__sleekxmpp.add_event_handler(_EVENT_MESSAGE, self._queue_message)
            self.__sleekxmpp.add_event_handler(_EVENT_GC_SUBJECT, self._queue_message)
            self.__sleekxmpp.add_event_handler(_EVENT_GC_PRESENCE, self._queue_message)
            self.__sleekxmpp.add_event_handler(_EVENT_PRESENCE_ERROR, self._queue_presence_error)
            self.__sleekxmpp.add_event_handler(_EVENT_DISCONNECTED, self._queue_connection_error)
            self.__sleekxmpp.schedule(_TASK_C2S_CHECK_NAME, _TASK_C2S_CHECK_INTERVAL,
                                      self._do_c2s_connection_check, repeat=True)

        return self.__sleekxmpp

    def _queue_message(self, message: ElementBase):
        """ Unify message format and put it into messages queue

        :param dict message:
        :return None:
        """
        if message['type'] == MessageError.MESSAGE_TYPE_ERROR:
            self._message_queue.put(
                MessageError(
                    MessageError.EXCEPTION_MESSAGE_TPL.format(message['error']['code'], message['error']['text'])
                )
            )
        else:
            try:
                self._message_queue.put(_convert_message(message))
            except ValueError:
                # Not acceptable message, ignore it
                pass

    def _queue_presence_error(self, presence: dict):
        """ Put presence error into messages queue

        :param dict presence:
        :return None:
        """
        remote_member = JID.from_string(presence['from'].bare)
        self._message_queue.put(S2SConnectionError(presence['error']['text'], remote=remote_member))

    def _queue_connection_error(self, _=None):
        """ Put connection error into messages queue

        :return None:
        """
        if self._connected:
            self.disconnect(wait=False, notify=False)
            self._message_queue.put(C2SConnectionError('Connection broken'))

    def _do_c2s_connection_check(self):
        """ Check C2S connection if possible

        :return None:
        """
        try:
            if self._connected and not self._connection_lock.locked():
                self.ping()
        except C2SConnectionError:
            self._queue_connection_error()
        except RuntimeError:
            # Command is not supported, do nothing
            pass

    @property
    def connection(self) -> sleekxmpp.ClientXMPP:
        """ Get raw xmpp connection

        :return sleekxmpp.ClientXMPP:
        """
        if not self._connected:
            raise ClientDisconnectedError()

        return self._sleekxmpp

    def __exit__(self, *args) -> bool:
        """ Close connection on exit if needed

        :param tuple args:
        :return bool:
        """
        if self._connected:
            return super().__exit__(*args)

        return False


class MUCCommand(_base.Command):
    """ Multi-user chat commands """

    def send(self, message: str, receiver: JID):
        """ Send message to a groupchat

        :param str message: Chat message text
        :param JID receiver: Groupchat JID
        :return None:
        """
        self._client.connection.send_message(receiver.jid, message, mtype='groupchat')

    def enter(self, conference: JID, nick=None):
        """ Enter into a conference

        :param JID conference: Groupchat JID
        :param nick: Nick to use in the chat. If none connection JID is to be used
        :return None:
        """
        self._client.connection.plugin[_PLUGIN_MUC].joinMUC(conference.jid, nick or str(self._client.jid))

    def leave(self, conference: JID, nick=None, reason=''):
        """ Leave a conference

        :param JID conference: Groupchat JID
        :param str nick: Nick used in the chat. If none connection JID is to be used
        :param str reason: Leave message, default ''
        :return None:
        """
        self._client.connection.plugin[_PLUGIN_MUC].leaveMUC(conference.jid, nick or str(self._client.jid), msg=reason)

    @property
    def name(self) -> str:
        """ Command unique name

        Command is to be attached as client's attribute
        named as the command is.

        :return str:
        """
        return 'chat'

    def __call__(self, message: str, receiver: JID):
        """ Send chat message on command call

        :param str message: Chat message text
        :param JID receiver: Groupchat JID
        :return None:
        """
        self.send(message, receiver)


class PingCommand(_base.Command):
    """ XMPP ping

    Used for C2S and S2S ping to check if any connection is alive
    """

    @property
    def name(self) -> str:
        """ Command unique name

        Command is to be attached as client's attribute
        named as the command is.

        :return str:
        """
        return 'ping'

    def _do_ping(self, destination=None, timeout=None) -> int:
        """ Ping destination by jid

        :param JID destination: Destination JID or None to check C2S connection
        :param int timeout: Time to wait for a response, in seconds
        :return int:
        """
        try:
            destination_str = destination.jid if destination else None
            ping = self._client.connection.plugin[_PLUGIN_PING].ping(jid=destination_str,
                                                                     ifrom=str(self._client.jid),
                                                                     timeout=timeout)
        except sleekexception.IqError as e:
            if e.condition != MessageError.CONDITION_NOT_IMPLEMENTED:
                # feature-not-implemented error does not mean that connection is broken
                raise C2SConnectionError(e) if destination is None else S2SConnectionError(e, remote=destination)
            ping = -1
        except sleekexception.XMPPError as e:
            raise C2SConnectionError(e) if destination is None else S2SConnectionError(e, remote=destination)

        return ping

    def __call__(self, destination=None, timeout=None) -> int:
        """ Ping destination by jid

        :param JID destination: Destination JID or None to check C2S connection
        :param int timeout: Time to wait for a response, in seconds
        :return int:
        """
        return self._do_ping(destination, timeout)
