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

        self.vbox = QtGui.QVBoxLayout(self)
        # self.vbox.setContentsMargins(0, 0, 0, 0)
        self.lbs = []  # disposable labels
        self.checks = []   # checkbox list

    def sizeHint(self):
        return QtCore.QSize(200, len(self.checks) * 20 + len(self.lbs) * 40)

    def set_requirements(self, pc, dstore, requirements):

        self.setUpdatesEnabled(False)
        snap = models.CharacterSnapshot(pc)
        # if self.fr: self.fr.deleteLater()

        for c in self.checks:
            c.deleteLater()
        self.checks = []

        for l in self.lbs:
            l.deleteLater()
        self.lbs = []

        # self.fr = QtGui.QFrame()
        # ly = QtGui.QVBoxLayout(self.fr)

        for r in requirements:

            ck = QtGui.QCheckBox()
            self.checks.append(ck)

            lb = None
            if type(r) is dal.requirements.RequirementOption:
                ck.setEnabled(False)
            else:
                ck.setEnabled(r.type == 'more')

            if r.type == 'more':
                # if type is more then it's likely the description is verbose
                # better place it on a separated label
                # lb = QtGui.QTextEdit(unicode.format(u"<em>{0}</em>", r.text))
                lb = QtGui.QTextEdit()
                lb.setText(unicode.format(u"<em>{0}</em>", r.text))
                # lb.setWordWrap (True)
                lb.setAlignment(QtCore.Qt.AlignJustify)
                # lb.setBuddy(ck)
                self.lbs.append(lb)

                ck.setText(self.tr("Role play"))
            else:
                ck.setText(r.text)
                # check if requirement match
                ck.setChecked(r.match(snap, dstore))

            self.vbox.addWidget(ck)
            if lb:
                self.vbox.addWidget(lb)

        # self.vbox.addItem(ly)
        self.setUpdatesEnabled(True)

    def match(self):
        for c in self.checks:
            if not c.isChecked():
                return False
        return True

    def match_at_least_one(self):
        if len(self.checks) == 0:
            return True
        for c in self.checks:
            if c.isChecked():
                return True
        return False
