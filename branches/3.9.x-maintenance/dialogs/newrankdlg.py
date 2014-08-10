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

from PySide import QtGui, QtCore

import dal
import dal.query
import models
import widgets

class NextRankDlg(QtGui.QDialog):
    def __init__(self, pc, dstore, parent = None):
        super(NextRankDlg, self).__init__(parent)        
        self.pc     = pc
        self.dstore = dstore
        
        self.build_ui()
        self.connect_signals()
        
        #self.setWindowFlags(QtCore.Qt.Tool)
        self.setWindowTitle(self.tr("L5R: CM - Advance Rank"))
        
    def build_ui(self):
        vbox = QtGui.QVBoxLayout(self)
        vbox.addWidget(QtGui.QLabel(self.tr("""\
You can now advance your Rank,
what would you want to do?
                                    """)))
        self.bt_go_on        = QtGui.QPushButton(
                               self.tr("Advance in my current school")
                               )
        self.bt_new_school_1 = QtGui.QPushButton(
                               self.tr("Buy 'Multiple School' advantage\n"
                                       "and join a new school"))
        self.bt_new_school_2 = QtGui.QPushButton(
                               self.tr("Just join a new school"))
                               
        for bt in [self.bt_go_on, self.bt_new_school_1, self.bt_new_school_2]:
            bt.setMinimumSize(QtCore.QSize(0, 38))
        
        vbox.addWidget(self.bt_go_on       )
        vbox.addWidget(self.bt_new_school_1)
        vbox.addWidget(self.bt_new_school_2)
        
        vbox.setSpacing(12)
        
        # check if the PC is following an alternate path
        if self.pc.get_school().is_path:
            # offer to going back
            self.bt_go_on.setText( self.tr("Go back to your old school"))            
        
    def connect_signals(self):
        self.bt_go_on.clicked.connect(self.simply_go_on)
        self.bt_new_school_1.clicked.connect(self.merit_plus_school)
        self.bt_new_school_2.clicked.connect(self.join_new_school)
    
    def join_new_school(self):
        dlg = SchoolChoiceDlg(self.pc, self.dstore, self)
        if dlg.exec_() == QtGui.QDialog.Rejected:
            #self.reject()
            return
        sc = dal.query.get_school(self.dstore, dlg.get_school_id())
        
        school_nm  = sc.name
        school_obj = models.CharacterSchool(sc.id)
        school_obj.tags = sc.tags
        school_obj.school_rank = 0

        school_obj.affinity   = sc.affinity
        school_obj.deficiency = sc.deficiency
               
        self.pc.schools.append(school_obj)
        
        # check free kihos
        if sc.kihos:
            self.pc.set_free_kiho_count( sc.kihos.count )
        
        # check for alternate path
        if school_obj.has_tag('alternate'):
            school_obj.is_path = True
            school_obj.path_rank = self.pc.get_insight_rank()

        self.pc.set_current_school_id(sc.id)        
        self.pc.set_can_get_other_tech(True)
        
        self.accept()        
               
    def merit_plus_school(self):       
        mult_school_merit = dal.query.get_merit(self.dstore, 'multiple_schools')
        try:
            uuid = mult_school_merit.id
            name = mult_school_merit.name
            rule = mult_school_merit.id            
            cost = mult_school_merit.get_rank_value(1)
            
            if not uuid or not cost: self.reject()            
                
            itm      = models.PerkAdv(uuid, 1, cost)
            itm.rule = rule
            itm.desc = unicode.format(self.tr("{0} Rank {1}, XP Cost: {2}"),
                                      name,
                                      1, itm.cost)
                                  
            if (itm.cost + self.pc.get_px()) > self.pc.exp_limit:
                QtGui.QMessageBox.warning(self, self.tr("Not enough XP"),
                self.tr("Cannot purchase.\nYou've reached the XP Limit."))
                self.reject()
                return
                
            self.pc.add_advancement(itm)
            self.join_new_school()
        except:
            self.reject()
            
    def simply_go_on(self):
        # check if the PC is following an alternate path
        if self.pc.get_school().is_path:
            # the PC want to go back to the old school.
            # find the first school that is not a path
            for s in reversed(self.pc.schools):
                if not s.is_path:
                    self.pc.set_current_school_id(s.school_id)
                    
        self.pc.set_can_get_other_tech(True)
        self.accept()

