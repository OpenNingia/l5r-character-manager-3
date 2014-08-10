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
import dal
import dal.query
import widgets

from PySide import QtCore, QtGui

class BuyPerkDialog(QtGui.QDialog):
    
    tag       = None
    adv       = None
    pc        = None
    dstore    = None
    perk_id   = 0
    perk_nm   = ''
    perk_rule = None
    item      = None
    edit_mode = False    

    def __init__(self, pc, tag, dstore, parent = None):
        super(BuyPerkDialog, self).__init__(parent)
        self.tag = tag
        self.pc  = pc
        self.dstore = dstore
        self.build_ui()
        self.load_data()
        
    def build_ui(self):
        if self.tag == 'merit':
            self.setWindowTitle(self.tr("Add Advantage"))
        else:
            self.setWindowTitle(self.tr("Add Disadvantage"))
            
        self.setMinimumSize(400, 0)
                        
        self.bt_accept = QtGui.QPushButton(self.tr("Ok")    , self)
        self.bt_cancel = QtGui.QPushButton(self.tr("Cancel"), self)            
        
        lvbox = QtGui.QVBoxLayout(self)        
            
        grp     = QtGui.QGroupBox(self.tr("SubType"), self)
        vbox    = QtGui.QVBoxLayout(grp)
        self.cb_subtype = QtGui.QComboBox(self)
        self.cb_subtype.currentIndexChanged.connect( self.on_subtype_select )
        vbox.addWidget(self.cb_subtype)
        lvbox.addWidget(grp)
        
        grp     = None
        if self.tag == 'merit':
            grp     = QtGui.QGroupBox(self.tr("Advantage"), self)        
        else:
            grp     = QtGui.QGroupBox(self.tr("Disadvantage"), self)
        vbox    = QtGui.QVBoxLayout(grp)
        self.cb_perk = QtGui.QComboBox(self)
        self.cb_perk.currentIndexChanged.connect( self.on_perk_select )
        vbox.addWidget(self.cb_perk)           
        lvbox.addWidget(grp)
        
        grp     = QtGui.QGroupBox(self.tr("Rank"), self)
        vbox    = QtGui.QVBoxLayout(grp)
        self.cb_rank = QtGui.QComboBox(self)
        self.cb_rank.currentIndexChanged.connect( self.on_rank_select )
        vbox.addWidget(self.cb_rank)
        lvbox.addWidget(grp)
        
        grp     = QtGui.QGroupBox(self.tr("Notes"), self)
        vbox    = QtGui.QVBoxLayout(grp)
        self.tx_notes = QtGui.QTextEdit(self)
        vbox.addWidget(self.tx_notes)
        lvbox.addWidget(grp)     
        
        if self.tag == 'merit':
            grp     = QtGui.QGroupBox(self.tr("XP Cost"), self)
        else:
            grp     = QtGui.QGroupBox(self.tr("XP Gain"), self)
        vbox    = QtGui.QVBoxLayout(grp)
        self.cost_widget = widgets.CostSelection(self)
        vbox.addWidget(self.cost_widget)
        lvbox.addWidget(grp)       
        
        
        self.btbox = QtGui.QDialogButtonBox(QtCore.Qt.Horizontal)
        self.btbox.addButton(self.bt_accept, QtGui.QDialogButtonBox.AcceptRole)
        self.btbox.addButton(self.bt_cancel, QtGui.QDialogButtonBox.RejectRole)
        
        self.btbox.accepted.connect(self.on_accept)
        self.btbox.rejected.connect(self.close    )
        
        lvbox.addWidget(self.btbox)

    def load_data(self):
        # load subtypes       
        for typ in self.dstore.perktypes:
            self.cb_subtype.addItem(typ.name, typ.id)
        
        
    def set_edit_mode(self, flag):
        self.edit_mode = flag

        self.cb_subtype.setEnabled(not flag)
        self.cb_perk.setEnabled   (not flag)
        self.cb_rank.setEnabled   (not flag)
        
        self.cb_subtype.parent().setVisible(not flag)
        
        self.cb_rank   .blockSignals(flag)
        self.cb_perk   .blockSignals(flag)
        self.cb_subtype.blockSignals(flag)

        self.cost_widget.set_manual_only(flag)
        
    def load_item(self, perk):                
        self.cb_perk.clear()

        perk_id  = perk.adv.perk
        perk_itm = dal.query.get_merit(self.dstore, perk_id) or dal.query.get_flaw(self.dstore, perk_id)
               
        self.cb_perk.addItem(perk.name, perk_itm)        
        self.cb_perk.setCurrentIndex(0)
        
        self.item = perk.adv
        
        self.cost_widget.set_manual_cost( abs(self.item.cost) )
        self.tx_notes.setPlainText(self.item.extra)
        
    def on_subtype_select(self, text = ''):
        if self.edit_mode: return

        self.item = None
        self.cb_perk.clear()
        
        selected = self.cb_subtype.currentIndex()
        if selected < 0:
            return
        type_ = self.cb_subtype.itemData(selected)
        
        # populate perks        
        perks = self.dstore.merits if ( self.tag == 'merit' ) else self.dstore.flaws
        perks = [ x for x in perks if x.type == type_ ]
        
        for p in perks:
            self.cb_perk.addItem(p.name, p)        
        
    def on_perk_select(self, text = ''):
        if self.edit_mode: return

        self.item = None
        self.cb_rank.clear()
    
        selected = self.cb_perk.currentIndex()
        if selected < 0:
            return
        perk = self.cb_perk.itemData(selected)
        self.perk_id = perk.id
        self.perk_nm = perk.name
               
        # get perk rule
        self.perk_rule = perk.rule
        
        # populate ranks
        for rank in perk.ranks:
            self.cb_rank.addItem(self.tr("Rank %d") % rank.id, rank)
        
    def on_rank_select(self, text = ''):
        selected = self.cb_rank.currentIndex()
        if selected < 0:
            return
        rank = self.cb_rank.itemData(selected)        
        cost = rank.value
        tag  = None  
        self.cost_widget.set_manual_only(cost == 0)
        #self.set_manual_cost(0)
        if cost != 0:
            # look for exceptions
            cost = abs(cost)
            for discount in rank.exceptions:
                t = discount.tag
                discounted = discount.value
                
                if self.pc.has_tag(t):
                    cost = int(discounted)
                    tag  = t
                    break
                    
            if cost <= 0:
                cost = 1
                    
        self.item = models.PerkAdv(self.perk_id, rank.id, cost, tag)       
        if tag:
            self.cost_widget.set_discount_reason(tag)
        self.cost_widget.set_suggested_cost(self.item.cost)
        
                
    def update_perk(self):       
        self.item.extra = self.tx_notes.toPlainText()
        self.item.cost  = abs(self.cost_widget.get_cost())  
        if self.tag == 'flaw':
            self.item.cost *= -1
        
    def on_accept(self):
        if self.edit_mode:
            self.update_perk()
            self.accept()
            return
        
        if not self.item:
            QtGui.QMessageBox.warning(self, self.tr("Perk not found"),
                                      self.tr("Please select a perk."))
            return
        
        self.item.rule  = self.perk_rule
        self.item.extra = self.tx_notes.toPlainText()
        self.item.cost  = abs(self.cost_widget.get_cost())

        if self.tag == 'merit':
            self.item.desc = self.tr("%s Rank %d, XP Cost: %d") % ( self.perk_nm, self.item.rank, self.item.cost )
            
            if (self.item.cost + self.pc.get_px()) > self.pc.exp_limit:
                QtGui.QMessageBox.warning(self, self.tr("Not enough XP"),
                self.tr("Cannot purchase.\nYou've reached the XP Limit."))
                return
        else:
            self.item.desc = self.tr("%s Rank %d, XP Gain: %d") % ( self.perk_nm, self.item.rank, abs(self.item.cost) )
            
        if self.tag == 'flaw':
            self.item.cost *= -1
        
        self.item.tag = self.tag
        self.pc.add_advancement      (self.item)        
        self.process_special_effects (self.item)        
        self.accept()
        
    def process_special_effects(self, item):
        def _add_free_skill_rank(skill_id):
            skill = dal.query.get_skill(self.dstore, skill_id)

            cur_value = self.pc.get_skill_rank(skill_id)
            new_value = cur_value + 1
            cost = 0
            adv = models.SkillAdv(skill_id, 0)
            adv.rule = dal.query.get_mastery_ability_rule(self.dstore, skill_id, new_value)
            adv.desc = unicode.format(self.tr("{0}, Rank {1} to {2}. Gained by {3}"),
                                      skill.name, cur_value, new_value, self.perk_nm )
            self.pc.add_advancement(adv)
            
        if item.rule == 'fk_gaijin_pepper':
            # add a rank in Craft (Explosives), zero cost :)
            _add_free_skill_rank("craft_explosives")
        elif item.rule == 'fk_gozoku':
            # add a rank in Lore (Gozoku), zero cost :)
            _add_free_skill_rank("lore_gozoku")
        elif item.rule == 'fk_kolat':
            # add a rank in Lore (Kolat), zero cost :)
            _add_free_skill_rank("lore_kolat")
        elif item.rule == 'fk_lying_darkness':
            # add a rank in Lore (Lying Darkness), zero cost :)
            _add_free_skill_rank("lore_lying_darkness")
        elif item.rule == 'fk_maho':
            # add a rank in Lore (Maho), zero cost :)
            _add_free_skill_rank("lore_maho")
