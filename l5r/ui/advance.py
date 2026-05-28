# -*- coding: utf-8 -*-
# Copyright (C) 2014-2026 Daniele Simonetti
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# Rank-advancement nicebar checks and the dialog launchers they trigger
# (rank-up, school spell grant, free kiho, wildcard skill choice,
# affinity / deficiency choice, skill / emphasis purchase).
# Extracted from l5r/main.py during the Phase 4 split — no behaviour
# changes. Expects self.nicebar, self.pc, self.skill_table_view, and
# self.show_nicebar / self.update_from_model from other mixins.

from qtpy import QtCore, QtWidgets

import l5r.api as api
import l5r.api.character
import l5r.api.character.rankadv
import l5r.api.data
import l5r.dialogs as dialogs

from l5r.util import log


class AdvanceMixin:
    """Rank-up checks and dialog launchers."""

    def act_choose_skills(self):
        dlg = dialogs.SelWcSkills(self.pc, self)
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            api.character.rankadv.clear_skills_to_choose()
            self.update_from_model()

    def check_rank_advancement(self):
        if self.nicebar:
            return

        potential_insight_rank_ = api.character.insight_rank()
        actual_insight_rank_ = api.character.insight_rank(strict=True)

        log.rules.debug(u"check rank advancement. potential rank: %d, actual rank: %d",
                        potential_insight_rank_, actual_insight_rank_)

        if potential_insight_rank_ > actual_insight_rank_:
            # HEY, NEW RANK DUDE!
            lb = QtWidgets.QLabel(self.tr("You reached the next rank, you have an opportunity"
                                          " to decide your destiny."), self)
            bt = QtWidgets.QPushButton(self.tr("Advance rank"), self)
            bt.setSizePolicy(QtWidgets.QSizePolicy.Maximum,
                             QtWidgets.QSizePolicy.Preferred)
            bt.clicked.connect(self.show_advance_rank_dlg)
            self.show_nicebar([lb, bt])

    def check_school_new_spells(self):
        if self.nicebar:
            return

        # Show nicebar if can get other spells
        if api.character.rankadv.has_granted_free_spells():
            lb = QtWidgets.QLabel(
                self.tr("You now fit the requirements to learn other Spells"), self)
            bt = QtWidgets.QPushButton(self.tr("Learn Spells"), self)
            bt.setSizePolicy(QtWidgets.QSizePolicy.Maximum,
                             QtWidgets.QSizePolicy.Preferred)
            bt.clicked.connect(self.learn_next_school_spells)
            self.show_nicebar([lb, bt])

    def check_free_kihos(self):
        if self.nicebar:
            return

        # Show nicebar if can get free kihos
        if api.character.rankadv.get_gained_kiho_count() > 0:
            lb = QtWidgets.QLabel(
                self.tr("You can learn {0} kihos for free").format(api.character.rankadv.get_gained_kiho_count()), self)
            bt = QtWidgets.QPushButton(self.tr("Learn Kihos"), self)
            bt.setSizePolicy(QtWidgets.QSizePolicy.Maximum,
                             QtWidgets.QSizePolicy.Preferred)
            bt.clicked.connect(self.learn_next_free_kiho)
            self.show_nicebar([lb, bt])

    def check_new_skills(self):
        if self.nicebar:
            return

        # Show nicebar if pending wildcard skills
        if api.character.rankadv.has_granted_skills_to_choose():
            lb = QtWidgets.QLabel(
                self.tr("Your school gives you the choice of certain skills"), self)
            bt = QtWidgets.QPushButton(self.tr("Choose Skills"), self)
            bt.setSizePolicy(QtWidgets.QSizePolicy.Maximum,
                             QtWidgets.QSizePolicy.Preferred)
            bt.clicked.connect(self.act_choose_skills)
            self.show_nicebar([lb, bt])

    def check_affinity_wc(self):
        if self.nicebar:
            return

        rank_ = api.character.rankadv.get_last()
        if not rank_:
            return

        log.app.info(u"check if the player can choose his affinity/deficiency: [%s] / [%s] ",
                     u", ".join(rank_.affinities_to_choose),
                     u", ".join(rank_.deficiencies_to_choose))

        if api.character.rankadv.has_granted_affinities_to_choose():
            lb = QtWidgets.QLabel(
                self.tr("You school grant you to choose an elemental affinity."), self)
            bt = QtWidgets.QPushButton(self.tr("Choose Affinity"), self)
            bt.setSizePolicy(QtWidgets.QSizePolicy.Maximum,
                             QtWidgets.QSizePolicy.Preferred)
            bt.clicked.connect(self.show_select_affinity)
            self.show_nicebar([lb, bt])
        elif api.character.rankadv.has_granted_deficiencies_to_choose():
            lb = QtWidgets.QLabel(
                self.tr("You school grant you to choose an elemental deficiency."), self)
            bt = QtWidgets.QPushButton(self.tr("Choose Deficiency"), self)
            bt.setSizePolicy(QtWidgets.QSizePolicy.Maximum,
                             QtWidgets.QSizePolicy.Preferred)
            bt.clicked.connect(self.show_select_deficiency)
            self.show_nicebar([lb, bt])

    def learn_next_school_spells(self):
        dlg = dialogs.SpellAdvDialog(self.pc, 'bounded', self)
        dlg.setWindowTitle(self.tr('Choose School Spells'))
        dlg.set_header_text(self.tr("<center><h2>Your school has granted you \
                                     the right to choose some spells.</h2> \
                                     <h3><i>Choose with care.</i></h3></center>"))
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            api.character.rankadv.clear_spells_to_choose()
            self.update_from_model()

    def learn_next_free_kiho(self):
        dlg = dialogs.KihoDialog(self.pc, self)
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            self.update_from_model()

    def show_advance_rank_dlg(self):
        dlg = dialogs.NextRankDlg(self.pc, self)
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            self.update_from_model()

    def show_select_affinity(self):

        rank_ = api.character.rankadv.get_last()
        if not rank_:
            return

        to_choose = rank_.affinities_to_choose.pop()

        chooses = None
        if 'nonvoid' in to_choose:
            chooses = [api.data.get_ring(x).text for x in api.data.rings() if x != 'void']
        else:
            chooses = [api.data.get_ring(x).text for x in api.data.rings()]

        affinity, is_ok = QtWidgets.QInputDialog.getItem(self,
                                                        "L5R: CM",
                                                        self.tr(
                                                            "Select your elemental affinity"),
                                                        chooses, 0, False)
        if is_ok:
            ring_ = [x for x in api.data.rings() if api.data.get_ring(x).text == affinity]
            if len(ring_):
                rank_.affinities.append(ring_[0])
        else:
            rank_.affinities_to_choose.append(to_choose)

        self.update_from_model()

    def show_select_deficiency(self):

        rank_ = api.character.rankadv.get_last()
        if not rank_:
            return

        to_choose = rank_.deficiencies_to_choose.pop()

        chooses = None
        if 'nonvoid' in to_choose:
            chooses = [api.data.get_ring(x).text for x in api.data.rings() if x != 'void']
        else:
            chooses = [api.data.get_ring(x).text for x in api.data.rings()]

        deficiency, is_ok = QtWidgets.QInputDialog.getItem(self,
                                                          "L5R: CM",
                                                          self.tr(
                                                              "Select your elemental deficiency"),
                                                          chooses, 0, False)

        if is_ok:
            ring_ = [x for x in api.data.rings() if api.data.get_ring(x).text == deficiency]
            if len(ring_):
                rank_.deficiencies.append(ring_[0])
        else:
            rank_.deficiencies.append(to_choose)

        self.update_from_model()
