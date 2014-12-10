# -*- coding: UTF-8

"""
Simple http client
"""

__all__ = ['Client']

from http import client

# Common default constants
HTTP_CLIENT_CHUNK_SIZE = 10240
HTTP_CLIENT_CONNECTION_TIMEOUT = 20
USER_AGENT = 'Mozilla/5.0 (X11; Linux i686; rv:23.0) Gecko/20100101 Firefox/23.0'


class ReadResponseException(Exception):
    """
    Exception if connection is closed by remote server or transfer completed
    """
    pass


class Client:
    """
    Simple HTTP-client for browsing
    """

    # Default fake headers set
    _headers = {
        'Accept':          'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'ru,en-us;q=0.7,en;q=0.3',
        'Cache-Control':   'max-age=0',
        'Connection':      'keep-alive',
        'Host':            None,
        'User-Agent':      USER_AGENT
    }

    def __init__(self, host, port=None):
        """
        Init client
        :param host: str - remote server host
        :param port: int - remote server port
        """
        self._host = host
        self._headers['Host'] = host

        self._port = port
        self._response = None

        self._connect()

    def _connect(self):
        """
        Connect to specified host
        """
        self._connection = client.HTTPConnection(self._host, self._port, timeout=HTTP_CLIENT_CONNECTION_TIMEOUT)

    def get(self, uri):
        """
        Get content of page
        :param uri: string - request uri
        :return:    string - decoded response
        """
        self.send_request(uri)

        content = b''
        while True:
            try:
                content += self.get_chunk()
            except ReadResponseException:
                break

        return content.decode()

    def send_request(self, uri):
        """
        Send prepared request to a server
        :param uri: string - request uri
        """
        try:
            self._connection.request('GET', uri, headers=self._headers)
            self._response = self._connection.getresponse()
        except client.BadStatusLine:
            self._connect()
            self.send_request(uri)

    def get_header(self, name):
        """
        Get response header
        :param name: string - header name
        :return:     string - header value
        """
        return self._response.getheader(name)

    def get_chunk(self, size=HTTP_CLIENT_CHUNK_SIZE):
        """
        Get next chunk of response data
        :param size: int    - chunk size to fetch at once
        :return:     binary - response chunk
        """
        chunk = None
        if not self._response.closed:
            chunk = self._response.read(size)
        if not chunk:
            raise ReadResponseException

        return chunk

    def close(self):
        """
        Close connection
        """
        self._connection.close()

    def set_header(self, header, value):
        """
        Set value to header specified
        :param header: string - Header name
        :param value: string  - Value
        """
        self._headers[header] = value

    def change_user_agent(self, user_agent):
        """
        Use new user-agent
        :param user_agent: string - User-Agent
        """
        self.set_header('User-Agent', user_agent)
