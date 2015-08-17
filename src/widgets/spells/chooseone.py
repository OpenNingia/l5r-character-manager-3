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
import api.character.spells
import api.character.rankadv

from widgets.searchbox import SearchBox

from PySide import QtCore, QtGui
from asq.initiators import query
from asq.selectors import a_


class ChooseOneSpell(QtGui.QWidget):
    valueChanged = QtCore.Signal(object)

    cb_element = None
    cb_mastery = None
    cb_spell = None

    sb_search = None

    # filters
    exclude_owned = False
    exclude_maho = True
    only_maho = False
    exclude_deficiency = False

    spells_to_show = []

    @property
    def spell(self):
        return api.data.spell.get(self.get_selected_spell())

    def __init__(self, parent=None):
        super(ChooseOneSpell, self).__init__(parent)

        self.cb_element = QtGui.QComboBox(self)
        self.cb_mastery = QtGui.QComboBox(self)
        self.cb_spell = QtGui.QComboBox(self)
        self.sb_search = SearchBox(self)

        form = QtGui.QFormLayout(self)

        form.addRow("", self.sb_search)
        form.addRow(self.tr("Ring"), self.cb_element)
        form.addRow(self.tr("Mastery"), self.cb_mastery)
        form.addRow(self.tr("Spell"), self.cb_spell)

        # vbox.addWidget(self.sb_search)
        #vbox.addItem(form)

        #self.vbl = vbox
        self.fol = form

        self.connect_signals()

    def sizeHint(self):
        return QtCore.QSize(440, 320)

    def set_exclude_owned(self, flag):
        self.exclude_owned = flag

    def set_exclude_maho(self, flag):
        self.exclude_maho = flag

    def set_only_maho(self, flag):
        self.only_maho = flag

    def set_exclude_deficiency(self, flag):
        self.exclude_deficiency = flag

    def load(self):
        self.load_spells()

    def set(self, spell):
        if not spell:
            return

        self.blockSignals(True)
        self.cb_spell.blockSignals(True)

        self.set_element(spell.element)
        self.set_mastery(spell.mastery)

        idx = self.cb_spell.findData(spell.id)
        self.cb_spell.setCurrentIndex(idx)
        self.cb_spell.blockSignals(False)

        self.blockSignals(False)

    def connect_signals(self):
        self.cb_element.currentIndexChanged.connect(self.on_element_changed)
        self.cb_mastery.currentIndexChanged.connect(self.on_mastery_changed)
        self.cb_spell.currentIndexChanged.connect(self.on_spell_changed)
        self.sb_search.newSearch.connect(self.on_search)

    def load_spells(self):

        spells_to_show = api.data.spell.character_can_learn()

        if self.only_maho:
            pass
            # todo
        elif self.exclude_maho:
            pass
            # todo

        if self.exclude_deficiency:
            pass
            # todo

        if self.exclude_owned:
            # exclude owned spells
            spells_to_show = query(spells_to_show) \
                .where(lambda x: x.id not in api.character.spells.all()).to_list()

            # exclude skills already in advancement
            spells_to_show = query(spells_to_show) \
                .where(lambda x: x.id not in api.character.rankadv.get_current().spells).to_list()

            # exclude common spells

        self.spells_to_show = spells_to_show

        self.update_elements()

    def update_elements(self):
        elements = query(self.spells_to_show) \
            .distinct(a_('element')) \
            .select(a_('element')).to_list()

        self.cb_element.blockSignals(True)
        self.cb_element.clear()
        for r in api.data.rings():
            if r.id in elements:
                self.cb_element.addItem(r.name, r.id)
        self.cb_element.blockSignals(False)

        if self.cb_element.count() > 0:
            self.on_element_changed(0)

    def update_masteries(self):

        if self.cb_element.currentIndex() < 0:
            return

        elmt = self.get_selected_element()

        masteries = query(self.spells_to_show) \
            .where(lambda x: x.element == elmt) \
            .order_by(a_('mastery')) \
            .distinct(a_('mastery')) \
            .select(a_('mastery')).to_list()

        self.cb_mastery.blockSignals(True)
        self.cb_mastery.clear()
        for r in masteries:
            self.cb_mastery.addItem(r, r)
        self.cb_mastery.blockSignals(False)

        if self.cb_mastery.count() > 0:
            self.on_mastery_changed(0)

    def update_spells(self):

        elmt = self.get_selected_element()
        mstr = self.get_selected_mastery()

        spells = query(self.spells_to_show) \
            .where(lambda x: x.element == elmt and x.mastery == mstr) \
            .order_by(lambda x: x.name)

        self.cb_spell.blockSignals(True)
        self.cb_spell.clear()
        for c in spells:
            self.cb_spell.addItem(c.name, c.id)
        self.cb_spell.blockSignals(False)

        if self.cb_spell.count() > 0:
            self.on_spell_changed(0)

    def get_selected_element(self):
        return self.cb_element.itemData(self.cb_element.currentIndex())

    def get_selected_mastery(self):
        return self.cb_mastery.itemData(self.cb_mastery.currentIndex())

    def get_selected_spell(self):
        return self.cb_spell.itemData(self.cb_spell.currentIndex())

    def on_element_changed(self, idx):
        self.update_masteries()

    def on_mastery_changed(self, idx):
        self.update_spells()

    def on_spell_changed(self, idx):

        if self.signalsBlocked():
            return

        sp = self.get_selected_spell()
        self.valueChanged.emit(sp)

    def on_search(self, tx):

        # search spell
        found_spells = api.data.spells.search_spell_by_text(tx.lower())
        learnable_spells = [x for x in found_spells if x in self.spells_to_show]
        if len(learnable_spells):
            self.set(learnable_spells[0])
            return

    # def set_categ(self, categ):
    #     idx = self.cb_categories.findData(categ)
    #     self.cb_categories.setCurrentIndex(idx)
