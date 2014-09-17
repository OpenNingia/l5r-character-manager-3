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

from PySide import QtGui, QtCore
import os
import sys
import iconloader
from toolbar_rc import *


class SearchBox(QtGui.QLineEdit):

    newSearch = QtCore.Signal(str)

    def __init__(self, parent=None):
        super(SearchBox, self).__init__(parent)

        self._timer = QtCore.QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.on_timeout)

        self._button = QtGui.QToolButton(self)

        clear_icon = iconloader.icon('edit-clear',
                                     QtGui.QIcon(':/icons/edit-clear.png'))
        self._button.setIcon(clear_icon)

        self._button.setStyleSheet('border: 0px; padding: 0px;')
        self._button.setCursor(QtCore.Qt.ArrowCursor)
        self._button.clicked.connect(self.on_button_click)

        frameWidth = self.style().pixelMetric(QtGui.QStyle.PM_DefaultFrameWidth)
        buttonSize = self._button.sizeHint()

        self.setStyleSheet('QLineEdit {padding-right: %dpx; }' % (buttonSize.width() + frameWidth + 1))
        self.setMinimumSize(max(self.minimumSizeHint().width(), buttonSize.width() + frameWidth * 2 + 2),
                            max(self.minimumSizeHint().height(), buttonSize.height() + frameWidth * 2 + 2))

        self.textChanged.connect(self.on_text_changed)

        self.set_search_delay_ms(600)

    def resizeEvent(self, event):
        buttonSize = self._button.sizeHint()
        frameWidth = self.style().pixelMetric(QtGui.QStyle.PM_DefaultFrameWidth)
        self._button.move(self.rect().right() - frameWidth - buttonSize.width(),
                          (self.rect().bottom() - buttonSize.height() + 1) / 2)
        super(SearchBox, self).resizeEvent(event)

    def set_search_delay_ms(self, delay):
        self._timer.setInterval(600)

    def on_text_changed(self, text):
        self._timer.start()

    def on_timeout(self):
        self.newSearch.emit(self.text())

    def on_button_click(self):
        self._timer.stop()
        self.setText("")
        self.on_timeout()

# ## MAIN ## #


def main():
    app = QtGui.QApplication(sys.argv)

    dlg = QtGui.QDialog()
    vbox = QtGui.QVBoxLayout(dlg)
    search_box = SearchBox(dlg)
    label = QtGui.QLabel(dlg)
    vbox.addWidget(search_box)
    vbox.addWidget(label)
    search_box.newSearch.connect(label.setText)
    dlg.exec_()
    #sys.exit(app.exec_())

if __name__ == '__main__':
    main()
