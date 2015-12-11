#!/usr/bin/env python3
# -*- coding: UTF-8

""" Dewyatochka setup script """

import os
import sys
import shlex
import platform
from datetime import datetime
from collections import defaultdict
from functools import reduce

from distutils import log
from distutils.core import setup, Command, Extension


#
# Package configuration begin
#
# Application metadata
METADATA = {
    'name': 'dewyatochka',
    'description': 'Dewyatochka Improved',
    'long_description': 'Dewyatochka bot. Improved version',
    'url': 'https://github.com/kawashiro/dewyatochka2',
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

# Distribution dir
DIST_DIR = 'dist/'

# Building dir
BUILD_DIR = 'build/'

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
#
# Package configuration end
#


class GenOverlayCommand(Command):
    """ Create Gentoo overlay """
    description = __doc__

    # Command name
    name = 'genoverlay'

    # Package slot
    pkg_slot = 'net-misc'

    # Package name, using one from metadata
    pkg_name = None

    # Building live-package
    pkg_version = '9999'

    # Package home dir
    pkg_home = None

    # CLI opt args
    user_options = [
        ('root=', None, 'Create overlay in this alternate directory'),
    ]

    # Overlay root
    root = None

    # Overlay sources root
    src_root = None

    def initialize_options(self):
        """Set default values for all the options that this command supports

        :return None:
        """
        self.root = _abs(DIST_DIR, 'gentoo')
        self.src_root = _abs('pkg', 'gentoo')
        self.pkg_name = configure_metadata().get('name')

    def finalize_options(self):
        """Set final values for all the options that this command supports

        :return None:
        """
        pass

    def run(self):
        """ Create overlay

        :return None:
        """
        self.pkg_home = self.root + os.sep + self.pkg_slot + os.sep + self.pkg_name

        self.mkpath(self.root, mode=0o755)
        self._create_layout()
        self._create_ebuild()
        self.copy_tree(self.src_root + os.sep + 'files', self.pkg_home + os.sep + 'files')
        _shell_exec('ebuild %s digest', self.pkg_home + os.sep + self.pkg_name + '-' + self.pkg_version + '.ebuild')

    def _create_layout(self):
        """ Create layout.conf

        :return None:
        """
        conf_path = self.root + os.sep + 'metadata' + os.sep + 'layout.conf'
        if os.path.isfile(conf_path):
            log.info('layout.conf already exists, keeping')
        else:
            self.mkpath(os.path.dirname(conf_path), mode=0o755)
            with open(conf_path, 'w') as f:
                log.info('creating new layout.conf at %s', conf_path)
                f.write('masters = gentoo\n')

    def _create_ebuild(self, metadata=None, skeleton=None):
        """ Create ebuild file

        :param dict metadata:
        :param str skeleton:
        :return None:
        """
        if skeleton is None:
            skeleton = self.src_root + '/dewyatochka.ebuild.skel'
        if metadata is None:
            metadata = configure_metadata()

        self.mkpath(self.pkg_home)
        destination = self.pkg_home + os.sep + self.pkg_name + '-' + self.pkg_version + '.ebuild'

        with open(skeleton) as sf, open(destination, 'w') as df:
            log.info('creating ebuild at %s', destination)
            df.write(sf.read().format(**metadata))


class DebianBuildCommand(Command):
    """ Build debian package """
    description = __doc__

    # Command name
    name = 'bdist_deb'

    # Package name, using one from metadata
    pkg_name = None

    # Package version
    pkg_version = None

    # CLI opt args
    user_options = [
        ('live', None, 'Generate a new version number for live (VCS) package'),
    ]

    # Boolean opts
    boolean_options = ['live']

    # Build normal package by default
    live = False

    # Package destination
    destination = None

    # Building directory
    build_dir = None

    # Overlay sources root
    src_root = None

    # Build platform
    platform = None

    def initialize_options(self):
        """Set default values for all the options that this command supports

        :return None:
        """
        self.destination = _abs(DIST_DIR, 'debian')
        self.build_dir = _abs(BUILD_DIR, 'debian')
        self.src_root = _abs('pkg', 'debian')
        self.pkg_name = 'python3-%s' % configure_metadata().get('name')
        self.platform = platform.machine()
        if self.platform == 'x86_64':
            self.platform = 'amd64'

    def finalize_options(self):
        """Set final values for all the options that this command supports

        :return None:
        """
        if self.live:
            now = datetime.now()
            self.pkg_version = now.strftime('%Y.%m.%d-') + str(int(now.timestamp()) % 86400)
        else:
            self.pkg_version = configure_metadata()['version'] + '-1'

    def run(self):
        """ Create package

        :return None:
        """
        self._create_control()
        self._write_configs()
        _shell_exec(
            'install -m 755 %s %s',
            os.sep.join([self.src_root, 'postinst.sh']),
            os.sep.join([self.build_dir, 'DEBIAN', 'postinst'])
        )
        _shell_exec(
            'install -m 755 %s %s',
            os.sep.join([self.src_root, 'postrm.sh']),
            os.sep.join([self.build_dir, 'DEBIAN', 'postrm'])
        )
        self.mkpath(os.sep.join([self.build_dir, 'etc', 'init.d']), mode=0o755)
        _shell_exec(
            'install -m 755 %s %s',
            os.sep.join([self.src_root, 'dewyatochkad.initd']),
            os.sep.join([self.build_dir, 'etc', 'init.d', 'dewyatochkad'])
        )

        _shell_exec('%s %s install -O2 --root=%s --install-layout=deb',
                    sys.executable, __file__, self.build_dir)
        _shell_exec('find %s -type f -name "*.so" | xargs strip -s -v', self.build_dir)
        _shell_exec('fakeroot dpkg-deb --build %s', self.build_dir)

        self.mkpath(self.destination)
        self.move_file(
            _abs(BUILD_DIR) + os.sep + 'debian.deb',
            self.destination + os.sep + self.pkg_name + '_' + self.pkg_version + '-' + self.platform + '.deb'
        )

    def _create_control(self):
        """ Create DEBIAN/control file

        :return None:
        """
        skeleton = self.src_root + os.sep + 'control.skel'

        metadata = configure_metadata()
        metadata['pkg_name'] = self.pkg_name
        metadata['pkg_version'] = self.pkg_version
        metadata['pkg_platform'] = self.platform

        self.mkpath(self.build_dir + os.sep + 'DEBIAN')
        destination = self.build_dir + os.sep + 'DEBIAN' + os.sep + 'control'

        with open(skeleton) as sf, open(destination, 'w') as df:
            log.info('creating control stanza at %s', destination)
            df.write(sf.read().format(**metadata))

    def _write_configs(self):
        """ Write config files list

        :return None:
        """
        files_list = []
        for destination, files in configure_configs()['data_files']:
            for file_ in files:
                files_list.append(destination + os.sep + os.path.basename(file_.split(ETC_DIR)[1]))

        with open(os.sep.join([self.build_dir, 'DEBIAN', 'conffiles']), 'w') as cf:
            cf.write('\n'.join(files_list))
            cf.write('\n')


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
    return {
        'ext_modules': [Extension(p, [os.sep.join([SRC_DIR, p.replace('.', os.sep), 'module.c'])]) for p in C_PACKAGES]
    }


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


def configure_commands() -> dict:
    """ Get custom commands dict """
    commands = (
        GenOverlayCommand,
        DebianBuildCommand,
    )

    return {'cmdclass': {c_class.name: c_class for c_class in commands}}


def _abs(*rel: str) -> str:
    """ Get absolute path disregarding CWD """
    return os.path.realpath(os.sep.join((os.path.dirname(__file__) or '.',) + rel))


def _shell_exec(command, *args):
    """ Exec shell command

    :param str command:
    :param tuple args:
    :return None:
    """
    command_ = command % tuple(map(shlex.quote, args))
    log.info('running: %s' % command_)
    status = os.system(command_)
    if status > 0:
        raise RuntimeError('Command "%s" exited with status %d' % (command_, status))


if __name__ == '__main__':
    # Setup, Dewyatochka, setup! ^-^
    params = {}
    params.update(configure_metadata())
    params.update(configure_python_packages())
    params.update(configure_c_packages())
    params.update(configure_scripts())
    params.update(configure_configs())
    params.update(configure_commands())

    setup(requires=DEPENDS, **params)
