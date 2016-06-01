# -*- coding: utf-8 -*-
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

import l5r.api as api
import l5r.api.character
import l5r.api.character.schools
import l5r.api.character.spells
import l5r.api.character.rankadv
import l5r.api.data
import l5r.api.data.schools
import l5r.api.data.spells

import l5r.widgets as widgets
from PyQt5 import QtCore, QtGui, QtWidgets


def colored_span(col, text):
    """return a span element with colored text"""
    return "<span style='color:{0}'>{1}</span>".format(col, text)


class SpellAdvDialog(QtWidgets.QDialog):

    # character model
    pc = None
    # error bar, visible on error
    error_bar = None
    # title bar
    header = None
    # widget for spell selection
    spell_wdg = None
    # label for page count
    lb_pgcnt = None
    # buttons
    bt_next = None
    bt_back = None
    # page counter and current page pointer
    page_count = 1
    current_page = 0
    # radio buttons for maho options
    grp_maho = None
    rb_omaho = None
    rb_amaho = None
    rb_nmaho = None
    # frame layout
    vbox_lo = None
    # selected spells
    selected = None
    # modality, can be 'bounded' or 'freeform'
    mode = None
    # array of properties per page, each property is a dictionary
    properties = None
    # max pages
    max_page_count = 50

    def __init__(self, pc, mode='bounded', parent=None):
        super(SpellAdvDialog, self).__init__(parent)
        self.pc = pc
        self.mode = mode

        if mode == 'bounded':
            self.page_count = api.character.rankadv.get_pending_spells_count()
        self.properties = [None] * self.max_page_count
        self.build_ui()
        self.connect_signals()
        self.setup()
        self.load_data()

    def build_ui(self):
        self.vbox_lo = QtWidgets.QVBoxLayout(self)
        self.bt_next = QtWidgets.QPushButton(self.tr('Next'), self)
        self.bt_back = QtWidgets.QPushButton(self.tr('Back'), self)
        self.lb_pgcnt = QtWidgets.QLabel(self)
        self.spell_wdg = widgets.SpellItemSelection(self.pc, self)
        self.header = QtWidgets.QLabel(self)
        self.error_bar = QtWidgets.QLabel(self)

        center_fr = QtWidgets.QFrame(self)
        cfr_vbox = QtWidgets.QVBoxLayout(center_fr)

        # player school
        player_school_id = api.character.schools.get_current()
        player_school_ob = api.data.schools.get(player_school_id)
        player_school_nm = (
            player_school_ob.name if player_school_ob is not None
            else "" )

        lb_school_txt = QtWidgets.QLabel(self.tr("School:"), self)
        lb_school_val = QtWidgets.QLabel(player_school_nm, self)

        # player affinities
        player_affinities_lst = api.character.spells.affinities()
        player_affinities_str = ', '.join(player_affinities_lst)

        lb_aff_txt = QtWidgets.QLabel(self.tr("Affinities:"), self)
        lb_aff_val = QtWidgets.QLabel(player_affinities_str, self)

        player_deficiencies_lst = api.character.spells.deficiencies()
        player_deficiencies_str = ', '.join(player_deficiencies_lst)

        lb_def_txt = QtWidgets.QLabel(self.tr("Deficiencies:"), self)
        lb_def_val = QtWidgets.QLabel(player_deficiencies_str, self)

        if player_deficiencies_str == 'special':
            lb_aff_val.setText(self.tr('See school description'))
        if player_deficiencies_str == 'special':
            lb_def_val.setText(self.tr('See school description'))

        # spell selection
        lb_restrictions = QtWidgets.QLabel(self.tr('Restrictions'), self)
        self.tx_restrictions = QtWidgets.QLabel(self)

        # form layout
        player_info_fr = QtWidgets.QFrame(self)
        player_info_ly = QtWidgets.QFormLayout(player_info_fr)
        player_info_ly.addRow(lb_school_txt, lb_school_val)
        player_info_ly.addRow(lb_aff_txt, lb_aff_val)
        player_info_ly.addRow(lb_def_txt, lb_def_val)
        player_info_ly.addRow(lb_restrictions, self.tx_restrictions)

        self.grp_maho = QtWidgets.QGroupBox(self.tr('Maho'), self)
        bottom_bar = QtWidgets.QFrame(self)

        self.rb_amaho = QtWidgets.QRadioButton(self.tr('Allow Maho'), self)
        self.rb_nmaho = QtWidgets.QRadioButton(self.tr('No Maho'), self)
        self.rb_omaho = QtWidgets.QRadioButton(self.tr('Only Maho'), self)

        self.rb_amaho.setProperty('tag', 'allow_maho')
        self.rb_nmaho.setProperty('tag', 'no_maho')
        self.rb_omaho.setProperty('tag', 'only_maho')

        # maho groupbox
        maho_hbox = QtWidgets.QHBoxLayout(self.grp_maho)
        maho_hbox.addWidget(self.rb_amaho)
        maho_hbox.addWidget(self.rb_nmaho)
        maho_hbox.addWidget(self.rb_omaho)

        self.rb_amaho.setChecked(True)

        # bottom bar
        hbox = QtWidgets.QHBoxLayout(bottom_bar)
        hbox.addWidget(self.lb_pgcnt)
        hbox.addStretch()
        hbox.addWidget(self.bt_back)
        hbox.addWidget(self.bt_next)

        cfr_vbox.addWidget(player_info_fr)
        cfr_vbox.addWidget(self.spell_wdg)
        cfr_vbox.addWidget(self.grp_maho)
        cfr_vbox.setContentsMargins(100, 20, 100, 20)

        self.vbox_lo.addWidget(self.header)
        self.vbox_lo.addWidget(center_fr)
        self.vbox_lo.addWidget(self.error_bar)
        self.vbox_lo.addWidget(bottom_bar)

        self.resize(620, 640)
        self.update_label_count()

    def connect_signals(self):
        self.bt_next.clicked.connect(self.next_page)
        self.bt_back.clicked.connect(self.prev_page)

        self.rb_amaho.toggled.connect(self.on_maho_toggled)
        self.rb_nmaho.toggled.connect(self.on_maho_toggled)
        self.rb_omaho.toggled.connect(self.on_maho_toggled)

        self.spell_wdg.spell_changed.connect(self.on_spell_changed)

    def load_data(self):
        current_spell = self.selected[self.current_page]
        pc_spells = [api.data.spells.get(x) for x in api.character.spells.get_all()]

        blacklist = pc_spells + \
            [x for x in self.selected if x is not current_spell]

        self.spell_wdg.set_spell(current_spell)
        self.spell_wdg.set_blacklist(blacklist)

        self.bt_back.setVisible(self.current_page != 0)
        if self.current_page == self.page_count - 1:
            self.bt_next.setText(self.tr('Finish'))
        else:
            self.bt_next.setText(self.tr('Next'))

        props = self.properties[self.current_page]

        if props:
            self.update_restrictions(props)

            if 'maho' in props:
                if props['maho'] == 'only_maho':
                    self.rb_omaho.setChecked(True)
                elif props['maho'] == 'no_maho':
                    self.rb_nmaho.setChecked(True)
                else:
                    self.rb_amaho.setChecked(True)

            self.grp_maho.setEnabled('maho' not in props)

            if 'ring' in props:
                self.spell_wdg.set_element_restriction(props['ring'])
            else:
                self.spell_wdg.set_element_restriction(None)

            if 'tag' in props:
                self.spell_wdg.set_tag_restriction(props['tag'])

            self.spell_wdg.set_no_defic('no_defic' in props)

        self.update_label_count()

    def setup(self):
        if self.mode == 'bounded':
            idx = 0
            for wc in api.character.rankadv.get_starting_spells_to_choose():
                ring, qty, tag = (None, None, None)

                if len(wc) == 3:
                    ring, qty, tag = wc
                elif len(wc) == 2:
                    ring, qty = wc

                print(
                    'wildcard, ring: {0}, qty: {1}, tag: {2}'.format(ring, qty, tag))
                for i in range(idx, qty + idx):
                    self.properties[i] = {}
                    self.properties[i]['tag'] = tag
                    if 'maho' in ring:
                        self.properties[i]['maho'] = 'only_maho'
                    # elif models.chmodel.ring_from_name(ring) >= 0:
                    elif 'any' not in ring:
                        self.properties[i]['ring'] = ring
                    if 'nodefic' in ring:
                        self.properties[i]['no_defic'] = True
                idx += qty

            self.page_count = max(idx, self.page_count)
        else:
            self.properties = [None] * self.page_count

        self.selected = [None] * self.page_count

    def set_header_text(self, text):
        self.header.setText(text)

    def update_label_count(self):
        self.lb_pgcnt.setText(
            self.tr('Page {0} of {1}').format(self.current_page + 1, self.page_count))

    def next_page(self):
        self.selected[self.current_page] = self.spell_wdg.get_spell()
        if self.current_page == self.page_count - 1:
            self.accept()
        else:
            self.current_page += 1
            self.load_data()

    def prev_page(self):
        self.selected[self.current_page] = self.spell_wdg.get_spell()
        self.current_page -= 1
        self.load_data()

    def on_maho_toggled(self):
        sender_ = self.sender()
        if not sender_.isChecked():
            return
        self.spell_wdg.set_maho_filter(self.sender().property('tag'))

    def on_spell_changed(self, spell):
        self.bt_next.setEnabled(self.spell_wdg.can_learn())

    def update_restrictions(self, properties):
        self.tx_restrictions.setText(
            self.get_restrictions_string(properties)
        )

    def get_restrictions_string(self, properties):
        o = u""

        tag_ = properties['tag'] if 'tag' in properties else None
        ring_ = properties['ring'] if 'ring' in properties else None
        no_maho_ = False
        only_maho_ = False
        no_defic = 'no_defic' in properties

        if 'maho' in properties:
            only_maho_ = properties['maho'] == 'only_maho'
            no_maho_ = properties['maho'] == 'no_maho'

        if ring_ and ring_[0] == '!':
            o = self.tr("any spell but [{0}]").format(colored_span('orange', ring_[1:]))
        elif tag_ and tag_[0] == '!':
            o = self.tr("any spell but [{0}]").format(colored_span('orange', tag_[1:]))
        elif tag_ is not None or ring_ is not None:
            o = self.tr("a [{0}] spell").format(colored_span('navy', tag_ or ring_))
        else:
            o = self.tr("Any spell")

        if no_maho_:
            o += u", {0}".format(self.tr("but Maho spells"))
        elif only_maho_:
            o += u", {0}".format(self.tr("only Maho spells"))

        if no_defic:
            o += u", {0}".format(self.tr("Excluded deficiency"))

        return o

    def accept(self):
        for s in self.selected:
            if not s:
                return False  # do not exit the form!!!

            if self.mode == 'bounded':
                api.character.spells.add_school_spell(s.id)
            else:
                api.character.spells.add_spell(s.id)
            # self.pc.add_spell(s.id)

        super(SpellAdvDialog, self).accept()
