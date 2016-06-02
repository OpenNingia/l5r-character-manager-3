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
import l5r.api.character.merits
import l5r.api.character.flaws

import l5r.api.data.merits
import l5r.api.data.flaws
from l5r.util import log


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


class PerkViewModel(QtCore.QAbstractListModel):

    def __init__(self, type_, parent=None):
        super(PerkViewModel, self).__init__(parent)

        self.items = []
        self.type = type_
        self.text_color = QtGui.QBrush(QtGui.QColor(0x15, 0x15, 0x15))
        self.bg_color = [QtGui.QBrush(QtGui.QColor(0xFF, 0xEB, 0x82)),
                         QtGui.QBrush(QtGui.QColor(0xEB, 0xFF, 0x82))]
        self.item_size = QtCore.QSize(32, 32)

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self.items)

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
            return item.name
        elif role == QtCore.Qt.ForegroundRole:
            return self.text_color
        elif role == QtCore.Qt.BackgroundRole:
            return self.bg_color[index.row() % 2]
        elif role == QtCore.Qt.SizeHintRole:
            return self.item_size
        elif role == QtCore.Qt.ToolTipRole:
            return item.notes
        elif role == QtCore.Qt.UserRole:
            return item
        return None


