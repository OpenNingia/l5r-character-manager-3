# -*- coding: utf-8 -*-
# Copyright (C) 2014-2022 Daniele Simonetti
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.

from subprocess import Popen
import os
import sys

from PyQt5 import QtCore, QtGui, QtWidgets

APP_NAME = 'l5rcm'
HERE = os.path.abspath(os.path.dirname(__file__))

if hasattr(sys, "frozen"):
    HERE = os.path.dirname(HERE)

MY_CWD = os.getcwd()

if not os.path.exists(os.path.join(MY_CWD, 'share/l5rcm')):
    MY_CWD = HERE
    if not os.path.exists(os.path.join(MY_CWD, 'share/l5rcm')):
        MY_CWD = os.path.dirname(HERE)

from l5r.util import log
log.app.info(u"l5rcm base dir: %s", MY_CWD)


def get_app_file(rel_path):
    if os.name == 'nt':
        return os.path.join(MY_CWD, 'share/l5rcm', rel_path)
    else:
        sys_path = '/usr/share/l5rcm'
        if os.path.exists(sys_path):
            return os.path.join(sys_path, rel_path)
        return os.path.join(MY_CWD, 'share/l5rcm', rel_path)


def get_app_icon_path(size=(48, 48)):
    size_str = '%dx%d' % size
    if os.name == 'nt':
        return os.path.join(MY_CWD, 'share/icons/l5rcm/%s' % size_str, APP_NAME + '.png')
    else:
        sys_path = '/usr/share/icons/l5rcm/%s' % size_str
        if os.path.exists(sys_path):
            return os.path.join(sys_path, APP_NAME + '.png')
        return os.path.join(MY_CWD, 'share/icons/l5rcm/%s' % size_str, APP_NAME + '.png')


def get_tab_icon(name):
    if os.name == 'nt':
        return os.path.join(MY_CWD, 'share/icons/l5rcm/tabs/', name + '.png')
    else:
        sys_path = '/usr/share/icons/l5rcm/tabs/'
        if os.path.exists(sys_path):
            return os.path.join(sys_path, name + '.png')
        return os.path.join(MY_CWD, 'share/icons/l5rcm/tabs/', name + '.png')


def get_icon_path(name, size=(48, 48)):
    base = "share/icons/l5rcm/"
    if size is not None:
        base += '%dx%d' % size

    if os.name == 'nt':
        return os.path.join(MY_CWD, base, name + '.png')
    else:
        sys_path = '/usr/' + base
        if os.path.exists(sys_path):
            return os.path.join(sys_path, name + '.png')
        return os.path.join(MY_CWD, base, name + '.png')
