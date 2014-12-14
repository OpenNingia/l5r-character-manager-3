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
import api.character.skills as pc_skills
from chooseone import ChooseOneSkill
from PySide import QtCore, QtGui
from asq.initiators import query

class ChooseMoreSkill(QtGui.QWidget):

    statusChanged = QtCore.Signal(bool)

    chooser = None
    header = None
    footer = None
    bt_prev = None
    bt_next = None
    current = 0
    selected = []

    def __init__(self, parent = None):
        super(ChooseMoreSkill, self).__init__(parent)

        self.header = QtGui.QLabel(self)
        self.footer = QtGui.QLabel(self)
        self.chooser = ChooseOneSkill(self)
        self.bt_prev = QtGui.QPushButton("<", self)
        self.bt_next = QtGui.QPushButton(">", self)

        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(self.bt_prev)
        hbox.addWidget(self.chooser)
        hbox.addWidget(self.bt_next)

        vbox = QtGui.QVBoxLayout(self)
        vbox.addWidget(self.header)
        vbox.addItem(hbox)
        vbox.addWidget(self.footer)

        self.vbl = vbox

        self.bt_prev.clicked.connect(self.on_prev)
        self.bt_next.clicked.connect(self.on_next)

    def load(self):
        self.current = 0
        self.update()

    def update(self):
        self.update_header()
        self.update_footer()

        if len(self.selected) > self.current:
            self.chooser.set(self.selected)
        else:
            self.chooser.load()

        if len(self.selected) == len( pc_skills.get_wildcards() ):
            self.statusChanged.emit(True)

    def update_header(self):

        wc = pc_skills.get_wildcard(self.current)
        if not wc:
            return

        wl = ws.wildcards
        if len(wl):
            or_wc  = [x.value for x in wl if not x.modifier or x.modifier == 'or']
            not_wc = [x.value for x in wl if x.modifier and x.modifier == 'not'  ]

            sw1 = self.tr(' or ' ).join (or_wc)
            sw2 = ', '.join(not_wc)

            if ( wl[0].value == 'any' ):
                sw1 = 'one'

            if len(not_wc):
                lb = self.tr('Any {0}, not {1} skill (rank {2}):').format(sw1, sw2, ws.rank)
            else:
                lb = self.tr('Any {0} skill (rank {1}):').format(sw1, ws.rank)

        self.title.setText(lb)

    def update_footer(self):

        wcc = pc_skills.get_wildcards()
        self.footer.setText(self.tr("{0} of {1}").format(self.current+1, len(wcc)))

    def on_prev(self):
        self.current -= 1
        self.update()

    def on_next(self):
        self.current += 1
        self.update()
