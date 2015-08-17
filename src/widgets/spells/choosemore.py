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
import api.data.spells
import api.data.schools
import api.character.rankadv

from chooseone import ChooseOneSpell
from PySide import QtCore, QtGui
from asq.initiators import query
from asq.selectors import a_
from copy import deepcopy
from l5rcmcore import get_icon_path

def blue(text):
    return u'<p style="color: #00A"><em>{}</em></p>'.format(text)

def selected(text):
    return u'<p style="background: #00A color: #FFF"><em>{}</em></p>'.format(text)

class ChooseMoreSpells(QtGui.QWidget):

    statusChanged = QtCore.Signal(bool)

    chooser = None
    header = None
    footer = None
    bt_prev = None
    bt_next = None
    tx_spells = None
    school = None
    current = 0
    tot = 0
    selected = []

    def __init__(self, parent = None):
        super(ChooseMoreSpells, self).__init__(parent)

        self.header = QtGui.QLabel(self)
        self.footer = QtGui.QLabel(self)

        self.chooser = ChooseOneSpell(self)
        self.chooser.set_exclude_owned(True)

        self.bt_prev = QtGui.QToolButton(self)
        self.bt_next = QtGui.QToolButton(self)

        self.bt_prev.setIcon(QtGui.QIcon(get_icon_path('arrow_left', (16, 16))))
        self.bt_next.setIcon(QtGui.QIcon(get_icon_path('arrow_right', (16, 16))))
        self.bt_prev.setAutoRaise(True)
        self.bt_next.setAutoRaise(True)

        # area with list of learned skills
        self.tx_spells = QtGui.QTextEdit(self)
        self.tx_spells.setReadOnly(True)

        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(self.bt_prev)
        hbox.addWidget(self.chooser)
        hbox.addWidget(self.bt_next)

        vbox = QtGui.QVBoxLayout(self)
        vbox.addWidget(self.header)
        vbox.addItem(hbox)
        vbox.addWidget(self.footer)
        vbox.addWidget(self.tx_spells)

        self.vbl = vbox

        self.bt_prev.clicked.connect(self.on_prev)
        self.bt_next.clicked.connect(self.on_next)

        self.chooser.valueChanged.connect(self.on_spell_chooser_value_changed)

    def load(self):
        self.current = 0
        self.school = api.character.rankadv.get_current().school
        self.tot = (len(api.data.schools.get_spells_to_choose(self.school)))
        self.update()

    def update(self):
        self.update_chooser()

        self.update_header()
        self.update_footer()

        self.update_buttons()

        self.update_spells()

        if len(self.selected) == self.tot:
            self.statusChanged.emit(True)

    def update_header(self):

        def update_header_skill_chooser():

            stc = api.data.schools.get_spells_to_choose(self.school)

            if len(stc) <= self.current:
                return ""

            wc = stc[self.current]

            if not wc:
                return ""

            # wl = wc.wildcards
            # if len(wl):
            #     inclusive = api.data.skills.get_inclusive_tags(wl)
            #     exclusive = api.data.skills.get_exclusive_tags(wl)
            #
            #     exclusive_string = self.tr("not {0} skill").format(', '.join(exclusive))
            #
            #     if wl[0].value == 'any':
            #         inclusive_string = self.tr('Any skill')
            #     else:
            #         inclusive_string = self.tr('Any {0} skill').format(self.tr(' or ').join(inclusive))
            #
            #     if len(exclusive):
            #         lb = self.tr('{0}, {1} (rank {2}):').format(inclusive_string, exclusive_string, wc.rank)
            #     else:
            #         lb = self.tr('{0} (rank {1}):').format(inclusive_string, wc.rank)
            #     return lb
            return ""

    def update_footer(self):
        self.footer.setText(self.tr("{0} of {1}").format(self.current+1, self.tot))

    def update_spells(self):

        html = '<div style="margin-right: 50; margin-top: 50; font-size: 14pt;">'

        # def normal_spell(name, element, mastery):
        #     return '<p>{0}: {1}</p>'.format(name, mastery)
        #
        # def wildcard_skill(name, rank):
        #     if emph:
        #         return '<p style="color: #00A">{0}: {1} ({2})</p>'.format(name, rank, emph)
        #     return '<p style="color: #00A">{0}: {1}</p>'.format(name, rank)
        #
        # def current_skill(name, rank, emph = None):
        #     if emph:
        #         return '<p style="color: #FFF; background: #23E">{0}: {1} ({2})</p>'.format(name, rank, emph)
        #     return '<p style="color: #FFF; background: #23E">{0}: {1}</p>'.format(name, rank)
        #
        # for s in api.data.schools.get_skills(self.school):
        #     if s.emph and s.emph.startswith('*'):
        #         html += normal_skill(api.data.skills.get(s.id).name, s.rank, self.get_emph_selected_for(s.id))
        #     else:
        #         html += normal_skill(api.data.skills.get(s.id).name, s.rank, s.emph)
        #
        # for i, wc in enumerate(api.data.schools.get_skills_to_choose(self.school)):
        #     if len(self.selected) > i:
        #         if i == self.current:
        #             html += current_skill(self.selected[i], wc.rank)
        #         else:
        #             html += wildcard_skill(self.selected[i], wc.rank)

        html += '</div>'
        self.tx_spells.setHtml(html)

    def update_buttons(self):

        self.bt_next.setEnabled(self.current < self.tot - 1)
        self.bt_prev.setEnabled(self.current > 0)

    def update_chooser(self):

        def update_spell_chooser():

            # already selected
            if len(self.selected) > self.current:
                self.chooser.blockSignals(True)

            stc = api.data.schools.get_spells_to_choose(self.school)
            wildcard_filter = []
            owned_filter = []
            if len(stc) > self.current:
                wildcard_filter = stc[self.current].wildcards

            owned_filter = [x.id for x in self.selected]

            print('owned filter 1', owned_filter, self.current)
            if len(self.selected) > self.current and self.selected[self.current].id in owned_filter:
                owned_filter.remove(self.selected[self.current].id)

            print('owned filter 2', owned_filter, self.current)
            self.chooser.set_filter(wildcard_filter, owned_filter)
            self.chooser.load()

            # update chooser value with saved one
            if len(self.selected) > self.current:
                if self.selected[self.current]:
                    print('set chooser skill', self.selected[self.current].id, 'idx', self.current)
                    self.chooser.set(self.selected[self.current])
                else:
                    print('selected at', self.current, 'is none')

        # enable/disable chooser
        self.chooser.setEnabled(self.tot > self.current)

        update_spell_chooser()

        self.chooser.blockSignals(False)

    def select_current_spell(self):
        sp = self.chooser.spell

        if not sp and len(self.selected) > self.current:
            del self.selected[self.current]

        if sp:
            print('set spell', sp.id, 'idx', self.current)
            if len(self.selected) <= self.current:
                self.selected.append(self.chooser.spell)
            else:
                self.selected[self.current] = self.chooser.spell

    def on_prev(self):
        self.current -= 1
        self.update()

    def on_next(self):
        self.current += 1
        self.update()

    def on_spell_chooser_value_changed(self, val):
        self.select_current_spell()
        self.update()
