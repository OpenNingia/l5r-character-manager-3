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

import sys
import models
import dal

from PySide import QtCore, QtGui


class RequirementsWidget(QtGui.QWidget):

    def __init__(self, parent=None):
        super(RequirementsWidget, self).__init__(parent)

        self.label = QtGui.QLabel(self)
        self.label.setWordWrap(True)
        self.label.setSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.MinimumExpanding)
        vbox = QtGui.QVBoxLayout(self)
        # vbox.setContentsMargins(0, 0, 0, 0)
        vbox.addWidget(self.label)
        # vbox.setSizeConstraint(QtGui.QLayout.SetMinimumSize)

        self.reset()

    def green(self, text):
        return u'<p style="color: #0A0"><b>\u221A</b>{}</p>'.format(text)

    def red(self, text):
        return u'<p style="color: #A00"><b>x</b> {}</p>'.format(text)

    def blue(self, text):
        return u'<p style="color: #00A"><em>{}</em></p>'.format(text)

    def sizeHint(self):
        return QtCore.QSize(400, len(self.paragraphs) * 30 + 100 + self.bonus_height)

    def reset(self):
        self.matches_all = True
        self.matches_at_least_one = True
        self.bonus_height = 0
        self.paragraphs = []

    def set_requirements(self, pc, dstore, requirements):

        # self.setUpdatesEnabled(False)
        self.reset()

        snap = models.CharacterSnapshot(pc)

        if len(requirements) > 0:
            self.matches_at_least_one = False

        for r in requirements:
            if r.type == 'more':
                self.matches_at_least_one = True
                self.bonus_height = 400
                self.paragraphs.append(self.blue(r.text))
            elif r.match(snap, dstore):
                self.matches_at_least_one = True
                self.paragraphs.append(self.green(r.text))
            else:
                self.matches_all = False
                self.paragraphs.append(self.red(r.text))

        # self.setUpdatesEnabled(True)

        self.label.setText("\n".join(self.paragraphs))
        self.update()

    def match(self):
        return self.matches_all

    def match_at_least_one(self):
        return self.matches_at_least_one
