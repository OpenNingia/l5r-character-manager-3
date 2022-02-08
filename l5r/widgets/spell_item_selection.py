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

import sys

import l5r.api as api
import l5r.api.character.spells
import l5r.api.data.spells
from l5r.util import log

from PyQt5 import QtCore, QtGui, QtWidgets

def em(text):
    return u'<em>{}</em>'.format(text)

class SpellItemSelection(QtWidgets.QWidget):

    cb_element = None
    cb_mastery = None
    cb_spell = None

    lb_ring = None
    lb_mastery = None
    lb_spell = None

    form_lo = None

    # filter can be 'no_maho', 'allow_maho' or 'only_maho'
    maho_flt = None
    no_deficiency = None

    pc = None

    # spell blacklist
    blacklist = None

    # text browser for spell description
    tx_descr = None

    # spell changed
    spell_changed = QtCore.pyqtSignal(int)

    def __init__(self, pc, parent=None):
        super(SpellItemSelection, self).__init__(parent)

        self.pc = pc

        self.tag = None
        self.element = None

        self.cb_element = QtWidgets.QComboBox(self)
        self.cb_mastery = QtWidgets.QComboBox(self)
        self.cb_spell = QtWidgets.QComboBox(self)

        self.lb_ring = QtWidgets.QLabel(self.tr('Ring'), self)
        self.lb_mastery = QtWidgets.QLabel(self.tr('Mastery'), self)
        self.lb_spell = QtWidgets.QLabel(self.tr('Spell'), self)
        self.lb_tags = QtWidgets.QLabel(self.tr('Tags'), self)
        self.lb_mastery_mod = QtWidgets.QLabel(self.tr('Mastery modifier:'), self)
        self.lb_book = QtWidgets.QLabel(self)

        self.tx_descr = QtWidgets.QTextEdit(self)
        self.tx_tags = QtWidgets.QLabel(self)
        self.tx_mastery_mod = QtWidgets.QLabel(self)

        self.cb_element.setEditable(False)
        self.cb_mastery.setEditable(False)

        self.tx_descr.setReadOnly(True)        
        self.tx_descr.setLineWrapMode(QtWidgets.QTextEdit.WidgetWidth)
        self.tx_descr.setWordWrapMode(QtGui.QTextOption.WordWrap)

        form_lo = QtWidgets.QFormLayout()
        form_lo.setVerticalSpacing(9)
        form_lo.setHorizontalSpacing(9)
        form_lo.addRow(self.lb_ring, self.cb_element)
        form_lo.addRow(self.lb_mastery, self.cb_mastery)
        form_lo.addRow(self.lb_spell, self.cb_spell)
        form_lo.addRow(self.lb_tags, self.tx_tags)
        form_lo.addRow(self.lb_mastery_mod, self.tx_mastery_mod)

        vbox = QtWidgets.QVBoxLayout(self)
        vbox.addItem(form_lo)
        vbox.addWidget(self.tx_descr)
        vbox.addWidget(self.lb_book)

        self.cb_element.currentIndexChanged.connect(self.on_ring_change)
        self.cb_mastery.currentIndexChanged.connect(self.on_mastery_change)
        self.cb_spell  .currentIndexChanged.connect(self.on_spell_change)

        # Rings are fixed
        self.cb_element.addItem(self.tr('Earth'), 'earth')
        self.cb_element.addItem(self.tr('Air'), 'air')
        self.cb_element.addItem(self.tr('Water'), 'water')
        self.cb_element.addItem(self.tr('Fire'), 'fire')
        self.cb_element.addItem(self.tr('Void'), 'void')
        self.cb_element.addItem(self.tr('Multi-Element'), 'multi')
        self.cb_element.addItem(self.tr('Dragon Spells'), 'dragon')

        # Also masteries are fixed now
        for x in range(0, 6):
            self.cb_mastery.addItem(
                self.tr('Mastery Level {0}').format(x + 1), x + 1)

    def set_blacklist(self, bk):
        self.blacklist = bk
        self.update_spell_list()

    def set_maho_filter(self, filter):
        self.maho_flt = filter
        self.update_spell_list()

    def set_no_defic(self, flag):
        self.no_deficiency = flag
        self.update_spell_list()

    def set_element_restriction(self, ring):
        self.element = ring

    def set_tag_restriction(self, tag):
        self.tag = tag

    def on_ring_change(self, index):
        ring = self.get_ring()
        self.update_spell_list()

    def on_mastery_change(self, index):
        self.update_spell_list()

    def on_spell_change(self, index):
        spell = self.get_spell()
        if spell:
            spell_tags = api.data.spells.tags(spell.id, api.character.schools.get_current())
            self.tx_descr.setText(spell.desc)
            self.tx_tags.setText(', '.join(spell_tags))
            self.update_book(spell)

            self.spell_changed.emit(self.get_spell())

            mmod = api.character.spells.get_mastery_modifier(spell)

            if mmod == 0:
                self.tx_mastery_mod.setText(self.tr("None"))
            elif mmod > 0:
                self.tx_mastery_mod.setText("<span style='color:green'>+{}</span>".format(mmod))
            else:
                self.tx_mastery_mod.setText("<span style='color:red'>{}</span>".format(mmod))

    def update_book(self, spell_data):
        try:
            source_book = spell_data.pack
            page_number = spell_data.page

            if not source_book:
                self.lb_book.setText("")
            elif not page_number:                
                self.lb_book.setText(em(source_book.display_name))
            else:
                self.lb_book.setText(em(self.tr(f"{source_book.display_name}, page {page_number}")))
        except:
            log.ui.error(f'cannot load source book for spell: {spell_data.id}', exc_info=1)

    def update_spell_list(self):

        ring = self.get_ring()
        mastery = self.get_mastery()

        self.cb_spell.clear()

        def get_avail_spells():
            if mastery <= 0:
                return []

            no_defic = self.no_deficiency

            if ring in api.character.spells.deficiencies() and no_defic:
                return []

            if self.maho_flt == 'only_maho':
                return api.data.spells.get_maho_spells(ring, mastery)
            elif self.maho_flt == 'no_maho':
                return api.data.spells.get_spells(ring, mastery, maho=False)
            else:
                return api.data.spells.get_spells(ring, mastery, maho=True)

        avail_spells = get_avail_spells()

        # remove blacklisted spells
        if not self.blacklist:
            self.blacklist = []

        avail_spells = [x for x in avail_spells if x not in self.blacklist]

        if len(avail_spells) == 0:
            self.cb_spell.addItem(self.tr('No spell available'), None)
        else:
            for spell in avail_spells:
                self.cb_spell.addItem(spell.name, spell)

    def set_spell(self, spell):
        if spell:
            log.ui.debug('set spell: {0}', spell.id)

            self.cb_element.blockSignals(True)
            self.cb_mastery.blockSignals(True)

            for i in range(0, self.cb_element.count()):
                if self.cb_element.itemData(i) == spell.element:
                    self.cb_element.setCurrentIndex(i)
                    self.on_ring_change(i)
                    break

            for i in range(0, self.cb_mastery.count()):
                if self.cb_mastery.itemData(i) == spell.mastery:
                    self.cb_mastery.setCurrentIndex(i)
                    self.on_mastery_change(i)
                    break

            self.update_spell_list()

            for i in range(0, self.cb_spell.count()):
                if self.cb_spell.itemData(i) == spell:
                    self.cb_spell.setCurrentIndex(i)
                    break

            self.cb_element.blockSignals(False)
            self.cb_mastery.blockSignals(False)
        else:
            self.cb_element.setCurrentIndex(0)
            self.on_ring_change(0)

        if self.get_spell() is not None:
            self.spell_changed.emit(self.get_spell())

    def get_spell(self):
        return self.cb_spell.itemData(self.cb_spell.currentIndex())

    def get_ring(self):
        return self.cb_element.itemData(self.cb_element.currentIndex())

    def get_mastery(self):
        return self.cb_mastery.itemData(self.cb_mastery.currentIndex()) or 0

    def can_learn(self):
        if not self.get_spell():
            return False
        else:
            return (
                api.character.spells.is_learnable(self.get_spell()) and
                self.match_element_restriction() and
                self.match_tag_restriction())

    def match_tag_restriction(self):
        if not self.tag:
            return True
        spell = self.get_spell()
        if not spell:
            return False
        return api.data.spells.has_tag(spell.id, self.tag, api.character.schools.get_current())

    def match_element_restriction(self):
        if not self.element:
            return True
        spell = self.get_spell()
        if not spell:
            return False

        if self.element[0] == '!':
            return self.element[1:] != spell.element
        return self.element == spell.element
