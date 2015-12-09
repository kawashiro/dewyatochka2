#!/usr/bin/env python3
# -*- coding: UTF-8

""" Dewyatochka setup script """

import sys
import os
from collections import defaultdict
from functools import reduce

from distutils.core import setup, Extension


#
# Package configuration begin

# Application metadata
METADATA = {
    'name': 'dewyatochka',
    'description': 'Dewyatochka Improved',
    'long_description': 'Dewyatochka bot. Improved version',
    'url': 'http://under-construction.localhost',
    'maintainer': 'Kawashiro Nitori',
    'maintainer_email': 'nitori@localhost',
    'license': 'GPL-3',
    'platforms': ['POSIX']
}

# Dependencies
DEPENDS = {
    'sleekxmpp',
    'pyquery',
    'pyasn1_modules',
    'SQLAlchemy',
    'lxml',
}

# Sources dir
SRC_DIR = 'src/'

# Config files dir
ETC_DIR = 'data/etc'

# Python packages
PY_PACKAGES = {
    'dewyatochka',
}

# Binary packages
C_PACKAGES = {
    'dewyatochka.core.daemon._utils',
}

# Executable scripts
SCRIPTS = {
    'dewyatochkad',
    'dewyatochkactl',
}

# Package configuration end
#


def configure_metadata() -> dict:
    """ Process package metadata configuration """
    metadata = METADATA.copy()

    # Some dirty hack to define version in one place
    sys.path.insert(0, _abs(SRC_DIR))
    from dewyatochka import __version__
    metadata['version'] = __version__

    return metadata


def configure_python_packages() -> dict:
    """ Process python packages configuration """
    return {
        'packages':
            reduce(lambda acc, pkg: acc +
                   [d[0][len(_abs(SRC_DIR)) + 1:].replace(os.sep, '.')
                    for d in sorted(os.walk(_abs(SRC_DIR, pkg)))
                    if '__pycache__' not in d[0] and '__init__.py' in d[2]],
                   PY_PACKAGES, []),
        'package_dir': {'': SRC_DIR}
    }


def configure_c_packages() -> dict:
    """ Configure extensions """
    return {'ext_modules': [Extension(p, [_abs(SRC_DIR, p.replace('.', os.sep), 'module.c')]) for p in C_PACKAGES]}


def configure_scripts() -> dict:
    """ Configure executable scripts """
    return {'scripts': list(map(lambda n: _abs(SRC_DIR, n), SCRIPTS))}


def configure_configs() -> dict:
    """ Config files configuration """
    cfg_src = _abs(ETC_DIR)
    cfg_dst = os.sep.join(['', 'etc', METADATA['name']])

    mappings = defaultdict(list)
    for dir_self, _, files in os.walk(cfg_src):
        for file in files:
            mappings[dir_self.replace(cfg_src, cfg_dst)].append(os.sep.join([dir_self, file]))

    return {'data_files': [(k, mappings[k]) for k in mappings]}


def _abs(*rel: str) -> str:
    """ Get absolute path disregarding CWD """
    return os.path.realpath(os.sep.join((os.path.dirname(__file__) or '.',) + rel))


if __name__ == '__main__':
    # Setup, Dewyatochka, setup! ^-^
    params = {}
    params.update(configure_metadata())
    params.update(configure_python_packages())
    params.update(configure_c_packages())
    params.update(configure_scripts())
    params.update(configure_configs())

    setup(requires=DEPENDS, **params)
