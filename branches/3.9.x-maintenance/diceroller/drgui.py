# -*- coding: iso-8859-1 -*-
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
from drcore import *
import random
import os

class DiceRoller(QtGui.QDialog):
    def __init__(self, parent = None):
        super(DiceRoller, self).__init__(parent)
        
        # UI
        self.build_ui()
        self.setWindowTitle('L5R: CM - Dice Roller')
        
        # PERSISTENCE
        self.saved_expr = []
        self.load_expressions()
        
        # LOGIC
        random.seed()

    def build_ui(self):
        layout_ = QtGui.QHBoxLayout(self)
        layout_.setContentsMargins(0,0,0,0)
        layout_.setSpacing(0)
        
        # EXCLUSIVE BUTTON GROUP
        saved_bt_grp = QtGui.QButtonGroup(self)
        saved_bt_grp.setExclusive(True)
        
        saved_roll_frame = QtGui.QFrame(self)
        sr_vbox = QtGui.QVBoxLayout(saved_roll_frame)    
        sr_vbox.setAlignment(QtCore.Qt.AlignTop)
        
        dr_frame = QtGui.QFrame(self)
        vbox = QtGui.QVBoxLayout(dr_frame)
        
        grp_expr  = QtGui.QGroupBox("Expression ( e.g. (4k2+5)*2 )", self)
        h_        = QtGui.QHBoxLayout(grp_expr)
        le_expr   = QtGui.QLineEdit(self)
        bt_roll   = QtGui.QPushButton("Roll"  , self)
        bt_save   = QtGui.QPushButton("Save"  , self)
        bt_del    = QtGui.QPushButton("Delete", self)
        
        bt_del.setEnabled (False)
        
        h_.addWidget(le_expr)
        h_.addWidget(bt_roll)
        h_.addWidget(bt_save)
        h_.addWidget(bt_del )
        
        grp_rules = QtGui.QGroupBox("Rules", self)
        v_        = QtGui.QVBoxLayout(grp_rules)
        rb_none   = QtGui.QRadioButton ("Explode None", self)
        rb_10     = QtGui.QRadioButton ("Explode 10", self)
        rb_9      = QtGui.QRadioButton ("Explode 9", self)
        rb_8      = QtGui.QRadioButton ("Explode 8", self)        
        for w in [rb_none, rb_10, rb_9, rb_8]:
            v_.addWidget(w)
            
        ck_1      = QtGui.QCheckBox    ("Reroll 1", self)
        ck_1.setChecked(False)
        ck_2      = QtGui.QCheckBox    ("Only Explode Once", self)
        ck_2.setChecked(False)        
        v_.addWidget(ck_1)
        v_.addWidget(ck_2)
        
        rb_10.setChecked(True)
        
        grp_dtl   = QtGui.QGroupBox("Details", self)
        v_        = QtGui.QVBoxLayout(grp_dtl)
        lv_dtl    = QtGui.QListView(self) 
        mod_dtl   = QtGui.QStringListModel(self)
        lv_dtl.setModel(mod_dtl)
        v_.addWidget(lv_dtl)        
        
        grp_tot   = QtGui.QGroupBox("Total", self)
        v_        = QtGui.QVBoxLayout(grp_tot)
        le_tot    = QtGui.QLineEdit(self) 
        le_tot.setReadOnly(True)
        v_.addWidget(le_tot)
        
        for w in [grp_expr, grp_rules, grp_dtl, grp_tot]:
            vbox.addWidget(w)
            
        le_expr.returnPressed.connect(self.solve_expr)
        
        bt_roll.clicked.connect(self.solve_expr)
        bt_save.clicked.connect(self.save_expr )
        bt_del .clicked.connect(self.del_expr  )
        
        QtCore.QObject.connect(saved_bt_grp, 
                               QtCore.SIGNAL("buttonPressed(int)"), 
                               self.on_expr_bt_pressed)
        
        self.saved_bt_grp = saved_bt_grp
        self.sr_vbox      = sr_vbox
        
        self.le_expr = le_expr
        self.le_tot  = le_tot
        
        self.bt_roll = bt_roll
        self.bt_save = bt_save
        self.bt_del  = bt_del
        
        self.rb_none = rb_none
        self.rb_10   = rb_10
        self.rb_9    = rb_9
        self.rb_8    = rb_8
        self.ck_1    = ck_1
        self.ck_2    = ck_2
        
        self.mod_dtl = mod_dtl
        
        layout_.addWidget(saved_roll_frame)
        layout_.addWidget(dr_frame)
        
    def closeEvent(self, event):
        self.save_expressions()
    
    def load_expressions(self):        
        if not os.path.exists('saved_expr'):
            return
            
        with open('saved_expr', 'rt') as fobj:        
            i = 0
            for expr in fobj:
                expr = expr.strip()
                self.saved_expr.append(expr)
                self.add_save_expr_bt(i, expr)
                i += 1        
        
    def save_expressions(self):
        with open('saved_expr', 'wt') as fobj:              
            for expr in self.saved_expr:
                fobj.write(expr)
                fobj.write('\n')
               
    def add_save_expr_bt(self, expr_id, expr_nm = None):
        # add button
        bt = QtGui.QPushButton(expr_nm or str(expr_id), self)
        bt.setCheckable(True)
        bt.setChecked(True)
        self.saved_bt_grp.addButton(bt, expr_id)
        self.sr_vbox.addWidget(bt)
        
    def save_expr(self):
        expr     = self.le_expr.text()
        if len(expr) == 0:
            return
                
        if len(self.saved_expr) > 16:
            return # TOO MUCH                
        
        if expr in self.saved_expr:
            return # ALREADY IN
                    
        self.add_save_expr_bt(len(self.saved_expr), expr)
        self.saved_expr.append(expr)
    
    def del_expr(self):
        expr_id = self.saved_bt_grp.checkedId()
                               
        if expr_id < 0 or expr_id >= len(self.saved_expr):
            return
                
        bt = self.saved_bt_grp.button(expr_id)
        if bt:
            self.saved_bt_grp.removeButton(bt)
            bt.close()
            
        del self.saved_expr[expr_id]
        
    def on_expr_bt_pressed(self, bt_id):
        self.bt_del.setEnabled(bt_id >= 0)
        if bt_id < 0 or bt_id >= len(self.saved_expr): return
        
        self.le_expr.setText(self.saved_expr[bt_id])
        
    def solve_expr(self):
        self.clear_log()
        
        expr = self.le_expr.text()
        rpn  = ''
        val  = 0
        try:
            rpn = math_to_rpn(expr)
        except:
            print 'failed math_to_rpn, expr: %s' % expr
        
        if self.rb_none.isChecked():
            set_explode(999)
        elif self.rb_10.isChecked():
            set_explode(10)
        elif self.rb_9.isChecked():
            set_explode(9)
        elif self.rb_8.isChecked():
            set_explode(8)
            
        set_reroll_1    (self.ck_1.isChecked())
        set_explode_once(self.ck_2.isChecked())
            
        set_output_cb( self.add_to_log )
        
        try:
            val = rpn_solve(rpn)            
        except:
            print 'failed rpn_solve, rpn: %s' % repr(rpn)
            
        self.le_tot.setText(str(val))
        
    def clear_log(self):
        self.mod_dtl.setStringList([])
        
    def add_to_log(self, str_):
        if len(str_) > 0:
            self.mod_dtl.setStringList( self.mod_dtl.stringList() + [str_])
            