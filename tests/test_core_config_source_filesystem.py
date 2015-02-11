# -*- coding=utf-8

""" Tests suite for dewyatochka.core.log.get_logger """

from os import path

import unittest

from dewyatochka.core.config.source.filesystem import *
from dewyatochka.core.config.exception import ReadError


# Root path to config test files
_CONFIG_FILES_ROOT = path.dirname(__file__) + '/files/config'


class _VoidFilesystemSource(Filesystem):
    """ Filesystem abstract methods stubs """

    def _do_read(self, files: list) -> dict:
        """ Read and parse set of files specified

        :param set files:
        :return dict:
        """
        return {}

    @property
    def file_extension(self) -> str:
        """ Extension indicating appropriate config file format

        :return str:
        """
        return '.ini'


class TestFilesystem(unittest.TestCase):
    """ Covers dewyatochka.core.config.source.filesystem.Filesystem """

    def test_init(self):
        """ Test __init__() """
        config_source = _VoidFilesystemSource(_CONFIG_FILES_ROOT)
        self.assertEqual(_CONFIG_FILES_ROOT, config_source._path)

    def test_files(self):
        """ Test directory scan """
        file = _CONFIG_FILES_ROOT + '/ini_file.ini'
        self.assertEqual([file], _VoidFilesystemSource(file)._files)

        directory = _CONFIG_FILES_ROOT + '/ini_directory'
        self.assertEqual({directory + '/test_config1.ini', directory + '/test_config2.ini'},
                         _VoidFilesystemSource(directory)._files)

        self.assertRaises(IOError, _VoidFilesystemSource('/foo.bar').read)


class TestINIFiles(unittest.TestCase):
    """ Covers dewyatochka.core.config.source.filesystem.INIFiles """

    def test_do_read(self):
        """ Test configs parsing """
        config = INIFiles(_CONFIG_FILES_ROOT + '/ini_file.ini').read()
        self.assertEqual({'section1': {'foo': 'bar'}, 'DEFAULT': {}},
                         {section: dict(config[section]) for section in config})

        config = INIFiles(_CONFIG_FILES_ROOT + '/ini_directory/').read()
        self.assertEqual({'section1': {'foo': 'bar'}, 'section2': {'bar': 'baz'}, 'DEFAULT': {}},
                         {section: dict(config[section]) for section in config})

        corrupted_source = INIFiles(_CONFIG_FILES_ROOT + '/corrupted_ini_file.ini')
        self.assertRaises(ReadError, corrupted_source.read)

    def test_file_extension(self):
        """ Test file_extension property """
        self.assertEqual('.ini', INIFiles('void').file_extension)
