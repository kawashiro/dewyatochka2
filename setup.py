#!/usr/bin/env python3
# -*- coding: UTF-8

""" Dewyatochka setup script """

import sys
import os
from distutils.core import setup, Extension

# Some dirty hack to define version in one place
sys.path.insert(0, os.path.realpath(os.path.dirname(__file__)) + '/src')
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
    requires=['sleekxmpp', 'pyquery'],
    extras_require={
        'html': ['pyquery'],
        'ssl': ['pyasn1_modules'],
        'db': ['sqlalchemy']
    },
    # Python packages
    package_dir={'': 'src/'},
    packages=['dewyatochka',
              'dewyatochka.applications',
              'dewyatochka.applications.daemon',
              'dewyatochka.applications.daemon._process',
              'dewyatochka.applications.daemon._process.conference',
              'dewyatochka.core',
              'dewyatochka.core.config',
              'dewyatochka.core.config.source',
              'dewyatochka.core.daemon',
              'dewyatochka.core.data',
              'dewyatochka.core.log',
              'dewyatochka.core.network',
              'dewyatochka.core.network.xmpp',
              'dewyatochka.core.network.xmpp.client',
              'dewyatochka.core.plugin',
              'dewyatochka.core.plugin.helper_sys',
              'dewyatochka.core.plugin.loader',
              'dewyatochka.core.plugin.message_sys',
              'dewyatochka.core.plugin.message_sys.matcher',
              'dewyatochka.core.plugin.ctl_sys',
              'dewyatochka.core.utils',
              'dewyatochka.plugins'],
    # Python extensions
    ext_modules=[Extension('dewyatochka.core.daemon._utils', ['src/ext/daemon/utilsmodule.c'])],
    # Executable files
    scripts=['src/dewyatochkad', 'src/dewyatochkactl'],
    # Data files
    data_files=[
        ('/etc/dewyatochka', ['data/etc/dewyatochka.ini', 'data/etc/conferences.ini']),
        ('/etc/dewyatochka/ext', ['data/etc/ext/hentai.ini', 'data/etc/ext/mail_ru.ini']),
        ('/var/lib/dewyatochka', ['data/var-lib/.FAKE'])
    ]
)
