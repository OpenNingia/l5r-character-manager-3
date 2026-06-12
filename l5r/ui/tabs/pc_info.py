# -*- coding: utf-8 -*-
# Copyright (C) 2014-2026 Daniele Simonetti
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# Tab 1 — Personal info / rings & attributes / flags / void / wounds /
# initiative / armor TN. Largest of the tab mixins. Extracted from
# l5r/main.py during the Phase 4 split — no behaviour changes.

from qtpy import QtCore, QtGui, QtWidgets

import l5r.api as api
import l5r.api.character
import l5r.api.data
import l5r.api.data.clans
import l5r.api.data.families
import l5r.api.data.schools
import l5r.api.rules
import l5r.models as models
import l5r.widgets as widgets

from l5r.api.data import CMErrors
from l5r.ui.helpers import new_horiz_line, new_small_le, new_small_plus_bt
from l5r.util import log, names
from l5r.util.fsutil import get_app_file, get_icon_path


class PcInfoSink(QtCore.QObject):
    """Qt slots for Tab 1 widgets (name generator, family/school edit
    buttons, experience-limit edit)."""

    def __init__(self, window):
        super().__init__(window)
        self.window = window

    def generate_name(self):
        """generate a random name for the character"""
        window = self.window

        gender = self.sender().property('gender')
        if gender == 'male':
            name = names.get_random_name(get_app_file('male.txt'))
        else:
            name = names.get_random_name(get_app_file('female.txt'))
        window.pc.name = name
        window.update_from_model()

    def on_set_exp_limit(self):
        window = self.window

        val, ok = QtWidgets.QInputDialog.getInt(window, 'Set Experience Limit',
                                                "XP Limit:", window.pc.exp_limit,
                                                0, 10000, 1)
        if ok:
            window.set_exp_limit(val)

    def on_add_exp_points(self):
        window = self.window

        val, ok = QtWidgets.QInputDialog.getInt(window, 'Add Experience Points',
                                                "XP awarded:", 1,
                                                1, 10000, 1)
        if ok:
            window.set_exp_limit(window.pc.exp_limit + val)

    def on_edit_family(self):
        window = self.window
        dlg = widgets.FamilyChooserDialog(window)
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            window.update_from_model()

    def on_edit_first_school(self):
        window = self.window
        dlg = widgets.FirstSchoolChooserDialog(window)
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            window.update_from_model()


