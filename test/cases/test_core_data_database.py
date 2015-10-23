# -*- coding=utf-8

""" Tests suite for dewyatochka.core.data.database """

import os
import time
import threading

import unittest
from unittest.mock import Mock, MagicMock, call, patch

from sqlalchemy.sql.schema import MetaData

from dewyatochka.core.data.database import *


# Root path to test files directory
_FILES_ROOT = os.path.realpath(os.path.dirname(__file__) + '/../files/database')


class TestSyncWrapper(unittest.TestCase):
    """ Tests suite for dewyatochka.core.data.database.readable_query / writable_query """

    class _TestClass:
        """ Class with synchronous methods """

        def __init__(self):
            self._callee = MagicMock()

        def __exec(self, *args):
            self._callee('start', *args)
            time.sleep(0.05)
            self._callee('end', *args)

        @readable_query
        def read_method(self, *args):
            """ Readable query emulation """
            self.__exec(*args)

        @writable_query
        def write_method(self, *args):
            """ Writable query emulation """
            self.__exec(*args)

        @property
        def callee(self):
            """ Get callee """
            return self._callee

    @staticmethod
    def __async(barrier, method, *args, **kwargs):
        """ Run async """
        def _target(*args_, **kwargs_):
            method(*args_, **kwargs_)
            barrier.wait()

        threading.Thread(target=_target, args=args, kwargs=kwargs).start()

    def test_sync_wrapper(self):
        """ Test decorators """
        barrier = threading.Barrier(5)
        class_ = self._TestClass()

        self.__async(barrier, class_.read_method, 'read #1')
        self.__async(barrier, class_.write_method, 'write')
        self.__async(barrier, class_.write_method, 'write')
        self.__async(barrier, class_.read_method, 'read #2')

        barrier.wait()

        class_.callee.assert_has_calls([
            call('start', 'read #1'),
            call('start', 'read #2'),
            call('end', 'read #1'),
            call('end', 'read #2'),
            call('start', 'write'),
            call('end', 'write'),
            call('start', 'write'),
            call('end', 'write'),
        ])


class TestThreadSafeSingleton(unittest.TestCase):
    """ Tests suite for dewyatochka.core.data.database.ThreadSafeSingleton """

    def test_instantiation(self):
        """ Check if instance is always the same """
        class _Singleton(metaclass=ThreadSafeSingleton):
            pass

        obj1 = _Singleton()
        obj2 = _Singleton()

        self.assertEqual(obj1, obj2)


class TestObjectMeta(unittest.TestCase):
    """ Tests suite for dewyatochka.core.data.database.ObjectMeta """

    @patch('dewyatochka.core.data.database.mapper')
    def test_init(self, mapper_mock):
        """ Test instantiation """
        class _ObjectMeta(ObjectMeta):
            table_mock = Mock()
            _table = table_mock

        class _ObjectMeta2(ObjectMeta):
            properties_mock = {'foo': 'bar'}
            table_mock = Mock()
            _table = table_mock
            _mapping_properties = properties_mock

        class _Object(metaclass=_ObjectMeta):
            pass

        class _Object2(metaclass=_ObjectMeta2):
            pass

        mapper_mock.assert_has_calls([
            call(_Object, _Object.table_mock, {}),
            call(_Object2, _ObjectMeta2.table_mock, _ObjectMeta2.properties_mock)
        ])

    @patch('dewyatochka.core.data.database.mapper')
    def test_undefined_attr(self, *_):
        """ Test unknown attribute getter """
        class _ObjectMeta(ObjectMeta):
            _table = Mock()

        class _Object(metaclass=_ObjectMeta):
            pass

        self.assertRaises(UnmappedFieldError, lambda: _Object.foo)


class TestStoreableObject(unittest.TestCase):
    """ Tests suite for dewyatochka.core.data.database.StoreableObject """

    def test_init(self):
        """ Test instantiation """
        obj = StoreableObject(foo='bar')
        self.assertEqual(obj.foo, 'bar')

    def test_stored(self):
        """ Test `stored` property definition """
        self.assertTrue(StoreableObject(id=9000).stored)
        self.assertFalse(StoreableObject(id=None).stored)
        self.assertFalse(StoreableObject().stored)


class TestCacheableObject(unittest.TestCase):
    """ Tests suite for dewyatochka.core.data.database.CacheableObject """

    def test_caching(self):
        """ Test caching on regular instantiation """
        class _CacheableObject(CacheableObject):
            _key = 'cache_key'

        obj1 = _CacheableObject(cache_key='val1')
        obj2 = _CacheableObject(cache_key='val2')
        obj3 = _CacheableObject()

        self.assertEqual(_CacheableObject.get_cached(), dict(val1=obj1, val2=obj2))
        self.assertEqual(CacheableObject.get_cached(), {})

        obj2.free()
        obj3.free()
        self.assertEqual(_CacheableObject.get_cached(), dict(val1=obj1))


