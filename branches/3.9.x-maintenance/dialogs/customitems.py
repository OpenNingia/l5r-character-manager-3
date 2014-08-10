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

import models
import rules
import dal
import dal.query

from PySide import QtCore, QtGui

def grouped_widget(title, widget, parent = None):
    grp     = QtGui.QGroupBox(title, parent)
    vbox    = QtGui.QVBoxLayout(grp)
    vbox.addWidget(widget)
    
    return grp

class CustomArmorDialog(QtGui.QDialog):
    def __init__(self, pc, parent = None):
        super(CustomArmorDialog, self).__init__(parent)
        self.pc  = pc
        self.item = None
        self.build_ui()
        self.load_data()
        
    def build_ui(self):
        self.setWindowTitle(self.tr("Add Custom Armor"))
            
        self.setMinimumSize(400, 0)
                        
        self.bt_accept = QtGui.QPushButton(self.tr("Ok")    , self)
        self.bt_cancel = QtGui.QPushButton(self.tr("Cancel"), self)            
        
        lvbox = QtGui.QVBoxLayout(self)
        self.tx_name = QtGui.QLineEdit(self)           
        lvbox.addWidget(grouped_widget(self.tr("Name"), self.tx_name, self))

        self.tx_tn = QtGui.QLineEdit(self)                
        self.tx_rd = QtGui.QLineEdit(self) 
        fr      = QtGui.QFrame(self)
        hbox    = QtGui.QHBoxLayout(fr)
        hbox.addWidget(grouped_widget(self.tr("Armor TN" ), self.tx_tn, self))
        hbox.addWidget(grouped_widget(self.tr("Reduction"), self.tx_rd, self))      
        lvbox.addWidget(fr)
        
        self.tx_notes = QtGui.QTextEdit(self)         
        lvbox.addWidget(grouped_widget(self.tr("Notes"), self.tx_notes, self))
        
        self.btbox = QtGui.QDialogButtonBox(QtCore.Qt.Horizontal)
        self.btbox.addButton(self.bt_accept, QtGui.QDialogButtonBox.AcceptRole)
        self.btbox.addButton(self.bt_cancel, QtGui.QDialogButtonBox.RejectRole)
        
        self.btbox.accepted.connect(self.on_accept)
        self.btbox.rejected.connect(self.close    )
        
        lvbox.addWidget(self.btbox)
        
    def load_data(self):
        if self.pc.armor is None:
            return
        self.tx_name .setText(self.pc.armor.name    )
        self.tx_tn   .setText(str(self.pc.armor.tn) )
        self.tx_rd   .setText(str(self.pc.armor.rd) )
        self.tx_notes.setText(self.pc.armor.desc)
            
    def on_accept(self):
        self.item = models.ArmorOutfit()
        try:
            self.item.tn   = int(self.tx_tn.text())
            self.item.rd   = int(self.tx_rd.text())
        except:
            self.item.tn   = 0
            self.item.rd   = 0
        
        self.item.name = self.tx_name.text()
        self.item.desc = self.tx_notes.toPlainText()
        
        if self.item.name == '':
            QtGui.QMessageBox.warning(self, self.tr("Custom Armor"),
                                      self.tr("Please enter a name."))
            return
        
        self.pc.armor = self.item
        self.accept()

