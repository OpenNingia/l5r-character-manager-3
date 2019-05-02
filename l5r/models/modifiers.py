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
import l5r.api.rules
from l5r.util.settings import L5RCMSettings

MOD_TYPES = {
    "none": "Select a modifier",
    "wdmg": "Damage Roll",
    # "spcr" : "Spell Casting Roll",
    "anyr": "Any Roll",
    "skir": "Skill Roll",
    "atkr": "Attack Roll",
    "trat": "Trait Roll",
    "ring": "Ring Roll",
    "hrnk": "Health Rank",
    "artn": "Armor TN",
    "arrd": "Armor RD",
    "init": "Initiative",
    "wpen": "Wound Penalty",
}

MOD_DTLS = {
    "none": ("none", "N/A"),
    "anyr": ("none", "N/A"),
    "hrnk": ("none", "N/A"),
    "skir": ("skill", "Select Skill"),
    "trat": ("trait", "Select Trait"),
    "ring": ("ring", "Select Ring"),
    "wdmg": ("aweap", "Select Weapon"),
    'atkr': ("aweap", "Select Weapon"),
    "artn": ("none", "N/A"),
    "arrd": ("none", "N/A"),
    "init": ("none", "N/A"),
    "wpen": ("none", "N/A"),
}


class ModifierModel(object):

    def __init__(self):
        self.type = 'none'
        self.dtl = None
        self.value = (0, 0, 0)
        self.reason = "I'm just this good"
        self.active = False


class ModifiersTableViewModel(QtCore.QAbstractTableModel):
    user_change = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super(ModifiersTableViewModel, self).__init__(parent)

        self.items = []
        self.headers = [
            self.tr('Modifies'),
            self.tr('Detail'),
            self.tr('Value'),
            self.tr('Reason')]

        self.dirty = False
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
            return self.__display_role(item, index.column())
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
        elif role == QtCore.Qt.CheckStateRole:
            return self.__checkstate_role(item, index.column())
        elif role == QtCore.Qt.UserRole:
            return item
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
        elif role == QtCore.Qt.EditRole:
            if index.column() == 0:
                item.type = value
            elif index.column() == 1:
                item.dtl = value
            elif index.column() == 2:
                item.value = api.rules.parse_rtk_with_bonus(value)
            elif index.column() == 3:
                item.reason = value
            else:
                ret = False
            ret = True
        else:
            ret = super(ModifiersTableViewModel, self).setData(
                index, value, role)

        if ret:
            self.user_change.emit()
        return ret

    def __display_role(self, item, column):
        if column == 0:
            return MOD_TYPES[item.type] if item.type else None
        if column == 1:
            return item.dtl or (MOD_DTLS[item.type][1] if item.type in MOD_DTLS else None)
        if column == 2:
            return api.rules.format_rtk_t(item.value)
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
            model.unsaved = True
            self.dirty = False
