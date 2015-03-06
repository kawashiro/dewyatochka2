# -*- coding: UTF-8

""" zadolba.li html parser

Functions
=========
    parse_page_url  -- Get stories from page by page num
    parse_page_html -- Parse page's html code and get stories list
    site_iterator   -- Yields all the posts found beginning from the page specified

Attributes
==========
    RawPost -- Raw post immutable structure
"""

__all__ = ['RawPost', 'parse_page_url', 'parse_page_html', 'site_iterator']

import re
from collections import namedtuple
from functools import reduce

from lxml.html import HtmlElement, tostring
from pyquery import PyQuery

from dewyatochka.core.utils.http import WebClient


# Raw post immutable structure (id: int, title: str, text: str, tags: frozenset)
RawPost = namedtuple('RawPost', ('id', 'title', 'text', 'tags'))

# Regexp to extract text from raw post html code
_post_new_line_regexp = re.compile(r'<br\s*/?>', re.I)
_post_sanitize_regexp = re.compile(r'<.*?>')


class _ClientFactory():
    """ Creates http client """

    # Site host
    __HTTP_HOST = 'zadolba.li'

    # Client instance
    __client = None

    @classmethod
    def create(cls) -> WebClient:
        """ Create new client or return instantiated one

        :return WebClient:
        """
        if cls.__client is None:
            cls.__client = WebClient(cls.__HTTP_HOST)

        return cls.__client


def _get_page_url(page: str) -> str:
    """ Get absolute page url by page num

    :param str page:
    :return str:
    """
    return '/%s' % page


def _parse_post(html_element: HtmlElement) -> RawPost:
    """ Parse post html element

    :param HTMLElement html_element:
    :return RawPost:
    """
    post_pyq_el = PyQuery(html_element)

    story_id = int(post_pyq_el('div.id span')[0].text)
    story_title = post_pyq_el('h2 a')[0].text
    tags = frozenset(tag.text.strip() for tag in post_pyq_el('div.tags a'))

    story_text = '\n'.join(
        map(
            lambda line: _post_sanitize_regexp.sub(r'', line),
            reduce(
                lambda msg_lines, lines: msg_lines + lines,
                [_post_new_line_regexp.split(tostring(line, encoding='unicode'))
                 for line in post_pyq_el('div.text p')]
            )
        )
    )

    return RawPost(story_id, story_title, story_text, tags)


def parse_page_url(page: str) -> list:
    """ Get stories from page by page num

    :param str page: Page num (e.g. 20131117)
    :return list:
    """
    return parse_page_html(_ClientFactory.create().get(_get_page_url(page)))


def parse_page_html(html) -> list:
    """ Parse page's html code and get stories list

    :param str|PyQuery html: Page html code or PyQuery object
    :return list:
    """
    html_doc = html if isinstance(html, PyQuery) else PyQuery(html)
    posts_collection = html_doc('div.story[id^="story-"]')

    return [_parse_post(post) for post in posts_collection]


def site_iterator(start_page='') -> RawPost:
    """ Yields all the posts found beginning from the page specified

    :param str start_page: Page num (e.g. 20131117) or empty ti start from beginning
    :return RawPost:
    """
    posts = []
    pages_links = [_get_page_url(start_page)]
    web_client = _ClientFactory.create()
    while True:
        while pages_links:
            current_page = pages_links.pop()
            html_doc = web_client.get(current_page)
            posts = parse_page_html(html_doc)
            if posts:
                prev_page = html_doc('div.nav-common li.prev a')[0].attrib['href']
                pages_links = [link.attrib['href']
                               for link in list(html_doc('div.nav-common a'))[1:3]
                               if link.attrib['href'] < prev_page]
                pages_links.append(prev_page)
                break

        if not posts:
            raise StopIteration()
        while posts:
            yield posts.pop(0)
