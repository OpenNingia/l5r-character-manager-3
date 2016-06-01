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
import l5r.models as models

from copy import copy

from PyQt5 import QtCore, QtGui, QtWidgets


def paintLayout(painter, item):
    layout = item.layout()
    if layout:
        for i in range(0, layout.count()):
            paintLayout(painter, layout.itemAt(i))
    painter.drawRect(item.geometry())


def clearLayout(item):
    layout = item.layout()
    if layout:
        for i in range(0, layout.count()):
            sub_item = layout.itemAt(i)
            clearLayout(sub_item)
            layout.removeItem(sub_item)

class RequirementsWidget(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super(RequirementsWidget, self).__init__(parent)

        self.vbox = QtWidgets.QVBoxLayout(self)
        self.vbox.setContentsMargins(0, 0, 0, 0)

        self.checks = []   # checkbox list
        self.rpg_placeholders = []
        self.debug = False

        fr = QtWidgets.QFrame()
        ly = QtWidgets.QVBoxLayout(fr)

        # max 10 checkboxes
        for i in range(0, 10):
            ck = QtWidgets.QCheckBox(self)
            ck.setVisible(False)
            ly.addWidget(ck)
            self.checks.append(ck)

        for i in range(0, 5):
            lb = QtWidgets.QLabel(self)
            ck = QtWidgets.QCheckBox(self)
            ck.setVisible(False)
            lb.setVisible(False)

            lb.setWordWrap(True)
            lb.setAlignment(QtCore.Qt.AlignJustify)
            lb.setBuddy(ck)

            ly.addWidget(ck)
            ly.addWidget(lb)
            self.rpg_placeholders.append((lb, ck))

        self.vbox.addWidget(fr)

        self.setSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding)

    def paintEvent(self, ev):
        if not self.debug:
            return
        painter = QtGui.QPainter(self)
        if self.layout():
            paintLayout(painter, self.layout())

    def set_requirements(self, pc, dstore, requirements):

        self.setUpdatesEnabled(False)

        for ck in self.checks:
            ck.setVisible(False)
        for ph in self.rpg_placeholders:
            lb, ck = ph
            lb.setVisible(False)
            ck.setVisible(False)

        self.setUpdatesEnabled(False)
        snap = models.CharacterSnapshot(pc)

        checks_stack = copy(self.checks)
        rpg_stack = copy(self.rpg_placeholders)

        for r in requirements:

            ck = None
            lb = None

            if r.type == 'more':
                ph = rpg_stack.pop()
                lb, ck = ph
                lb.setText(u"<em>{0}</em>".format(r.text))
                ck.setText(self.tr("Role play"))
                ck.setEnabled(True)
            else:
                ck = checks_stack.pop()
                ck.setEnabled(False)
                ck.setText(r.text)
                ck.setChecked(r.match(snap, dstore))

            if ck:
                ck.setVisible(True)
            if lb:
                lb.setVisible(True)

        self.setUpdatesEnabled(True)

    def match(self):
        for c in self.checks:
            if not c.isVisible():
                continue
            if not c.isChecked():
                return False
        for p in self.rpg_placeholders:
            l, c = p
            if not c.isVisible():
                continue
            if not c.isChecked():
                return False
        return True

    def match_at_least_one(self):
        if not self.checks[0].isVisible():
            return True
        for c in self.checks:
            if c.isChecked():
                return True
        return False
