# -*- coding: UTF-8

""" AniDB import logic

Functions
=========
    parse_xml_file  -- Get list of AniDBCartoon from xml-file
    import_xml_file -- Load new xml file
    fetch_xml_file  -- Fetch new xml file if needed
    update_database -- Update database from remote file
"""

__all__ = ['parse_xml_file', 'import_xml_file', 'fetch_xml_file', 'update_database']

import os
import struct
import time

from lxml import etree

from dewyatochka.core.utils.http import WebClient
from dewyatochka.core.plugin.base import PluginLogService

from .model import RemoteCartoon, RemoteCartoonTitle
from .entry import StorageHelper


# Remote file location
_ANI_DB_REMOTE_HOST = 'anidb.net'
_ANI_DB_REMOTE_URL = '/api/animetitles.xml.gz'

# Sync params
_DB_SYNC_TIME_FILE_EXT = '.last'
_DB_SYNC_MIN_INTERVAL = 86400  # AniDB limitations
_DB_SYNC_XML_FILE_NAME = 'animetitles.xml.gz'

# XML attributes
_XML_ATTR_ID = 'aid'
_XML_ATTR_TYPE = 'type'
_XML_ATTR_LANG = '{http://www.w3.org/XML/1998/namespace}lang'
_XML_XPATH_CARTOONS = '/anime'
_XML_XPATH_TITLES = 'title'


def parse_xml_file(file) -> list:
    """ Get list of AniDBCartoon from xml-file

    :param object file: File-like object or string (file path)
    :return list:
    """
    result = []
    for anime_el in etree.parse(file).findall(_XML_XPATH_CARTOONS):
        aid = int(anime_el.attrib[_XML_ATTR_ID])
        titles = [RemoteCartoonTitle(e.text, e.attrib[_XML_ATTR_TYPE], e.attrib[_XML_ATTR_LANG])
                  for e in anime_el.findall(_XML_XPATH_TITLES)]
        result.append(RemoteCartoon(aid, titles))

    return result


def import_xml_file(file_path: str, log: PluginLogService):
    """ Load new xml file

    :param str file_path: Path to XML file
    :param PluginLogService log: Logger instance
    :return None:
    """
    def _add_cartoons_task(storage):
        """ Insert all the cartoons into db """
        for cartoon in cartoons:
            storage.add_cartoon(cartoon, commit=False)

    log.info('Parsing cartoons file %s', file_path)
    cartoons = parse_xml_file(file_path)
    log.info('Found %d cartoons', len(cartoons))

    log.debug('Waiting for storage helper\'s queue to be empty')
    StorageHelper.stop()

    log.debug('Adding cartoons to storage queue')
    StorageHelper.run_task(lambda s: s.recreate(), background=True)
    StorageHelper.run_task(_add_cartoons_task, background=True)
    StorageHelper.run_task(lambda s: s.db_session.commit(), background=True)

    log.debug('Resuming storage helper')
    StorageHelper.resume()


def fetch_xml_file(file_path, log: PluginLogService) -> bool:
    """ Fetch new xml file if needed

    :param str file_path: Path to save file to
    :param PluginLogService log: Logger instance
    :return bool:
    """
    sync_file_path = file_path + _DB_SYNC_TIME_FILE_EXT
    sync_file_flags = 'rb+' if os.path.isfile(sync_file_path) else 'xb+'
    with open(sync_file_path, sync_file_flags) as sync_file:
        try:
            # noinspection PyTypeChecker
            sync_time, = struct.unpack('i', sync_file.read())
        except struct.error:
            sync_time = 0

        current_time = int(time.time())
        if current_time < sync_time + _DB_SYNC_MIN_INTERVAL:
            log.info('Only %d seconds passed after the last successful cartoons sync', current_time - sync_time)
            return False

        log.info('Downloading xml-file from http://%s%s to %s', _ANI_DB_REMOTE_HOST, _ANI_DB_REMOTE_URL, file_path)
        with WebClient(_ANI_DB_REMOTE_HOST) as web_client:
            xml_data = web_client.get(_ANI_DB_REMOTE_URL)

        with open(file_path, 'wb') as xml_file:
            xml_file_len = xml_file.write(xml_data)

        sync_file.seek(0)
        sync_file.truncate()
        sync_file.write(struct.pack('i', current_time))
        sync_file.close()
        log.info('Downloaded successfully (%d bytes)', xml_file_len)

    return True


def update_database(log: PluginLogService):
    """ Update database from remote file

    :param PluginLogService log: Logger instance
    :return None:
    """
    xml_file_path = os.path.dirname(StorageHelper.run_task(lambda s: s.path)) + str(os.sep) + _DB_SYNC_XML_FILE_NAME

    log.info('Starting cartoons DB sync')
    if fetch_xml_file(xml_file_path, log):
        import_xml_file(xml_file_path, log)
        log.info('Synchronized successfully')
    else:
        log.info('Synchronisation is not needed')
