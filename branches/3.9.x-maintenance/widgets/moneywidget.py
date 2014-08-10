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

import sys
from PySide import QtCore, QtGui

def new_small_le(parent = None, ro = False):
    le = QtGui.QLineEdit(parent)
    le.setSizePolicy( QtGui.QSizePolicy.Maximum,
                      QtGui.QSizePolicy.Maximum )
    le.setMaximumSize( QtCore.QSize(32, 24) )
    le.setReadOnly(ro)
    return le

class MoneyWidget(QtGui.QWidget):

    valueChanged = QtCore.Signal(tuple)

    def __init__(self, parent = None):
        super(MoneyWidget, self).__init__(parent)

        self.value = (0, 0, 0)
        
        hbox = QtGui.QHBoxLayout(self)
        hbox.setContentsMargins(0,0,0,0)
        
        self.tkoku = le_koku, lb_koku = new_small_le(self), QtGui.QLabel(self.tr('Koku'), self)
        self.tbu   = le_bu  , lb_bu   = new_small_le(self), QtGui.QLabel(self.tr('Bu')  , self)
        self.tzeni = le_zeni, lb_zeni = new_small_le(self), QtGui.QLabel(self.tr('Zeni'), self)
        
        for ed in [le_koku, le_bu, le_zeni]:
            ed.setAlignment( QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter )
            ed.editingFinished.connect(self.on_edit)
        
        hbox.addStretch()
        for w in self.tkoku: hbox.addWidget(w)
        for w in self.tbu  : hbox.addWidget(w)
        for w in self.tzeni: hbox.addWidget(w)
        hbox.addStretch()
        
        self.set_value( (0, 0, 0) )

    def on_edit(self):
        old_value = self.value
        try:
            self.value = ( int(self.tkoku[0].text()), int(self.tbu[0].text()), int(self.tzeni[0].text()) )
            self.valueChanged.emit(self.value)
        except:
            self.value = old_value
            self.set_value(self.value)

    def set_value(self, value):
        if len(value) != 3:
            raise Exception('Invalid value')
            
        self.value = value
        
        self.tkoku[0].setText( str(value[0]) )
        self.tbu  [0].setText( str(value[1]) )
        self.tzeni[0].setText( str(value[2]) )
        
        self.valueChanged.emit(self.value)

    def get_value(self):
        return self.value
        
    def get_koku(self):
        return self.value[0]

    def get_bu(self):
        return self.value[1]

    def get_zeni(self):
        return self.value[2]
        
### MAIN ###
def main():
    app = QtGui.QApplication(sys.argv)

    dlg = QtGui.QDialog()
    vbox = QtGui.QVBoxLayout(dlg)
    vbox.addWidget( MoneyWidget(dlg) )
    dlg.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
