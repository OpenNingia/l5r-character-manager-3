# -*- coding: utf-8 -*-
# Copyright (C) 2014-2026 Daniele Simonetti
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# Tab 4 — Powers (Katas + Kihos). Extracted from l5r/main.py during the
# Phase 4 split — no behaviour changes.

from qtpy import QtCore, QtGui, QtWidgets

import l5r.dialogs as dialogs
import l5r.models as models
import l5r.widgets as widgets

from l5r.api.data import CMErrors
from l5r.util.fsutil import get_icon_path


class PowersSink(QtCore.QObject):
    """Qt slots for Tab 4 katas + kihos toolbar buttons."""

    def __init__(self, window):
        super().__init__(window)
        self.window = window

    def act_buy_kata(self):
        window = self.window
        dlg = dialogs.KataDialog(window.pc, window)
        dlg.exec_()
        window.update_from_model()

    def act_buy_kiho(self):
        window = self.window
        dlg = dialogs.KihoDialog(window.pc, window)
        dlg.exec_()
        window.update_from_model()

    def act_buy_tattoo(self):
        window = self.window
        dlg = dialogs.TattooDialog(window.pc, window)
        dlg.exec_()
        window.update_from_model()

    def act_del_kata(self):
        window = self.window
        sel_idx = window.kata_view.selectionModel().currentIndex()
        if not sel_idx.isValid():
            return
        sel_itm = window.ka_table_view.model().data(sel_idx, QtCore.Qt.UserRole)
        window.remove_advancement_item(sel_itm.adv)

    def act_del_kiho(self):
        window = self.window
        sel_idx = window.kiho_view.selectionModel().currentIndex()
        if not sel_idx.isValid():
            return
        sel_itm = window.ki_table_view.model().data(sel_idx, QtCore.Qt.UserRole)
        window.remove_advancement_item(sel_itm.adv)


class PowersTabMixin:
    """Tab 4: katas table + kihos table (with tattoo button)."""

    def build_ui_page_4(self):
        self.ka_view_model = models.KataTableViewModel(self)
        self.ki_view_model = models.KihoTableViewModel(self)

        # enable sorting through a proxy model
        self.ka_sort_model = models.ColorFriendlySortProxyModel(self)
        self.ka_sort_model.setDynamicSortFilter(True)
        self.ka_sort_model.setSourceModel(self.ka_view_model)

        self.ki_sort_model = models.ColorFriendlySortProxyModel(self)
        self.ki_sort_model.setDynamicSortFilter(True)
        self.ki_sort_model.setSourceModel(self.ki_view_model)

        frame_ = QtWidgets.QFrame(self)
        vbox = QtWidgets.QVBoxLayout(frame_)

        self.kata_view = self._build_kata_frame(self.ka_sort_model, vbox)
        self.kiho_view = self._build_kiho_frame(self.ki_sort_model, vbox)

        self.tabs.addTab(frame_, self.tr("Powers"))

    def _build_kata_frame(self, model, layout):
        grp = QtWidgets.QGroupBox(self.tr("Kata"), self)
        hbox = QtWidgets.QHBoxLayout(grp)

        fr_ = QtWidgets.QFrame(self)
        vbox = QtWidgets.QVBoxLayout(fr_)
        vbox.setContentsMargins(3, 3, 3, 3)

        # advantages/disadvantage vertical toolbar
        def _make_vertical_tb():
            vtb = widgets.VerticalToolBar(self)
            vtb.addStretch()

            cb_buy = self.powers_sink.act_buy_kata
            cb_remove = self.powers_sink.act_del_kata

            self.add_kata_bt = vtb.addButton(
                QtGui.QIcon(get_icon_path('buy', (16, 16))),
                self.tr("Add new Kata"), cb_buy)

            self.del_kata_bt = vtb.addButton(
                QtGui.QIcon(get_icon_path('minus', (16, 16))),
                self.tr("Remove Kata"), cb_remove)

            self.add_kata_bt.setEnabled(True)
            self.del_kata_bt.setEnabled(True)

            vtb.addStretch()
            return vtb

        # View
        view = QtWidgets.QTableView(self)
        view.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                           QtWidgets.QSizePolicy.Expanding)
        view.setSortingEnabled(True)
        view.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Interactive)
        view.horizontalHeader().setStretchLastSection(True)
        view.horizontalHeader().setCascadingSectionResizes(True)
        view.setModel(model)
        view.doubleClicked.connect(self.sink4.on_kata_item_activate)
        self.ka_table_view = view
        self.table_views.append(view)

        vbox.addWidget(view)

        hbox.addWidget(_make_vertical_tb())
        hbox.addWidget(fr_)

        layout.addWidget(grp)

        return view

    def _build_kiho_frame(self, model, layout):
        grp = QtWidgets.QGroupBox(self.tr("Kiho"), self)
        hbox = QtWidgets.QHBoxLayout(grp)

        fr_ = QtWidgets.QFrame(self)
        vbox = QtWidgets.QVBoxLayout(fr_)
        vbox.setContentsMargins(3, 3, 3, 3)

        # advantages/disadvantage vertical toolbar
        def _make_vertical_tb():
            vtb = widgets.VerticalToolBar(self)
            vtb.addStretch()

            cb_buy = self.powers_sink.act_buy_kiho
            cb_remove = self.powers_sink.act_del_kiho
            cb_buy_tattoo = self.powers_sink.act_buy_tattoo

            self.add_kiho_bt = vtb.addButton(
                QtGui.QIcon(get_icon_path('buy', (16, 16))),
                self.tr("Add new Kiho"), cb_buy)

            self.add_tattoo_bt = vtb.addButton(
                QtGui.QIcon(get_icon_path('buy', (16, 16))),
                self.tr("Add new Tattoo"), cb_buy_tattoo)

            self.del_kiho_bt = vtb.addButton(
                QtGui.QIcon(get_icon_path('minus', (16, 16))),
                self.tr("Remove Kiho"), cb_remove)

            self.add_kiho_bt.setEnabled(True)
            self.del_kiho_bt.setEnabled(True)

            vtb.addStretch()
            return vtb

        # View
        view = QtWidgets.QTableView(self)
        view.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                           QtWidgets.QSizePolicy.Expanding)
        view.setSortingEnabled(True)
        view.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Interactive)
        view.horizontalHeader().setStretchLastSection(True)
        view.horizontalHeader().setCascadingSectionResizes(True)
        view.setModel(model)
        view.doubleClicked.connect(self.sink4.on_kiho_item_activate)
        self.ki_table_view = view
        self.table_views.append(view)

        vbox.addWidget(view)

        hbox.addWidget(_make_vertical_tb())
        hbox.addWidget(fr_)

        layout.addWidget(grp)

        return view

    def do_buy_kata(self, kata):
        """attempt to buy a new kata"""
        if self.buy_kata(kata) == CMErrors.NOT_ENOUGH_XP:
            self.not_enough_xp_advise(self)

    def do_buy_kiho(self, kiho):
        """attempt to buy a new kiho"""
        if self.buy_kiho(kiho) == CMErrors.NOT_ENOUGH_XP:
            self.not_enough_xp_advise(self)
