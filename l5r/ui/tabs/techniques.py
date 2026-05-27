# -*- coding: utf-8 -*-
# Copyright (C) 2014-2026 Daniele Simonetti
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# Tab 3 — Spells + Techs (Techniques). Extracted from l5r/main.py
# during the Phase 4 split — no behaviour changes.

from qtpy import QtCore, QtWidgets, QtGui

import l5r.dialogs as dialogs
import l5r.models as models
import l5r.widgets as widgets

from l5r.api.data import CMErrors
from l5r.util.fsutil import get_icon_path


class TechniquesTabMixin:
    """Tab 3: spell table (with affinity/deficiency) + tech table."""

    def build_ui_page_3(self):
        self.sp_view_model = models.SpellTableViewModel(self)
        self.th_view_model = models.TechViewModel(self)

        # enable sorting through a proxy model
        self.sp_sort_model = models.ColorFriendlySortProxyModel(self)
        self.sp_sort_model.setDynamicSortFilter(True)
        self.sp_sort_model.setSourceModel(self.sp_view_model)

        frame_ = QtWidgets.QFrame(self)
        vbox = QtWidgets.QVBoxLayout(frame_)

        self._build_spell_frame(self.sp_sort_model, vbox)
        self._build_tech_frame(self.th_view_model, vbox)

        self.tabs.addTab(frame_, self.tr("Techniques"))

    def _build_spell_frame(self, model, layout):
        grp = QtWidgets.QGroupBox(self.tr("Spells"), self)
        hbox = QtWidgets.QHBoxLayout(grp)

        fr_ = QtWidgets.QFrame(self)
        vbox = QtWidgets.QVBoxLayout(fr_)
        vbox.setContentsMargins(3, 3, 3, 3)

        # advantages/disadvantage vertical toolbar
        def _make_vertical_tb():
            vtb = widgets.VerticalToolBar(self)
            vtb.addStretch()

            cb_buy = self.act_buy_spell
            cb_remove = self.act_del_spell
            cb_memo = self.act_memo_spell

            self.add_spell_bt = vtb.addButton(
                QtGui.QIcon(get_icon_path('buy', (16, 16))),
                self.tr("Add new spell"), cb_buy)

            self.del_spell_bt = vtb.addButton(
                QtGui.QIcon(get_icon_path('minus', (16, 16))),
                self.tr("Remove spell"), cb_remove)

            self.memo_spell_bt = vtb.addButton(
                QtGui.QIcon(get_icon_path('book', (16, 16))),
                self.tr("Memorize/Forget spell"), cb_memo)

            self.del_spell_bt.setEnabled(False)

            vtb.addStretch()
            return vtb

        # View
        view = QtWidgets.QTableView(fr_)
        view.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                           QtWidgets.QSizePolicy.Expanding)
        view.setSortingEnabled(True)
        view.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Interactive)
        view.horizontalHeader().setStretchLastSection(True)
        view.horizontalHeader().setCascadingSectionResizes(True)
        view.setModel(model)
        self.table_views.append(view)
        sm = view.selectionModel()
        sm.currentRowChanged.connect(self.on_spell_selected)
        self.spell_table_view = view

        # Affinity/Deficiency
        self.lb_affin = QtWidgets.QLabel(self.tr("None"), self)
        self.lb_defic = QtWidgets.QLabel(self.tr("None"), self)

        aff_fr = QtWidgets.QFrame(self)
        aff_fr.setSizePolicy(QtWidgets.QSizePolicy.Preferred,
                             QtWidgets.QSizePolicy.Maximum)
        fl = QtWidgets.QFormLayout(aff_fr)
        fl.addRow(self.tr("<b><i>Affinity</i></b>"), self.lb_affin)
        fl.addRow(self.tr("<b><i>Deficiency</i></b>"), self.lb_defic)
        fl.setHorizontalSpacing(60)
        fl.setVerticalSpacing(5)
        fl.setContentsMargins(0, 0, 0, 0)

        vbox.addWidget(aff_fr)
        vbox.addWidget(view)

        hbox.addWidget(_make_vertical_tb())
        hbox.addWidget(fr_)
        layout.addWidget(grp)

        view.doubleClicked.connect(self.sink4.on_spell_item_activate)

        return view

    def _build_tech_frame(self, model, layout):
        grp = QtWidgets.QGroupBox(self.tr("Techs"), self)
        vbox = QtWidgets.QVBoxLayout(grp)

        # View
        view = QtWidgets.QTableView(self)
        view.setSortingEnabled(False)
        view.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.Interactive)
        view.horizontalHeader().setStretchLastSection(True)
        view.horizontalHeader().setCascadingSectionResizes(True)

        view.setModel(model)
        self.table_views.append(view)
        vbox.addWidget(view)
        layout.addWidget(grp)

        view.doubleClicked.connect(self.sink4.on_tech_item_activate)

        return view

    def act_memo_spell(self):
        # get selected spell
        sm_ = self.spell_table_view.selectionModel()
        if sm_.hasSelection():
            model_ = self.spell_table_view.model()
            spell_itm = model_.data(sm_.currentIndex(), QtCore.Qt.UserRole)

            err_ = CMErrors.NO_ERROR
            if spell_itm.memo:
                self.remove_advancement_item(spell_itm.adv)
            else:
                err_ = self.memo_spell(spell_itm.spell_id)

            if err_ != CMErrors.NO_ERROR:
                if err_ == CMErrors.NOT_ENOUGH_XP:
                    self.not_enough_xp_advise(self)
                return

            idx = None
            for i in range(0, self.spell_table_view.model().rowCount()):
                idx = self.spell_table_view.model().index(i, 0)
                if model_.data(idx, QtCore.Qt.UserRole).spell_id == spell_itm.spell_id:
                    break
            if idx.isValid():
                sm_.setCurrentIndex(idx, (QtCore.QItemSelectionModel.Select |
                                          QtCore.QItemSelectionModel.Rows))

    def act_buy_spell(self):
        dlg = dialogs.SpellAdvDialog(self.pc, 'freeform', self)
        dlg.setWindowTitle(self.tr('Add New Spell'))
        dlg.set_header_text(
            self.tr("<center><h2>Select the spell to learn</h2></center>"))
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            self.update_from_model()

    def act_del_spell(self):
        # get selected spell
        sm_ = self.spell_table_view.selectionModel()
        if sm_.hasSelection():
            model_ = self.spell_table_view.model()
            spell_itm = model_.data(sm_.currentIndex(), QtCore.Qt.UserRole)

            if spell_itm.memo:
                return
            self.remove_spell(spell_itm.spell_id)

    def on_spell_selected(self, current, previous):
        # get selected spell
        model_ = self.spell_table_view.model()
        spell_itm = model_.data(current, QtCore.Qt.UserRole)

        # toggle remove
        self.del_spell_bt.setEnabled(not spell_itm.memo)
