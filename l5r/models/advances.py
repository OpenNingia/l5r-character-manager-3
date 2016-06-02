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
from datetime import datetime
import time

from l5r.util import log
from l5r.util.settings import L5RCMSettings


class Advancement(object):
    BUY_FOR_FREE = False

    @staticmethod
    def set_buy_for_free(flag):
        Advancement.BUY_FOR_FREE = flag
        log.rules.info(u"set buy for free? %s", Advancement.BUY_FOR_FREE)

    @staticmethod
    def get_buy_for_free():
        return Advancement.BUY_FOR_FREE

    def __init__(self, tag, cost):
        self.type = tag
        self.desc = ''
        self.rule = None
        self.timestamp = time.time()

        if Advancement.get_buy_for_free():
            self.cost = 0
        else:
            self.cost = cost

    def __str__(self):
        return self.desc


class AttribAdv(Advancement):

    def __init__(self, attrib, cost):
        super(AttribAdv, self).__init__('attrib', cost)
        self.attrib = attrib


class VoidAdv(Advancement):

    def __init__(self, cost):
        super(VoidAdv, self).__init__('void', cost)


class SkillAdv(Advancement):

    def __init__(self, skill, cost):
        super(SkillAdv, self).__init__('skill', cost)
        self.skill = skill


class SkillEmph(Advancement):

    def __init__(self, skill, text, cost):
        super(SkillEmph, self).__init__('emph', cost)
        self.skill = skill
        self.text = text


class PerkAdv(Advancement):

    def __init__(self, perk, rank, cost, tag=None):
        super(PerkAdv, self).__init__('perk', cost)
        self.perk = perk
        self.rank = rank
        self.tag = tag
        self.extra = ''


class KataAdv(Advancement):

    def __init__(self, kata_id, rule, cost):
        super(KataAdv, self).__init__('kata', cost)
        self.kata = kata_id
        self.rule = rule


class KihoAdv(Advancement):

    def __init__(self, kiho_id, rule, cost):
        super(KihoAdv, self).__init__('kiho', cost)
        self.kiho = kiho_id
        self.rule = rule


class SpellAdv(Advancement):

    def __init__(self, spell_id):
        super(SpellAdv, self).__init__('spell', 0)
        self.spell = spell_id


class MemoSpellAdv(Advancement):

    def __init__(self, spell_id, cost):
        super(MemoSpellAdv, self).__init__('memo_spell', cost)
        self.spell = spell_id


class AdvancementViewModel(QtCore.QAbstractListModel):

    def __init__(self, parent=None):
        super(AdvancementViewModel, self).__init__(parent)

        self.items = []
        self.settings = L5RCMSettings()

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self.items)

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
        for adv in reversed(model.advans):
            self.add_item(adv)

    def data(self, index, role):
        if not index.isValid() or index.row() >= len(self.items):
            return None
        item = self.items[index.row()]
        if role == QtCore.Qt.DisplayRole:
            return item.type
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
