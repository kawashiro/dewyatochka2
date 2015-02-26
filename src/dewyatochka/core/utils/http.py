# -*- coding: UTF-8

""" Client for web browsing

Classes
=======
    WebClient -- Simple high-level HTTP-client for browsing

Attributes
==========
    TYPE_HTML -- text/html
    TYPE_JSON -- application/json
    TYPE_TEXT -- text/plain
"""

__all__ = ['WebClient']

from http.client import HTTPConnection, HTTPSConnection
from urllib.parse import urlencode
import json
from html.parser import HTMLParser

from dewyatochka import __version__

try:
    from pyquery import PyQuery

except ImportError:
    class PyQuery():
        """ Just a stub """
        def __init__(self, html):
            self._html = html

        def __call__(self, *_):
            """ Runtime error on selector assign attempt """
            raise RuntimeError('PyQuery is not installed')

        def __str__(self) -> str:
            """ Allow to fetch raw html as a fallback """
            return self._html


# Default user agent to use
_DEFAULT_USER_AGENT = 'Dewyatochka/%s' % __version__

# Content-types
TYPE_HTML = 'text/html'
TYPE_JSON = 'application/json'
TYPE_TEXT = 'text/plain'


def _parse_content_type_enc(content_type: str, default=None) -> str:
    """ Get encoding from content-type value

    :param str content_type:
    :param str default:
    :return str:
    """
    for item in content_type.split(';'):
        item = item.strip()
        if item.startswith('charset='):
            return item[8:]
    else:
        return default


def _get_http_encoding(headers: dict, default='UTF-8') -> str:
    """ Get encoding from headers

    :param dict headers:
    :param str default:
    :return str:
    """
    content_type = headers.get('Content-Type', '')
    return _parse_content_type_enc(content_type, default)


def _text_parser(content, headers: dict) -> str:
    """ bytes -> str

    :param bytes content:
    :param dict headers:
    :return str:
    """
    return content.decode(_get_http_encoding(headers))


def _json_parser(content: bytes, headers: dict):
    """ str -> any (content dependent)

    :param bytes content:
    :param dict headers:
    :returns: Content dependent
    """
    encoding = _get_http_encoding(headers)
    return json.loads(content.decode(encoding), encoding)


def _html_parser(content, headers: dict) -> PyQuery:
    """ str -> PyQuery parser or a stub

    :param str content:
    :param dict headers:
    :return PyQuery:
    """
    class _HTMLParser(HTMLParser):
        """ Private html parser implementation """

        __html_encoding = None

        def handle_starttag(self, tag: str, attrs: list):
            """ Handle start tag
            :param str tag: Tag name
            :param list attrs: Attributes
            """
            if self.__html_encoding or tag.lower() != 'meta':
                return  # FIXME: Completely break when encoding is found

            attrs_dict = dict(attrs)
            if attrs_dict.get('http-equiv') != 'Content-Type':
                return

            self.__html_encoding = _parse_content_type_enc(attrs_dict.get('content', ''))

        @property
        def encoding(self) -> str:
            """ Get parsed encoding value
            :return str:
            """
            return self.__html_encoding

    # Try to get encoding from headers, use 1-byte encoding by default
    http_encoding = _get_http_encoding(headers, 'iso-8859-1')
    str_content = content.decode(http_encoding, 'ignore')

    # Try to get encoding from html-doc and if it differs use it for strict decoding
    html_parser = _HTMLParser()
    html_parser.feed(str_content)
    if html_parser.encoding and html_parser.encoding != http_encoding:
        str_content = content.decode(html_parser.encoding)

    return PyQuery(str_content)


def _get_parser(content_type: str) -> callable:
    """ Get content parser by content type numeric code

    :param str content_type:
    :return callable:
    """
    return {
        TYPE_TEXT: _text_parser,
        TYPE_HTML: _html_parser,
        TYPE_JSON: _json_parser,
    }.get(content_type, lambda c, *_: c)


class WebClient:
    """ Simple high-level HTTP-client for browsing """

    def __init__(self, host, port=None, https=False):
        """ Init client, create initial headers set

        :param str host: Remote server host
        :param int port: int Remote server port
        :param bool https: Use HTTPS instead of HTTP
        """
        self._headers = {'Accept': 'text/html,application/xhtml+xml,application/xml,text/plain',
                         'Connection': 'keep-alive', 'Host': host, 'User-Agent': _DEFAULT_USER_AGENT}
        self._connection = (HTTPSConnection if https else HTTPConnection)(host, port)

    def get(self, uri, query=None, content_type=None):
        """ Get content by uri

        :param str uri: Request uri
        :param dict query: Query params
        :param str content_type: Expected content-type
        :returns: Depends on content type expected
        """
        if query is not None:
            uri = '?'.join([uri, urlencode(query)])

        self._connection.request('GET', uri, headers=self._headers)
        response = self._connection.getresponse()

        content = response.read()
        headers = dict(response.getheaders())
        content_type = content_type or response.getheader('Content-Type').split(';')[0].strip()

        if content_type:
            content = _get_parser(content_type)(content, headers)

        return content

    def user_agent(self, user_agent: str):
        """  Set new user agent string

        :param str user_agent: New user-agent
        :return None:
        """
        self._headers['User-Agent'] = user_agent

    def connect(self):
        """ Establish connection

        :return None:
        """
        self._connection.connect()

    def close(self):
        """ Close connection

        :return None:
        """
        self._connection.close()

    def __enter__(self):
        """ Do nothing

        :return None:
        """
        return self

    def __exit__(self, *_) -> bool:
        """ Close connection on exit

        :param tuple _:
        :return bool:
        """
        self.close()
        return False
