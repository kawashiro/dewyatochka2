# -*- coding: UTF-8

""" Utils for data access

Classes
=======
    ObjectMeta          -- Abstract metaclass for ORM objects
    UnmappedFieldError  -- Error on access to undefined object field
    StorageMeta         -- Abstract metaclass for storage implementations
"""

__all__ = ['ObjectMeta', 'UnmappedFieldError', 'StorageMeta']


from abc import ABCMeta, abstractproperty

from sqlalchemy import Table, MetaData
from sqlalchemy.orm import mapper


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


class StorageMeta(type):
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
