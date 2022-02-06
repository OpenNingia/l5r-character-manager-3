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
__author__ = 'Daniele'


def pause_signals(wdgs):
    """block signals for all the given widgets"""
    for w in wdgs:
        w.blockSignals(True)


def resume_signals(wdgs):
    """resume signals for all the given widgets"""
    for w in wdgs:
        w.blockSignals(False)


class QtSignalLock(object):
    """apply RAI technique to pause and restore signals"""

    def __init__(self, widgets):
        """store widgets"""
        self.widgets = widgets

    def __enter__(self):
        """pause signals on enter"""
        pause_signals(self.widgets)

    def __exit__(self, type, value, tb):
        """resume signals on exit"""
        resume_signals(self.widgets)

