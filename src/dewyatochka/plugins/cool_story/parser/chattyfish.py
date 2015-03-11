# -*- coding: UTF-8

""" Parsers for ChattyFish Ltd. projects

Classes
=======
    ZadolbaLiParser -- zadolba.li html parser
    ItHappensParser -- ithappens.me html parser
"""

__all__ = ['ZadolbaLiParser', 'ItHappensParser']

from abc import abstractproperty

from lxml.html import HtmlElement
from pyquery import PyQuery

from ._base import *


class _BaseParser(AbstractParser):
    """ Common ChattyFish logic (all projects use the same markup) """

    @abstractproperty
    def _web_host(self) -> str:
        """ Remote server hostname

        :return str:
        """
        pass

    def _parse_posts_collection(self, html: PyQuery) -> list:
        """ Get posts HTMLElement[] collection

        :param PyQuery html: Page PyQuery object
        :return list:
        """
        return html('div.story[id^="story-"]')

    def _parse_pages_collection(self, html: PyQuery) -> list:
        """ Get pages urls for indexation

        :param PyQuery html: Page PyQuery object
        :return list:
        """
        try:
            prev_page = html('div.nav-common li.prev a')[0].attrib['href']
            pages_links = [link.attrib['href']
                           for link in reversed(list(html('div.nav-common a'))[1:3])
                           if link.attrib['href'] < prev_page]
            pages_links.insert(0, prev_page)
        except IndexError:
            pages_links = []  # No lins at this page

        return pages_links

    def _parse_post(self, html_element: HtmlElement) -> RawPost:
        """ Parse post html element

        :param HTMLElement html_element:
        :return RawPost:
        """
        post_pyq_el = PyQuery(html_element)

        story_id = int(post_pyq_el('div.id span')[0].text)
        story_title = post_pyq_el('h2 a')[0].text
        tags = frozenset(tag.text.strip() for tag in post_pyq_el('div.tags a'))
        story_text = parse_multiline_html(post_pyq_el('div.text p'))

        return RawPost(story_id, self.name, story_title, story_text, tags)


class ZadolbaLiParser(_BaseParser):
    """ zadolba.li html parser """

    @property
    def _web_host(self) -> str:
        """ Remote server hostname

        :return str:
        """
        return 'zadolba.li'


class ItHappensParser(_BaseParser):
    """ ithappens.me html parser """

    @property
    def _web_host(self) -> str:
        """ Remote server hostname

        :return str:
        """
        return 'ithappens.me'
