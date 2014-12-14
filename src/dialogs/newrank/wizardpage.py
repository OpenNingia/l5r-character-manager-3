# Copyright (C) 2014 Daniele Simonetti
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

import os
import sys
from PySide import QtCore, QtGui

class WizardPage (QtGui.QWidget):

    nextAllowed = QtCore.Signal(bool)

    def __init__(self, widget=None, parent=None):
        super(WizardPage, self).__init__(parent)

        self._skippable = False
        self._first = False
        self._final = False

        self.widget = None

    @property
    def skippable(self):
        return self._skippable

    @skippable.setter
    def skippable(self, value):
        self._skippable = value

    @property
    def first(self):
        return self._first

    @first.setter
    def first(self, value):
        self._first = value

    @property
    def final(self):
        return self._final

    @final.setter
    def final(self, value):
        self._final = value

    def get_summary_widget(self):
        return QtGui.QWidget(self)

    def get_h1_text(self):
        return "placeholder"

    def _set_ui(self, w):
        self.widget = w
        hbox = QtGui.QHBoxLayout(self)
        hbox.addStretch()
        hbox.addWidget(w)
        hbox.addStretch()

    def load(self):
        if hasattr(self.widget, 'load'):
            self.widget.load()

    def clear(self):
        if hasattr(self.widget, 'clear'):
            self.widget.clear()

    def apply_rank_advancement(self):
        if hasattr(self.widget, 'apply_rank_advancement'):
            self.widget.apply_rank_advancement()