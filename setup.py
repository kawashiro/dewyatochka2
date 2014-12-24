#!/usr/bin/env python3
# -*- coding: UTF-8

"""
Dewyatochka setup script
"""

from distutils.core import setup  # , Extension

setup(
    # Metadata
    name='dewyatochka',
    version='0.0.1',
    description='Dewyatochka Improved',
    long_description='Dewyatochka Jabber bot core',
    url='http://kawashi.ro',
    maintainer='Kawashiro Nitori',
    maintainer_email='nitori@kawashi.ro',
    license='GPL-3',
    platforms=['POSIX'],
    # Python packages
    package_dir={'': 'src/'},
    packages=['dewyatochka', 'dewyatochka.core', 'dewyatochka.plugins', 'dewyatochka.utils'],
    # Python extensions
    #ext_modules=[Extension('dewyatochka.binary', ['src/ext/binarymodule/binarymodule.c'])],
    # Executable files
    scripts=['src/dewyatochkad'],
    # Data files
    data_files=[('/etc/dewyatochka', ['data/dewyatochka.ini', 'data/conferences.ini'])]
)
