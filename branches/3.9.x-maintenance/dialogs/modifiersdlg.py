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
import rules
from PySide import QtCore, QtGui
#from models.modifiers import 
class ModifierDialog(QtGui.QDialog):

    # data storage
    dstore         = None
    # title bar
    header         = None
    # frame layout
    vbox_lo        = None 
    # buttons
    bt_ok          = None
    # controls
    cb_modifier    = None
    tx_value       = None
    tx_detail      = None
    tx_reason      = None
    
    def __init__(self, pc, dstore, parent = None):
        super(ModifierDialog, self).__init__(parent)
        self.pc     = pc
        self.dstore = dstore
        self.item   = None        
        
        self.build_ui       ()
        self.connect_signals()
        self.setup          ()
        
    def build_ui(self):
        self.vbox_lo  = QtGui.QVBoxLayout(self)        
        self.bt_ok    = QtGui.QPushButton(self.tr('Save'), self)        
        self.header   = QtGui.QLabel(self)                                
        center_fr     = QtGui.QFrame(self)
        center_fr.setFrameStyle(QtGui.QFrame.Sunken)
        cfr_fbox      = QtGui.QFormLayout(center_fr)       

        # bottom bar
        bottom_bar     = QtGui.QFrame(self)                                
        hbox = QtGui.QHBoxLayout(bottom_bar)
        hbox.addStretch()
        hbox.addWidget(self.bt_ok)
        
        self.cb_modifier = QtGui.QComboBox(self)
        self.tx_detail   = QtGui.QLineEdit(self)
        self.tx_value    = QtGui.QLineEdit(self)        
        self.tx_reason   = QtGui.QLineEdit(self)
        
        cfr_fbox.addRow(self.tr("Modifier"), self.cb_modifier)
        cfr_fbox.addRow(self.tr("Detail"  ), self.tx_detail  )
        cfr_fbox.addRow(self.tr("Value"   ), self.tx_value   )
        cfr_fbox.addRow(self.tr("Reason"  ), self.tx_reason  )
        
        cfr_fbox.setContentsMargins(160, 20, 160, 20)
        
        self.vbox_lo.addWidget(self.header)
        self.vbox_lo.addWidget(center_fr  )
        self.vbox_lo.addWidget(bottom_bar )
        
        self.resize( 600, 300 )
        
    def connect_signals(self):
        self.bt_ok.clicked.connect( self.accept )
        self.cb_modifier.currentIndexChanged.connect( self.on_modifier_change )
        
    def setup(self):
        self.set_header_text(self.tr('''
        <center>
        <h1>Add or Edit a modifier</h1>
        <p style="color: #666">Modifiers represent the way your character performs better in some contexts</p>
        </center>
        '''))
        
        self.setWindowTitle(self.tr("L5RCM: Modifiers")) 
        self.load_modifier(None)
        
    def load_modifier(self, item):
        
        # modifier's types
        cur_idx = -1
        for mk in models.MOD_TYPES.iterkeys():
            if mk == 'none': continue
            self.cb_modifier.addItem(models.MOD_TYPES[mk], mk)
            if item and mk == item.type:
                cur_idx = self.cb_modifier.count() - 1
        self.cb_modifier.setCurrentIndex(cur_idx)
        
        if item:            
            self.tx_reason .setText( item.reason )
            self.tx_value  .setText( rules.format_rtk_t(item.value) )
            self.tx_detail .setText( item.dtl or ( models.MOD_DTLS[item.type][1] if item.type in models.MOD_DTLS else None ) )           
        
        self.item = item
        
    def set_header_text(self, text):
        self.header.setText(text)
        
    def on_modifier_change(self, idx):
        idx = self.cb_modifier.currentIndex()
        mod = self.cb_modifier.itemData(idx)
        
        def __skill_completer():
            all_skills = []
            for t in self.dstore.skills:
                all_skills.append(t.name)
            cmp = QtGui.QCompleter(all_skills)
            #cmp.setCompletionMode(QtGui.QCompleter.InlineCompletion)
            return cmp
            
        def __weap_completer():
            pc = self.pc
            aweaps = []
            for w in pc.get_weapons():
                aweaps.append(w.name)
            cmp = QtGui.QCompleter(aweaps)
            #cmp.setCompletionMode(QtGui.QCompleter.InlineCompletion)
            return cmp
            
        dtl = models.MOD_DTLS[mod] if mod else 'none' 
        
        # set detail completer
        
        if dtl[0] == 'skill':
            self.tx_detail.setPlaceholderText( self.tr("Type skill name") )
            self.tx_detail.setCompleter(__skill_completer())
            self.tx_detail.setEnabled(True)
        elif dtl[0] == 'aweap':
            self.tx_detail.setPlaceholderText( self.tr("Type weapon name") )
            self.tx_detail.setCompleter(__weap_completer())
            self.tx_detail.setEnabled(True)
        else:
            self.tx_detail.setPlaceholderText("")
            self.tx_detail.setText("")
            self.tx_detail.setEnabled(False)
                           
    def accept(self):
        # save item
        self.item.type   = self.cb_modifier.itemData( self.cb_modifier.currentIndex() )
        self.item.reason = self.tx_reason.text()
        self.item.dtl    = self.tx_detail.text()
        self.item.value  = rules.parse_rtk_with_bonus(self.tx_value.text())
        super(ModifierDialog, self).accept()
            