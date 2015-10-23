# -*- coding=utf-8

""" Tests suite for dewyatochka.core.config.source.filesystem """

from os import path

import unittest

from dewyatochka.core.config.source.filesystem import *
from dewyatochka.core.config.exception import ReadError


# Root path to config test files
_CONFIG_FILES_ROOT = path.dirname(__file__) + '/../files/config'
_CONFIG_FILES_ROOT_REAL = path.realpath(_CONFIG_FILES_ROOT)


class TestFilesystem(unittest.TestCase):
    """ Tests suite for dewyatochka.core.config.source.filesystem.Filesystem """
    def test_files(self):
        """ Test directory scan """
        class _VoidFilesystemSource(Filesystem):
            """ Filesystem abstract methods stubs """
            file_extension = '.ini'

            def _do_read(self, files: list) -> dict:
                """ Abstract method stub """
                return {}

            @property
            def files(self):
                """ Files list getter """
                return self._files

        file = _CONFIG_FILES_ROOT_REAL + '/ini_file.ini'
        self.assertEqual(_VoidFilesystemSource(file).files, {file})

        directory = _CONFIG_FILES_ROOT_REAL + '/ini_directory'
        self.assertEqual(_VoidFilesystemSource(directory).files,
                         {directory + '/test_config1.ini', directory + '/test_config2.ini'})

        self.assertRaises(IOError, _VoidFilesystemSource('/foo.bar').read)


class TestINIFiles(unittest.TestCase):
    """ Tests suite for dewyatochka.core.config.source.filesystem.INIFiles """

    def test_do_read(self):
        """ Test configs parsing """
        config = INIFiles(_CONFIG_FILES_ROOT + '/ini_file.ini').read()
        self.assertEqual({section: dict(config[section]) for section in config},
                         {'section1': {'foo': 'bar'}})

        config = INIFiles(_CONFIG_FILES_ROOT + '/ini_directory/').read()
        self.assertEqual({section: dict(config[section]) for section in config},
                         {'section1': {'foo': 'bar'}, 'section2': {'bar': 'baz'}})

        corrupted_source = INIFiles(_CONFIG_FILES_ROOT + '/corrupted_ini_file.ini')
        self.assertRaises(ReadError, corrupted_source.read)
