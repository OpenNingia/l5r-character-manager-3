# -*- coding: utf-8 -*-
# Copyright (C) 2014-2026 Daniele Simonetti
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# Tab 11 — Settings panel. Extracted from l5r/main.py during the
# Phase 4 split — no behaviour changes.

import l5r.widgets as widgets


class SettingsTabMixin:
    """Tab 11: instantiate SettingsWidget and add it to the tab bar."""

    def build_ui_page_settings(self):
        self.settings_widgets = widgets.SettingsWidget(self)
        self.tabs.addTab(self.settings_widgets, self.tr("Settings"))
        self.settings_widgets.setup(self)
