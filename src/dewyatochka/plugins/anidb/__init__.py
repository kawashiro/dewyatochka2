# -*- coding: UTF-8

""" Suggests cartoons from anidb.net

Modules
=======
    model -- SQLite storage, common logic
"""

import time

from dewyatochka.core import plugin
from dewyatochka.core.config.exception import SectionRetrievingError

from . import model

__all__ = ['model']


@plugin.bootstrap
def init_storage(registry):
    """ Set storage params

    :param registry:
    :return None:
    """
    db_path = registry.config.get('db_path')
    if db_path:
        model.Storage().path = db_path

    model.Storage().create()


@plugin.control('import-file', 'Update cartoons database from xml file specified')
def import_file(inp, outp, **_):
    """ Update cartoons database from xml file specified

    :param inp:
    :param outp:
    :param _:
    :return None:
    """
    data_source = model.XmlDataSource(inp.args.get('xml'))

    outp.say('Importing cartoons from file "%s"', data_source.file)
    cartoons_total = model.import_data(data_source)
    outp.say('Imported %d cartoons', cartoons_total)


@plugin.control('recreate', 'Create a new empty cartoons db')
def recreate(outp, **_):
    """ Create a new empty db

    :param outp:
    :param _:
    :return None:
    """
    model.Storage().recreate()
    outp.info('Cartoons storage successfully recreated at %s', model.Storage().path)


@plugin.schedule('@daily')
@plugin.control('update', 'Update database')
def update(**kwargs):
    """ Update DB

    :param dict kwargs: Entry point dependent
    :return None:
    """
    log = kwargs.get('outp') or kwargs.get('registry').log
    current_time = int(time.time())

    data_source = model.WebXMLDataSource()
    interval_checker = model.SyncIntervalChecker(data_source.file)

    if interval_checker.is_outdated(current_time):
        recreate(outp=log)
        log.info('Updating cartoons DB from web')
        data_source.download()
        cartoons_total = model.import_data(data_source)
        interval_checker.modified_at = current_time
        log.info('Imported %d cartoons', cartoons_total)

    else:
        log.info('Only %d seconds passed after the last successful cartoons sync',
                 current_time - interval_checker.modified_at)


@plugin.chat_command('cartoon')
def cartoon_command_handler(inp, outp, registry):
    """ Yield a random cartoon

    :param inp:
    :param outp:
    :param registry:
    :return None:
    """
    template = registry.config.get('message')
    if not template:
        raise SectionRetrievingError('`message` config param is required for AniDB plugin')

    cartoon = model.Storage().random_cartoon
    msg_params = {'user': inp.sender.resource, 'title': cartoon.primary_title, 'url': cartoon.url}

    outp.say(template.format(**msg_params))