class CustomWeaponDialog(QtGui.QDialog):
    def __init__(self, pc, dstore, parent = None):
        super(CustomWeaponDialog, self).__init__(parent)
        self.pc  = pc
        self.dstore  = dstore
        self.item = None
        self.edit_mode = False
        self.build_ui()
        self.load_data()
        
    def build_ui(self):
        self.setWindowTitle(self.tr("Add Custom Weapon"))
            
        self.setMinimumSize(400, 0)
                        
        self.bt_accept = QtGui.QPushButton(self.tr("Ok")    , self)
        self.bt_cancel = QtGui.QPushButton(self.tr("Cancel"), self)            
        
        # Weapon Name
        lvbox = QtGui.QVBoxLayout(self)
        self.tx_name = QtGui.QLineEdit(self)           
        lvbox.addWidget(grouped_widget(self.tr("Name"), self.tx_name, self))
        
        # Base Weapon
        self.cb_base_weap = QtGui.QComboBox(self)
        lvbox.addWidget(grouped_widget(self.tr("Base Weapon"), self.cb_base_weap, self))        
        self.cb_base_weap.currentIndexChanged.connect( self.on_base_weap_change )
        
        # Stats
        stats_fr = QtGui.QFrame(self)
        form_lo  = QtGui.QFormLayout(stats_fr)        
        
        self.tx_dr      = QtGui.QLineEdit(self)
        self.tx_dr_alt  = QtGui.QLineEdit(self)
        self.tx_rng     = QtGui.QLineEdit(self)
        self.tx_str     = QtGui.QLineEdit(self)
        self.tx_min_str = QtGui.QLineEdit(self)
        
        form_lo.addRow(self.tr("Primary DR"     ), self.tx_dr)
        form_lo.addRow(self.tr("Secondary DR"   ), self.tx_dr_alt)
        form_lo.addRow(self.tr("Range"          ), self.tx_rng)
        form_lo.addRow(self.tr("Weapon Strength"), self.tx_str)
        form_lo.addRow(self.tr("Min. Strength"  ), self.tx_min_str)
        
        lvbox.addWidget(grouped_widget(self.tr("Stats"), stats_fr, self))
        
        self.tx_notes = QtGui.QTextEdit(self)         
        lvbox.addWidget(grouped_widget(self.tr("Notes"), self.tx_notes, self))
        
        self.btbox = QtGui.QDialogButtonBox(QtCore.Qt.Horizontal)
        self.btbox.addButton(self.bt_accept, QtGui.QDialogButtonBox.AcceptRole)
        self.btbox.addButton(self.bt_cancel, QtGui.QDialogButtonBox.RejectRole)
        
        self.btbox.accepted.connect(self.on_accept)
        self.btbox.rejected.connect(self.close    )
        
        lvbox.addWidget(self.btbox)
        
    def load_data(self):                            
        for weapon in self.dstore.weapons:
            self.cb_base_weap.addItem(weapon.name, weapon.name)
                
    def load_item(self, item):
        self.tx_name    .setText( item.name   )
        self.tx_dr      .setText( item.dr     )
        self.tx_dr_alt  .setText( item.dr_alt )
        self.tx_rng     .setText( item.range  )
        self.tx_notes   .setText( item.rule   )
        self.tx_str     .setText( str(item.strength) )
        self.tx_min_str .setText( str(item.min_str)  )        
        self.item = item
        self.cb_base_weap.setVisible(False)

    def on_base_weap_change(self, text = ''):        
        selected = self.cb_base_weap.currentIndex()
        if selected < 0:
            return
            
        weap_uuid = self.cb_base_weap.itemData(selected)
        self.item = itm = models.weapon_outfit_from_db(self.dstore, weap_uuid)
        
        self.tx_str    .setText( str(itm.strength) )
        self.tx_min_str.setText( str(itm.min_str)  )

        self.tx_dr     .setText( itm.dr     )
        self.tx_dr_alt .setText( itm.dr_alt )               
        self.tx_rng    .setText( itm.range  )
        self.tx_name   .setText( itm.name   )
        self.tx_notes  .setText( itm.rule   )
        
        print(self.item.__dict__)
        
    def on_accept(self):
        if not self.item:
            self.item = models.WeaponOutfit()
        
        def _try_get_int(widget):            
            try: 
                return int(widget.text()) 
            except: 
                return 0
                
        def _try_get_dr(widget):
            text = widget.text()
            r, k = rules.parse_rtk(text)
            return rules.format_rtk(r,k)
        
        self.item.strength = _try_get_int(self.tx_str     )
        self.item.min_str  = _try_get_int(self.tx_min_str )

        self.item.dr     = _try_get_dr(self.tx_dr    ) or self.tr("N/A")
        self.item.dr_alt = _try_get_dr(self.tx_dr_alt) or self.tr("N/A")
        self.item.range  = self.tx_rng  .text()      
        self.item.name   = self.tx_name .text()
        self.item.rule   = self.tx_notes.toPlainText()
        
        if self.item.name == '':
            QtGui.QMessageBox.warning(self, self.tr("Custom Weapon"),
                                      self.tr("Please enter a name."))
            return
        if not self.edit_mode:
            #print('add {0}, tags: {1}'.format(self.item.name, self.item.tags))
            self.pc.add_weapon( self.item )
        self.accept()
        