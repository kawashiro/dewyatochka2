# -*- coding: UTF-8

""" SQLite storage, common logic

Classes
=======
    Storage           -- Cartoons storage
    Cartoon           -- Cartoon representation
    CartoonTitle      -- Cartoon title representation
    StorageHelper     -- Storage helper thread

Attributes
==========
    RemoteCartoon      -- Remote cartoon structure
    RemoteCartoonTitle -- Remote cartoon title structure
"""

import re
import locale
import random
from collections import namedtuple

from sqlalchemy import Table, Column, Integer, String, UniqueConstraint, ForeignKey, desc
from sqlalchemy.orm import relationship
from sqlalchemy.orm.exc import NoResultFound

from dewyatochka.core.data.database import SQLIteStorage, StoreableObject, ObjectMeta
from dewyatochka.core.data.database import StorageHelper as StorageHelperBase

__all__ = ['Storage', 'Cartoon', 'CartoonTitle', 'RemoteCartoon', 'RemoteCartoonTitle']


# Remote data structures
RemoteCartoon = namedtuple('AniDBCartoon', ['id', 'titles'])
RemoteCartoonTitle = namedtuple('AniDBCartoonTitle', ['title', 'type', 'lang'])


class Storage(SQLIteStorage):
    """ Cartoons storage """

    # Default path to db file
    _DEFAULT_DB_PATH = '/var/lib/dewyatochka/ani.db'

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

    def __init__(self, file=None):
        """ Init sqlite storage

        :param str file:
        """
        super().__init__(file or self._DEFAULT_DB_PATH)
        self.__last_cartoon = None

    def add_cartoon(self, cartoon: RemoteCartoon, commit=True):
        """ Add a new cartoon

        :param RemoteCartoon cartoon: Cartoon tuple
        :param bool commit: Commit changes to db or not
        :return None:
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

        db_titles = [CartoonTitle(cartoon_aid=cartoon.id, title=t) for t in other_titles]
        db_cartoon = Cartoon(aid=cartoon.id, primary_title=main_title, titles=db_titles)

        self.db_session.add(db_cartoon)
        self.db_session.add_all(db_titles)
        if commit:
            self.db_session.commit()

    @property
    def last_cartoon(self):
        """ Get the last cartoon. Raise runtime error is storage is empty

        :return Cartoon:
        """
        if self.__last_cartoon is None:
            try:
                self.__last_cartoon = self.db_session.query(Cartoon).order_by(desc(Cartoon.id)).first()
            except NoResultFound:
                raise RuntimeError('Storage is empty')

        return self.__last_cartoon

    @property
    def random_cartoon(self):
        """ Get a random cartoon

        :return Cartoon:
        """
        return self.db_session \
            .query(Cartoon) \
            .filter(Cartoon.id == random.randint(1, self.last_cartoon.id)) \
            .order_by(Cartoon.id) \
            .first()


class StorageHelper(StorageHelperBase):
    """ Storage helper thread """
    pass


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
