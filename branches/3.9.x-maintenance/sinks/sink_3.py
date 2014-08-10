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

from PySide import QtCore, QtGui

import dialogs

class Sink3(QtCore.QObject):
    def __init__(self, parent = None):
        super(Sink3, self).__init__(parent)
        self.form = parent
        
    def show_add_weapon(self):   
        form = self.form
        
        dlg = dialogs.ChooseItemDialog(form.pc, 'weapon', form.dstore, form)
        filter = self.sender().parent().property('filter')        
        if filter is not None:
            dlg.set_filter(filter)
        if dlg.exec_() == QtGui.QDialog.DialogCode.Accepted:
            form.update_from_model()

    def show_add_cust_weapon(self):
        form = self.form
        
        dlg = dialogs.CustomWeaponDialog(form.pc, form.dstore, form)
        if dlg.exec_() == QtGui.QDialog.DialogCode.Accepted:
            form.update_from_model()

    def edit_selected_weapon(self):
        form = self.form
        
        view_ = None
        try:            
            view_ = self.sender().parent().property('source')
        except Exception as e:
            print repr(e)
        if view_ is None:
            return
        sel_idx = view_.selectionModel().currentIndex()
        if not sel_idx.isValid():
            return
        sel_itm = view_.model().data(sel_idx, QtCore.Qt.UserRole)
        dlg = dialogs.CustomWeaponDialog(form.pc, form.dstore, form)
        dlg.edit_mode = True
        print('loading weap {0}, tags: {1}'.format(sel_itm.name, sel_itm.tags))
        dlg.load_item(sel_itm)
        if dlg.exec_() == QtGui.QDialog.DialogCode.Accepted:
            form.update_from_model()
            
    def remove_selected_weapon(self):
        form = self.form
        
        view_ = None
        try:            
            view_ = self.sender().parent().property('source')
        except Exception as e:
            print repr(e)
        if view_ is None:
            return
        sel_idx = view_.selectionModel().currentIndex()
        if not sel_idx.isValid():
            return
        sel_itm = view_.model().data(sel_idx, QtCore.Qt.UserRole)
        form.pc.weapons.remove(sel_itm)
        form.update_from_model()

    def on_increase_item_qty(self):
        form = self.form
        
        view_ = None
        try:            
            view_ = self.sender().parent().property('source')
        except Exception as e:
            print repr(e)
        if view_ is None:
            return
        sel_idx = view_.selectionModel().currentIndex()
        if not sel_idx.isValid():
            return
        sel_itm = view_.model().data(sel_idx, QtCore.Qt.UserRole)
        if sel_itm.qty < 9999:
            sel_itm.qty += 1
            form.update_from_model()            
            sel_idx = view_.model().index(sel_idx.row(), 0)
            view_.selectionModel().setCurrentIndex(sel_idx, 
                QtGui.QItemSelectionModel.Select | QtGui.QItemSelectionModel.Rows)

    def on_decrease_item_qty(self):        
        form = self.form
        
        view_ = None
        try:            
            view_ = self.sender().parent().property('source')
        except Exception as e:
            print repr(e)
        if view_ is None:
            return
        sel_idx = view_.selectionModel().currentIndex()
        if not sel_idx.isValid():
            return
        sel_itm = view_.model().data(sel_idx, QtCore.Qt.UserRole)
        if sel_itm.qty > 1:
            sel_itm.qty -= 1
            form.update_from_model()
            sel_idx = view_.model().index(sel_idx.row(), 0)
            view_.selectionModel().setCurrentIndex(sel_idx,
                QtGui.QItemSelectionModel.Select | QtGui.QItemSelectionModel.Rows)            