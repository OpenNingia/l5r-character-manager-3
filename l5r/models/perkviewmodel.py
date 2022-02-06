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

from PyQt5 import QtCore, QtGui

import l5r.api as api
import l5r.api.character.merits
import l5r.api.character.flaws

import l5r.api.data.merits
import l5r.api.data.flaws
from l5r.util import log
from l5r.util.settings import L5RCMSettings

class PerkItemModel(object):

    def __init__(self):
        self.name = ''
        self.cost = ''
        self.rank = ''
        self.tag = ''
        self.notes = ''
        self.adv = None

    def __str__(self):
        return self.name


class PerkViewModel(QtCore.QAbstractTableModel):

    def __init__(self, type_, parent=None):
        super(PerkViewModel, self).__init__(parent)

        self.items = []

        self.headers = [
            self.tr('Name'),
            self.tr('Rank'),
            self.tr('Value')]

        self.type = type_
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

    def build_item_model(self, model, perk_adv):
        itm = PerkItemModel()
        perk = api.data.merits.get(perk_adv.perk) or api.data.flaws.get(perk_adv.perk)

        if perk:
            itm.adv = perk_adv
            itm.name = perk.name
            itm.rank = perk_adv.rank
            itm.tag = perk_adv.tag
            itm.cost = perk_adv.cost
            itm.notes = perk_adv.extra
        else:
            log.model.error(u"perk not found: %s", perk_adv.perk)

        return itm

    def add_item(self, model, item_id):
        row = self.rowCount()
        self.beginInsertRows(QtCore.QModelIndex(), row, row)
        self.items.append(self.build_item_model(model, item_id))
        self.endInsertRows()

    def clean(self):
        self.beginResetModel()
        self.items = []
        self.endResetModel()

    def update_from_model(self, model):
        self.clean()
        if self.type == 'merit':
            for perk in api.character.merits.get_all():
                self.add_item(model, perk)
        else:
            for perk in api.character.flaws.get_all():
                self.add_item(model, perk)

    def data(self, index, role):
        if not index.isValid() or index.row() >= len(self.items):
            return None
        item = self.items[index.row()]
        if role == QtCore.Qt.DisplayRole:
            if index.column() == 0:
                return item.name
            if index.column() == 1:
                return item.rank
            if index.column() == 2:
                return abs(item.cost)
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
        elif role == QtCore.Qt.ToolTipRole:
            return item.notes
        elif role == QtCore.Qt.UserRole:
            return item
        return None


