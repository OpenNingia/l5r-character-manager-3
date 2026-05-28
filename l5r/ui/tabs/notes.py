# -*- coding: utf-8 -*-
# Copyright (C) 2014-2026 Daniele Simonetti
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# Tab 9 — Notes editor and personal-information form. Extracted from
# l5r/main.py during the Phase 4 split — no behaviour changes.

from qtpy import QtWidgets

import l5r.widgets as widgets

from l5r.ui.helpers import new_vert_line


class NotesTabMixin:
    """Tab 9: rich-text notes + anagraphic / family form."""

    def build_ui_page_9(self):
        mfr = QtWidgets.QFrame(self)
        vbox = QtWidgets.QVBoxLayout(mfr)

        self.tx_pc_notes = widgets.SimpleRichEditor(self)
        vbox.addWidget(self.tx_pc_notes)

        def build_pers_info():
            grp = QtWidgets.QGroupBox(self.tr("Personal Informations"), self)
            grp.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                              QtWidgets.QSizePolicy.Preferred)

            hgrp = QtWidgets.QHBoxLayout(grp)

            # anagraphic

            afr = QtWidgets.QFrame(self)
            afl = QtWidgets.QFormLayout(afr)

            self.tx_pc_sex = QtWidgets.QLineEdit(self)
            self.tx_pc_age = QtWidgets.QLineEdit(self)
            self.tx_pc_height = QtWidgets.QLineEdit(self)
            self.tx_pc_weight = QtWidgets.QLineEdit(self)
            self.tx_pc_hair = QtWidgets.QLineEdit(self)
            self.tx_pc_eyes = QtWidgets.QLineEdit(self)

            afl.addRow(self.tr("Sex"), self.tx_pc_sex)
            afl.addRow(self.tr("Age"), self.tx_pc_age)
            afl.addRow(self.tr("Height"), self.tx_pc_height)
            afl.addRow(self.tr("Weight"), self.tx_pc_weight)
            afl.addRow(self.tr("Hair"), self.tx_pc_hair)
            afl.addRow(self.tr("Eyes"), self.tx_pc_eyes)
            hgrp.addWidget(afr)

            # separator
            hgrp.addWidget(new_vert_line())

            # parents
            bfr = QtWidgets.QFrame(self)
            bfl = QtWidgets.QFormLayout(bfr)

            self.tx_pc_father = QtWidgets.QLineEdit(self)
            self.tx_pc_mother = QtWidgets.QLineEdit(self)
            self.tx_pc_bro = QtWidgets.QLineEdit(self)
            self.tx_pc_sis = QtWidgets.QLineEdit(self)
            self.tx_pc_marsta = QtWidgets.QLineEdit(self)
            self.tx_pc_spouse = QtWidgets.QLineEdit(self)
            self.tx_pc_childr = QtWidgets.QLineEdit(self)

            bfl.addRow(self.tr("Father"), self.tx_pc_father)
            bfl.addRow(self.tr("Mother"), self.tx_pc_mother)
            bfl.addRow(self.tr("Brothers"), self.tx_pc_bro)
            bfl.addRow(self.tr("Sisters"), self.tx_pc_sis)
            bfl.addRow(self.tr("Marital Status"), self.tx_pc_marsta)
            bfl.addRow(self.tr("Spouse"), self.tx_pc_spouse)
            bfl.addRow(self.tr("Children"), self.tx_pc_childr)
            hgrp.addWidget(bfr)

            self.pers_info_widgets = [
                self.tx_pc_sex, self.tx_pc_age,
                self.tx_pc_height, self.tx_pc_weight,
                self.tx_pc_hair, self.tx_pc_eyes,
                self.tx_pc_father, self.tx_pc_mother,
                self.tx_pc_bro, self.tx_pc_marsta,
                self.tx_pc_sis, self.tx_pc_spouse, self.tx_pc_childr]

            # link personal information widgets
            self.tx_pc_sex.link = 'sex'
            self.tx_pc_age.link = 'age'
            self.tx_pc_height.link = 'height'
            self.tx_pc_weight.link = 'weight'
            self.tx_pc_hair.link = 'hair'
            self.tx_pc_eyes.link = 'eyes'
            self.tx_pc_father.link = 'father'
            self.tx_pc_mother.link = 'mother'
            self.tx_pc_bro.link = 'brothers'
            self.tx_pc_sis.link = 'sisters'
            self.tx_pc_marsta.link = 'marsta'
            self.tx_pc_spouse.link = 'spouse'
            self.tx_pc_childr.link = 'childr'

            return grp

        vbox.addWidget(build_pers_info())

        self.tabs.addTab(mfr, self.tr("Notes"))
