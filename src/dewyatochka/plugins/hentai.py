# -*- coding: UTF-8

"""
e-hentai galleries adapter (simple search by keywords)
"""

__all__ = []

import re
import random
from html.parser import HTMLParser
from urllib import parse as urlparse
from dewyatochka.utils import http
from dewyatochka.core import plugin


# Global config section
_CONFIG_SECTION = 'hentai'

# Domain to fetch galleries from
_HENTAI_DOMAIN = 'g.e-hentai.org'

# URI to a hentai galleries listing
_HENTAI_SEARCH_URI = '/?f_doujinshi=1' \
                     '&f_manga=1' \
                     '&f_artistcg=0' \
                     '&f_gamecg=0' \
                     '&f_western=0' \
                     '&f_non-h=0' \
                     '&f_imageset=0' \
                     '&f_cosplay=0' \
                     '&f_asianporn=0' \
                     '&f_misc=0' \
                     '&f_srdd=5' \
                     '&f_search=%s'

# Regexp to find all galleries in the listing
_galleries_list_regexp = re.compile(r'<td class="itd" onmouseover="preload_pane_image_delayed\(.*?'
                                    r'<a href="([^"]+)" onmouseover="show_image_pane[^>]*>([^<]+)</a>.*?'
                                    r'</td>', re.I)

# HTML parser instance
_html_parser = HTMLParser()


@plugin.chat_command('hentai')
def hentai_command_handler(message, application, **kwargs):
    """
    Handle hentai command
    :param message: dict
    :param application: Application
    :param kwargs: dict
    :return: str|None
    """
    config_section = application.config.section(_CONFIG_SECTION)
    search_keywords = ' '.join(kwargs.get('command_args', []))
    message_args = {'user': message['from'].resource, 'keywords': search_keywords}

    html_result = http.Client(_HENTAI_DOMAIN).get(_HENTAI_SEARCH_URI % urlparse.quote_plus(search_keywords))
    galleries = _galleries_list_regexp.findall(html_result)
    if galleries:
        gallery_link, gallery_title = galleries[random.randint(0, len(galleries))]
        message_format = config_section['message_found']
        message_args.update({
            'title': _html_parser.unescape(gallery_title),
            'url': _html_parser.unescape(gallery_link)
        })
    else:
        message_format = config_section.get('message_not_found')

    return message_format.format(**message_args) if message_format else None