class PcInfoTabMixin:
    """Tab 1: identity (name, clan, family, school), rings/attributes,
    honor/glory/status/taint/infamy flags, void points, initiative,
    armor TN, wounds."""

    def build_ui_page_1(self):

        mfr = QtWidgets.QFrame(self)
        self.tabs.addTab(mfr, self.tr("Character"))

        mvbox = QtWidgets.QVBoxLayout(mfr)
        mvbox.setContentsMargins(0, 0, 0, 0)

        def add_pc_info(row, col):
            fr_pc_info = QtWidgets.QFrame(self)
            fr_pc_info.setSizePolicy(QtWidgets.QSizePolicy.Preferred,
                                     QtWidgets.QSizePolicy.Maximum)

            grid = QtWidgets.QGridLayout(fr_pc_info)
            self.tx_pc_name = QtWidgets.QLineEdit(self)
            self.tx_pc_rank = QtWidgets.QLineEdit(self)
            self.lb_pc_clan = QtWidgets.QLabel(self)
            self.lb_pc_family = QtWidgets.QLabel(self)
            self.lb_pc_school = QtWidgets.QLabel(self)
            self.tx_pc_exp = QtWidgets.QLineEdit(self)
            self.tx_pc_ins = QtWidgets.QLineEdit(self)

            # School
            fr_school = QtWidgets.QFrame(self)
            hb_school = QtWidgets.QHBoxLayout(fr_school)
            hb_school.setContentsMargins(0, 0, 0, 0)

            bt_edit_school = QtWidgets.QToolButton(self)
            bt_edit_school.setToolTip(self.tr("Edit character first school"))
            bt_edit_school.setAutoRaise(True)
            bt_edit_school.setIcon(QtGui.QIcon(get_icon_path('edit', (16, 16))))

            hb_school.addWidget(QtWidgets.QLabel(self.tr("School"), self))
            hb_school.addWidget(bt_edit_school)

            # Family
            bt_edit_family = QtWidgets.QToolButton(self)
            bt_edit_family.setToolTip(self.tr("Edit character family and clan"))
            bt_edit_family.setAutoRaise(True)
            bt_edit_family.setIcon(QtGui.QIcon(get_icon_path('edit', (16, 16))))

            fr_family = QtWidgets.QFrame(self)
            hb_family = QtWidgets.QHBoxLayout(fr_family)
            hb_family.setContentsMargins(0, 0, 0, 0)
            hb_family.addWidget(QtWidgets.QLabel(self.tr("Family")))
            hb_family.addWidget(bt_edit_family)

            # Place "generate random name" near the Name label
            lb_name = QtWidgets.QLabel(self.tr("Name"), self)
            bt_generate_male = QtWidgets.QToolButton(self)
            bt_generate_male.setIcon(
                QtGui.QIcon(get_icon_path('male', (16, 16))))
            bt_generate_female = QtWidgets.QToolButton(self)
            bt_generate_female.setIcon(
                QtGui.QIcon(get_icon_path('female', (16, 16))))
            bt_generate_male  .setAutoRaise(True)
            bt_generate_male  .setToolTip(self.tr("Random male name"))
            bt_generate_female.setAutoRaise(True)
            bt_generate_female.setToolTip(self.tr("Random female name"))
            hb_name = QtWidgets.QHBoxLayout()
            hb_name.addWidget(lb_name)
            hb_name.addWidget(bt_generate_male)
            hb_name.addWidget(bt_generate_female)

            # gender tag, connect signals
            bt_generate_male  .setProperty('gender', 'male')
            bt_generate_female.setProperty('gender', 'female')
            bt_generate_male  .clicked.connect(self.pc_info_sink.generate_name)
            bt_generate_female.clicked.connect(self.pc_info_sink.generate_name)

            grid.addLayout(hb_name, 0, 0)
            grid.addWidget(QtWidgets.QLabel(self.tr("Clan"), self), 1, 0)
            grid.addWidget(fr_family, 2, 0)
            grid.addWidget(fr_school, 3, 0)

            self.bt_edit_family = bt_edit_family
            self.bt_edit_school = bt_edit_school

            # 3rd column
            fr_exp = QtWidgets.QFrame(self)
            hb_exp = QtWidgets.QHBoxLayout(fr_exp)
            hb_exp.setContentsMargins(0, 0, 0, 0)
            lb_exp = QtWidgets.QLabel(self.tr("Exp. Points"), self)
            bt_exp = QtWidgets.QToolButton(self)
            bt_exp.setToolTip(self.tr("Edit experience points"))
            bt_exp.setAutoRaise(True)
            bt_exp.setIcon(QtGui.QIcon(get_icon_path('edit', (16, 16))))
            bt_add_exp = QtWidgets.QToolButton(self)
            bt_add_exp.setToolTip(self.tr("Add experience points"))
            bt_add_exp.setAutoRaise(True)
            bt_add_exp.setIcon(QtGui.QIcon(get_icon_path('add', (16, 16))))
            hb_exp.addWidget(lb_exp)
            hb_exp.addWidget(bt_exp)
            hb_exp.addWidget(bt_add_exp)

            grid.addWidget(QtWidgets.QLabel(self.tr("Rank"), self), 0, 3)
            grid.addWidget(fr_exp, 1, 3)
            grid.addWidget(QtWidgets.QLabel(self.tr("Insight"), self), 2, 3)

            self.bt_set_exp_points = bt_exp
            self.bt_add_exp_points = bt_add_exp

            # 2nd column
            grid.addWidget(self.tx_pc_name, 0, 1, 1, 2)
            grid.addWidget(self.lb_pc_clan, 1, 1, 1, 2)
            grid.addWidget(self.lb_pc_family, 2, 1, 1, 2)
            grid.addWidget(self.lb_pc_school, 3, 1, 1, 2)

            # 4th column
            grid.addWidget(self.tx_pc_rank, 0, 4, 1, 2)
            grid.addWidget(self.tx_pc_exp, 1, 4, 1, 2)
            grid.addWidget(self.tx_pc_ins, 2, 4, 1, 2)

            self.tx_pc_rank.setReadOnly(True)
            self.tx_pc_exp.setReadOnly(True)
            self.tx_pc_ins.setReadOnly(True)

            fr_pc_info.setLayout(grid)
            mvbox.addWidget(fr_pc_info)

        def build_trait_frame():
            fr = QtWidgets.QFrame(self)
            fr.setSizePolicy(QtWidgets.QSizePolicy.Preferred,
                             QtWidgets.QSizePolicy.Maximum)
            hbox = QtWidgets.QHBoxLayout(fr)
            grp = QtWidgets.QGroupBox(self.tr("Rings and Attributes"), self)
            grid = QtWidgets.QGridLayout(grp)
            grid.setSpacing(1)

            # rings
            rings = [(self.tr("Earth"), new_small_le(self)), (self.tr("Air"), new_small_le(self)),
                     (self.tr("Water"), new_small_le(self)), (self.tr("Fire"), new_small_le(self)),
                     (self.tr("Void"), new_small_le(self))]

            # keep reference to the rings
            self.rings = rings

            for i in range(0, 4):
                grid.addWidget(QtWidgets.QLabel(rings[i][0]), i, 0)
                grid.addWidget(rings[i][1], i, 1)

            # void ring with plus button
            void_fr = QtWidgets.QFrame(self)
            void_hbox = QtWidgets.QHBoxLayout(void_fr)
            void_hbox.setContentsMargins(0, 0, 0, 0)
            void_bt = new_small_plus_bt(self)
            void_hbox.addWidget(rings[4][1])
            void_hbox.addWidget(void_bt)
            void_bt.clicked.connect(self.on_void_increase)
            grid.addWidget(QtWidgets.QLabel(rings[4][0]), 4, 0)
            grid.addWidget(void_fr, 4, 1)

            attribs = []
            # Earth ring
            attribs.append((self.tr("Stamina"), new_small_le(self)))
            attribs.append((self.tr("Willpower"), new_small_le(self)))
            attribs[0][1].setProperty('attrib_id', models.ATTRIBS.STAMINA)
            attribs[1][1].setProperty('attrib_id', models.ATTRIBS.WILLPOWER)
            # Air ring
            attribs.append((self.tr("Reflexes"), new_small_le(self)))
            attribs.append((self.tr("Awareness"), new_small_le(self)))
            attribs[2][1].setProperty('attrib_id', models.ATTRIBS.REFLEXES)
            attribs[3][1].setProperty('attrib_id', models.ATTRIBS.AWARENESS)
            # Water ring
            attribs.append((self.tr("Strength"), new_small_le(self)))
            attribs.append((self.tr("Perception"), new_small_le(self)))
            attribs[4][1].setProperty('attrib_id', models.ATTRIBS.STRENGTH)
            attribs[5][1].setProperty('attrib_id', models.ATTRIBS.PERCEPTION)
            # Fire ring
            attribs.append((self.tr("Agility"), new_small_le(self)))
            attribs.append((self.tr("Intelligence"), new_small_le(self)))
            attribs[6][1].setProperty('attrib_id', models.ATTRIBS.AGILITY)
            attribs[7][1].setProperty('attrib_id', models.ATTRIBS.INTELLIGENCE)

            self.attribs = attribs

            # map increase trait signals
            self.trait_sig_mapper = QtCore.QSignalMapper(self)

            def _attrib_frame(i):
                fr = QtWidgets.QFrame(self)
                hbox = QtWidgets.QHBoxLayout(fr)
                hbox.setContentsMargins(3, 0, 9, 0)
                # small plus button
                tag = str(attribs[i][1].property('attrib_id'))
                bt = new_small_plus_bt(self)
                hbox.addWidget(attribs[i][1])
                hbox.addWidget(bt)
                self.trait_sig_mapper.setMapping(bt, tag)
                bt.clicked.connect(self.trait_sig_mapper.map)
                return fr

            for i in range(0, 8, 2):
                grid.addWidget(QtWidgets.QLabel(attribs[i][0]),
                               (i // 2), 2, 1, 1, QtCore.Qt.AlignLeft)
                grid.addWidget(_attrib_frame(i), (i // 2), 3, 1, 1,
                               QtCore.Qt.AlignLeft)

                grid.addWidget(QtWidgets.QLabel(attribs[i + 1][0]),
                               (i // 2), 4, 1, 1, QtCore.Qt.AlignLeft)
                grid.addWidget(_attrib_frame(i + 1), (i // 2), 5, 1, 1,
                               QtCore.Qt.AlignLeft)
            grid.addWidget(QtWidgets.QLabel(self.tr("<b>Void Points</b>")),
                           4, 2, 1, 3,
                           QtCore.Qt.AlignHCenter)

            self.void_points = widgets.CkNumWidget(count=10, parent=self)
            grid.addWidget(self.void_points, 5, 2, 1, 3,
                           QtCore.Qt.AlignHCenter)

            hbox.addWidget(grp)

            return fr

        def build_flags_frame():
            tx_flags = [self.tr("Honor"), self.tr("Glory"),
                        self.tr("Status"), self.tr("Shadowland Taint"),
                        self.tr("Infamy")]

            ob_flags_p = []
            ob_flags_r = []
            fr = QtWidgets.QFrame(self)
            vbox = QtWidgets.QVBoxLayout(fr)
            vbox.setContentsMargins(0, 0, 0, 0)
            vbox.setSpacing(0)
            row = 1
            for f in tx_flags:
                fr_ = QtWidgets.QFrame(self)
                lay = QtWidgets.QGridLayout(fr_)
                lay.setContentsMargins(0, 0, 0, 0)
                lay.setSpacing(0)
                lay.addWidget(QtWidgets.QLabel('<b>%s</b>' % f), row, 0)
                l = new_small_le(self, False)
                lay.addWidget(l, row, 1)
                w = widgets.CkNumWidget(count=9, parent=self)
                lay.addWidget(w, row + 1, 0, 1, 2, QtCore.Qt.AlignHCenter)
                ob_flags_p.append(w)
                ob_flags_r.append(l)
                vbox.addWidget(fr_)
            self.pc_flags_points = ob_flags_p
            self.pc_flags_rank = ob_flags_r

            return fr

        def add_traits_and_flags():
            trait_frame = build_trait_frame()
            flags_frame = build_flags_frame()

            fr = QtWidgets.QFrame(self)
            hbox = QtWidgets.QHBoxLayout(fr)

            fr.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                             QtWidgets.QSizePolicy.Maximum)

            hbox.addWidget(trait_frame)
            hbox.addWidget(flags_frame)

            mvbox.addWidget(fr)

        def add_pc_quantities(row, col):
            fr = QtWidgets.QFrame(self)
            fr.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                             QtWidgets.QSizePolicy.Maximum)
            hbox = QtWidgets.QHBoxLayout(fr)

            monos_ = QtGui.QFont('Monospace')
            monos_.setStyleHint(QtGui.QFont.Courier)

            # initiative
            grp = QtWidgets.QGroupBox(self.tr("Initiative"), self)

            grd = QtWidgets.QFormLayout(grp)

            self.tx_base_init = QtWidgets.QLineEdit(self)
            self.tx_mod_init = QtWidgets.QLineEdit(self)
            self.tx_cur_init = QtWidgets.QLineEdit(self)

            self.tx_base_init.setReadOnly(True)
            self.tx_mod_init .setReadOnly(True)
            self.tx_cur_init .setReadOnly(True)

            grd.addRow(self.tr("Base"), self.tx_base_init)
            grd.addRow(self.tr("Modifier"), self.tx_mod_init)
            grd.addRow(self.tr("Current"), self.tx_cur_init)

            hbox.addWidget(grp, 1)

            # Armor TN
            grp = QtWidgets.QGroupBox(self.tr("Armor TN"), self)

            grd = QtWidgets.QFormLayout(grp)

            self.tx_armor_nm = QtWidgets.QLineEdit(self)
            self.tx_base_tn = QtWidgets.QLineEdit(self)
            self.tx_armor_tn = QtWidgets.QLineEdit(self)
            self.tx_armor_rd = QtWidgets.QLineEdit(self)
            self.tx_cur_tn = QtWidgets.QLineEdit(self)

            self.tx_armor_nm.setReadOnly(True)
            self.tx_base_tn .setReadOnly(True)
            self.tx_armor_tn.setReadOnly(True)
            self.tx_armor_rd.setReadOnly(True)
            self.tx_cur_tn  .setReadOnly(True)

            grd.addRow(self.tr("Name"), self.tx_armor_nm)
            grd.addRow(self.tr("Base"), self.tx_base_tn)
            grd.addRow(self.tr("Armor"), self.tx_armor_tn)
            grd.addRow(self.tr("Reduction"), self.tx_armor_rd)
            grd.addRow(self.tr("Current"), self.tx_cur_tn)

            hbox.addWidget(grp, 1)

            # Wounds
            grp = QtWidgets.QGroupBox(self.tr("Wounds"), self)

            grd = QtWidgets.QGridLayout(grp)

            wnd = [(QtWidgets.QLabel(self), new_small_le(self), new_small_le(self)),
                   (QtWidgets.QLabel(self), new_small_le(self), new_small_le(self)),
                   (QtWidgets.QLabel(self), new_small_le(self), new_small_le(self)),
                   (QtWidgets.QLabel(self), new_small_le(self), new_small_le(self)),
                   (QtWidgets.QLabel(self), new_small_le(self), new_small_le(self)),
                   (QtWidgets.QLabel(self), new_small_le(self), new_small_le(self)),
                   (QtWidgets.QLabel(self), new_small_le(self), new_small_le(self)),

                   (QtWidgets.QLabel(self.tr("Out"), self),
                                                                                  new_small_le(self),
                                                                                  new_small_le(self))]

            self.wounds = wnd
            self.wnd_lb = grp

            row_ = 0
            col_ = 0
            for i in range(0, len(wnd)):
                if i == 4:
                    col_ = 3
                    row_ = 0

                grd.addWidget(wnd[i][0], row_, col_)
                grd.addWidget(wnd[i][0], row_, col_)
                grd.addWidget(wnd[i][1], row_, col_ + 1)
                grd.addWidget(wnd[i][2], row_, col_ + 2)
                row_ += 1

            hbox.addWidget(grp, 2)

            mvbox.addWidget(fr)

        add_pc_info(0, 0)
        mvbox.addWidget(new_horiz_line(self))
        add_traits_and_flags()
        mvbox.addWidget(new_horiz_line(self))
        add_pc_quantities(4, 0)

    # --- signal handlers --------------------------------------------------

    def on_trait_increase(self, tag):
        """raised when user click on the small '+' button near traits"""

        trait_ = api.data.get_trait_by_index(int(tag))
        if not trait_:
            log.ui.error(u"trait not found by index: %s", tag)
            return

        if self.increase_trait(int(tag)) == CMErrors.NOT_ENOUGH_XP:
            self.not_enough_xp_advise(self)

    def on_void_increase(self):
        """raised when user click on the small '+' button near void ring"""
        if self.increase_void() == CMErrors.NOT_ENOUGH_XP:
            self.not_enough_xp_advise(self)

    def on_pc_name_change(self):
        self.pc.name = self.tx_pc_name.text()

    def on_pers_info_change(self):
        w = self.sender()
        if hasattr(w, 'link'):
            self.pc.set_property(w.link, w.text())

    # Honor/Glory/Status/Taint/Infamy are tracked in 0.1 increments. The
    # API setter for each flag, keyed by its index in the flag widget lists.
    _flag_setters = (
        api.character.set_honor,
        api.character.set_glory,
        api.character.set_status,
        api.character.set_taint,
        api.character.set_infamy,
    )

    def _flag_value(self, idx):
        """Combine the free-text rank field and the 0.1-step points widget
        for flag *idx* into a single float.

        The rank field is plain text, so tolerate a decimal entry such as
        ``"2.5"`` instead of crashing on ``int(...)`` (issue #380). When the
        user types a fractional value directly, it is authoritative and the
        points widget is ignored; otherwise the two are combined."""
        try:
            rank = float(self.pc_flags_rank[idx].text())
        except (ValueError, TypeError):
            rank = 0.0
        if rank != int(rank):
            return rank
        points = self.pc_flags_points[idx].value
        return rank + float(points) / 10

    def on_flag_points_change(self):
        fl = self.sender()
        idx = self.pc_flags_points.index(fl)
        self._flag_setters[idx](self._flag_value(idx))

    def on_flag_rank_change(self):
        fl = self.sender()
        idx = self.pc_flags_rank.index(fl)
        self._flag_setters[idx](self._flag_value(idx))

    def on_void_points_change(self):
        val = self.void_points.value
        self.pc.set_void_points(val)

    # --- field setters used by update_from_model --------------------------

    def set_clan(self, clan_id):
        """Set UI clan"""

        clan_ = api.data.clans.get(clan_id)
        if clan_:
            self.lb_pc_clan.setText(clan_.name)
        else:
            self.lb_pc_clan.setText(self.tr("No Clan"))

    def set_family(self, family_id):
        """Set UI family"""
        family_ = api.data.families.get(family_id)
        if family_:
            self.lb_pc_family.setText(family_.name)
        else:
            self.lb_pc_family.setText(self.tr("No Family"))

    def set_school(self, school_id):
        """Set UI school"""
        school_ = api.data.schools.get(school_id)
        if school_:
            self.lb_pc_school.setText(school_.name)
        else:
            self.lb_pc_school.setText(self.tr("No School"))

    def set_void_points(self, value):
        if self.void_points.value == value:
            return
        self.void_points.set_value(value)

    def set_flag(self, flag, value):
        rank, points = api.rules.split_decimal(value)
        # set rank
        self.pc_flags_rank[flag].setText(str(rank))
        # set points
        self.pc_flags_points[flag].set_value(int(points * 10))

    def set_honor(self, value):
        self.set_flag(0, value)

    def set_glory(self, value):
        self.set_flag(1, value)

    def set_status(self, value):
        self.set_flag(2, value)

    def set_taint(self, value):
        self.set_flag(3, value)

    def set_infamy(self, value):
        self.set_flag(4, value)
