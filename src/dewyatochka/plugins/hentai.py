# -*- coding: UTF-8

""" e-hentai galleries adapter (simple search by keywords) """

import random

from dewyatochka.core.plugin import chat_command

__all__ = []


# Domain to fetch galleries from
_HENTAI_DOMAIN = 'g.e-hentai.org'

# URI to a hentai galleries listing
_HENTAI_SEARCH_PARAMS = {'f_doujinshi': '1',
                         'f_manga':     '1',
                         'f_artistcg':  '0',
                         'f_gamecg':    '0',
                         'f_western':   '0',
                         'f_non-h':     '0',
                         'f_imageset':  '0',
                         'f_cosplay':   '0',
                         'f_asianporn': '0',
                         'f_misc':      '0',
                         'f_srdd':      '5'}


@chat_command('hentai')
def hentai_command_handler(inp, outp, registry):
    """ Handle hentai command

    :param inp:
    :param outp:
    :param registry:
    :return None:
    """
    from dewyatochka.core.utils.http import WebClient
    
    search_keywords = ' '.join(inp.text.split(' ')[1:])
    message_args = {'user': inp.sender.resource, 'keywords': search_keywords}
    hentai_params = _HENTAI_SEARCH_PARAMS.copy()
    hentai_params['f_search'] = search_keywords

    html_doc = WebClient(_HENTAI_DOMAIN).get('/', hentai_params)
    galleries = [(el.attrib['href'], el.text) for el in html_doc('a[href^="http://%s/g/"]' % _HENTAI_DOMAIN)]

    if galleries:
        gallery_link, gallery_title = galleries[random.randint(0, len(galleries))]
        message_format = registry.config.get('message_found')
        message_args.update({'title': gallery_title, 'url': gallery_link})
    else:
        message_format = registry.config.get('message_not_found')

    if message_format:
        outp.say(message_format.format(**message_args))
    else:
        registry.log.warning('Message format is not defined, command result ignored (cnt: %d)' % len(galleries))
