# -*- coding: utf-8 -*-
# Copyright (C) 2014-2022 Daniele Simonetti
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

from PyQt5 import QtCore, QtGui, QtWidgets
from l5r.util.settings import L5RCMSettings


class DataPackModel(QtCore.QAbstractTableModel):

    def __init__(self, parent=None):
        super(DataPackModel, self).__init__(parent)
        self.items = []
        self.headers = [self.tr('Name'),
                        self.tr('Language'),
                        self.tr('Version'),
                        self.tr('Authors')]

        self.settings = L5RCMSettings()

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self.items)

    def columnCount(self, parent=QtCore.QModelIndex()):
        return len(self.headers)

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        if orientation != QtCore.Qt.Horizontal:
            return None
        if role == QtCore.Qt.DisplayRole:
            return self.headers[section]
        return None

    def data(self, index, role=QtCore.Qt.UserRole):
        if not index.isValid() or index.row() >= len(self.items):
            return None
        item = self.items[index.row()]
        if role == QtCore.Qt.DisplayRole:
            if index.column() == 0:
                return item.display_name
            if index.column() == 1:
                return item.language or self.tr("All")
            if index.column() == 2:
                return item.version or self.tr("N/A")
            if index.column() == 3:
                return ", ".join(item.authors) if (item.authors is not None) else ""
        elif role == QtCore.Qt.ForegroundRole:
            if index.row() % 2:
                return self.settings.ui.table_row_color_alt_fg
            return self.settings.ui.table_row_color_fg
        elif role == QtCore.Qt.BackgroundRole:
            if index.row() % 2:
                return self.settings.ui.table_row_color_alt_bg
            return self.settings.ui.table_row_color_bg
        elif role == QtCore.Qt.SizeHintRole:
            return self.settings.ui.table_row_size
        elif role == QtCore.Qt.UserRole:
            return item
        elif role == QtCore.Qt.CheckStateRole:
            return self.__checkstate_role(item, index.column())
        return None

    def setData(self, index, value, role):
        if not index.isValid():
            return False

        ret = False
        item = self.items[index.row()]
        self.dirty = True

        if index.column() == 0 and role == QtCore.Qt.CheckStateRole:
            item.active = (value == QtCore.Qt.Checked)
            ret = True
        else:
            ret = super(DataPackModel, self).setData(index, value, role)

        return ret

    def flags(self, index):
        if not index.isValid():
            return QtCore.Qt.ItemIsDropEnabled
        flags = QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled
        if index.column() == 0:
            flags |= QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEditable
        return flags

    def __checkstate_role(self, item, column):
        if column == 0:
            return QtCore.Qt.Checked if item.active else QtCore.Qt.Unchecked
        return None

    def add_item(self, item):
        row = self.rowCount()
        self.beginInsertRows(QtCore.QModelIndex(), row, row)
        self.items.append(item)
        self.endInsertRows()

    def clean(self):
        self.beginResetModel()
        self.items = []
        self.endResetModel()


class ManageDataPackDlg(QtWidgets.QDialog):

    def __init__(self, dstore, parent=None):
        super(ManageDataPackDlg, self).__init__(parent)

        self.dstore = dstore

        self.build_ui()
        self.load_data()

    def build_ui(self):
        self.setWindowTitle(self.tr("Data Pack Manager"))

        vbox = QtWidgets.QVBoxLayout(self)

        grp = QtWidgets.QGroupBox(self.tr("Available data packs"))
        self.view = QtWidgets.QTableView(self)
        vbox2 = QtWidgets.QVBoxLayout(grp)
        vbox2.addWidget(self.view)

        bts = QtWidgets.QDialogButtonBox()

        bts.addButton(self.tr("Discard"), QtWidgets.QDialogButtonBox.RejectRole)
        bts.addButton(self.tr("Save"), QtWidgets.QDialogButtonBox.AcceptRole)

        vbox.addWidget(grp)
        vbox.addWidget(bts)

        bts.accepted.connect(self.on_accept)
        bts.rejected.connect(self.reject)

        self.setMinimumSize(QtCore.QSize(440, 330))

    def load_data(self):
        from copy import deepcopy
        self.packs = deepcopy(self.dstore.packs)
        model = DataPackModel(self)
        for pack in self.packs:
            model.add_item(pack)
        self.view.setModel(model)

    def on_accept(self):
        self.dstore.packs = self.packs
        self.accept()
