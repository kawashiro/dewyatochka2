# -*- coding: UTF-8

""" SQLite storage, common logic

Classes
=======
    Storage             -- Cartoons storage
    Cartoon             -- Cartoon representation
    CartoonTitle        -- Cartoon title representation
    CartoonConverter    -- Converts remote cartoon data to local one
    SyncIntervalChecker -- Checks sync time interval
    XmlDataSource       -- XML cartoons source
    WebXMLDataSource    -- External XML data source
    CartoonMeta         -- Cartoon metadata
    CartoonTitleMeta    -- Cartoon title metadata

Attributes
==========
    RemoteCartoon      -- Remote cartoon structure
    RemoteCartoonTitle -- Remote cartoon title structure

Functions
=========
    import_data -- Update cartoons database from data source specified
"""

import os
import re
import time
import struct
import locale
import random
from collections import namedtuple

from lxml import etree
from sqlalchemy import Table, Column, Integer, String, UniqueConstraint, ForeignKey, desc
from sqlalchemy.orm import relationship

from dewyatochka.core.data.database import SQLIteStorage, StoreableObject, ObjectMeta, readable_query, writable_query
from dewyatochka.core.utils.http import WebClient


__all__ = ['Storage', 'Cartoon', 'CartoonTitle', 'RemoteCartoon', 'RemoteCartoonTitle',
           'CartoonConverter', 'SyncIntervalChecker', 'XmlDataSource', 'WebXMLDataSource',
           'import_data', 'CartoonMeta', 'CartoonTitleMeta']


# Remote data structures
RemoteCartoon = namedtuple('AniDBCartoon', ['id', 'titles'])
RemoteCartoonTitle = namedtuple('AniDBCartoonTitle', ['title', 'type', 'lang'])


class Storage(SQLIteStorage):
    """ Cartoons storage """

    # Default path to db file
    _DEFAULT_DB_PATH = '/var/lib/dewyatochka/ani.db'

    def __init__(self):
        """ Init sqlite storage """
        super().__init__()

        self.__last_cartoon = None

    @writable_query
    def add_cartoon(self, cartoon, commit=True):
        """ Add a new cartoon

        :param Cartoon cartoon: Cartoon db object
        :param bool commit: Commit changes to db or not
        :return None:
        """
        self.db_session.add(cartoon)
        self.db_session.add_all(cartoon.titles)

        if commit:
            self.db_session.commit()

    @property
    @readable_query
    def last_cartoon(self):
        """ Get the last cartoon. Raise runtime error is storage is empty

        :return Cartoon:
        """
        if self.__last_cartoon is None:
            self.__last_cartoon = self.db_session.query(Cartoon).order_by(desc(Cartoon.id)).first()
            if self.__last_cartoon is None:
                raise RuntimeError('Storage is empty')

        return self.__last_cartoon

    @property
    @readable_query
    def random_cartoon(self):
        """ Get a random cartoon

        :return Cartoon:
        """
        return self.db_session \
            .query(Cartoon) \
            .filter(Cartoon.id == random.randint(1, self.last_cartoon.id)) \
            .order_by(Cartoon.id) \
            .first()


class CartoonTitleMeta(ObjectMeta):
    """ Cartoon title metadata """

    @property
    def _table(cls) -> Table:
        """ Get table associated with metadata

        :param type cls: Obj class
        :return Table:
        """
        return Table('titles', Storage.metadata,
                     Column('id', Integer, primary_key=True),
                     Column('cartoon_aid', Integer, ForeignKey('cartoons.aid')),
                     Column('title', String(255)))


class CartoonTitle(StoreableObject, metaclass=CartoonTitleMeta):
    """ Cartoon title representation """

    # noinspection PyShadowingBuiltins
    def __init__(self, id=None, cartoon_aid=None, title=None):
        """ Init object

        :param int id:
        :param int cartoon_aid:
        :param str title:
        """
        super().__init__(id=id, cartoon_aid=cartoon_aid, title=title)


class CartoonMeta(ObjectMeta):
    """ Cartoon metadata """

    @property
    def _table(cls) -> Table:
        """ Get table associated with metadata

        :param type cls: Obj class
        :return Table:
        """
        return Table('cartoons', Storage.metadata,
                     Column('id', Integer, primary_key=True),
                     Column('aid', Integer),
                     Column('primary_title', String(255)),
                     UniqueConstraint('aid'))

    @property
    def _mapping_properties(cls) -> dict:
        """ Get object mapping properties

        :return dict:
        """
        return {'titles': relationship(CartoonTitle)}


class Cartoon(StoreableObject, metaclass=CartoonMeta):
    """ Cartoon representation """

    # Cartoon url template
    __URL = 'http://anidb.net/perl-bin/animedb.pl?show=anime&aid=%d'

    # noinspection PyShadowingBuiltins
    def __init__(self, id=None, aid=None, primary_title=None, titles=None):
        """ Init object

        :param int id:
        :param int aid:
        :param str title:
        :param list titles:
        """
        super().__init__(id=id, aid=aid, primary_title=primary_title, titles=titles or [])

    @property
    def url(self) -> str:
        """ Get external url

        :return str:
        """
        return self.__URL % self.aid


