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

from l5r.util.fsutil import get_icon_path
from l5r.util.settings import L5RCMSettings

import l5r.api as api
import l5r.api.data.spells
import l5r.api.character.schools


class SpellItemModel(object):

    def __init__(self):
        self.id = ''
        self.name = ''
        self.ring = ''
        self.mastery = ''
        self.range = ''
        self.area = ''
        self.duration = ''
        self.raises = ''
        self.desc = ''
        self.memo = False
        self.is_school = False
        self.tags = ''
        self.spell_id = 0
        self.adv = None

    def __str__(self):
        return self.name


class SpellTableViewModel(QtCore.QAbstractTableModel):

    def __init__(self, parent=None):
        super(SpellTableViewModel, self).__init__(parent)

        self.items = []
        self.headers = [
            self.tr('Name'),
            self.tr('Ring'),
            self.tr('Mastery'),
            self.tr('Range'),
            self.tr('Area of Effect'),
            self.tr('Duration'),
            self.tr('Raises')]

        self.settings = L5RCMSettings()
        if parent:
            self.bold_font = parent.font()
            self.bold_font.setBold(True)

        self.memo_icon = QtGui.QIcon(get_icon_path('book', (16, 16)))

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

    def data(self, index, role):
        if not index.isValid() or index.row() >= len(self.items):
            return None
        item = self.items[index.row()]
        if role == QtCore.Qt.DisplayRole:
            if index.column() == 0:
                return item.name
            if index.column() == 1:
                return item.ring
            if index.column() == 2:
                return item.mastery
            if index.column() == 3:
                return item.range
            if index.column() == 4:
                return item.area
            if index.column() == 5:
                return item.duration
            if index.column() == 6:
                return item.raises
        elif role == QtCore.Qt.UserRole:
            return item
        elif role == QtCore.Qt.FontRole:
            if item.is_school and self.bold_font:
                return self.bold_font
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
            if index.column() == 1:
                if len(item.tags) > 0:
                    return 'Spell Tags: %s' % ', '.join(item.tags)
            if index.column() == 3:
                return item.range
            if index.column() == 4:
                return item.area
            if index.column() == 5:
                return item.duration
            if index.column() == 6:
                return item.raises
        elif role == QtCore.Qt.DecorationRole:
            if index.column() == 0 and item.memo:
                return self.memo_icon
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

    def build_item_model(self, sp_id):

        def get_element_(tag):
            try:
                return api.data.get_ring(tag).text
            except:
                return tag

        itm = SpellItemModel()

        spell = api.data.spells.get(sp_id)

        itm.id = spell.id
        itm.name = spell.name

        if api.data.spells.is_multi_element(spell.id):
            itm.ring = u", ".join([get_element_(x) for x in spell.elements])
        else:
            itm.ring = get_element_(spell.element)

        itm.mastery = spell.mastery
        itm.range = spell.range
        itm.area = spell.area
        itm.duration = spell.duration
        itm.raises = ', '.join(spell.raises)
        itm.desc = spell.desc

        itm.tags = ', '.join(api.data.spells.tags(spell.id))
        itm.spell_id = sp_id

        return itm

    def update_from_model(self, model):
        spells = api.character.spells.get_all()
        memo_spells = api.character.spells.get_memorized_spells()

        self.clean()

        for s in spells:
            itm = self.build_item_model(s)
            itm.memo = s in memo_spells

            self.add_item(itm)
