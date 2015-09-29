# -*- coding: UTF-8

""" File based config data sources

Classes
=======
    Filesystem -- Abstract filesystem-based data source
    INIFiles   -- Non-recursive INI-files parser
"""

from os import path, listdir
from abc import ABCMeta, abstractmethod, abstractproperty
import configparser

from dewyatochka.core.config.source import ConfigSource
from dewyatochka.core.config.exception import ReadError

__all__ = ['Filesystem', 'INIFiles']


class Filesystem(ConfigSource, metaclass=ABCMeta):
    """ Abstract filesystem-based data source

        Parses and merges data from a single file
        or all the files found in directory specified
    """

    def __init__(self, config_path: str):
        """ Create config parser instance for `path` file or directory

        If `path` is file only this file is to be read

        :param str config_path:
        """
        self._path = path.realpath(config_path)

    @property
    def _files(self) -> set:
        """ Get all readable files set

        :return list:
        """
        if path.isfile(self._path):
            files = [self._path]
        elif path.isdir(self._path):
            files = {file for file
                     in map(lambda f: path.sep.join((self._path, f)), listdir(self._path))
                     if path.isfile(file) and file.endswith(self.file_extension)}
        else:
            raise IOError('Failed to read config data from "%s": no such file or directory' % self._path)

        return files

    @abstractproperty
    def file_extension(self) -> str:  # pragma: no cover
        """ Extension indicating appropriate config file format

        :return str:
        """
        pass

    @abstractmethod
    def _do_read(self, files: set) -> dict:  # pragma: no cover
        """ Read and parse set of files specified

        :param set files:
        :return dict:
        """
        pass

    def read(self) -> dict:
        """ Read data and return dict-like object {'section': <...>}

        :return dict:
        """
        return self._do_read(self._files)


class INIFiles(Filesystem):
    """ Non-recursive INI-files parser

        Looks up for the *.ini files and tries to parse
        them using configparser.ConfigParser
    """

    def _do_read(self, files: set) -> dict:
        """ Read and parse set of files specified

        :param set files:
        :return: dict
        """
        try:
            parser = configparser.ConfigParser()
            parser.read(files)
        except configparser.Error as e:
            raise ReadError(e)

        return {section: parser[section] for section in parser.sections()}

    @property
    def file_extension(self) -> str:
        """ Extension indicating appropriate config file format

        :return str:
        """
        return '.ini'
