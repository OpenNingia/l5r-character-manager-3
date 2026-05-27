# -*- coding: utf-8 -*-
# Copyright (C) 2014-2026 Daniele Simonetti
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# Tab 5 — Perks (Advantages / Disadvantages a.k.a. Merits / Flaws).
# Extracted from l5r/main.py during the Phase 4 split — no behaviour
# changes.

from qtpy import QtCore, QtGui, QtWidgets

import l5r.dialogs as dialogs
import l5r.models as models
import l5r.widgets as widgets

from l5r.ui.helpers import new_item_groupbox
from l5r.util.fsutil import get_icon_path


class PerksSink(QtCore.QObject):
    """Qt slots for the Tab 5 merits / flaws (advantages / disadvantages)
    toolbar buttons and double-click."""

    def __init__(self, window):
        super().__init__(window)
        self.window = window

    def act_buy_merit(self):
        window = self.window
        dlg = dialogs.BuyPerkDialog(window.pc, 'merit', window)
        dlg.exec_()
        window.update_from_model()

    def act_buy_flaw(self):
        window = self.window
        dlg = dialogs.BuyPerkDialog(window.pc, 'flaw', window)
        dlg.exec_()
        window.update_from_model()

    def _open_merit(self, editmode):
        window = self.window

        sel_idx = window.merit_view.selectionModel().currentIndex()
        if not sel_idx.isValid():
            return
        sel_itm = window.merit_view.model().data(sel_idx, QtCore.Qt.UserRole)

        dlg = dialogs.BuyPerkDialog(window.pc, 'merit', window)
        dlg.set_edit_mode(editmode)
        dlg.load_item(sel_itm)
        dlg.exec_()
        if editmode:
            window.update_from_model()

    def act_view_merit(self):
        self._open_merit(False)

    def act_edit_merit(self):
        self._open_merit(True)

    def _open_flaw(self, editmode):
        window = self.window

        sel_idx = window.flaw_view.selectionModel().currentIndex()
        if not sel_idx.isValid():
            return
        sel_itm = window.flaw_view.model().data(sel_idx, QtCore.Qt.UserRole)

        dlg = dialogs.BuyPerkDialog(window.pc, 'flaw', window)
        dlg.set_edit_mode(editmode)
        dlg.load_item(sel_itm)
        dlg.exec_()
        if editmode:
            window.update_from_model()

    def act_view_flaw(self):
        self._open_flaw(False)

    def act_edit_flaw(self):
        self._open_flaw(True)

    def act_del_merit(self):
        window = self.window
        sel_idx = window.merit_view.selectionModel().currentIndex()
        if not sel_idx.isValid():
            return
        sel_itm = window.merit_view.model().data(sel_idx, QtCore.Qt.UserRole)
        window.remove_advancement_item(sel_itm.adv)

    def act_del_flaw(self):
        window = self.window
        sel_idx = window.flaw_view.selectionModel().currentIndex()
        if not sel_idx.isValid():
            return
        sel_itm = window.flaw_view.model().data(sel_idx, QtCore.Qt.UserRole)
        window.remove_advancement_item(sel_itm.adv)


class PerksTabMixin:
    """Tab 5: merits (advantages) + flaws (disadvantages)."""

    def build_ui_page_5(self):
        mfr = QtWidgets.QFrame(self)
        vbox = QtWidgets.QVBoxLayout(mfr)

        # advantages/disadvantage vertical toolbar
        def _make_vertical_tb(tag, has_edit, has_remove):
            vtb = widgets.VerticalToolBar(self)
            vtb.addStretch()

            cb_buy = (self.perks_sink.act_buy_merit if tag == 'merit'
                      else self.perks_sink.act_buy_flaw)
            cb_edit = (self.perks_sink.act_edit_merit if tag == 'merit'
                       else self.perks_sink.act_edit_flaw)
            cb_remove = (self.perks_sink.act_del_merit if tag == 'merit'
                         else self.perks_sink.act_del_flaw)

            vtb.addButton(QtGui.QIcon(get_icon_path('buy', (16, 16))),
                          self.tr("Add Perk"), cb_buy)

            if has_edit:
                vtb.addButton(QtGui.QIcon(get_icon_path('edit', (16, 16))),
                              self.tr("Edit Perk"), cb_edit)

            if has_remove:
                vtb.addButton(QtGui.QIcon(get_icon_path('minus', (16, 16))),
                              self.tr("Remove Perk"), cb_remove)

            vtb.addStretch()
            return vtb

        self.merits_view_model = models.PerkViewModel('merit')
        self.flaws_view_model = models.PerkViewModel('flaws')

        self.merits_sort_model = models.ColorFriendlySortProxyModel(self)
        self.merits_sort_model.setDynamicSortFilter(True)
        self.merits_sort_model.setSourceModel(self.merits_view_model)

        self.flaws_sort_model = models.ColorFriendlySortProxyModel(self)
        self.flaws_sort_model.setDynamicSortFilter(True)
        self.flaws_sort_model.setSourceModel(self.flaws_view_model)

        merit_view = QtWidgets.QTableView(self)
        merit_view.setSortingEnabled(True)
        merit_view.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.Interactive)
        merit_view.horizontalHeader().setStretchLastSection(True)
        merit_view.horizontalHeader().setCascadingSectionResizes(True)
        merit_view.doubleClicked.connect(self.perks_sink.act_view_merit)
        merit_view.setModel(self.merits_sort_model)
        merit_vtb = _make_vertical_tb('merit', True, True)
        fr_ = QtWidgets.QFrame(self)
        hb_ = QtWidgets.QHBoxLayout(fr_)
        hb_.setContentsMargins(3, 3, 3, 3)
        hb_.addWidget(merit_vtb)
        hb_.addWidget(merit_view)
        vbox.addWidget(new_item_groupbox(self.tr("Advantages"), fr_))

        flaw_view = QtWidgets.QTableView(self)
        flaw_view.setSortingEnabled(True)
        flaw_view.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.Interactive)
        flaw_view.horizontalHeader().setStretchLastSection(True)
        flaw_view.horizontalHeader().setCascadingSectionResizes(True)
        flaw_view.doubleClicked.connect(self.perks_sink.act_view_flaw)
        flaw_view.setModel(self.flaws_sort_model)
        flaw_vtb = _make_vertical_tb('flaw', True, True)
        fr_ = QtWidgets.QFrame(self)
        hb_ = QtWidgets.QHBoxLayout(fr_)
        hb_.setContentsMargins(3, 3, 3, 3)
        hb_.addWidget(flaw_vtb)
        hb_.addWidget(flaw_view)
        vbox.addWidget(new_item_groupbox(self.tr("Disadvantages"), fr_))

        self.merit_view = merit_view
        self.flaw_view = flaw_view
        self.table_views.append(self.merit_view)
        self.table_views.append(self.flaw_view)

        self.tabs.addTab(mfr, self.tr("Perks"))
