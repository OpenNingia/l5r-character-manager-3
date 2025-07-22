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

import os
import l5r.models as models
import l5r.dialogs as dialogs

import l5r.widgets as widgets
import l5rdal as dal
import l5rdal.query

import l5r.api as api
import l5r.api.character

from l5r.util import log, osutil


class Sink4(QtCore.QObject):

    def __init__(self, parent=None):
        super(Sink4, self).__init__(parent)
        self.form = parent

    def add_new_modifier(self):
        item = models.ModifierModel()
        self.form.pc.add_modifier(item)
        dlg = dialogs.ModifierDialog(self.form.pc, self.form)
        dlg.set_modifier(item)
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            self.form.update_from_model()

    def edit_selected_modifier(self):
        index = self.form.mod_view.selectionModel().currentIndex()
        if not index.isValid():
            return
        item = index.model().data(index, QtCore.Qt.UserRole)
        dlg = dialogs.ModifierDialog(
            self.form.pc, self.form)
        dlg.set_modifier(item)
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            self.form.update_from_model()

    def remove_selected_modifier(self):
        index = self.form.mod_view.selectionModel().currentIndex()
        if not index.isValid():
            return
        item = index.model().data(index, QtCore.Qt.UserRole)
        self.form.pc.modifiers.remove(item)
        self.form.update_from_model()

    # DATA MENU
    def import_data_act(self):
        data_pack_files = self.form.select_import_data_pack()
        if data_pack_files:
            self.form.import_data_packs(data_pack_files)

    def manage_data_act(self):
        dlg = dialogs.ManageDataPackDlg(self.form.dstore, self.form)
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            self.form.update_data_blacklist()
            self.reload_data_act()

    def reload_data_act(self):
        self.form.reload_data()
        self.form.create_new_character()

    def add_equipment(self):
        equip_list = self.form.pc.get_property('equip', [])
        equip_list.append(self.tr('Doubleclick to edit'))
        self.form.update_from_model()

    def remove_selected_equipment(self):
        try:
            index = self.form.equip_view.selectionModel().currentIndex()
            if not index.isValid():
                return

            indexRow = index.row()
            newIndexRow = max(0, index.row()-1)
            newIndexCol = index.column()
            newIndexParent = index.parent()
            itemModel = index.model()

            start_outfit = api.character.get_starting_outfit() or []
            equip_list = self.form.pc.get_property('equip') or []

            if indexRow < len(start_outfit):
                # delete from starting outfit
                del start_outfit[indexRow]
                api.character.set_starting_outfit(start_outfit)
            else:
                indexRow -= len(start_outfit)
                if indexRow < len(equip_list):
                    del equip_list[indexRow]

            self.form.update_from_model()
            
            sibling = itemModel.index(newIndexRow, newIndexCol, newIndexParent)
            if sibling.isValid():
                self.form.equip_view.selectionModel().setCurrentIndex(sibling, QtCore.QItemSelectionModel.SelectCurrent)
        except:
            log.ui.error("Shit happens", exc_info=1, stack_info=True)


    def on_money_value_changed(self, value):
        api.character.set_money(value)

    # EDIT FAMILY
    def on_edit_family(self):
        form = self.form
        dlg = widgets.FamilyChooserDialog(form)
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            form.update_from_model()

    # EDIT FIRST SCHOOL
    def on_edit_first_school(self):
        form = self.form
        dlg = widgets.FirstSchoolChooserDialog(form)
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            form.update_from_model()

    def on_tech_item_activate(self, index):
        item = self.form.th_view_model.data(index, QtCore.Qt.UserRole)
        try:
            school, tech = api.data.schools.get_technique(item.id)
        except:
            log.ui.error("cannot retrieve information from tech model.", exc_info=1)
        else:
            self._simple_description_dialog(
                self.form,
                tech.name,
                school.name,
                tech.desc
            )

    def on_spell_item_activate(self, index):
        item = self.form.sp_sort_model.data(index, QtCore.Qt.UserRole)
        try:
            spell = api.data.spells.get(item.spell_id)
        except Exception as e:
            log.ui.error("cannot retrieve information from spell model.", exc_info=1)
        else:
            self._simple_description_dialog(
                self.form,
                spell.name,
                self._subtitle(
                    "{element}, Mastery {mastery}",
                    element=self._get_element_ring(spell),
                    mastery=spell.mastery
                ),
                spell.desc
            )

    def on_kata_item_activate(self, index):
        item = self.form.ka_sort_model.data(index, QtCore.Qt.UserRole)
        try:
            kata = api.data.powers.get_kata(item.id)
        except Exception as e:
            log.ui.error("cannot retrieve information from kata model.", exc_info=1)
        else:
            self._simple_description_dialog(
                self.form,
                kata.name,
                self._subtitle(
                    '{element}, Mastery {mastery}',
                    element=self._get_element_ring(kata),
                    mastery=kata.mastery
                ),
                kata.desc
            )

    def on_kiho_item_activate(self, index):
        item = self.form.ki_sort_model.data(index, QtCore.Qt.UserRole)
        try:
            kiho = api.data.powers.get_kiho(item.id)
        except Exception as e:
            log.ui.error("cannot retrieve information from kiho model.", exc_info=1)
        else:
            self._simple_description_dialog(
                self.form,
                kiho.name,
                self._subtitle(
                    '{type} - {element},  Mastery {mastery}',
                    element=self._get_element_ring(kiho),
                    mastery=kiho.mastery,
                    type=kiho.type
                ),
                kiho.desc
            )

    def on_skill_item_activate(self, index):
        item = self.form.sk_sort_model.data(index, QtCore.Qt.UserRole)
        try:
            skill = api.data.skills.get(item)
        except Exception as e:
            log.ui.error("cannot retrieve information from skill model.", exc_info=1)
        else:            
            description = self.tr('<h3>Mastery Abilities:</h3>')
            for i in skill.mastery_abilities:
                description += '<B>{rank}</B>: {desc}<BR/>\n'.format(
                    rank=i.rank,
                    desc=i.desc,
                )

            if skill.desc:
                description += self.tr('<h3>Description</h3>')
                description += skill.desc

            self._simple_description_dialog(
                self.form,
                skill.name,
                skill.type,
                description
            )

    def _subtitle(self, format, **kwargs):
        subtitle = self.tr(format)
        return subtitle.format(**kwargs)

    def _get_element_ring(self, item):
        ring_ = api.data.get_ring(item.element)
        if not ring_:
            return item.element
        return ring_.text

    def _simple_description_dialog(self, parent, title, subtitle, desc):
        dlg = widgets.SimpleDescriptionDialog(parent)
        dlg.description().set_title(title)
        dlg.description().set_subtitle(subtitle)
        dlg.description().set_content(desc)
        dlg.exec_()
