# -*- coding: utf-8 -*-
# Copyright (C) 2014-2026 Daniele Simonetti
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# Wound / health display mixin. Extracted from l5r/main.py during the
# Phase 4 split — no behaviour changes.
# Expects ``self.wounds`` to be a list of (QLabel, QLineEdit, QLineEdit)
# tuples populated by Tab 1's build_ui_page_1.

import l5r.api as api
import l5r.api.rules

from l5r.util.settings import L5RCMSettings


class HealthDisplayMixin:
    """Render wound table rows and penalty labels from the rules layer."""

    def update_wound_penalties(self):
        WOUND_PENALTIES_NAMES = [
            self.tr("Healthy"),
            self.tr("Nicked"),
            self.tr("Grazed"),
            self.tr("Hurt"),
            self.tr("Injured"),
            self.tr("Crippled"),
            self.tr("Down"),
        ]

        for i in reversed(range(0, 7)):
            if i < 7:
                penalty = api.rules.get_wound_penalties(i)
                text = u"{0} (+{1})".format(WOUND_PENALTIES_NAMES[i], penalty)
            else:
                text = WOUND_PENALTIES_NAMES[i]
            self.wounds[i][0].setText(text)

        # TODO Create a generate mechanism for data-pack defined bonus to penalties.
        # TODO toku bushi school removes some penalties

    def display_health(self):
        settings = L5RCMSettings()
        method = settings.app.health_method
        if method == 'default':
            self.display_health_default()
        elif method == 'wounds':
            self.display_total_wounds()
        else:
            self.display_health_stacked()

    def display_health_default(self):
        wounds_table = api.rules.get_wounds_table()
        if not wounds_table:
            return
        for i, (i_inc, i_total, i_stacked, i_inc_wounds, i_total_wounds, i_stacked_wounds) in enumerate(wounds_table):
            self.wounds[i][1].setText(str(i_inc))
            self.wounds[i][2].setText(str(i_inc_wounds) if i_inc_wounds else '')

    def display_health_stacked(self):
        wounds_table = api.rules.get_wounds_table()
        if not wounds_table:
            return
        for i, (i_inc, i_total, i_stacked, i_inc_wounds, i_total_wounds, i_stacked_wounds) in enumerate(wounds_table):
            self.wounds[i][1].setText(str(i_total))
            self.wounds[i][2].setText(str(i_total_wounds) if i_total_wounds else '')

    def display_total_wounds(self):
        wounds_table = api.rules.get_wounds_table()
        if not wounds_table:
            return
        for i, (i_inc, i_total, i_stacked, i_inc_wounds, i_total_wounds, i_stacked_wounds) in enumerate(wounds_table):
            self.wounds[i][1].setText(str(i_stacked))
            self.wounds[i][2].setText(str(i_stacked_wounds) if i_stacked_wounds else '')

    def get_health_rank(self, idx):
        return self.wounds[idx][1].text()
