# -*- coding: UTF-8

""" Dewyatochka root package

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

Copyright (C) 2015 Kawashiro Nitori

Sub-packages
============
    core         -- Core package, contains all the packages needed dewyatochka to work
    plugins      -- Originally empty package used for builtin and third-party plugins auto loading
    applications -- High-level applications implementation

Attributes
==========
    __version__ -- Core lib version
"""

__version__ = '0.0.1'

__all__ = ['applications', 'core', 'plugins', '__version__']
