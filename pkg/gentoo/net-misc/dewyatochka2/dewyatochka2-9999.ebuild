# Copyright 2014-Infinity Kawashiro Nitori
# Distributed under the terms of the GNU General Public License v3

EAPI=5
PYTHON_COMPAT=( python{3_3,3_4} )

inherit eutils distutils-r1 git-2 user

MY_PN=SleekXMPP
MY_P=${MY_PN}-${PV}

DESCRIPTION="The most stupid bakabot ever"
HOMEPAGE="http://kawashi.ro"
EGIT_REPO_URI="https://github.com/kawashiro/dewyatochka2.git"

LICENSE="GPL-3"
SLOT="0"
KEYWORDS=""

DEPEND=">=dev-python/sleekxmpp-1.3[${PYTHON_USEDEP}]
        >=dev-python/pyquery-1.2[${PYTHON_USEDEP}]
        dev-python/pyasn1-modules[${PYTHON_USEDEP}]"

src_install()
{
	# Install app
	distutils-r1_src_install
	# Install init scriipt
	newinitd "${FILESDIR}"/dewyatochkad.initd dewyatochkad
}

pkg_postinst()
{
	# Add new user & group
	enewgroup dewyatochka
	enewuser dewyatochka -1 -1 -1 dewyatochka
}
