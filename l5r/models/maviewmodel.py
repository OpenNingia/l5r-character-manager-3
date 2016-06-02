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
import l5r.api.character.skills
import l5r.api.data.skills
from l5r.util import log
from l5r.util.settings import L5RCMSettings


class MaItemModel(object):

    def __init__(self):
        self.skill_name = ''
        self.skill_rank = ''
        self.desc = ''

    def __str__(self):
        return self.desc


class MaViewModel(QtCore.QAbstractTableModel):

    def __init__(self, parent=None):
        super(MaViewModel, self).__init__(parent)

        self.items = []
        self.headers = [
            self.tr('Skill'),
            self.tr('Rank'),
            self.tr('Effect')]

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

    def add_item(self, sk_name, sk_rnk, ma_brief):
        row = self.rowCount()
        self.beginInsertRows(QtCore.QModelIndex(), row, row)

        itm = MaItemModel()
        itm.skill_name = sk_name
        itm.skill_rank = str(sk_rnk)
        itm.desc = ma_brief

        self.items.append(itm)
        self.endInsertRows()

    def clean(self):
        self.beginResetModel()
        self.items = []
        self.endResetModel()

    def get_mastery_abilities(self):
        for sk_uuid in api.character.skills.get_all():
            sk_rank = api.character.skills.get_skill_rank(sk_uuid)
            sk = api.data.skills.get(sk_uuid)

            if not sk:
                log.model.error(u"skill not found: %s", sk_uuid)
                continue

            mas = [x for x in sk.mastery_abilities if x.rank <= sk_rank]

            for ma in mas:
                yield sk.name, ma.rank, ma.desc

    def update_from_model(self, model):
        self.clean()
        for sk_name, sk_rnk, ma_brief in self.get_mastery_abilities():
            self.add_item(sk_name, sk_rnk, ma_brief)

    def data(self, index, role):
        if not index.isValid() or index.row() >= len(self.items):
            return None
        item = self.items[index.row()]
        if role == QtCore.Qt.DisplayRole:
            if index.column() == 0:
                return item.skill_name
            if index.column() == 1:
                return item.skill_rank
            if index.column() == 2:
                return item.desc
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


