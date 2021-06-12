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
import l5r.api.data.outfit
import l5r.api.data.skills

from l5r.util import log
from l5r.util.settings import L5RCMSettings


class ArmorOutfit(object):

    def __init__(self):
        self.tn = 0
        self.rd = 0
        self.name = ''
        self.desc = ''
        self.rule = ''
        self.cost = ''


class WeaponOutfit(object):

    def __init__(self):
        self.dr = ''
        self.dr_alt = ''
        self.name = ''
        self.desc = ''
        self.rule = ''
        self.cost = ''
        self.range = ''
        self.strength = 0
        self.min_str = 0
        self.qty = 1
        self.skill_id = None
        self.skill_nm = ''
        self.base_atk = ''
        self.max_atk = ''
        self.base_dmg = ''
        self.max_dmg = ''
        self.tags = []
        self.trait = ''


def weapon_outfit_from_db(weap_nm, sk_uuid=None):
    itm = WeaponOutfit()

    weapon = api.data.outfit.get_weapon(weap_nm)
    effect_ = api.data.outfit.get_effect(weapon.effectid)
    effect_tx = effect_.text if effect_ is not None else ''

    itm.name = weapon.name
    itm.dr = weapon.dr or 'N/A'
    itm.dr_alt = weapon.dr2 or 'N/A'
    itm.rule = weapon.effectid
    itm.desc = effect_tx
    itm.cost = weapon.cost or 'N/A'
    itm.range = weapon.range or 'N/A'
    itm.strength = weapon.strength or 'N/A'
    itm.min_str = weapon.min_strength or 'N/A'
    itm.tags = weapon.tags
    itm.skill_id = weapon.skill

    try:
        itm.skill_nm = api.data.skills.get(weapon.skill).name
        itm.trait = api.data.skills.get(weapon.skill).trait
    except Exception as ex:
        log.model.error(u"weapon skill not found: %s", weapon.skill)

    return itm


def armor_outfit_from_db(armor_nm):
    itm = ArmorOutfit()

    armor = api.data.outfit.get_armor(armor_nm)
    effect_ = api.data.outfit.get_effect(armor.effectid)
    effect_tx = effect_.text if effect_ is not None else ''

    itm.name = armor.name
    itm.tn = armor.tn
    itm.rd = armor.rd
    itm.rule = effect_tx
    itm.cost = armor.cost

    return itm


class WeaponTableViewModel(QtCore.QAbstractTableModel):

    def __init__(self, type_, parent=None):
        super(WeaponTableViewModel, self).__init__(parent)
        self.type = type_
        self.items = []
        if type_ == 'melee':
            self.headers = [
                self.tr('Name'),
                self.tr('DR'),
                self.tr('Sec. DR'),
                self.tr('ATK Roll'),
                self.tr('Mod. ATK Roll'),
                self.tr('DMG Roll'),
                self.tr('Mod. DMG Roll')]
        elif type_ == 'ranged':
            self.headers = [
                self.tr('Name'),
                self.tr('Range'),
                self.tr('Strength'),
                self.tr('Min. Str.'),
                self.tr('ATK Roll'),
                self.tr('Mod. ATK Roll')]
        elif type_ == 'arrow':
            self.headers = [
                self.tr('Name'),
                self.tr('DR'),
                self.tr('Quantity')]

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
            if self.type == 'melee':
                return self.melee_display_role(item, index.column())
            elif self.type == 'ranged':
                return self.ranged_display_role(item, index.column())
            elif self.type == 'arrow':
                return self.arrow_display_role(item, index.column())
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

    def melee_display_role(self, item, column):
        if column == 0:
            return item.name
        if column == 1:
            return item.dr
        if column == 2:
            return item.dr_alt
        if column == 3:
            return item.base_atk
        if column == 4:
            return item.max_atk
        if column == 5:
            return item.base_dmg
        if column == 6:
            return item.max_dmg
        return None

    def ranged_display_role(self, item, column):
        if column == 0:
            return item.name
        if column == 1:
            return item.range
        if column == 2:
            return item.strength
        if column == 3:
            return item.min_str
        if column == 4:
            return item.base_atk
        if column == 5:
            return item.max_atk
        return None

    def arrow_display_role(self, item, column):
        if column == 0:
            return item.name
        if column == 1:
            return item.dr
        if column == 2:
            return item.qty
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

    def update_from_model(self, model):
        self.clean()
        for w in model.get_weapons():
            if self.type in w.tags:
                # calculate weapon atk
                w.base_atk = api.rules.format_rtk_t(
                    api.rules.calculate_base_attack_roll(model, w))
                w.max_atk = api.rules.format_rtk_t(
                    api.rules.calculate_mod_attack_roll(model, w))
                w.base_dmg = api.rules.format_rtk_t(
                    api.rules.calculate_base_damage_roll(model, w))
                w.max_dmg = api.rules.format_rtk_t(
                    api.rules.calculate_mod_damage_roll(model, w))
                self.add_item(w)


class EquipmentListModel(QtCore.QAbstractListModel):

    def __init__(self, parent=None):
        super(EquipmentListModel, self).__init__(parent)

        self.school_outfit = []
        self.items = []
        self.settings = L5RCMSettings()

        self.bold_font = None
        if self.parent:
            self.bold_font = parent.font()
            self.bold_font.setBold(True)

    def rowCount(self, parent=QtCore.QModelIndex()):
        # if not self.items:
        #    return 0
        return len(self.items) + len(self.school_outfit)

    def flags(self, index):
        if not index.isValid():
            return QtCore.Qt.ItemIsDropEnabled
        flags = QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsEditable
        return flags

    def add_item(self, item):
        row = self.rowCount()
        self.beginInsertRows(QtCore.QModelIndex(), row, row)
        # self.items.append(item)
        self.endInsertRows()

    def clean(self):
        self.beginResetModel()
        self.school_outfit = []
        self.items = []
        self.endResetModel()

    def is_school_item(self, index):
        if not index.isValid():
            return False
        return index.row() < len(self.school_outfit)

    def update_from_model(self, model):
        self.clean()
        equip_list = model.get_property('equip', [])

        starting_outfit_ = []
        first_rank_ = api.character.rankadv.get_first()
        if first_rank_:
            starting_outfit_ = first_rank_.outfit

        for e in starting_outfit_ + equip_list:
            self.add_item(e)
        self.items = equip_list
        self.school_outfit = starting_outfit_

    def data(self, index, role=QtCore.Qt.UserRole):
        # if not self.items or not index.isValid() or index.row() >= len(self.items):
        #    return None
        if not index.isValid():
            return None

        item = None
        if self.is_school_item(index):
            item = self.school_outfit[index.row()]
        else:
            item = self.items[index.row() - len(self.school_outfit)]

        try:
            item = item.decode('utf-8')
        except:
            pass

        if role == QtCore.Qt.DisplayRole:
            return item
        if role == QtCore.Qt.EditRole:
            return item
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
        elif role == QtCore.Qt.FontRole:
            if self.is_school_item(index):
                return self.bold_font
        elif role == QtCore.Qt.UserRole:
            return item
        return None

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        if role != QtCore.Qt.EditRole:
            return super(EquipmentListModel, self).setData(index, value, role)
        else:
            if self.is_school_item(index):
                self.school_outfit[index.row()] = value.encode('utf-8')
            else:
                self.items[index.row() - len(self.school_outfit)] = value.encode('utf-8')
        return True
