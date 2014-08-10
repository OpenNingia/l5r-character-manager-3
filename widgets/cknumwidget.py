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

def find(f, seq):
  """Return first item in sequence where f(item) == True."""
  for item in seq:
    if f(item):
      return item

class CkNumWidget(QtGui.QWidget):

    valueChanged = QtCore.Signal(int, int)

    def __init__(self, count = 9, parent = None):
        super(CkNumWidget, self).__init__(parent)

        self.count  = count
        self.checks = []
        self.value  = 0
        hbox = QtGui.QHBoxLayout(self)
        hbox.setSpacing(0)
        hbox.setContentsMargins(0,0,0,0)
        for i in xrange(0, count):
            ck = QtGui.QCheckBox(self)
            self.checks.append( ck )
            hbox.addWidget( ck )
            ck.clicked.connect(self.on_ck_toggled)
            ck.setObjectName( str(i+1) )

    def on_ck_toggled(self):
        old_v = self.value
        fred = find(lambda ck: ck == self.sender(), self.checks)
        flag = fred.isChecked()
        
        if int(fred.objectName()) == old_v:
            self.value = self.value - 1
        else:
            self.value = int(fred.objectName())
                
        #print 'old_v: %d, value: %d' % (old_v, self.value)
         
        for i in xrange(0, self.count):
            ck = self.checks[i]
            if flag:
                if int(ck.objectName()) <= self.value:
                    self.checks[i].setChecked(flag)
                else:
                    self.checks[i].setChecked(not flag)
            else:
                if int(ck.objectName()) <= self.value:
                    self.checks[i].setChecked(not flag)
                else:
                    self.checks[i].setChecked(flag)
        if self.value != old_v:
            self.valueChanged.emit(old_v, self.value)

    def set_value(self, value):
        if value == self.value:
            return
        for i in xrange(0, self.count):
            ck = self.checks[i]
            if int(ck.objectName()) <= value:
                self.checks[i].setChecked(True)
            else:
                self.checks[i].setChecked(False)
        old_v = self.value
        self.value = value

        self.valueChanged.emit(old_v, value)

    def get_value(self):
        return self.value

### MAIN ###
def main():
    app = QtGui.QApplication(sys.argv)

    dlg = QtGui.QDialog()
    vbox = QtGui.QVBoxLayout(dlg)
    vbox.addWidget( CkNumWidget(dlg) )
    dlg.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
