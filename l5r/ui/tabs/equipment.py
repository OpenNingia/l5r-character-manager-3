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

from qtpy import QtGui

import l5r.models as models
import l5r.widgets as widgets

from l5r.ui.helpers import new_horiz_line
from l5r.util.fsutil import get_icon_path


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
                          self.tr("Add equipment"), self.sink4.add_equipment)
            vtb.addButton(QtGui.QIcon(get_icon_path('minus', (16, 16))),
                          self.tr("Remove equipment"), self.sink4.remove_selected_equipment)

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
            self.sink4.on_money_value_changed)

        vtb .setProperty('source', self.equip_view)
        self.tabs.addTab(frame_, self.tr("Equipment"))
