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
import rules
import dal
import dal.query

MOD_TYPES = {
    "none" : "Select a modifier",
    "wdmg" : "Damage Roll",
    #"spcr" : "Spell Casting Roll",
    "anyr" : "Any Roll",
    "skir" : "Skill Roll",
    "atkr" : "Attack Roll",
    "hrnk" : "Health Rank",    
    "artn" : "Armor TN",
    "arrd" : "Armor RD",
    "init" : "Initiative"
}

MOD_DTLS = {
    "none": ("none", "N/A"),
    "anyr": ("none", "N/A"),
    "hrnk": ("none", "N/A"),
    "skir": ("skill", "Select Skill"),
    "wdmg": ("aweap", "Select Weapon"),
    'atkr': ("aweap", "Select Weapon"),
    "artn": ("none", "N/A"),
    "arrd": ("none", "N/A"),
    "init": ("none", "N/A"),
}

class ModifierModel(object):
    def __init__(self):
        self.type   = 'none'
        self.dtl    = None
        self.value  = (0, 0, 0)
        self.reason = "I'm just this good"
        self.active = False
       
class ModifiersTableViewModel(QtCore.QAbstractTableModel):
    user_change = QtCore.Signal()
    
    def __init__(self, parent = None):
        super(ModifiersTableViewModel, self).__init__(parent)
        self.items = []
        self.headers = ['Modifies', 'Detail', 'Value', 'Reason']
        self.dirty   = False
        self.text_color = QtGui.QBrush(QtGui.QColor(0x15, 0x15, 0x15))
        self.bg_color   = [ QtGui.QBrush(QtGui.QColor(0xFF, 0xEB, 0x82)),
                            QtGui.QBrush(QtGui.QColor(0xEB, 0xFF, 0x82)) ]        
        self.item_size = QtCore.QSize(28, 28)

    def rowCount(self, parent = QtCore.QModelIndex()):
        return len(self.items)

    def columnCount(self, parent = QtCore.QModelIndex()):
        return len(self.headers)

    def headerData(self, section, orientation, role = QtCore.Qt.ItemDataRole.DisplayRole):
        if orientation != QtCore.Qt.Orientation.Horizontal:
            return None
        if role == QtCore.Qt.DisplayRole:
            return self.headers[section]
        return None

    def data(self, index, role = QtCore.Qt.UserRole):
        if not index.isValid() or index.row() >= len(self.items):
            return None
        item = self.items[index.row()]
        if role == QtCore.Qt.DisplayRole:
            return self.__display_role(item, index.column())
        elif role == QtCore.Qt.ForegroundRole:
            return self.text_color
        elif role == QtCore.Qt.BackgroundRole:
            return self.bg_color[ index.row() % 2 ]            
        elif role == QtCore.Qt.SizeHintRole:
            return self.item_size
        elif role == QtCore.Qt.CheckStateRole:
            return self.__checkstate_role(item, index.column())
        elif role == QtCore.Qt.UserRole:
            return item    
        return None
    
    def setData(self, index, value, role):
        if not index.isValid():
            return False
        
        ret  = False
        item = self.items[index.row()]
        self.dirty = True

        if index.column() == 0 and role == QtCore.Qt.CheckStateRole:
            item.active = (value == QtCore.Qt.Checked)
            ret = True
        elif role == QtCore.Qt.EditRole:
            if index.column() == 0:
                item.type = value
            elif index.column() == 1:
                item.dtl = value
            elif index.column() == 2:
                item.value = rules.parse_rtk_with_bonus(value)
            elif index.column() == 3:
                item.reason = value
            else:
                ret = False
            ret = True
        else:
            ret = super(ModifiersTableViewModel, self).setData(index, value, role)
        
        if ret:
            print('user change' + str(item.active))
            self.user_change.emit()
        return ret
        
    def __display_role(self, item, column):
        if column == 0:
            return MOD_TYPES[item.type] if item.type else None
        if column == 1:
            return item.dtl or ( MOD_DTLS[item.type][1] if item.type in MOD_DTLS else None )
        if column == 2:
            return rules.format_rtk_t(item.value)
        if column == 3:
            return item.reason
        return None
        
    def __checkstate_role(self, item, column):
        if column == 0:
            return QtCore.Qt.Checked if item.active else QtCore.Qt.Unchecked
        return None
        
    def flags(self, index):
        if not index.isValid():
            return QtCore.Qt.ItemIsDropEnabled
        flags = QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled
        if index.column() == 0:
	        flags |= QtCore.Qt.ItemIsUserCheckable        
        return flags

    def add_item(self, item):
        row = self.rowCount()
        self.beginInsertRows(QtCore.QModelIndex(), row, row)               
        self.items.append(item)
        self.endInsertRows()

    def clean(self):
        self.beginResetModel()
        self.items = []
        self.endResetModel()

    def update_from_model(self, model):
        self.clean()
        for m in model.get_modifiers():
            self.add_item(m)
        
        if self.dirty:
            print('set model unsaved')
            model.unsaved = True
            self.dirty    = False                        