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

from qtpy import QtGui

import l5r.models as models
import l5r.widgets as widgets

from l5r.util.fsutil import get_icon_path


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
                          self.tr("Add modifier"), self.sink4.add_new_modifier)
            vtb.addButton(QtGui.QIcon(get_icon_path('edit', (16, 16))),
                          self.tr("Edit modifier"), self.sink4.edit_selected_modifier)
            vtb.addButton(QtGui.QIcon(get_icon_path('minus', (16, 16))),
                          self.tr("Remove modifier"), self.sink4.remove_selected_modifier)

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
