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

import dal
import dal.query
import models
import widgets
from PySide import QtCore, QtGui

class SpellAdvDialog(QtGui.QDialog):

    # character model
    pc             = None
    # data storage
    dstore         = None
    # error bar, visible on error
    error_bar      = None
    # title bar
    header         = None
    # widget for spell selection
    spell_wdg      = None
    # label for page count
    lb_pgcnt       = None
    # buttons
    bt_next        = None
    bt_back        = None
    # page counter and current page pointer
    page_count     = 1
    current_page   = 0
    # radio buttons for maho options
    grp_maho       = None
    rb_omaho       = None
    rb_amaho       = None
    rb_nmaho       = None
    # frame layout
    vbox_lo        = None
    # selected spells
    selected       = None
    # modality, can be 'bounded' or 'freeform'
    mode           = None
    # array of properties per page, each property is a dictionary
    properties     = None
    # max pages
    max_page_count = 50

    def __init__(self, pc, dstore, mode = 'bounded', parent = None):
        super(SpellAdvDialog, self).__init__(parent)
        self.pc  = pc
        self.mode = mode
        self.dstore = dstore
        if mode == 'bounded':
            self.page_count = self.pc.get_how_many_spell_i_miss()
        self.properties = [None]*self.max_page_count
        self.build_ui()
        self.connect_signals()
        self.setup()
        self.load_data()

    def build_ui(self):
        self.vbox_lo = QtGui.QVBoxLayout(self)
        self.bt_next  = QtGui.QPushButton(self.tr('Next'), self)
        self.bt_back  = QtGui.QPushButton(self.tr('Back'), self)
        self.lb_pgcnt = QtGui.QLabel(self)
        self.spell_wdg = widgets.SpellItemSelection(self.pc, self.dstore, self)
        self.header    = QtGui.QLabel(self)
        self.error_bar = QtGui.QLabel(self)

        center_fr      = QtGui.QFrame(self)
        cfr_vbox       = QtGui.QVBoxLayout(center_fr)

        self.grp_maho  = QtGui.QGroupBox(self.tr('Maho'), self)
        bottom_bar     = QtGui.QFrame(self)

        self.rb_amaho       = QtGui.QRadioButton(self.tr('Allow Maho'), self)
        self.rb_nmaho       = QtGui.QRadioButton(self.tr('No Maho'),    self)
        self.rb_omaho       = QtGui.QRadioButton(self.tr('Only Maho'),  self)

        self.rb_amaho.setProperty('tag', 'allow_maho')
        self.rb_nmaho.setProperty('tag', 'no_maho'   )
        self.rb_omaho.setProperty('tag', 'only_maho' )

        # maho groupbox
        maho_hbox = QtGui.QHBoxLayout(self.grp_maho)
        maho_hbox.addWidget(self.rb_amaho)
        maho_hbox.addWidget(self.rb_nmaho)
        maho_hbox.addWidget(self.rb_omaho)

        self.rb_amaho.setChecked(True)

        # bottom bar
        hbox = QtGui.QHBoxLayout(bottom_bar)
        hbox.addWidget(self.lb_pgcnt)
        hbox.addStretch()
        hbox.addWidget(self.bt_back)
        hbox.addWidget(self.bt_next)

        cfr_vbox.addWidget(self.spell_wdg)
        cfr_vbox.addWidget(self.grp_maho)
        cfr_vbox.setContentsMargins(100, 20, 100, 20)

        self.vbox_lo.addWidget(self.header)
        self.vbox_lo.addWidget(center_fr)
        self.vbox_lo.addWidget(self.error_bar)
        self.vbox_lo.addWidget(bottom_bar)

        self.resize( 600, 400 )
        self.update_label_count()

    def connect_signals(self):
        self.bt_next.clicked.connect( self.next_page )
        self.bt_back.clicked.connect( self.prev_page )

        self.rb_amaho.toggled.connect( self.on_maho_toggled )
        self.rb_nmaho.toggled.connect( self.on_maho_toggled )
        self.rb_omaho.toggled.connect( self.on_maho_toggled )

    def load_data(self):
        current_spell = self.selected[self.current_page]
        pc_spells = [dal.query.get_spell(self.dstore, x) for x in self.pc.get_spells()]

        blacklist = pc_spells + [x for x in self.selected if x is not current_spell]

        self.spell_wdg.set_spell(current_spell)
        self.spell_wdg.set_blacklist(blacklist)

        self.bt_back.setVisible(self.current_page != 0)
        if self.current_page == self.page_count-1:
            self.bt_next.setText(self.tr('Finish'))
        else:
            self.bt_next.setText(self.tr('Next'))

        props = self.properties[self.current_page]
        print(self.current_page, props)
        if props:
            if 'maho' in props:
                if props['maho'] == 'only_maho':
                    self.rb_omaho.setChecked(True)
                elif props['maho'] == 'no_maho':
                    self.rb_nmaho.setChecked(True)
                else:
                    self.rb_amaho.setChecked(True)
            self.grp_maho.setEnabled('maho' not in props)
            if 'ring' in props:
                self.spell_wdg.set_fixed_ring(props['ring'])
            else:
                self.spell_wdg.set_fixed_ring(None)

            if 'tag' in props:
                self.spell_wdg.set_spell_tag(props['tag'])

            self.spell_wdg.set_no_defic('no_defic' in props)

        self.update_label_count()

    def setup(self):
        if self.mode == 'bounded':
            idx = 0
            for wc in self.pc.get_pending_wc_spells():
                ring, qty, tag = (None, None, None)

                if len(wc) == 3:
                    ring, qty, tag = wc
                elif len(wc) == 2:
                    ring, qty = wc

                print('wildcard, ring: {0}, qty: {1}, tag: {2}'.format(ring, qty, tag))
                for i in xrange(idx, qty+idx):
                    self.properties[i] = {}
                    self.properties[i]['tag'] = tag
                    if 'maho' in ring:
                        self.properties[i]['maho'] = 'only_maho'
                    #elif models.chmodel.ring_from_name(ring) >= 0:
                    elif 'any' not in ring:
                        self.properties[i]['ring'] = ring
                    if 'nodefic' in ring:
                        self.properties[i]['no_defic'] = True
                idx += qty

            self.page_count = max(idx, self.page_count)
        else:
            self.properties = [None]*self.page_count

        self.selected = [None]*self.page_count

    def set_header_text(self, text):
        self.header.setText(text)

    def update_label_count(self):
        self.lb_pgcnt.setText( self.tr('Page {0} of {1}').format(self.current_page+1, self.page_count) )

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
        self.spell_wdg.set_maho_filter( self.sender().property('tag') )

    def accept(self):
        for s in self.selected:
            if not s: return False # do not exit the form!!!

        self.pc.add_spell(s.id)

        super(SpellAdvDialog, self).accept()

