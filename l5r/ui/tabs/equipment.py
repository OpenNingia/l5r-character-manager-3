# -*- coding: utf-8 -*-
# Copyright (C) 2014-2026 Daniele Simonetti
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# Tab 10 — Equipment list + money widget. Extracted from l5r/main.py
# during the Phase 4 split — no behaviour changes.

from qtpy import QtCore, QtGui

import l5r.api as api
import l5r.api.character
import l5r.models as models
import l5r.widgets as widgets

from l5r.ui.helpers import new_horiz_line
from l5r.util import log
from l5r.util.fsutil import get_icon_path


class EquipmentSink(QtCore.QObject):
    """Qt slots for the Tab 10 equipment list + money widget."""

    def __init__(self, window):
        super().__init__(window)
        self.window = window

    def add_equipment(self):
        window = self.window
        equip_list = window.pc.get_property('equip', [])
        equip_list.append(self.tr('Doubleclick to edit'))
        window.update_from_model()

    def remove_selected_equipment(self):
        window = self.window
        try:
            index = window.equip_view.selectionModel().currentIndex()
            if not index.isValid():
                return

            indexRow = index.row()
            newIndexRow = max(0, index.row() - 1)
            newIndexCol = index.column()
            newIndexParent = index.parent()
            itemModel = index.model()

            start_outfit = api.character.get_starting_outfit() or []
            equip_list = window.pc.get_property('equip') or []

            if indexRow < len(start_outfit):
                # delete from starting outfit
                del start_outfit[indexRow]
                api.character.set_starting_outfit(start_outfit)
            else:
                indexRow -= len(start_outfit)
                if indexRow < len(equip_list):
                    del equip_list[indexRow]

            window.update_from_model()

            sibling = itemModel.index(newIndexRow, newIndexCol, newIndexParent)
            if sibling.isValid():
                window.equip_view.selectionModel().setCurrentIndex(
                    sibling, QtCore.QItemSelectionModel.SelectCurrent)
        except Exception:
            log.ui.error("Shit happens", exc_info=1, stack_info=True)

    def on_money_value_changed(self, value):
        api.character.set_money(value)


class EquipmentTabMixin:
    """Tab 10: equipment list view + money widget."""

    def build_ui_page_10(self):
        self.equip_view_model = models.EquipmentListModel(self)
        # self.equip_view_model.user_change.connect(self.update_from_model)

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
                          self.tr("Add equipment"), self.equipment_sink.add_equipment)
            vtb.addButton(QtGui.QIcon(get_icon_path('minus', (16, 16))),
                          self.tr("Remove equipment"), self.equipment_sink.remove_selected_equipment)

            vtb.addStretch()
            return vtb

        vtb = _make_vertical_tb()

        models_ = [
            (self.tr("Equipment"), 'list', _make_sortable(self.equip_view_model), None, vtb, None)
        ]

        frame_, views_ = self._build_generic_page(models_)
        self.equip_view = views_[0]

        font = self.equip_view.font()
        font.setPointSize(11)
        self.equip_view.setFont(font)

        self.money_widget = widgets.MoneyWidget(self)
        frame_.layout().setSpacing(12)
        frame_.layout().addWidget(new_horiz_line(self))
        frame_.layout().addWidget(self.money_widget)
        self.money_widget.valueChanged.connect(
            self.equipment_sink.on_money_value_changed)

        vtb .setProperty('source', self.equip_view)
        self.tabs.addTab(frame_, self.tr("Equipment"))
