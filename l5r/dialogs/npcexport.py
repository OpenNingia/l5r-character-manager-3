# -*- coding: utf-8 -*-
# Copyright (C) 2014 Daniele Simonetti
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.

import l5r.widgets as widgets
import os

from PyQt5 import QtCore, QtGui, QtWidgets


class NpcExportDialog(QtWidgets.QDialog):

    # title bar
    header = None
    # frame layout
    vbox_lo = None
    # buttons
    bt_ok = None
    # controls
    a_tx_files = []
    a_bt_browse = []
    # output
    paths = []

    def __init__(self, parent=None):
        super(NpcExportDialog, self).__init__(parent)

        self.build_ui()
        self.setup()

    def build_ui(self):
        self.vbox_lo = QtWidgets.QVBoxLayout(self)
        self.bt_ok = QtWidgets.QPushButton(self.tr('Export'), self)
        self.header = QtWidgets.QLabel(self)
        center_fr = QtWidgets.QFrame(self)
        # center_fr.setFrameStyle(QtWidgets.QFrame.Sunken)

        # bottom bar
        bottom_bar = QtWidgets.QFrame(self)
        hbox = QtWidgets.QHBoxLayout(bottom_bar)
        hbox.addStretch()
        hbox.addWidget(self.bt_ok)

        vb = QtWidgets.QVBoxLayout(center_fr)
        self.a_tx_files = [widgets.FileEdit(self), widgets.FileEdit(self)]
        self.a_bt_browse = [QtWidgets.QToolButton(self), QtWidgets.QToolButton(self)]

        fnt = QtGui.QFont()
        fnt.setPointSize(12.0)

        for bt in self.a_bt_browse:
            bt.setAutoRaise(True)
            bt.setFont(fnt)
            bt.setText('...')
            bt.clicked.connect(self.on_browse_file)

        for i, tx in enumerate(self.a_tx_files):
            tx.setPlaceholderText(self.tr("Path to a .l5r character file"))
            tx.setFont(fnt)

            fr = QtWidgets.QFrame(self)
            hb = QtWidgets.QHBoxLayout(fr)
            hb.addWidget(tx)
            hb.addWidget(self.a_bt_browse[i])
            vb.addWidget(fr)

        vb.setContentsMargins(40, 20, 40, 20)

        self.vbox_lo.addWidget(self.header)
        self.vbox_lo.addWidget(center_fr)
        self.vbox_lo.addWidget(bottom_bar)

        self.bt_ok.clicked.connect(self.accept)

        self.resize(600, 300)

    def on_browse_file(self):
        index = self.a_bt_browse.index(self.sender())
        if index < 0:
            return

        form = self.parent()
        if not form:
            return

        path = form.select_load_path()
        self.a_tx_files[index].setText(path)

    def setup(self):
        self.set_header_text(self.tr("""
        <center>
        <h1>Export up to two NPC in a single PDF</h1>
        <p style="color: #666">Select up to two character files and click the "Export" button.</p>
        </center>
        """))

        self.setWindowTitle(self.tr("L5RCM: NPC Sheet"))

    def set_header_text(self, text):
        self.header.setText(text)

    def accept(self):

        self.paths = []

        for tx in self.a_tx_files:
            if os.path.exists(tx.text()):
                self.paths.append(tx.text())

        super(NpcExportDialog, self).accept()
