# -*- coding: utf-8 -*-
# Copyright (C) 2014-2026 Daniele Simonetti
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# Tab 2 — Skills and Mastery Abilities. Extracted from l5r/main.py
# during the Phase 4 split — no behaviour changes.

from qtpy import QtCore, QtGui

import l5r.api as api
import l5r.api.data
import l5r.api.data.skills
import l5r.dialogs as dialogs
import l5r.models as models
import l5r.widgets as widgets

from l5r.api.data import CMErrors
from l5r.ui.item_description import show_description_dialog
from l5r.util import log
from l5r.util.fsutil import get_icon_path


class SkillsSink(QtCore.QObject):
    """Qt slot for the Tab 2 skill table double-click handler."""

    def __init__(self, window):
        super().__init__(window)
        self.window = window

    def on_skill_item_activate(self, index):
        item = self.window.sk_sort_model.data(index, QtCore.Qt.UserRole)
        try:
            skill = api.data.skills.get(item)
        except Exception:
            log.ui.error("cannot retrieve information from skill model.", exc_info=1)
            return

        description = self.tr('<h3>Mastery Abilities:</h3>')
        for i in skill.mastery_abilities:
            description += '<B>{rank}</B>: {desc}<BR/>\n'.format(
                rank=i.rank, desc=i.desc)

        if skill.desc:
            description += self.tr('<h3>Description</h3>')
            description += skill.desc

        show_description_dialog(self.window, skill.name, skill.type, description)


class SkillsTabMixin:
    """Tab 2: skills table + mastery-abilities table with a vertical toolbar."""

    def build_ui_page_2(self):
        self.sk_view_model = models.SkillTableViewModel(self)
        self.ma_view_model = models.MaViewModel(self)

        # enable sorting through a proxy model
        self.sk_sort_model = models.ColorFriendlySortProxyModel(self)
        self.sk_sort_model.setDynamicSortFilter(True)
        self.sk_sort_model.setSourceModel(self.sk_view_model)

        # enable sorting through a proxy model
        self.ma_sort_model = models.ColorFriendlySortProxyModel(self)
        self.ma_sort_model.setDynamicSortFilter(True)
        self.ma_sort_model.setSourceModel(self.ma_view_model)

        # skills vertical toolbar
        vtb = widgets.VerticalToolBar(self)
        vtb.addStretch()
        vtb.addButton(QtGui.QIcon(get_icon_path('add', (16, 16))),
                      self.tr("Add skill rank"), self.on_buy_skill_rank)
        vtb.addButton(QtGui.QIcon(get_icon_path('buy', (16, 16))),
                      self.tr("Buy skill emphasys"), self.show_buy_emph_dlg)
        vtb.addButton(QtGui.QIcon(get_icon_path('buy', (16, 16))),
                      self.tr("Buy another skill"), self.show_buy_skill_dlg)
        vtb.addStretch()

        models_ = [
            (
                "Skills",
                'table',
                self.sk_sort_model,
                None,
                vtb,
                self.skills_sink.on_skill_item_activate
            ),
            (
                self.tr("Mastery Abilities"),
                'table',
                self.ma_sort_model,
                None,
                None,
                None
            )
        ]
        frame_, views_ = self._build_generic_page(models_)

        if len(views_) > 0:
            self.skill_table_view = views_[0]

        self.tabs.addTab(frame_, self.tr("Skills"))

    def on_buy_skill_rank(self):
        # get selected skill
        sm_ = self.skill_table_view.selectionModel()
        if sm_.hasSelection():
            model_ = self.skill_table_view.model()
            skill_id = model_.data(sm_.currentIndex(), QtCore.Qt.UserRole)

            err_ = self.buy_next_skill_rank(skill_id)
            if err_ != CMErrors.NO_ERROR:
                if err_ == CMErrors.NOT_ENOUGH_XP:
                    self.not_enough_xp_advise(self)
                elif err_ == CMErrors.MISSING_ORIGIN:
                    self.missing_origin_advise(self)
                return

            idx = None
            for i in range(0, self.skill_table_view.model().rowCount()):
                idx = self.skill_table_view.model().index(i, 0)
                if model_.data(idx, QtCore.Qt.UserRole) == skill_id:
                    break
            if idx.isValid():
                sm_.setCurrentIndex(idx, (QtCore.QItemSelectionModel.Select |
                                          QtCore.QItemSelectionModel.Rows))

    def show_buy_skill_dlg(self):
        dlg = dialogs.BuyAdvDialog(self.pc, 'skill', self)
        dlg.exec_()
        self.update_from_model()

    def show_buy_emph_dlg(self):
        # get selected skill
        sm_ = self.skill_table_view.selectionModel()
        if sm_.hasSelection():
            model_ = self.skill_table_view.model()
            skill_id = model_.data(sm_.currentIndex(), QtCore.Qt.UserRole)

            dlg = dialogs.BuyAdvDialog(self.pc, 'emph', self)
            dlg.fix_skill_id(skill_id)
            dlg.exec_()
            self.update_from_model()