class SchoolChoiceDlg(QtGui.QDialog):
    def __init__(self, pc, dstore, parent = None):
        super(SchoolChoiceDlg,self).__init__(parent)
        
        self.pc     = pc
        self.dstore = dstore
        
        self.school_nm  = ''
        self.school_id  = 0
        self.school_tg  = []
        self.schools    = []
                
        self.build_ui       ()
        self.setWindowTitle(self.tr("L5R: CM - Select School"))        
        
    def sizeHint(self):
        return QtCore.QSize(600, 400)
        
    def build_ui(self):
    
        def build_filter_panel():
            fr = QtGui.QFrame(self)
            vb = QtGui.QVBoxLayout(fr)
            self.cx_base_schools = QtGui.QCheckBox(self.tr("Base schools"), self)
            self.cx_advc_schools = QtGui.QCheckBox(self.tr("Advanced schools"), self)
            self.cx_path_schools = QtGui.QCheckBox(self.tr("Alternate paths"), self)
            vb.addWidget(self.cx_base_schools)
            vb.addWidget(self.cx_advc_schools)
            vb.addWidget(self.cx_path_schools)
            return fr
        
        def build_requirements_panel():
            self.req_list = widgets.RequirementsWidget(self)
            return self.req_list
        
        vbox = QtGui.QVBoxLayout(self)
        
        self.header = QtGui.QLabel(self.tr('''
        <center>
        <h1>Choose the school to join</h1>
        <p style="color: #666">You can choose between normal schools, advanced schools and alternative paths<br/>
        If you choose an advanced school or alternative path be sure to check the requirements
        </p>
        </center>
        '''))        
        
        vbox.addWidget ( self.header )
        vbox.addSpacing( 12 )

        form = QtGui.QFormLayout()
        hbox = QtGui.QHBoxLayout()
        
        # Clan selection
        self.cb_clan = QtGui.QComboBox(self)
        form.addRow(self.tr("Clan"), self.cb_clan)
        self.cb_clan.currentIndexChanged.connect(self.on_clan_change)
        
        # School selection
        self.cb_school = QtGui.QComboBox(self)
        form.addRow(self.tr("School"), self.cb_school)
        self.cb_school.currentIndexChanged.connect(self.on_school_change)
        
        # Filter
        fr = build_filter_panel()
        form.addRow(self.tr("Filters"), fr)
        
        # Requirements
        fr = build_requirements_panel()
        form.addRow(self.tr("Requirements"), fr)
        
        hbox.addStretch(24)
        hbox.addLayout(form)
        hbox.addStretch(24)
        
        vbox.addLayout(hbox)
                
        # buttons
        self.bt_box    = QtGui.QDialogButtonBox(QtCore.Qt.Horizontal, self)
        
        self.bt_box.addButton(self.tr("Cancel") , QtGui.QDialogButtonBox.RejectRole)
        self.bt_box.addButton(self.tr("Confirm"), QtGui.QDialogButtonBox.AcceptRole)
        
        vbox.addStretch(12)
        vbox.addWidget(self.bt_box)
        
        # connections
        self.cx_base_schools.toggled.connect(self.refresh_data)
        self.cx_advc_schools.toggled.connect(self.refresh_data)
        self.cx_path_schools.toggled.connect(self.refresh_data)       
        self.bt_box.accepted.connect(self.on_accept)
        self.bt_box.rejected.connect(self.reject   )
        
        self.cx_base_schools.setChecked(True)
                    
    def refresh_data(self):
        clans   = []
        schools = []
        
        if self.cx_base_schools.isChecked():
            schools += dal.query.get_base_schools(self.dstore)
        if self.cx_advc_schools.isChecked():
            schools += [x for x in self.dstore.schools if 'advanced' in x.tags]
        if self.cx_path_schools.isChecked():
            schools += [x for x in self.dstore.schools if 'alternate' in x.tags]
        
        self.schools = schools
        
        self.cb_clan.clear()
        for c in [x.clanid for x in schools]:
            if c not in clans:
                clans.append(c)
                clan = dal.query.get_clan(self.dstore, c)
                self.cb_clan.addItem(clan.name, clan.id)
                                        
    def on_clan_change(self):    
        idx_ = self.cb_clan.currentIndex()
               
        clan_id = self.cb_clan.itemData(idx_)
        schools = [ x for x in self.schools if x.clanid == clan_id ]
        
        if self.pc.has_tag('bushi'):
            schools = [ x for x in schools if 'shugenja' not in x.tags ]
        elif self.pc.has_tag('shugenja'):
            schools = [ x for x in schools if 'bushi' not in x.tags ]
        
        self.cb_school.clear()
        def has_school(uuid):
            for s in self.pc.schools:
                if s.school_id == uuid:
                    return True
            return False
                    
        for school in schools:
            if not has_school(school.id):
                self.cb_school.addItem(school.name, school.id)
        
    def on_school_change(self):
        self.setUpdatesEnabled(False)
        
        idx_ = self.cb_school.currentIndex()       
        clan_idx_ = self.cb_clan.currentIndex()
        
        clan_id = self.cb_clan.itemData(clan_idx_)        
        school_id = self.cb_school.itemData(idx_)
                
        clan   = dal.query.get_clan  (self.dstore, clan_id)
        school = dal.query.get_school(self.dstore, school_id)
        
        if clan and school:
            self.school_tg = [clan.id] + school.tags
                                                   
            self.req_list.set_requirements( self.pc, self.dstore, school.require )
            
        self.setUpdatesEnabled(True)
        self.resize( self.sizeHint() )
        
    def on_accept(self):
        idx_           = self.cb_school.currentIndex()
        self.school_id = self.cb_school.itemData(idx_)
        self.school_nm = self.cb_school.itemText(idx_)
        
        if self.school_id:
            if not self.req_list.match():
                msgBox = QtGui.QMessageBox(self)
                msgBox.setWindowTitle('L5R: CM')
                msgBox.setText(self.tr("You don't have the requirements to join this school."))
                msgBox.exec_()                
            else:
                self.accept()
                
    def get_school_id(self):
        return self.school_id

    def get_school_name(self):
        return self.school_nm

    def get_school_tags(self):
        return self.school_tg
                
def test():
    import sys
    app = QtGui.QApplication(sys.argv)

    dlg = NextRankDlg(None, None)
    dlg.show()

    sys.exit(app.exec_())
    
if __name__ == '__main__':
    test()
    