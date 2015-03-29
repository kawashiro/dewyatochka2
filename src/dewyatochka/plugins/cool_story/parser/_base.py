# -*- coding: UTF-8

""" Common parsers logic

Classes
=======
    AbstractParser -- Abstract parser

Functions
=========
    parse_multiline_html -- Join html paragraphs collection into one multi line string

Attributes
==========
    RawPost -- Raw post immutable structure
"""

__all__ = ['AbstractParser', 'RawPost', 'parse_multiline_html']

import re
from collections import namedtuple
from functools import reduce
from abc import ABCMeta, abstractmethod, abstractproperty

from lxml.html import HtmlElement, tostring
from pyquery import PyQuery

from dewyatochka.core.utils.http import WebClient


# Raw post immutable structure (id: int, title: str, text: str, tags: frozenset)
RawPost = namedtuple('RawPost', ('id', 'source', 'title', 'text', 'tags'))

# Regexp to extract text from raw post html code
__post_new_line_regexp = re.compile(r'<br\s*/?>', re.I)
__post_sanitize_regexp = re.compile(r'<.*?>')


# Join html paragraphs collection into one multi line string
parse_multiline_html = lambda paragraphs: '\n'. \
    join(
        filter(
            None,
            map(
                lambda line: __post_sanitize_regexp.sub(r'', line).strip(),
                reduce(
                    lambda msg_lines, lines: msg_lines + lines,
                    [__post_new_line_regexp.split(tostring(line, encoding='unicode'))
                     for line in paragraphs]
                )
            )
        )
    )


class AbstractParser(metaclass=ABCMeta):
    """ Parser implementation

    Each parser is an iterable object that yields posts
    beginning from the last and ending on the first post
    """

    def __init__(self):
        """ Init parser object, define mandatory attributes """
        self.__client = None

    @abstractmethod
    def _parse_post(self, html_element: HtmlElement) -> RawPost:
        """ Parse post html element

        :param HTMLElement html_element:
        :return RawPost:
        """
        pass

    @abstractmethod
    def _parse_posts_collection(self, html: PyQuery) -> list:
        """ Get posts HTMLElement[] collection

        :param PyQuery html: Page PyQuery object
        :return list:
        """
        pass

    @abstractmethod
    def _parse_pages_collection(self, html: PyQuery) -> list:
        """ Get pages urls for indexation

        :param PyQuery html: Page PyQuery object
        :return list:
        """
        pass

    def parse_page_html(self, html) -> list:
        """ Parse page's html code and get stories list

        :param str|PyQuery html: Page html code or PyQuery object
        :return list:
        """
        html_doc = html if isinstance(html, PyQuery) else PyQuery(html)
        return [self._parse_post(post) for post in self._parse_posts_collection(html_doc)]

    def parse_page_url(self, page: str) -> list:
        """ Get stories from page by page url

        :param str page: Page url
        :return list:
        """
        return self.parse_page_html(self._client.get(page))

    @property
    def _web_host(self) -> str:
        """ Remote server hostname, normally same as hostname

        :return str:
        """
        return self.name

    @abstractproperty
    def name(self) -> str:
        """ Get unique name

        :return str:
        """
        pass

    @property
    def _client(self) -> WebClient:
        """ Get web client instance

        :return WebClient:
        """
        if self.__client is None:
            # noinspection PyTypeChecker
            self.__client = WebClient(self._web_host)

        return self.__client

    def __iter__(self, start_page='') -> RawPost:
        """ Yields all the posts found beginning from the page specified

        :param str start_page: Page url (e.g. "/20131117") or empty to start from beginning
        :return RawPost:
        """
        posts = []
        pages_links = [start_page or '/']
        while True:
            while pages_links:
                current_page = pages_links.pop(0)
                html_doc = self._client.get(current_page)
                posts = self.parse_page_html(html_doc)
                if posts:
                    pages_links = self._parse_pages_collection(html_doc)
                    break

            if not posts:
                raise StopIteration()
            while posts:
                yield posts.pop(0)
