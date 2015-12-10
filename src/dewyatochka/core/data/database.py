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


def __sync_wrapper_get_attr(obj, attr: str, default):
    """ Get attribute value

    Create attribute if it does not exist

    :param any obj: Target object
    :param str attr: Attribute name
    :param any default: Default value to be assigned
    :return any:
    """
    with __sync_wrapper_get_attr.lock:
        try:
            val = getattr(obj, attr)
        except AttributeError:
            val = default
        setattr(obj, attr, val)
    return val

# Global lock to be used in __sync_wrapper_get_attr()
__sync_wrapper_get_attr.lock = threading.RLock()


class _SyncFreeDbEvent(threading.Event):
    """ Event on free database

    This event is set when no concurrent operations are evaluating now and
    new readable and/or writable query can be evaluated
    """
    def __init__(self):
        """ Override inner lock class and default flag value

        Assuming that no query is running on event instantiation
        """
        super().__init__()
        self._cond = threading.Condition()
        self._owner = None
        self._flag = True

    def clear(self):
        """Set the internal flag to true

        :return None:
        """
        with self._cond:
            super().clear()
            self._owner = threading.get_ident()

    def wait(self, timeout=None):
        """ Block until the internal flag is true

        :param int timeout: Block timeout
        :return None:
        """
        with self._cond:
            if self._owner != threading.get_ident():
                super().wait(timeout)


class _SyncRFreeDbEvent(_SyncFreeDbEvent):
    """ Repeatable event

    Should be cleared as many times as it has been set before
    """
    def __init__(self):
        """ Init inner reading operations counter """
        super().__init__()
        self._clearing_cnt = 0

    def set(self):
        """Set the internal flag to true

        :return None:
        """
        with self._cond:
            self._clearing_cnt -= 1
            if self._clearing_cnt <= 0:
                self._clearing_cnt = 0
                super().set()

    def clear(self):
        """Reset the internal flag to false

        :return None:
        """
        with self._cond:
            super().clear()
            self._clearing_cnt += 1


def __sync_write_completed_event(obj) -> _SyncFreeDbEvent:
    """ Get "write completed" event

    This event is set when no writable operations are pending and
    new readable and/or writable query can be evaluated

    :param any obj:
    :return threading.Event:
    """
    return __sync_wrapper_get_attr(obj, '__w_completed', _SyncFreeDbEvent())


def __sync_read_completed_event(obj) -> _SyncRFreeDbEvent:
    """ Get "read completed" event

    This event is set when no operations are pending and
    new _writable_ query can be evaluated

    :param any obj:
    :return threading.Event:
    """
    return __sync_wrapper_get_attr(obj, '__r_completed', _SyncRFreeDbEvent())


def readable_query(method: callable) -> callable:
    """ Readable query decorator

    :param callable method: Storage method
    :return: callable
    """
    @wraps(method)
    def _wrapper(self_, *args, **kwargs):
        w_completed_event = __sync_write_completed_event(self_)
        r_completed_event = __sync_read_completed_event(self_)

        try:
            w_completed_event.wait()
            r_completed_event.clear()

            res = method(self_, *args, **kwargs)

        finally:
            r_completed_event.set()

        return res

    return _wrapper


def writable_query(method: callable) -> callable:
    """ Writable query decorator

    :param callable method: Storage method
    :return: callable
    """
    @wraps(method)
    def _wrapper(self_, *args, **kwargs):
        w_completed_event = __sync_write_completed_event(self_)
        r_completed_event = __sync_read_completed_event(self_)

        try:
            r_completed_event.wait()
            w_completed_event.wait()
            w_completed_event.clear()

            res = method(self_, *args, **kwargs)

        finally:
            w_completed_event.set()

        return res

    return _wrapper


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
    def _table(cls) -> Table:  # pragma: nocover
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
        try:
            self._cache[getattr(self, str(self._key))] = self
        except AttributeError:
            pass

    def free(self):
        """ Remove from cache

        :return None:
        """
        try:
            del self._cache[getattr(self, str(self._key))]
        except (KeyError, AttributeError):
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
    def _dsn(self) -> str:  # pragma: nocover
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
