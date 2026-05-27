# -*- coding: utf-8 -*-
# Copyright (C) 2014-2026 Daniele Simonetti
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# Tab 6 — Advancements history table. Extracted from l5r/main.py during
# the Phase 4 split — no behaviour changes.

from qtpy import QtWidgets

import l5r.models


class AdvancementsTabMixin:
    """Tab 6: rank-advancement history with a Refund button."""

    def build_ui_page_6(self):
        mfr = QtWidgets.QFrame(self)
        vbox = QtWidgets.QVBoxLayout(mfr)

        fr_ = QtWidgets.QFrame(self)
        fr_h = QtWidgets.QHBoxLayout(fr_)
        fr_h.setContentsMargins(0, 0, 0, 0)
        fr_h.addWidget(
            QtWidgets.QLabel(self.tr("""<p><i>Select the advancement to refund and hit the button</i></p>"""), self))
        bt_refund_adv = QtWidgets.QPushButton(self.tr("Refund"), self)
        bt_refund_adv.setSizePolicy(QtWidgets.QSizePolicy.Maximum,
                                    QtWidgets.QSizePolicy.Preferred)
        bt_refund_adv.clicked.connect(self.sink1.refund_advancement)
        fr_h.addWidget(bt_refund_adv)
        vbox.addWidget(fr_)

        self.adv_view_model = l5r.models.AdvancementViewModel(self)
        view = QtWidgets.QTableView(self)
        view.setSortingEnabled(False)
        view.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.Interactive)
        view.horizontalHeader().setStretchLastSection(True)
        view.horizontalHeader().setCascadingSectionResizes(True)

        self.table_views.append(view)
        view.setModel(self.adv_view_model)
        vbox.addWidget(view)

        self.adv_view = view

        self.tabs.addTab(mfr, self.tr("Advancements"))
