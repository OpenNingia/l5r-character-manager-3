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
import api.data.skills
import api.data.schools
import api.character.rankadv

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
    tx_skills = None
    school = None
    current = 0
    selected = []

    def __init__(self, parent = None):
        super(ChooseMoreSkill, self).__init__(parent)

        self.header = QtGui.QLabel(self)
        self.footer = QtGui.QLabel(self)
        self.chooser = ChooseOneSkill(self)
        self.bt_prev = QtGui.QPushButton("<", self)
        self.bt_next = QtGui.QPushButton(">", self)

        # area with list of learned skills
        self.tx_skills = QtGui.QTextEdit(self)
        self.tx_skills.setReadOnly(True)

        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(self.bt_prev)
        hbox.addWidget(self.chooser)
        hbox.addWidget(self.bt_next)

        vbox = QtGui.QVBoxLayout(self)
        vbox.addWidget(self.header)
        vbox.addItem(hbox)
        vbox.addWidget(self.tx_skills)
        vbox.addWidget(self.footer)

        self.vbl = vbox

        self.bt_prev.clicked.connect(self.on_prev)
        self.bt_next.clicked.connect(self.on_next)

    def load(self):
        self.current = 0
        self.school = api.character.rankadv.get_current().school
        self.update()

    def update(self):
        self.update_header()
        self.update_skills()
        self.update_footer()

        if len(self.selected) > self.current:
            self.chooser.set(self.selected)
        else:
            self.chooser.load()

        if len(self.selected) == len(api.data.schools.get_skills_to_choose(self.school)):
            self.statusChanged.emit(True)

    def update_header(self):

        stc = api.data.schools.get_skills_to_choose(self.school)
        wc = stc[self.current]

        if not wc:
            return

        wl = wc.wildcards
        if len(wl):
            or_wc  = [x.value for x in wl if not x.modifier or x.modifier == 'or']
            not_wc = [x.value for x in wl if x.modifier and x.modifier == 'not'  ]

            sw1 = self.tr(' or ').join(or_wc)
            sw2 = ', '.join(not_wc)

            if wl[0].value == 'any':
                sw1 = 'one'

            if len(not_wc):
                lb = self.tr('Any {0}, not {1} skill (rank {2}):').format(sw1, sw2, stc.rank)
            else:
                lb = self.tr('Any {0} skill (rank {1}):').format(sw1, wc.rank)

            self.header.setText(lb)

    def update_footer(self):

        stc = api.data.schools.get_skills_to_choose(self.school)
        self.footer.setText(self.tr("{0} of {1}").format(self.current+1, len(stc)))

    def update_skills(self):

        html = "<ul>"

        def add_skill(name, rank):
            return "<li>{0}: {1}</li>".format(name, rank)

        for s in api.data.schools.get_skills(self.school):
            html += add_skill(api.data.skills.get(s.id).name, s.rank)

        html += "</ul>"
        self.tx_skills.setHtml(html)

    def select_current_skill(self):
        if len(self.selected) <= self.current:
            self.selected.append(self.chooser.skill)
        else:
            self.selected[self.current] = self.chooser.skill

    def on_prev(self):
        self.select_current_skill()
        self.current -= 1
        self.update()

    def on_next(self):
        self.select_current_skill()
        self.current += 1
        self.update()
