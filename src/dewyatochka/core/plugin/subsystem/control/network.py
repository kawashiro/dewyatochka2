# -*- coding: UTF-8

""" Dewyatochka control protocol impl

Classes
=======
    SocketListener      -- Abstract socket listener
    Message             -- Abstract client request
    InvalidMessageError -- Error on invalid message payload
    Client              -- Control client impl
    StreamReader        -- Messages stream reader

Attributes
==========
    DEFAULT_SOCKET_PATH -- Default path to socket
"""

import os
import socket
import json
from threading import Lock

__all__ = ['Message', 'SocketListener', 'Client', 'StreamReader', 'InvalidMessageError', 'DEFAULT_SOCKET_PATH']


# Default path to socket
DEFAULT_SOCKET_PATH = '/var/run/dewyatochka/control.sock'


class InvalidMessageError(ValueError):
    """ Error on invalid message payload """
    pass


class Message:
    """ Abstract client request """

    def __init__(self, source=None, raw=None, **payload):
        """ Init received request

        :param socket.socket source: Socket the message was received from
        :param bytes raw: Raw data to be parsed instead of args
        :param dict payload: Data to fill message with
        """
        self._data = None
        self._source = source

        if payload:
            self._data = payload
        else:
            self._data = self._parse(raw)

    @staticmethod
    def _parse(raw_data: bytes) -> dict:
        """ Parse network message

        :param bytes raw_data:
        :return dict:
        """
        if not raw_data:
            raise InvalidMessageError()

        try:
            return json.loads(raw_data.decode()) or {}

        except ValueError:
            raise InvalidMessageError()

    @property
    def data(self) -> dict:
        """ Get data dict

        :return dict:
        """
        return self._data

    @property
    def source(self) -> socket.socket:
        """ Source socket getter

        :return socket.socket:
        """
        return self._source

    def encode(self) -> bytes:
        """ Serialize message

        :return bytes:
        """
        return json.dumps(self.data).encode() + StreamReader.MSG_DELIMITER

    def __getattr__(self, item: str):
        """ Attribute data access

        :param str item:
        :return any:
        """
        return self.data.get(item)

    def __setattr__(self, key: str, value):
        """ Set data value as attribute

        :param str key:
        :param any value:
        :return None:
        """
        if key.startswith('_'):
            super().__setattr__(key, value)
        else:
            self.data[key] = value


class StreamReader:
    """ Messages stream reader """

    # Delimiter between two  messages in stream
    MSG_DELIMITER = b'\x00'

    # End of stream flag
    MSG_END = b'\x01\x00'

    def __init__(self, sock: socket.socket):
        """ Init helper

        :param socket.socket sock:
        """
        self.__sock = sock
        self.__tail = b''

    def read_message(self) -> Message:
        """ Read a message from a socket

        :return Message:
        """
        message = None
        reset = False

        while not reset:
            chunk = self.__tail
            if self.__tail:
                self.__tail = b''

            try:
                chunk += self.__sock.recv(4096)
            except ConnectionResetError:
                reset = True

            if chunk.startswith(self.MSG_END):
                # Reached end of stream, return None
                break

            delimiter_pos = chunk.find(self.MSG_DELIMITER)
            if ~delimiter_pos:
                # Chunk is a complete message
                chunk, self.__tail = chunk[:delimiter_pos], chunk[delimiter_pos+1:]
                message = Message(self.__sock, chunk)
                break

            # Message end is not reached, continue
            self.__tail += chunk

        return message


class SocketListener:
    """ Abstract socket listener """

    def __init__(self, address=None, backlog=0):
        """ Init listener instance

        :param any address: Server address (impl dependent)
        :param int backlog: Max number of unaccepted connections
        """
        self.__address = address or DEFAULT_SOCKET_PATH
        self.__backlog = backlog

        self.__socket = None
        self.__status_change = Lock()
        self.__opened = False

    @property
    def _socket(self) -> socket.socket:
        """ Get socket

        :return:
        """
        if self.__socket is None:
            self.__socket = socket.socket(socket.AF_UNIX)

        return self.__socket

    @property
    def _address(self):
        """ Get bind address

        :return any:
        """
        return self.__address

    def open(self):
        """ Open socket

        :return None:
        """
        with self.__status_change:
            self._socket.settimeout(0.5)
            self._socket.bind(self.__address)
            self._socket.listen(self.__backlog)
            self.__opened = True

    @property
    def commands(self):
        """ Iterator over input data

        :return socket.socket:
        """
        def __send(conn, msg):
            try:
                conn.send(msg)
            except BrokenPipeError:
                pass

        while True:
            connection = None
            try:
                with self.__status_change:
                    if not self.__opened:
                        break
                    connection = self._socket.accept()[0]

                command = StreamReader(connection).read_message()
                if not command.name:
                    raise InvalidMessageError()
                yield command

            except socket.timeout:
                pass

            except InvalidMessageError:
                __send(connection, 'Message format unrecognized'.encode())

            else:
                __send(connection, StreamReader.MSG_END)

            finally:
                if connection:
                    connection.shutdown(socket.SHUT_RDWR)
                    connection.close()

    def close(self):
        """ Close socket

        :return None:
        """
        with self.__status_change:
            if not self.__opened:
                return
            try:
                self.__opened = False
                self._socket.close()
                os.unlink(self._address)
            except FileNotFoundError:
                pass

    def __enter__(self):
            """ Open socket on enter

            :return self:
            """
            self.open()
            return self

    def __exit__(self, *_):
        """ Close on exit

        :param tuple _:
        :return None:
        """
        self.close()


class Client:
    """ Control client impl

    WARNING: Not intended to be thread-safe!
    """

    def __init__(self, address=None, reader=None):
        """ Init client instance

        :param any address: Server address (impl dependent)
        :param StreamReader reader:
        """
        self.__socket = None

        self.__address = address or DEFAULT_SOCKET_PATH
        self.__reader = reader or StreamReader(self._socket)

    def connect(self):
        """ Connect to server

        :return None:
        """
        self._socket.connect(self.__address)

    def disconnect(self):
        """ Close connection

        :return None:
        """
        self._socket.close()

    def send(self, command: Message):
        """ Send a command

        :param ClientCommand command: Command to send
        :return None:
        """
        self._socket.send(command.encode())

        self._socket.send(StreamReader.MSG_END)
        self._socket.shutdown(socket.SHUT_WR)

    @property
    def input(self):
        """ Input messages iterator

        :return iterable:
        """
        while True:
            message = self.__reader.read_message()
            if message is not None:
                yield message
            else:
                break

    @property
    def _socket(self) -> socket.socket:
        """ Get connection

        :return socket.socket:
        """
        if self.__socket is None:
            self.__socket = socket.socket(socket.AF_UNIX)

        return self.__socket

    def __enter__(self):
        """ Open socket on enter

        :return self:
        """
        self.connect()
        return self

    def __exit__(self, *_):
        """ Close on exit

        :param tuple _:
        :return None:
        """
        self.disconnect()