class TestStorageMeta(unittest.TestCase):
    """ Tests suite for dewyatochka.core.data.database.StorageMeta """

    def test_metadata(self):
        """ Test metadata getter  """
        class _Storage(metaclass=StorageMeta):
            pass

        self.assertIsInstance(_Storage.metadata, MetaData)


class TestAbstractStorage(unittest.TestCase):
    """ Tests suite for dewyatochka.core.data.database.AbstractStorage """

    @patch('dewyatochka.core.data.database.sessionmaker')
    @patch('dewyatochka.core.data.database.create_engine')
    def test_db_session(self, create_engine_mock, sessionmaker_mock):
        """ Test session object instantiation """
        class _Storage(AbstractStorage):
            _dsn = 'dsn://'

        storage = _Storage()
        session = storage.db_session

        self.assertEqual(storage.db_session, session)
        sessionmaker_mock.assert_has_calls([call(bind=create_engine_mock())])
        create_engine_mock.assert_has_calls([call('dsn://', connect_args={})])

    @patch('dewyatochka.core.data.database.create_engine')
    @patch('dewyatochka.core.data.database.sessionmaker')
    def test_close(self, sessionmaker_mock, *_):
        """ Test closing db connection """
        class _Storage(AbstractStorage):
            _dsn = 'dsn://'

        storage = _Storage()
        session = storage.db_session

        storage.close()

        # noinspection PyUnresolvedReferences
        session.close.assert_called_once_with()
        (lambda: storage.db_session)()
        self.assertEqual(sessionmaker_mock.call_count, 2)

    def test_commit(self):
        """ Test data committing """
        class _Storage(AbstractStorage):
            _dsn = 'dsn://'
            db_session = Mock()

        storage = _Storage()
        storage.commit()

        storage.db_session.commit.assert_called_once_with()

    def test_create(self):
        """ Test storage create """
        class _Storage(AbstractStorage):
            _dsn = 'dsn://'
            metadata = Mock()
            db_session = Mock()

        _Storage().create()
        _Storage().metadata.create_all.assert_called_once_with(bind=_Storage.db_session.get_bind())


class TestSQLIteStorage(unittest.TestCase):
    """ Tests suite for dewyatochka.core.data.database.SQLIteStorage """

    def test_path(self):
        """ Test file path assigning """
        class _Storage(SQLIteStorage):
            _DEFAULT_DB_PATH = _FILES_ROOT + '/default.sqlite'
            close = Mock()

        storage = _Storage()
        self.assertEqual(storage.path, _FILES_ROOT + '/default.sqlite')
        storage.path = _FILES_ROOT + '/foo/../custom.sqlite'
        self.assertEqual(storage.path, _FILES_ROOT + '/custom.sqlite')
        storage.path = _FILES_ROOT + '/custom.sqlite'
        self.assertEqual(_Storage.close.call_count, 2)

    def test_connect_params(self):
        """ Test connect args and DSN """
        class _Storage(SQLIteStorage):
            """ Extended by getters impl """
            @property
            def dsn(self):
                """ DSN getter """
                return self._dsn

            @property
            def connect_args(self):
                """ Connect args getter """
                return self._connect_args

        storage = _Storage()
        storage.path = '/foo/bar.db'

        self.assertEqual(storage.dsn, 'sqlite:////foo/bar.db')
        self.assertEqual(storage.connect_args, {'check_same_thread': False})

    @patch('os.path.isfile')
    @patch.object(AbstractStorage, 'create')
    def test_create(self, abstract_create_mock, is_file_mock):
        """ Test create() method """
        is_file_mock.side_effect = [True, False]

        storage = SQLIteStorage()
        storage.path = '/existing.sqlite'
        storage.create()

        storage.path = '/not/existing.sqlite'
        storage.create()

        abstract_create_mock.assert_called_once_with()

    @patch('os.path.isfile')
    @patch('os.unlink')
    @patch.object(AbstractStorage, 'create')
    def test_recreate(self, abstract_create_mock, unlink_mock, is_file_mock):
        """ Test recreate() method """
        class _Storage(SQLIteStorage):
            close = Mock()

        storage = _Storage()
        is_file_mock.side_effect = [True, False]

        storage.path = '/existing.sqlite'
        storage.recreate()

        storage.path = '/not/existing.sqlite'
        storage.recreate()

        self.assertEqual(_Storage.close.call_count, 4)
        self.assertEqual(abstract_create_mock.call_count, 2)
        unlink_mock.assert_has_calls([call('/existing.sqlite')])
