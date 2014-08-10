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

class VerticalToolBar(QtGui.QFrame):
    def __init__(self, parent = None):
        super(VerticalToolBar, self).__init__(parent)
        self.vbox     = QtGui.QVBoxLayout(self)
        self.vbox.setContentsMargins(0, 6, 0, 6)        
        self.bt_size  = QtCore.QSize(16,16)       
    
    def addButton(self, icon, text, target_slot):
        tb = QtGui.QToolButton(self)
        tb.setIconSize(self.bt_size)
        tb.setToolButtonStyle(QtCore.Qt.ToolButtonFollowStyle)
        tb.setIcon(icon)
        tb.setToolTip(text)
        tb.clicked.connect( target_slot )
        self.vbox.addWidget(tb)        
        return tb
    
    def addStretch(self):
        self.vbox.addStretch(1)
        
    def addSpace(self):
        self.vbox.addSpacing(self.bt_size.height())
