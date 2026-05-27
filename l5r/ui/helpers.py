# -*- coding: utf-8 -*-
# Copyright (C) 2014-2026 Daniele Simonetti
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# Small widget factories shared across the UI tabs. Extracted from
# l5r/main.py during the Phase 4 split — no behaviour changes.

from qtpy import QtCore, QtGui, QtWidgets

from l5r.util.fsutil import get_icon_path


def new_small_le(parent=None, ro=True):
    le = QtWidgets.QLineEdit(parent)
    le.setSizePolicy(QtWidgets.QSizePolicy.Maximum,
                     QtWidgets.QSizePolicy.Maximum)
    le.setMaximumSize(QtCore.QSize(32, 24))
    le.setReadOnly(ro)
    return le


def new_horiz_line(parent=None):
    line = QtWidgets.QFrame(parent)
    line.setObjectName("hline")
    line.setGeometry(QtCore.QRect(3, 3, 3, 3))
    line.setFrameShape(QtWidgets.QFrame.HLine)
    line.setFrameShadow(QtWidgets.QFrame.Sunken)
    line.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
    return line


def new_vert_line(parent=None):
    line = QtWidgets.QFrame(parent)
    line.setObjectName("vline")
    line.setGeometry(QtCore.QRect(320, 150, 118, 3))
    line.setFrameShape(QtWidgets.QFrame.VLine)
    line.setFrameShadow(QtWidgets.QFrame.Sunken)
    return line


def new_item_groupbox(name, widget):
    grp = QtWidgets.QGroupBox(name, widget.parent())
    vbox = QtWidgets.QVBoxLayout(grp)
    vbox.addWidget(widget)
    return grp


def new_small_plus_bt(parent=None):
    bt = QtWidgets.QToolButton(parent)
    bt.setAutoRaise(True)
    bt.setText('+')
    bt.setIcon(
        QtGui.QIcon.fromTheme('gtk-add', QtGui.QIcon(
            get_icon_path('add', (16, 16)))))
    bt.setMaximumSize(16, 16)
    bt.setMinimumSize(16, 16)
    bt.setToolButtonStyle(QtCore.Qt.ToolButtonFollowStyle)
    return bt
