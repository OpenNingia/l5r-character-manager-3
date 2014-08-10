# Copyright (C) 2011 Daniele Simonetti
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

from PySide import QtCore, QtGui
APP_NAME = "L5R: CM"

def new_horiz_line(parent = None):
    line = QtGui.QFrame(parent)
    line.setObjectName("hline")
    line.setGeometry(QtCore.QRect(3, 3, 3, 3))
    line.setFrameShape(QtGui.QFrame.Shape.HLine)
    line.setFrameShadow(QtGui.QFrame.Sunken)
    line.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed)
    return line

class SimpleDescriptionView(QtGui.QWidget):
    def __init__(self, parent=None):
        super(SimpleDescriptionView, self).__init__(parent)

        self.lb_title    = QtGui.QLabel(self)
        self.lb_subtitle = QtGui.QLabel(self)
        #self.lb_content  = QtGui.QLabel(self)
        self.tx_content  = QtGui.QTextEdit(self)

        text_align = QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter;

        self.lb_title   .setAlignment(text_align)
        self.lb_subtitle.setAlignment(text_align)
        self.tx_content .setReadOnly (True)
        #self.lb_content .setAlignment(QtCore.Qt.AlignJustify | QtCore.Qt.AlignVCenter)
        #self.lb_content .setWordWrap (True)

        self.tx_content.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)

        vbox = QtGui.QVBoxLayout(self)
        vbox.addWidget(self.lb_title   )
        vbox.addWidget(self.lb_subtitle)
        vbox.addWidget(new_horiz_line(self))
        vbox.addWidget(self.tx_content )

    def set_title(self, text):
        self.lb_title.setText(u"""<h1>{}</h1>""".format(text))

    def set_subtitle(self, text):
        self.lb_subtitle.setText(u"""<em><h3 style="color:#666;">{}</h3></em>""".format(text))

    def set_content(self, text):
        self.tx_content.setText(u"""<p>{}</p>""".format(text))

    def sizeHint(self):
        return QtCore.QSize(400, 300)

class SimpleDescriptionDialog(QtGui.QDialog):
    def __init__(self, parent=None):
        super(SimpleDescriptionDialog, self).__init__(parent)

        self.descr = SimpleDescriptionView(self)
        self.bt    = QtGui.QPushButton(self.tr("Close"), self)

        self.vbox  = QtGui.QVBoxLayout(self)
        self.hbox  = QtGui.QHBoxLayout()
        self.hbox.addStretch()
        self.hbox.addWidget(self.bt)
        self.hbox.addStretch()
        self.vbox.addWidget(self.descr)
        self.vbox.addItem(self.hbox)

        self.setWindowTitle(APP_NAME)

        self.bt.clicked.connect( self.accept )

    def description(self):
        return self.descr
