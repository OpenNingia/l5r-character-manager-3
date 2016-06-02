# -*- coding: utf-8 -*-
# Copyright (C) 2014 Daniele Simonetti
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

from PyQt5 import QtCore, QtGui

import l5r.api as api
import l5r.api.data
import l5r.api.data.powers
import l5r.api.character.powers
from l5r.util import log
from l5r.util.settings import L5RCMSettings


class KataItemModel(object):

    def __init__(self):
        self.name = ''
        self.mastery = ''
        self.element = ''
        self.id = False
        self.text = []

    def __str__(self):
        return self.name


class KataTableViewModel(QtCore.QAbstractTableModel):

    def __init__(self, parent=None):
        super(KataTableViewModel, self).__init__(parent)
        self.items = []
        self.headers = ['Name', 'Mastery', 'Element']
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
                return item.name
            if index.column() == 1:
                return item.mastery
            if index.column() == 2:
                return item.element
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

    def build_item_model(self, ka_id):
        itm = KataItemModel()
        ka = api.data.powers.get_kata(ka_id)

        if ka:
            itm.id = ka.id
            itm.name = ka.name
            itm.mastery = ka.mastery

            try:
                itm.element = api.data.get_ring(ka.element).text
            except:
                itm.element = ka.element

            itm.text = ka.desc
        else:
            log.model.error(u"kata not found: %s", ka_id)

        return itm

    def update_from_model(self, model):
        kata = api.character.powers.get_all_kata()

        self.clean()
        for s in kata:
            itm = self.build_item_model(s)
            self.add_item(itm)
