# -*- coding: utf-8 -*-
# Copyright (C) 2014-2026 Daniele Simonetti
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# Tab 7 — Weapons (melee + ranged + arrows). Extracted from l5r/main.py
# during the Phase 4 split — no behaviour changes.

from qtpy import QtCore, QtGui, QtWidgets

import l5r.dialogs as dialogs
import l5r.models as models
import l5r.widgets as widgets

from l5r.util import log
from l5r.util.fsutil import get_icon_path


class WeaponsSink(QtCore.QObject):
    """Qt slots for the Tab 7 weapons toolbars (melee / ranged / arrows).

    All toolbar buttons set a 'source' property pointing at the relevant
    QTableView; these slots read the active selection through that
    property via ``self.sender().parent().property('source')``.
    """

    def __init__(self, window):
        super().__init__(window)
        self.window = window

    def show_add_weapon(self):
        window = self.window
        dlg = dialogs.ChooseItemDialog(window.pc, 'weapon', window)
        filter = self.sender().parent().property('filter')
        if filter is not None:
            dlg.set_filter(filter)
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            window.update_from_model()

    def show_add_cust_weapon(self):
        window = self.window
        dlg = dialogs.CustomWeaponDialog(window.pc, window)
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            window.update_from_model()

    def edit_selected_weapon(self):
        window = self.window

        view_ = None
        try:
            view_ = self.sender().parent().property('source')
        except Exception:
            log.ui.error("Edit weapon error", exc_info=1)
        if view_ is None:
            return
        sel_idx = view_.selectionModel().currentIndex()
        if not sel_idx.isValid():
            return
        sel_itm = view_.model().data(sel_idx, QtCore.Qt.UserRole)
        dlg = dialogs.CustomWeaponDialog(window.pc, window)
        dlg.edit_mode = True
        log.ui.debug('loading weap {0}, tags: {1}'.format(sel_itm.name, sel_itm.tags))
        dlg.load_item(sel_itm)
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            window.update_from_model()

    def remove_selected_weapon(self):
        window = self.window

        view_ = None
        try:
            view_ = self.sender().parent().property('source')
        except Exception:
            log.ui.error("Remove weapon error", exc_info=1)
        if view_ is None:
            return
        sel_idx = view_.selectionModel().currentIndex()
        if not sel_idx.isValid():
            return
        sel_itm = view_.model().data(sel_idx, QtCore.Qt.UserRole)
        window.pc.weapons.remove(sel_itm)
        window.update_from_model()

    def _change_item_qty(self, delta):
        """Bump the selected item's qty by delta (clamped to [1, 9999])."""
        window = self.window

        view_ = None
        try:
            view_ = self.sender().parent().property('source')
        except Exception:
            log.ui.error("Change quantity error", exc_info=1)
        if view_ is None:
            return
        sel_idx = view_.selectionModel().currentIndex()
        if not sel_idx.isValid():
            return
        sel_itm = view_.model().data(sel_idx, QtCore.Qt.UserRole)
        new_qty = sel_itm.qty + delta
        if 1 <= new_qty <= 9999:
            sel_itm.qty = new_qty
            window.update_from_model()
            sel_idx = view_.model().index(sel_idx.row(), 0)
            view_.selectionModel().setCurrentIndex(
                sel_idx,
                QtCore.QItemSelectionModel.Select | QtCore.QItemSelectionModel.Rows)

    def on_increase_item_qty(self):
        self._change_item_qty(+1)

    def on_decrease_item_qty(self):
        self._change_item_qty(-1)


class WeaponsTabMixin:
    """Tab 7: three weapon tables with shared add/edit/remove toolbar."""

    def build_ui_page_7(self):
        self.melee_view_model = models.WeaponTableViewModel('melee', self)
        self.ranged_view_model = models.WeaponTableViewModel('ranged', self)
        self.arrow_view_model = models.WeaponTableViewModel('arrow', self)

        def _make_sortable(model):
            # enable sorting through a proxy model
            sort_model_ = models.ColorFriendlySortProxyModel(self)
            sort_model_.setDynamicSortFilter(True)
            sort_model_.setSourceModel(model)
            return sort_model_

        # weapon vertical toolbar
        def _make_vertical_tb(has_custom, has_edit, has_qty, filt):
            vtb = widgets.VerticalToolBar(self)
            vtb.setProperty('filter', filt)
            vtb.addStretch()
            vtb.addButton(QtGui.QIcon(get_icon_path('buy', (16, 16))),
                          self.tr("Add weapon"), self.weapons_sink.show_add_weapon)
            if has_custom:
                vtb.addButton(QtGui.QIcon(get_icon_path('custom', (16, 16))),
                              self.tr("Add custom weapon"), self.weapons_sink.show_add_cust_weapon)
            if has_edit:
                vtb.addButton(QtGui.QIcon(get_icon_path('edit', (16, 16))),
                              self.tr("Edit weapon"), self.weapons_sink.edit_selected_weapon)
            vtb.addButton(QtGui.QIcon(get_icon_path('minus', (16, 16))),
                          self.tr("Remove weapon"), self.weapons_sink.remove_selected_weapon)
            if has_qty:
                vtb.addButton(QtGui.QIcon(get_icon_path('add', (16, 16))),
                              self.tr("Increase Quantity"), self.weapons_sink.on_increase_item_qty)
                vtb.addButton(QtGui.QIcon(get_icon_path('minus', (16, 16))),
                              self.tr("Decrease Quantity"), self.weapons_sink.on_decrease_item_qty)

            vtb.addStretch()
            return vtb

        melee_vtb = _make_vertical_tb(True, True, False, 'melee')
        ranged_vtb = _make_vertical_tb(True, True, False, 'ranged')
        arrow_vtb = _make_vertical_tb(False, False, True, 'arrow')

        models_ = [
            (self.tr("Melee Weapons"), 'table', _make_sortable(self.melee_view_model), None, melee_vtb, None),
            (self.tr("Ranged Weapons"), 'table', _make_sortable(self.ranged_view_model), None, ranged_vtb, None),
            (self.tr("Arrows"), 'table', _make_sortable(self.arrow_view_model), None, arrow_vtb, None)
        ]

        frame_, views_ = self._build_generic_page(models_)

        melee_vtb .setProperty('source', views_[0])
        ranged_vtb.setProperty('source', views_[1])
        arrow_vtb .setProperty('source', views_[2])

        self.tabs.addTab(frame_, self.tr("Weapons"))
