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
import dal.query

class KihoItemModel(object):
    def __init__(self):
        self.name      = ''
        self.mastery   = ''
        self.element   = ''
        self.id        = False
        self.adv       = None
        self.text      = []

    def __str__(self):
        return self.name

class KihoTableViewModel(QtCore.QAbstractTableModel):
    def __init__(self, dstore, parent = None):
        super(KihoTableViewModel, self).__init__(parent)
        self.items = []
        self.headers = ['Name', 'Mastery', 'Element']
        self.text_color = QtGui.QBrush(QtGui.QColor(0x15, 0x15, 0x15))
        self.bg_color   = [ QtGui.QBrush(QtGui.QColor(0xFF, 0xEB, 0x82)),
                            QtGui.QBrush(QtGui.QColor(0xEB, 0xFF, 0x82)) ]        
        self.item_size = QtCore.QSize(28, 28)
        self.dstore = dstore

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
            if index.column() == 0:
                return item.name
            if index.column() == 1:
                return item.mastery
            if index.column() == 2:
                return item.element
        elif role == QtCore.Qt.ForegroundRole:
            return self.text_color
        elif role == QtCore.Qt.BackgroundRole:
            return self.bg_color[ index.row() % 2 ]            
        elif role == QtCore.Qt.SizeHintRole:
            return self.item_size
        elif role == QtCore.Qt.UserRole:
            return item
        return None

    def flags(self, index):
        if not index.isValid():
            return QtCore.Qt.ItemIsDropEnabled
        flags = QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled
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

    def build_item_model(self, ki_id):
        itm = KihoItemModel()
        ki = dal.query.get_kiho(self.dstore, ki_id.kiho)
        if ki:
            itm.id       = ki.id
            itm.adv      = ki_id
            itm.name     = ki.name
            itm.mastery  = ki.mastery
            try:
                itm.element = dal.query.get_ring(self.dstore, ki.element).text
            except:
                itm.element = ki.element
            itm.text     = ki.desc
        else:
            print('cannot find kiho: {0}'.format(ki_id.kiho))
            
        if ki.type == 'tattoo':
            itm.mastery = "N/A"
            itm.element = "Tattoo"
        
        return itm

    def update_from_model(self, model):
        kiho = model.get_kiho()

        self.clean()
        for s in kiho:           
            itm = self.build_item_model(s)
            self.add_item(itm)
     