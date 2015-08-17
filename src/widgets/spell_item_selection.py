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
import dal
import dal.query

import api.character.spells
import api.data.spells

from PySide import QtCore, QtGui


class SpellItemSelection(QtGui.QWidget):

    cb_element = None
    cb_mastery = None
    cb_spell = None

    lb_ring = None
    lb_mastery = None
    lb_spell = None

    dstore = None

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
    spell_changed = QtCore.Signal(int)

    def __init__(self, pc, dstore, parent=None):
        super(SpellItemSelection, self).__init__(parent)

        self.dstore = dstore
        self.pc = pc

        self.tag = None
        self.element = None

        self.cb_element = QtGui.QComboBox(self)
        self.cb_mastery = QtGui.QComboBox(self)
        self.cb_spell = QtGui.QComboBox(self)

        self.lb_ring = QtGui.QLabel(self.tr('Ring'), self)
        self.lb_mastery = QtGui.QLabel(self.tr('Mastery'), self)
        self.lb_spell = QtGui.QLabel(self.tr('Spell'), self)
        self.lb_tags = QtGui.QLabel(self.tr('Tags'), self)
        self.lb_mastery_mod = QtGui.QLabel(self.tr('Mastery modifier:'), self)

        self.tx_descr = QtGui.QTextEdit(self)
        self.tx_tags = QtGui.QLabel(self)
        self.tx_mastery_mod = QtGui.QLabel(self)

        self.cb_element.setEditable(False)
        self.cb_mastery.setEditable(False)

        monos_ = QtGui.QFont('Monospace')
        monos_.setStyleHint(QtGui.QFont.Courier)

        self.tx_descr.setReadOnly(True)
        self.tx_descr.setFont(monos_)
        self.tx_descr.setLineWrapMode(QtGui.QTextEdit.WidgetWidth)
        self.tx_descr.setWordWrapMode(QtGui.QTextOption.WordWrap)

        form_lo = QtGui.QFormLayout()
        form_lo.setVerticalSpacing(9)
        form_lo.setHorizontalSpacing(9)
        form_lo.addRow(self.lb_ring, self.cb_element)
        form_lo.addRow(self.lb_mastery, self.cb_mastery)
        form_lo.addRow(self.lb_spell, self.cb_spell)
        form_lo.addRow(self.lb_tags, self.tx_tags)
        form_lo.addRow(self.lb_mastery_mod, self.tx_mastery_mod)

        vbox = QtGui.QVBoxLayout(self)
        vbox.addItem(form_lo)
        vbox.addWidget(self.tx_descr)

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
        #self.cb_element.addItem(self.tr('Dragon Spells'), 'dragon')

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

            self.spell_changed.emit(self.get_spell())

            mmod = (
                api.character.spells.special_spell_affinity(spell) -
                api.character.spells.special_spell_deficiency(spell)
            )

            if mmod == 0:
                self.tx_mastery_mod.setText(self.tr("None"))
            elif mmod > 0:
                self.tx_mastery_mod.setText("<span style='color:green'>+{}</span>".format(mmod))
            else:
                self.tx_mastery_mod.setText("<span style='color:red'>{}</span>".format(mmod))

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
                return dal.query.get_maho_spells(self.dstore, ring, mastery)
            elif self.maho_flt == 'no_maho':
                return [x for x in dal.query.get_spells(self.dstore, ring, mastery) if 'maho' not in x.tags]
            else:
                return dal.query.get_spells(self.dstore, ring, mastery)

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
            print('set spell: {0}', spell.id)

            self.cb_element.blockSignals(True)
            self.cb_mastery.blockSignals(True)

            for i in range(0, self.cb_element.count()):
                if self.cb_element.itemData(i) == spell.element:
                    self.cb_element.setCurrentIndex(i)
                    self.on_ring_change(i)
                    break

            for i in xrange(0, self.cb_mastery.count()):
                if self.cb_mastery.itemData(i) == spell.mastery:
                    self.cb_mastery.setCurrentIndex(i)
                    self.on_mastery_change(i)
                    break

            self.update_spell_list()

            for i in xrange(0, self.cb_spell.count()):
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
