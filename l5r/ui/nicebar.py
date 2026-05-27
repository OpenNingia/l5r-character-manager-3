# -*- coding: utf-8 -*-
# Copyright (C) 2014-2026 Daniele Simonetti
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# In-window notification strip ("nicebar"). Extracted from l5r/main.py
# during the Phase 4 split — no behaviour changes.
# Mixed into L5RMain via class L5RMain(L5RCMCore, ..., NicebarMixin).
#
# Expects the host class to have provided ``self.nicebar = None`` and
# ``self.mvbox`` (the main QVBoxLayout) during __init__ / build_ui.

from qtpy import QtWidgets


_NICEBAR_STYLESHEET = """
QWidget { background: beige;}
QPushButton {
    color: #333;
    border: 2px solid rgb(200,200,200);
    border-radius: 7px;
    padding: 5px;
    background: qradialgradient(cx: 0.3, cy: -0.4,
    fx: 0.3, fy: -0.4, radius: 1.35, stop: 0 #fff,
    stop: 1 rgb(255,170,0));
    min-width: 80px;
    }

QPushButton:hover {
    background: qradialgradient(cx: 0.3, cy: -0.4,
    fx: 0.3, fy: -0.4, radius: 1.35, stop: 0 #fff,
    stop: 1 rgb(255,100,30));
}

QPushButton:pressed {
    background: qradialgradient(cx: 0.4, cy: -0.1,
    fx: 0.4, fy: -0.1, radius: 1.35, stop: 0 #fff,
    stop: 1 rgb(255,200,50));
}
"""


class NicebarMixin:
    """Inline notification bar shown above the tab widget."""

    def show_nicebar(self, wdgs):
        self.nicebar = QtWidgets.QFrame(self)
        self.nicebar.setStyleSheet(_NICEBAR_STYLESHEET)
        self.nicebar.setMinimumSize(0, 32)

        # nicebar layout
        hbox = QtWidgets.QHBoxLayout(self.nicebar)
        hbox.setContentsMargins(9, 1, 9, 1)

        for w in wdgs:
            hbox.addWidget(w)

        self.mvbox.insertWidget(1, self.nicebar)
        self.nicebar.setVisible(True)

    def hide_nicebar(self):
        if not self.nicebar:
            return
        self.nicebar.setVisible(False)
        del self.nicebar
        self.nicebar = None
