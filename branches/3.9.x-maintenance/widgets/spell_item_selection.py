# Copyright (C) 2011 Daniele Simonetti
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
from PySide import QtCore, QtGui

class SpellItemSelection(QtGui.QWidget):

    cb_element = None
    cb_mastery = None
    cb_spell   = None

    lb_ring    = None
    lb_mastery = None
    lb_spell   = None

    dstore     = None

    form_lo    = None

    # filter can be 'no_maho', 'allow_maho' or 'only_maho'
    maho_flt      = None
    no_deficiency = None

    pc         = None

    # spell blacklist
    blacklist  = None

    # label for spell description
    lb_descr   = None

    def __init__(self, pc, dstore, parent = None):
        super(SpellItemSelection, self).__init__(parent)

        self.dstore = dstore
        self.pc     = pc

        self.tag         = None
        self.max_mastery = 0

        self.cb_element = QtGui.QComboBox(self)
        self.cb_mastery = QtGui.QComboBox(self)
        self.cb_spell   = QtGui.QComboBox(self)

        self.lb_ring    = QtGui.QLabel(self.tr('Ring'), self)
        self.lb_mastery = QtGui.QLabel(self.tr('Mastery'), self)
        self.lb_spell   = QtGui.QLabel(self.tr('Spell'), self)
        self.lb_descr   = QtGui.QLabel(self)
        self.lb_descr.setWordWrap(True)

        self.cb_element.setEditable(False)
        self.cb_mastery.setEditable(False)

        form_lo         = QtGui.QFormLayout()
        form_lo.addRow(self.lb_ring, self.cb_element)
        form_lo.addRow(self.lb_mastery, self.cb_mastery)
        form_lo.addRow(self.lb_spell, self.cb_spell)

        vbox            = QtGui.QVBoxLayout(self)
        vbox.addItem  (form_lo)
        vbox.addWidget(self.lb_descr)

        self.cb_element.currentIndexChanged.connect( self.on_ring_change     )
        self.cb_mastery.currentIndexChanged.connect( self.on_mastery_change  )
        self.cb_spell  .currentIndexChanged.connect( self.on_spell_change    )

        # Rings are fixed
        self.cb_element.addItem(self.tr('Earth'), 'earth')
        self.cb_element.addItem(self.tr('Air'  ), 'air')
        self.cb_element.addItem(self.tr('Water'), 'water')
        self.cb_element.addItem(self.tr('Fire' ), 'fire')
        self.cb_element.addItem(self.tr('Void' ), 'void')

    def set_blacklist(self, bk):
        self.blacklist = bk
        self.update_spell_list()

    def set_maho_filter(self, filter):
        self.maho_flt = filter
        self.update_spell_list()

    def set_no_defic(self, flag):
        self.no_deficiency = flag
        self.update_spell_list()

    def set_fixed_ring(self, ring):
        print('set_fixed_ring', ring)
        if not ring:
            self.cb_element.setEnabled(True)
            return
        if ring.startswith('!'):
            ring = ring[1:]
            for i in xrange(0, self.cb_element.count()):
                if self.cb_element.itemData(i) == ring:
                    self.cb_element.removeItem(i)
                    break
        else:
            for i in xrange(0, self.cb_element.count()):
                if self.cb_element.itemData(i) == ring:
                    self.cb_element.setCurrentIndex(i)
                    break

    def set_spell_tag(self, tag):
        self.tag = tag

    def on_ring_change(self, index):

        ring  = self.cb_element.itemData( self.cb_element.currentIndex() )

        # SPECIAL FLAGS
        only_maho = self.maho_flt == 'only_maho'
        no_defic  = self.no_deficiency

        # UPDATE MASTERY COMBOBOX BASED ON AFFINITY/DEFICIENCY
        affin = [ x for x in self.pc.get_affinity() if x not in self.pc.get_deficiency() ]
        defic = [ x for x in self.pc.get_deficiency() if x not in self.pc.get_affinity() ]

        self.cb_mastery.blockSignals(True)
        self.cb_mastery.clear()

        mod_ = 0
        for a in affin:
            if a == ring or ring in a: mod_ = 1
        for d in defic:
            if d == ring and not only_maho: mod_ = -1

        school_id = self.pc.get_school_id()

        # special handling of scorpion_yogo_wardmaster_school
        if school_id == 'scorpion_yogo_wardmaster_school':
            if self.tag == 'wards': mod_ = 1

        print("affinity: {0}, deficiency: {1}, element: {2}".format(affin, defic, ring))
        print('max mastery: {0}'.format(self.pc.get_insight_rank()+mod_))

        self.max_mastery = self.pc.get_insight_rank() + mod_;

        for x in xrange(0, self.max_mastery):
            self.cb_mastery.addItem(self.tr('Mastery Level {0}').format(x+1), x+1)

        self.cb_mastery.blockSignals(False)

        if self.cb_mastery.currentIndex() < 0:
            self.cb_mastery.setCurrentIndex(0)

        mastery = self.cb_mastery.itemData( self.cb_mastery.currentIndex() ) or 0

        if defic == ring and no_defic:
            self.cb_spell.clear()
        else:
            self.update_spell_list()

    def on_mastery_change(self, index):

        ring  = self.cb_element.itemData( self.cb_element.currentIndex() )
        mastery  = self.cb_mastery.itemData( self.cb_mastery.currentIndex() ) or 0

        affin = [ x for x in self.pc.get_affinity() if x not in self.pc.get_deficiency() ]
        defic = [ x for x in self.pc.get_deficiency() if x not in self.pc.get_affinity() ]

        # SPECIAL FLAGS
        only_maho = self.maho_flt == 'only_maho'
        no_defic  = self.no_deficiency

        if defic == ring and no_defic:
            self.cb_spell.clear()
        else:
            self.update_spell_list()

    def on_spell_change(self, index):
        spell  = self.cb_spell.itemData( self.cb_spell.currentIndex() )
        if spell: self.lb_descr.setText(
            "<em>{}</em>".format(spell.desc))

    def update_spell_list(self):
        ring  = self.cb_element.itemData( self.cb_element.currentIndex() )
        mastery  = self.cb_mastery.itemData( self.cb_mastery.currentIndex() ) or 0

        self.cb_spell.clear()

        def get_avail_spells():
            if mastery <= 0:
                return []

            no_defic  = self.no_deficiency
            defic     = [ x for x in self.pc.get_deficiency() if x not in self.pc.get_affinity() ]

            if ring in defic and no_defic:
                return []

            if self.maho_flt == 'only_maho':
                return dal.query.get_maho_spells(self.dstore, ring, mastery)
            elif self.maho_flt == 'no_maho':
                return [ x for x in dal.query.get_spells(self.dstore, ring, mastery) if 'maho' not in x.tags ]
            elif self.tag is not None:
                return [ x for x in dal.query.get_spells(self.dstore, ring, mastery) if self.tag in x.tags ]
            else:
                return dal.query.get_spells(self.dstore, ring, mastery)

        avail_spells = get_avail_spells()
        school_id    = self.pc.get_school_id()

        # special handling of scorpion_yogo_wardmaster_school
        if school_id == 'scorpion_yogo_wardmaster_school':
            if mastery == self.max_mastery:
                avail_spells = [x for x in avail_spells if 'travel' not in x.tags and 'craft' not in x.tags]

        # remove blacklisted spells
        if not self.blacklist:
            self.blacklist = []

        avail_spells = [ x for x in avail_spells if x not in self.blacklist ]

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

            for i in xrange(0, self.cb_element.count()):
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

    def get_spell(self):
        return self.cb_spell.itemData(self.cb_spell.currentIndex())
