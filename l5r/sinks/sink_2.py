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

import l5r.dialogs as dialogs


class Sink2(QtCore.QObject):

    def __init__(self, parent=None):
        super(Sink2, self).__init__(parent)
        self.form = parent

    def act_buy_merit(self):
        form = self.form

        dlg = dialogs.BuyPerkDialog(form.pc, 'merit', form)
        dlg.exec_()
        form.update_from_model()

    def act_buy_flaw(self):
        form = self.form

        dlg = dialogs.BuyPerkDialog(form.pc, 'flaw', form)
        dlg.exec_()
        form.update_from_model()

    def _open_merit(self, editmode):
        form = self.form

        sel_idx = form.merit_view.selectionModel().currentIndex()
        if not sel_idx.isValid():
            return
        sel_itm = form.merit_view.model().data(sel_idx, QtCore.Qt.UserRole)

        dlg = dialogs.BuyPerkDialog(form.pc, 'merit', form)

        dlg.set_edit_mode(editmode)
        dlg.load_item(sel_itm)
        dlg.exec_()
        if editmode:
            form.update_from_model()

    def act_view_merit(self):
        self._open_merit(False)

    def act_edit_merit(self):
        self._open_merit(True)

    def _open_flaw(self, editmode):
        form = self.form

        sel_idx = form.flaw_view.selectionModel().currentIndex()
        if not sel_idx.isValid():
            return
        sel_itm = form.flaw_view.model().data(sel_idx, QtCore.Qt.UserRole)

        dlg = dialogs.BuyPerkDialog(form.pc, 'flaw', form)

        dlg.set_edit_mode(editmode)
        dlg.load_item(sel_itm)
        dlg.exec_()
        if editmode:
            form.update_from_model()

    def act_view_flaw(self):
        self._open_flaw(False)

    def act_edit_flaw(self):
        self._open_flaw(True)

    def act_del_merit(self):
        form = self.form

        sel_idx = form.merit_view.selectionModel().currentIndex()
        if not sel_idx.isValid():
            return
        sel_itm = form.merit_view.model().data(sel_idx, QtCore.Qt.UserRole)
        form.remove_advancement_item(sel_itm.adv)

    def act_del_flaw(self):
        form = self.form

        sel_idx = form.flaw_view.selectionModel().currentIndex()
        if not sel_idx.isValid():
            return
        sel_itm = form.flaw_view.model().data(sel_idx, QtCore.Qt.UserRole)
        form.remove_advancement_item(sel_itm.adv)

    def act_buy_kata(self):
        form = self.form

        dlg = dialogs.KataDialog(form.pc, form)
        dlg.exec_()
        form.update_from_model()

    def act_buy_kiho(self):
        form = self.form
        dlg = dialogs.KihoDialog(form.pc, form)
        dlg.exec_()
        form.update_from_model()

    def act_buy_tattoo(self):
        form = self.form
        dlg = dialogs.TattooDialog(form.pc, form)
        dlg.exec_()
        form.update_from_model()

    def act_del_kata(self):
        form = self.form

        sel_idx = form.kata_view.selectionModel().currentIndex()
        if not sel_idx.isValid():
            return
        sel_itm = form.ka_table_view.model().data(sel_idx, QtCore.Qt.UserRole)
        form.remove_advancement_item(sel_itm.adv)

    def act_del_kiho(self):
        form = self.form

        sel_idx = form.kiho_view.selectionModel().currentIndex()
        if not sel_idx.isValid():
            return
        sel_itm = form.ki_table_view.model().data(sel_idx, QtCore.Qt.UserRole)
        form.remove_advancement_item(sel_itm.adv)
