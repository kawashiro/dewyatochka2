# -*- coding: UTF-8

"""
Filesystem config sources
"""

__all__ = ['Filesystem', 'INIFiles']

from abc import ABCMeta, abstractmethod, abstractproperty
from os import path, listdir
import configparser
from dewyatochka.core.config.source import ConfigSource
from dewyatochka.core.config.exception import ReadError


class Filesystem(ConfigSource, metaclass=ABCMeta):
    """
    Config stored in ini file
    """

    def __init__(self, config_path: str):
        """
        Create config parser instance for `path` file or directory
        :param config_path: str
        """
        self._path = path.realpath(config_path)

    @property
    def _files(self) -> set:
        """
        Get all readable files list
        :return: list
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
        """
        Extension indicating appropriate config file format
        :return: str
        """
        pass

    @abstractmethod
    def _do_read(self, files: set) -> dict:  # pragma: no cover
        """
        Read list of files specified
        :param files: list
        :return: dict
        """
        pass

    def read(self) -> dict:
        """
        Read file or directory and return dict-like object {'section': <...>}
        :return: dict
        """
        return self._do_read(self._files)


class INIFiles(Filesystem):
    """
    INI parser
    """

    def _do_read(self, files: set) -> dict:
        """
        Read list of files specified
        :param files: list
        :return: dict
        """
        try:
            parser = configparser.ConfigParser()
            parser.read(files)
        except configparser.Error as e:
            raise ReadError(e)

        return parser

    @property
    def file_extension(self) -> str:
        """
        Extension indicating appropriate config file format
        :return: str
        """
        return '.ini'
