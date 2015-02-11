#!/usr/bin/env python3
# -*- coding: UTF-8

""" Dewyatochka setup script """

import sys
import os
from distutils.core import setup  # , Extension

# Some dirty hack to define version in one place
sys.path.append(os.path.realpath(os.path.dirname(__file__)) + '/src')
from dewyatochka import __version__

setup(
    # Metadata
    name='dewyatochka',
    version=__version__,
    description='Dewyatochka Improved',
    long_description='Dewyatochka Jabber bot improved version',
    url='http://under-construction.example.com',
    maintainer='Kawashiro Nitori',
    maintainer_email='spam@example.com',
    license='GPL-3',
    platforms=['POSIX'],
    # Dependencies
    requires=['sleekxmpp'],
    # Python packages
    package_dir={'': 'src/'},
    packages=['dewyatochka',
              'dewyatochka.applications',
              'dewyatochka.core',
              'dewyatochka.core.config',
              'dewyatochka.core.config.source',
              'dewyatochka.core.log',
              'dewyatochka.core.network',
              'dewyatochka.core.network.xmpp',
              'dewyatochka.core.network.xmpp.client',
              'dewyatochka.plugins',
              'dewyatochka.utils'],
    # Python extensions
    #ext_modules=[Extension('dewyatochka.binary', ['src/ext/binarymodule/binarymodule.c'])],
    # Executable files
    scripts=['src/dewyatochkad'],
    # Data files
    data_files=[
        ('/etc/dewyatochka', ['data/etc/dewyatochka.ini', 'data/etc/conferences.ini']),
        ('/etc/dewyatochka/ext', ['data/etc/ext/hentai.ini', 'data/etc/ext/mail_ru.ini'])
    ]
)
