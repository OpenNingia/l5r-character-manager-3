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
import l5r.api.data.schools
from l5r.util.settings import L5RCMSettings


class TechItemModel(object):

    def __init__(self):
        self.name = ''
        self.school_name = ''
        self.school_id = ''
        self.tech_rank = ''
        self.rank = ''
        self.desc = ''
        self.id = ''

    def __str__(self):
        return self.name

    def __lt__(self, obj):
        return self.rank < obj.rank

    def __eq__(self, obj):
        return self.rank == obj.rank

    def __ne__(self, obj):
        return not self.__eq__(obj)

    def __hash__(self):
        return self.rank.__hash__()


class TechViewModel(QtCore.QAbstractTableModel):

    def __init__(self, parent=None):
        super(TechViewModel, self).__init__(parent)

        self.items = []
        self.headers = [
            self.tr('Rank'),
            self.tr('School'),
            self.tr('School Rank'),
            self.tr('Name')]

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

    def build_item_model(self, tech_id, rank):
        itm = TechItemModel()

        school_, tech_ = api.data.schools.get_technique(tech_id)

        if school_ and tech_:
            itm.name = tech_.name
            itm.id = tech_id
            itm.school_name = school_.name
            itm.school_id = school_.id

            itm.tech_rank = str(tech_.rank)
            itm.rank = str(rank)
        return itm

    def add_item(self, item_id, rank):
        row = self.rowCount()
        self.beginInsertRows(QtCore.QModelIndex(), row, row)
        self.items.append(self.build_item_model(item_id, rank))
        self.endInsertRows()

    def clean(self):
        self.beginResetModel()
        self.items = []
        self.endResetModel()

    def update_from_model(self, model):
        self.clean()

        # for r in api.character.rankadv.get_all():
        #     tech_ = api.character.schools.get_tech_by_rank(r.rank)
        #     if tech_:
        #         self.add_item(tech_, r.rank)

        for i in range(1, 10):
            tech_ = api.character.schools.get_tech_by_rank(i)
            if tech_:
                self.add_item(tech_, i)
 
        # sort by rank
        self.items.sort(key=lambda x: int(x.rank))

    def adjust_tech_rank(self, model, tech_id):
        paths = [x for x in model.schools if x.is_path and tech_id in x.techs]
        if len(paths):
            return paths[0].path_rank
        return 0

    def data(self, index, role):
        if not index.isValid() or index.row() >= len(self.items):
            return None
        item = self.items[index.row()]
        if role == QtCore.Qt.DisplayRole:
            if index.column() == 0:
                return item.rank
            if index.column() == 1:
                return item.school_name
            if index.column() == 2:
                return item.tech_rank
            if index.column() == 3:
                return item.name
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