class CartoonConverter:
    """ Converts remote cartoon data to local one """

    # English-translated title
    _TITLE_LANG_EN = 'en'

    # English transliterated title regexp
    _TITLE_LANG_TRANSLIT = re.compile(r'^x-[a-z]+t$', re.I)

    # Titles types
    _TITLE_TYPE_SHORT = 'short'
    _TITLE_TYPE_SYNONYM = 'syn'
    _TITLE_TYPE_MAIN = 'main'
    _TITLE_TYPE_OFFICIAL = 'official'

    # Types relevancy for main title determination (lowest first)
    _TITLE_TYPES_RELEVANCY = (
        _TITLE_TYPE_SHORT,
        _TITLE_TYPE_SYNONYM,
        _TITLE_TYPE_MAIN,
        _TITLE_TYPE_OFFICIAL
    )

    def convert(self, cartoon: RemoteCartoon) -> Cartoon:
        """ Convert data

        :param RemoteCartoon cartoon: Remote cartoon
        :return Cartoon:
        """
        if not len(cartoon.titles):
            raise ValueError('Cartoon must have at least one title')

        try:
            lang = locale.getlocale()[0].split('_')[0]
        except IndexError:
            lang = ''

        main_title = ''
        other_titles = set()
        title_index = 0
        last_relevancy = 0

        for title, t_type, t_lang in cartoon.titles:
            try:
                type_relevancy = self._TITLE_TYPES_RELEVANCY.index(t_type) + 1
            except ValueError:
                type_relevancy = 0
            lang_relevancy = (int(t_lang == lang) << 2) + \
                             (int(t_lang == self._TITLE_LANG_EN) << 1) + \
                             (int(self._TITLE_LANG_TRANSLIT.match(t_lang) is not None))
            title_relevancy = (lang_relevancy << 16) + (type_relevancy << 8) + title_index
            if title_relevancy >= last_relevancy:
                main_title = title
                last_relevancy = title_relevancy
            other_titles.add(title)
            title_index -= 1

        return Cartoon(
            aid=cartoon.id,
            primary_title=main_title,
            titles=[CartoonTitle(cartoon_aid=cartoon.id, title=t) for t in other_titles]
        )


class SyncIntervalChecker:
    """ Checks sync time interval """

    # Sync params
    _DB_SYNC_TIME_FILE_EXT = '.last'
    _DB_SYNC_MIN_INTERVAL = 86400  # AniDB limitations

    def __init__(self, related_file: str):
        """ Init checker

        :param str related_file:
        """
        self.__file_path = related_file + self._DB_SYNC_TIME_FILE_EXT
        self.__modified_at = None

    @property
    def __file_flags(self) -> str:
        """ Get file open flags

        :return str:
        """
        return 'rb+' if os.path.isfile(self.__file_path) else 'xb+'

    @property
    def modified_at(self) -> int:
        """ Get modification time timestamp

        :return int:
        """
        if self.__modified_at is not None:
            return self.__modified_at

        with open(self.__file_path, self.__file_flags) as sync_file:
            try:
                # noinspection PyTypeChecker
                self.__modified_at, = struct.unpack('i', sync_file.read())
            except struct.error:
                self.__modified_at = -1

        return self.__modified_at

    @modified_at.setter
    def modified_at(self, modified_at: int):
        """ Set modification time

        :param int modified_at: Timestamp
        :return None:
        """
        with open(self.__file_path, self.__file_flags) as sync_file:
            sync_file.seek(0)
            sync_file.truncate()
            sync_file.write(struct.pack('i', modified_at))

        self.__modified_at = modified_at

    def is_outdated(self, now=None) -> bool:
        """ Check if file is outdated relating on time specified

        :param int now: Current timestamp
        :return bool:
        """
        current_time = now or int(time.time())
        return current_time > self.modified_at + self._DB_SYNC_MIN_INTERVAL


class XmlDataSource:
    """ XML cartoons source """

    # XML attributes
    _XML_ATTR_ID = 'aid'
    _XML_ATTR_TYPE = 'type'
    _XML_ATTR_LANG = '{http://www.w3.org/XML/1998/namespace}lang'
    _XML_XPATH_CARTOONS = '/anime'
    _XML_XPATH_TITLES = 'title'

    # Default file name
    _DB_SYNC_XML_FILE_NAME = 'animetitles.xml.gz'

    def __init__(self, xml_file=None):
        """ Init data source

        :param str xml_file:
        """
        self._file = xml_file or os.path.dirname(Storage().path) + str(os.sep) + self._DB_SYNC_XML_FILE_NAME

    @property
    def file(self) -> str:
        """ File path getter

        :return str:
        """
        return self._file

    @property
    def cartoons(self) -> list:
        """ Get cartoons list

        :return list:
        """
        result = []
        for anime_el in etree.parse(self._file).findall(self._XML_XPATH_CARTOONS):
            aid = int(anime_el.attrib[self._XML_ATTR_ID])
            titles = [RemoteCartoonTitle(e.text, e.attrib[self._XML_ATTR_TYPE], e.attrib[self._XML_ATTR_LANG])
                      for e in anime_el.findall(self._XML_XPATH_TITLES)]
            result.append(RemoteCartoon(aid, titles))

        return result


class WebXMLDataSource(XmlDataSource):
    """ External XML data source """

    # Remote file location
    _ANI_DB_REMOTE_HOST = 'anidb.net'
    _ANI_DB_REMOTE_URL = '/api/animetitles.xml.gz'

    def download(self):
        """ Download external file

        :return None:
        """
        with WebClient(self._ANI_DB_REMOTE_HOST) as web_client:
            xml_data = web_client.get(self._ANI_DB_REMOTE_URL)

        with open(self._file, 'wb') as xml_file:
            xml_file.write(xml_data)


def import_data(source: XmlDataSource) -> int:
    """ Update cartoons database from data source specified

    :param XmlDataSource source: Cartoon source
    :return int:
    """
    cartoons_storage = Storage()  # Singleton
    cartoons_converter = CartoonConverter()

    cartoons_total = 0
    for cartoon in source.cartoons:
        cartoons_storage.add_cartoon(cartoons_converter.convert(cartoon), commit=False)
        cartoons_total += 1

    cartoons_storage.commit()

    return cartoons_total
