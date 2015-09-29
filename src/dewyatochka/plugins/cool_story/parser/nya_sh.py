# -*- coding: UTF-8

""" nya.sh html parser

Classes
=======
    Parser -- Parser implementation

Attributes
==========
    NYA_SH_SOURCE_NAME -- Source name constant
"""

import html
from html.parser import HTMLParser

from lxml.html import HtmlElement
from pyquery import PyQuery

from ._base import *

__all__ = ['Parser', 'NYA_SH_SOURCE_NAME']


# Source name constant
NYA_SH_SOURCE_NAME = 'nya.sh'


class Parser(AbstractParser):
    """ nya.sh parser """

    def __init__(self):
        """ Init parser object, create html parser for entities decoding """
        super().__init__()
        self.__html_parser = HTMLParser()

    @property
    def name(self) -> str:
        """ Get unique name

        :return str:
        """
        return NYA_SH_SOURCE_NAME

    def _parse_posts_collection(self, html_: PyQuery) -> list:
        """ Get posts HTMLElement[] collection

        :param PyQuery html_: Page PyQuery object
        :return list:
        """
        return html_('div.q')

    def _parse_pages_collection(self, html_: PyQuery) -> list:
        """ Get pages urls for indexation

        :param PyQuery html_: Page PyQuery object
        :return list:
        """
        pages_links = []
        links_list = html_('div.pages *')

        is_next_link = False
        for link in links_list:
            if is_next_link:
                pages_links.append(link.attrib['href'])
            elif link.tag == 'b':
                is_next_link = True

        return pages_links

    def _parse_post(self, html_element: HtmlElement) -> RawPost:
        """ Parse post html element

        :param HTMLElement html_element:
        :return RawPost:
        """
        post_pyq_el = PyQuery(html_element)

        story_id = int(post_pyq_el('div.sm a b')[0].text.lstrip('#'))
        story_text = html.unescape(parse_multiline_html(post_pyq_el('div.content')))

        return RawPost(story_id, self.name, '', story_text, frozenset())
