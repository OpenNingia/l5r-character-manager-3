# -*- coding: utf-8 -*-
# Copyright (C) 2014-2022 Daniele Simonetti
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

from PyQt5 import QtCore, QtGui, QtWidgets

import l5r.widgets as widgets
import l5r.api as api
import l5r.api.character.rankadv


class NextRankDlg(QtWidgets.QDialog):

    def __init__(self, pc, parent=None):
        super(NextRankDlg, self).__init__(parent)
        self.pc = pc

        self.build_ui()
        self.connect_signals()

        # self.setWindowFlags(QtCore.Qt.Tool)
        self.setWindowTitle(self.tr("L5R: CM - Advance Rank"))

    def build_ui(self):
        vbox = QtWidgets.QVBoxLayout(self)
        vbox.addWidget(QtWidgets.QLabel(self.tr("""\
You can now advance your Rank,
what would you want to do?
                                    """)))
        self.bt_go_on = QtWidgets.QPushButton(
            self.tr("Advance in my current school")
        )
        self.bt_new_school = QtWidgets.QPushButton(
            self.tr("Join a new school"))

        for bt in [self.bt_go_on, self.bt_new_school]:
            bt.setMinimumSize(QtCore.QSize(0, 38))

        vbox.addWidget(self.bt_go_on)
        vbox.addWidget(self.bt_new_school)

        vbox.setSpacing(12)

        is_path = api.data.schools.is_path(
            api.character.schools.get_current()
        )

        former_school_adv = api.character.rankadv.get_former_school()
        former_school = api.data.schools.get(former_school_adv.school) if former_school_adv else None

        # check if the PC is following an alternate path
        if is_path:
            # offer to going back
            if former_school:
                self.bt_go_on.setText(self.tr("Continue ") + former_school.name)
            else:
                self.bt_go_on.setText(self.tr("Go back to your old school"))
            self.bt_go_on.setEnabled(former_school != None)

    def connect_signals(self):
        self.bt_go_on.clicked.connect(self.simply_go_on)
        self.bt_new_school.clicked.connect(self.join_new_school)

    def join_new_school(self):
        dlg = widgets.SchoolChooserDialog(self)
        if dlg.exec_() == QtWidgets.QDialog.Rejected:
            return

        self.accept()

    def simply_go_on(self):

        is_path = api.data.schools.is_path(
            api.character.schools.get_current()
        )

        # check if the PC is following an alternate path
        if is_path:
            # the PC want to go back to the old school.
            # find the first school that is not a path

            api.character.rankadv.leave_path()
        else:
            api.character.rankadv.advance_rank()

        self.accept()


def test():
    import sys
    app = QtWidgets.QApplication(sys.argv)

    dlg = NextRankDlg(None, None)
    dlg.show()

    sys.exit(app.exec_())

if __name__ == '__main__':
    test()
