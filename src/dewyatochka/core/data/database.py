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
    ThreadSafeSingleton -- Abstract metaclass for singletons implementations

Functions
=========
    readable_query      -- Readable query decorator
    writable_query      -- Writable query decorator
"""

import os
import threading
from abc import ABCMeta, abstractproperty
from functools import wraps

from sqlalchemy import Table, MetaData, create_engine
from sqlalchemy.orm import mapper, sessionmaker, Session, reconstructor

__all__ = ['ObjectMeta', 'StoreableObject', 'CacheableObject', 'UnmappedFieldError',
           'StorageMeta', 'AbstractStorage', 'SQLIteStorage', 'ThreadSafeSingleton',
           'readable_query', 'writable_query']


def __sync_wrapper(method: callable, lock_attrs=()) -> callable:
    """ Wrap a method in thread-safe wrapper

    :param callable method:
    :param tuple lock_attrs:
    :return:
    """
    @wraps(method)
    def _wrapper(self_, *args, **kwargs):
        locks = []
        for lock_attr in lock_attrs:
            try:
                lock = getattr(self_, lock_attr)
            except AttributeError:
                lock = threading.RLock()
                setattr(self_, lock_attr, lock)
            locks.append(lock)

        try:
            for l in locks:
                l.acquire()
            return method(self_, *args, **kwargs)
        finally:
            for l in locks:
                l.release()

    return _wrapper


def readable_query(method: callable) -> callable:
    """ Readable query decorator

    :param callable method: Storage method
    :return: callable
    """
    return __sync_wrapper(method, ('__w_lock',))


def writable_query(method: callable) -> callable:
    """ Writable query decorator

    :param callable method: Storage method
    :return: callable
    """
    return __sync_wrapper(method, ('__w_lock', '__r_lock'))


class UnmappedFieldError(AttributeError):
    """ Error on access to undefined object field """
    pass


class ThreadSafeSingleton(type):
    """ Abstract metaclass for singletons implementations """

    def __init__(cls, what, bases=None, dict_=None):
        """ Create metadata instance

        :param str what:
        :param type bases:
        :param dict dict_:
        """
        super().__init__(what, bases, dict_)

        cls.__instance = None
        cls.__instantiation = threading.Lock()

    def __call__(cls):
        """ Singleton impl """
        with cls.__instantiation:
            if cls.__instance is None:
                cls.__instance = super().__call__()

            return cls.__instance


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


class StoreableObject:
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

    # Cached entities by title
    _cache = None

    # Unique key (field name)
    _key = None

    def __init__(self, **kwargs):
        """ Init object

        :param dict kwargs:
        """
        if self._key not in kwargs or kwargs[self._key] not in self._cache:
            # Do not re-init object if it is a cached instance
            super().__init__(**kwargs)
            self.cache()

    @reconstructor
    def cache(self):
        """ Put self into cache

        :return None:
        """
        self._cache[getattr(self, str(self._key))] = self

    def free(self):
        """ Remove from cache

        :return None:
        """
        try:
            del self._cache[getattr(self, str(self._key))]
        except KeyError:
            pass

    @classmethod
    def get_cached(cls) -> dict:
        """ Get all cached entities

        :return dict:
        """
        return cls._cache or {}

    def __new__(cls, **kwargs):
        """ Get cached tag instance instead of creating a new one

        :param dict kwargs:
        """
        if cls._cache is None:
            cls._cache = {}

        try:
            return cls._cache[kwargs[cls._key]]
        except KeyError:  # Unique key is not defined or an object is not cached yet
            pass

        return super().__new__(cls)


class StorageMeta(ThreadSafeSingleton, ABCMeta):
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
                bind=create_engine(self._dsn, connect_args=self._connect_args)
            )()

        return self.__db_session

    @abstractproperty
    def _dsn(self) -> str:
        """ Get db connection dsn

        :return str:
        """
        pass

    @property
    def _connect_args(self) -> dict:
        """ Additional connection args (engine specific)

        :return dict:
        """
        return {}

    @writable_query
    def commit(self):
        """ Commit changes

        :return None:
        """
        self.db_session.commit()

    def close(self):
        """ Close DB connection

        :return None:
        """
        if self.__db_session:
            self.__db_session.close()
            self.__db_session = None

    @writable_query
    def create(self):
        """ Create engine

        :return None:
        """
        self.close()
        # noinspection PyUnresolvedReferences
        self.__class__.metadata.create_all(bind=self.db_session.get_bind())


class SQLIteStorage(AbstractStorage):
    """ SQLIte based storage """

    # Default path to db file
    _DEFAULT_DB_PATH = None

    def __init__(self):
        """ Init sqlite storage """
        super().__init__()

        self.__file = None
        if self._DEFAULT_DB_PATH:
            self.path = self._DEFAULT_DB_PATH

    @property
    def _dsn(self) -> str:
        """ Get db connection dsn

        :return str:
        """
        return 'sqlite:///%s' % self.__file

    @property
    def _connect_args(self) -> dict:
        """ Additional connection args (engine specific)

        :return dict:
        """
        # ACHTUNG! Extremely undocumented and experimental feature
        # Originally PySQLite is not thread-safe so all the queries
        # MUST be mutexed by __sync_wrapper decorator
        return dict(check_same_thread=False)

    @property
    def path(self) -> str:
        """ Get path to db

        :return str:
        """
        return self.__file

    @path.setter
    def path(self, file: str):
        """ File path setter

        :param str file: DB file path
        :return None:
        """
        new_path = os.path.realpath(file)
        if new_path != self.path:
            self.close()
            self.__file = new_path

    @writable_query
    def create(self):
        """ Create engine

        :return None:
        """
        if not os.path.isfile(self.path):
            super().create()

    @writable_query
    def recreate(self):
        """ Recreate engine

        :return None:
        """
        self.close()

        if os.path.isfile(self.path):
            os.unlink(self.path)

        super().create()
