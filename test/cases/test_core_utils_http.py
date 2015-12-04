# -*- coding=utf-8

""" Tests suite for dewyatochka.core.utils.http """

import unittest
from unittest.mock import patch, call

from dewyatochka.core.utils.http import *
from dewyatochka import __version__


class TestWebClient(unittest.TestCase):
    """ Tests suite for dewyatochka.core.utils.http.WebClient """

    @patch('dewyatochka.core.utils.http.HTTPConnection')
    @patch('dewyatochka.core.utils.http.HTTPSConnection')
    def test_connection(self, https_connection_mock, http_connection_mock):
        """ Test connection management """
        with WebClient('localhost', 123):
            http_connection_mock.assert_called_once_with('localhost', 123)
            http_connection_mock().connect.assert_called_once_with()
        http_connection_mock().close.assert_called_once_with()

        with WebClient('localhost', 123, https=True):
            https_connection_mock.assert_called_once_with('localhost', 123)
            https_connection_mock().connect.assert_called_once_with()
        https_connection_mock().close.assert_called_once_with()

    @patch('dewyatochka.core.utils.http.HTTPConnection')
    def test_get_raw(self, http_connection_class_mock):
        """ Test raw content download """
        raw_content_mock = b'\xCA\xFE\xBA\xBE'
        http_connection_mock = http_connection_class_mock()
        http_connection_mock.getresponse.return_value = raw_content_mock

        # Default params
        self.assertEqual(WebClient('localhost').get_raw('/foo'), raw_content_mock)
        # New user agent + query params
        web_client = WebClient('localhost')
        web_client.user_agent('NewUserAgent')
        self.assertEqual(web_client.get_raw('/foo', {'%bar': '?baz&'}), raw_content_mock)

        http_connection_mock.request.assert_has_calls([
            call('GET', '/foo', headers={
                'Host': 'localhost',
                'User-Agent': 'Dewyatochka/%s' % __version__,
                'Connection': 'keep-alive',
                'Accept': 'text/html,application/xhtml+xml,application/xml,text/plain,application/json'
            }),
            call('GET', '/foo?%25bar=%3Fbaz%26', headers={
                'Host': 'localhost',
                'User-Agent': 'NewUserAgent',
                'Connection': 'keep-alive',
                'Accept': 'text/html,application/xhtml+xml,application/xml,text/plain,application/json'
            })
        ])
        self.assertEqual(http_connection_mock.getresponse.call_count, 2)

    @staticmethod
    def _setup_response(connection_mock, body, content_type=None):
        """ Setup connection mock for return value needed

        :param Mock connection_mock:
        :param any body:
        :param str content_type:
        :return None:
        """
        response_mock = connection_mock().getresponse()
        response_mock.read.return_value = body
        if content_type is not None:
            response_mock.getheaders.return_value = [('Content-Type', content_type)]
            response_mock.getheader.side_effect = (lambda h: content_type if h == 'Content-Type' else None)

    @patch('dewyatochka.core.utils.http.HTTPConnection')
    def test_parsers(self, http_connection_mock):
        """ Test content-type detecting """
        self._setup_response(http_connection_mock, b'{"foo": "bar"}')
        self.assertDictEqual(WebClient('localhost').get('/', content_type='application/json'), {'foo': 'bar'})

        self._setup_response(http_connection_mock, b'{"foo": "bar"}')
        self.assertEqual(WebClient('localhost').get('/', content_type='text/plain'), '{"foo": "bar"}')

        self._setup_response(
            http_connection_mock,
            b'''
                <!DOCTYPE html>
                <html>
                    <head>
                        <title>Hello, world!</title>
                        <meta name="Generator" content="Microsoft FrontPage 4.0" />
                        <meta http-equiv="Content-Type" content="text/plain; charset=cp1251" />
                    </head>
                    <body>
                        \xCF\xF0\xE8\xE2\xE5\xF2, \xEC\xE8\xF0!!
                    </body>
                </html>
            ''',
            'text/html'
        )
        document_text = WebClient('localhost').get('/')('body')[0].text.strip()
        self.assertEqual(document_text, 'Привет, мир!!')
