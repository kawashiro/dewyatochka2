# -*- coding: UTF-8

""" Database access

Classes
=======
    ObjectMeta          -- Abstract metaclass for ORM objects
    StoreableObject     -- Object storeable in db
    CacheableObject     -- Object statically cached by some unique key
    UnmappedFieldError  -- Error on access to undefined object field
    StorageMeta         -- Abstract metaclass for storage implementations
    AbstractStorage     -- Very abstract storage
    SQLIteStorage       -- SQLIte based storage
"""

__all__ = ['ObjectMeta', 'StoreableObject', 'CacheableObject', 'UnmappedFieldError',
           'StorageMeta', 'AbstractStorage', 'SQLIteStorage']


import os
from abc import ABCMeta, abstractproperty

from sqlalchemy import Table, MetaData, create_engine
from sqlalchemy.orm import mapper, sessionmaker, Session


class UnmappedFieldError(AttributeError):
    """ Error on access to undefined object field """
    pass


class ObjectMeta(type, metaclass=ABCMeta):
    """ Abstract metaclass for ORM objects """

    def __init__(cls, what, bases=None, dict_=None):
        """ Create a mapped class

        :param str what:
        :param type bases:
        :param dict dict_:
        """
        super().__init__(what, bases, dict_)
        mapper(cls, cls._table, cls._mapping_properties)

    @property
    def _mapping_properties(cls) -> dict:
        """ Get object mapping properties

        :return dict:
        """
        return {}

    @abstractproperty
    def _table(cls) -> Table:
        """ Get table associated with metadata

        :param type cls: Obj class
        :return Table:
        """
        pass

    def __getattr__(cls, item):
        """ Raise a special exception on not existent attribute

        :param str item:
        :return None:
        """
        raise UnmappedFieldError('Field %s is not mapped to an object %s' % (item, cls))


class StoreableObject():
    """ Object storeable in db """

    # Primary key
    _primary = 'id'

    def __init__(self, **kwargs):
        """ Init object

        :param dict kwargs:
        """
        for field in kwargs:
            setattr(self, field, kwargs[field])

    @property
    def stored(self) -> bool:
        """ Is flag stored in db

        :return bool:
        """
        try:
            stored = getattr(self, self._primary) is not None
        except AttributeError:
            stored = False

        return stored


class CacheableObject(StoreableObject):
    """ Object statically cached by some unique key """

    # Cached tags by title
    _cache = {}

    # Unique key (field name)
    _key = None

    def __init__(self, **kwargs):
        """ Init object

        :param dict kwargs:
        """
        if self._key not in kwargs or kwargs[self._key] not in self._cache:
            # Do not re-init object if it is a cached instance
            super().__init__(**kwargs)

    def __new__(cls, **kwargs):
        """ Get cached tag instance instead of creating a new one

        :param dict kwargs:
        """
        try:
            return cls._cache[kwargs[cls._key]]
        except KeyError:  # Unique key is not defined or an object is not cached yet
            pass

        return super().__new__(cls)


class StorageMeta(ABCMeta):
    """ Abstract metaclass for storage implementations """

    def __init__(cls, what, bases=None, dict_=None):
        """ Create metadata instance

        :param str what:
        :param type bases:
        :param dict dict_:
        """
        super().__init__(what, bases, dict_)
        cls.__metadata = MetaData()

    @property
    def metadata(cls):
        """ Get MetaData instance

        :param AbstractStorageMeta cls: self
        :return MetaData:
        """
        return cls.__metadata


class AbstractStorage(metaclass=StorageMeta):
    """ Very abstract storage """

    def __init__(self):
        """ Init storage """
        self.__db_session = None

    @property
    def db_session(self) -> Session:
        """ Get DB session

        :return Session:
        """
        if self.__db_session is None:
            self.__db_session = sessionmaker(
                bind=create_engine(self._dsn)
            )()

        return self.__db_session

    @abstractproperty
    def _dsn(self) -> str:
        """ Get db connection dsn

        :return str:
        """
        pass

    def recreate(self):
        """ Recreate engine

        :return None:
        """
        # noinspection PyUnresolvedReferences
        self.__class__.metadata.create_all(bind=self.db_session.get_bind())

    def __enter__(self):
        """ __enter__()

        :return Storage:
        """
        return self

    def __exit__(self, *_) -> bool:
        """ Close session on exit

        :param tuple _:
        :return bool:
        """
        self.db_session.close()
        return False


class SQLIteStorage(AbstractStorage):
    """ SQLIte based storage """

    def __init__(self, file):
        """ Init sqlite storage

        :param str file:
        """
        super().__init__()
        self.__file = os.path.realpath(file)

    @property
    def _dsn(self) -> str:
        """ Get db connection dsn

        :return str:
        """
        return 'sqlite:///%s' % self.__file

    @property
    def path(self) -> str:
        """ Get path to db

        :return str:
        """
        return self.__file

    def recreate(self):
        """ Recreate engine

        :return None:
        """
        self.db_session.close()

        if os.path.isfile(self.path):
            os.unlink(self.path)

        super().recreate()
