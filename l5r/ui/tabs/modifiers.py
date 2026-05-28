# -*- coding: utf-8 -*-
# Copyright (C) 2014-2026 Daniele Simonetti
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# Tab 8 — Modifiers. Extracted from l5r/main.py during the Phase 4
# split — no behaviour changes.

from qtpy import QtCore, QtGui, QtWidgets

import l5r.dialogs as dialogs
import l5r.models as models
import l5r.widgets as widgets

from l5r.util.fsutil import get_icon_path


class ModifiersSink(QtCore.QObject):
    """Qt slots for the Tab 8 modifiers toolbar."""

    def __init__(self, window):
        super().__init__(window)
        self.window = window

    def add_new_modifier(self):
        window = self.window
        item = models.ModifierModel()
        window.pc.add_modifier(item)
        dlg = dialogs.ModifierDialog(window.pc, window)
        dlg.set_modifier(item)
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            window.update_from_model()

    def edit_selected_modifier(self):
        window = self.window
        index = window.mod_view.selectionModel().currentIndex()
        if not index.isValid():
            return
        item = index.model().data(index, QtCore.Qt.UserRole)
        dlg = dialogs.ModifierDialog(window.pc, window)
        dlg.set_modifier(item)
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            window.update_from_model()

    def remove_selected_modifier(self):
        window = self.window
        index = window.mod_view.selectionModel().currentIndex()
        if not index.isValid():
            return
        item = index.model().data(index, QtCore.Qt.UserRole)
        window.pc.modifiers.remove(item)
        window.update_from_model()


class ModifiersTabMixin:
    """Tab 8: modifiers table with add/edit/remove toolbar."""

    def build_ui_page_8(self):
        # modifiers
        self.mods_view_model = models.ModifiersTableViewModel(self)
        self.mods_view_model.user_change.connect(self.update_from_model)

        def _make_sortable(model):
            # enable sorting through a proxy model
            sort_model_ = models.ColorFriendlySortProxyModel(self)
            sort_model_.setDynamicSortFilter(True)
            sort_model_.setSourceModel(model)
            return sort_model_

        # weapon vertical toolbar
        def _make_vertical_tb():
            vtb = widgets.VerticalToolBar(self)
            vtb.addStretch()
            vtb.addButton(QtGui.QIcon(get_icon_path('buy', (16, 16))),
                          self.tr("Add modifier"), self.modifiers_sink.add_new_modifier)
            vtb.addButton(QtGui.QIcon(get_icon_path('edit', (16, 16))),
                          self.tr("Edit modifier"), self.modifiers_sink.edit_selected_modifier)
            vtb.addButton(QtGui.QIcon(get_icon_path('minus', (16, 16))),
                          self.tr("Remove modifier"), self.modifiers_sink.remove_selected_modifier)

            vtb.addStretch()
            return vtb

        vtb = _make_vertical_tb()

        models_ = [
            (self.tr("Modifiers"), 'table', _make_sortable(self.mods_view_model), None, vtb, None)
        ]

        frame_, views_ = self._build_generic_page(models_)
        self.mod_view = views_[0]

        vtb .setProperty('source', self.mod_view)
        self.tabs.addTab(frame_, self.tr("Modifiers"))
