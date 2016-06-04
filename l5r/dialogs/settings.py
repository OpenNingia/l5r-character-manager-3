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

from PyQt5 import QtGui, QtWidgets

class SettingsDialog(QtWidgets.QDialog):
    """Application settings dialog"""

    def __init__(self, parent=None):
        super(SettingsDialog, self).__init__(parent)

        # build interface
        self.area = QtWidgets.QScrollArea(self)
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.area)
        layout.setContentsMargins(0, 0, 0, 0)

        fr = QtWidgets.QFrame()
        vb = QtWidgets.QVBoxLayout(fr)
        vb.setContentsMargins(32, 32, 32, 32)

        # Generic
        vb.addWidget(QtWidgets.QLabel(self.tr("<h2>Generic</h2>")))
        self.ck_use_system_lang = QtWidgets.QCheckBox(
            self.tr("Use system language"), self)
        self.cb_select_lang = QtWidgets.QComboBox(self)
        self.ck_use_system_font = QtWidgets.QCheckBox(
            self.tr("Use system font"), self)

        hb1 = QtWidgets.QHBoxLayout()
        self.cb_select_font = QtWidgets.QFontComboBox(self)
        self.sz_font_size = QtWidgets.QDoubleSpinBox(self)
        for w in [self.cb_select_font, self.sz_font_size]:
            hb1.addWidget(w)

        self.ck_show_banner = QtWidgets.QCheckBox(
            self.tr("Show application banner"), self)

        vb.addWidget(self.ck_use_system_lang)
        vb.addWidget(self.cb_select_lang)
        vb.addWidget(self.ck_use_system_font)
        vb.addLayout(hb1)
        vb.addWidget(self.ck_show_banner)

        #
        vb.addWidget(QtWidgets.QLabel(self.tr("<h2>Health display</h2>")))
        fr.setLayout(vb)

        self.area.setWidget(fr)
        self.area.viewport().setBackgroundRole(QtGui.QPalette.Light);
        self.area.viewport().setAutoFillBackground(True);

        self.setLayout(layout)
        print('layout', self.layout())

def test():
    a = QtWidgets.QApplication([])
    d = SettingsDialog()
    d.show()
    a.exec_()

if __name__ == "__main__":
    test()