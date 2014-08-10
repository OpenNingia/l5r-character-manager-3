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

class XpTextBox(QtGui.QLineEdit):
    
    sub_text = None
    
    def __init__(self, parent = None):
        super(XpTextBox, self).__init__(parent)
        self.sub_text = self.tr('XP')
        
    def paintEvent(self, event):
        super(XpTextBox, self).paintEvent(event)
        
        painter = QtGui.QPainter(self)
        painter.save()
        
        # a nice gray pen
        pen = QtGui.QPen( QtCore.Qt.darkGray, 1 )
        painter.setPen(pen)
        right_margin = 5

        # measure the string to draw
        font_metric = painter.fontMetrics()        
        tx_rect     = font_metric.boundingRect(self.sub_text)       
        
        painter.drawText(event.rect().width() - right_margin - tx_rect.width(), event.rect().top() + tx_rect.height(), self.sub_text)
        
        painter.restore()        
        

class CostSelection(QtGui.QWidget):

    rb_suggested = None
    rb_manual    = None
    
    tx_suggested = None
    tx_manual    = None
    
    vbox         = None
    
    suggested    = 0
    manual       = 0
    reason       = None
    
    def __init__(self, parent = None):
        super(CostSelection, self).__init__(parent)
        
        self.rb_suggested = QtGui.QRadioButton(self.tr('Suggested Value'), self)
        self.rb_manual    = QtGui.QRadioButton(self.tr('Manual Value'),self)

        self.tx_suggested = XpTextBox(self)
        self.tx_manual    = XpTextBox(self)

        vbox              = QtGui.QVBoxLayout(self)
        vbox.addStretch()
        vbox.addWidget(self.rb_suggested)
        vbox.addWidget(self.tx_suggested)
        vbox.addWidget(self.rb_manual)
        vbox.addWidget(self.tx_manual)
        
        self.rb_suggested.toggled.connect( self.tx_suggested.setEnabled )
        self.rb_manual   .toggled.connect( self.tx_manual   .setEnabled )
        self.rb_manual   .toggled.connect( self.tx_manual   .selectAll  )
        self.rb_manual   .toggled.connect( self.tx_manual   .setFocus   )
        
        self.rb_suggested.setChecked(True)
        self.tx_manual   .setEnabled(False)
        
        self.tx_manual   .setContentsMargins(18, 0, 0, 0)
        self.tx_suggested.setContentsMargins(18, 0, 0, 0)
        self.tx_suggested.setReadOnly(True)        
        
        validator = QtGui.QIntValidator(self)
        validator.setRange(-9999, 9999)
        self.tx_manual.setValidator(validator)
        self.tx_manual   .setText('0')
        
        self.tx_manual.textChanged.connect( self.on_manual_text_change )
        
    def set_suggested_cost(self, cost):
        self.suggested = cost
        self.update_suggested_text()
        
    def set_discount_reason(self, reason):
        self.reason = reason
        self.update_suggested_text()
        
    def update_suggested_text(self):
        if self.reason:
            self.tx_suggested.setText( '{0} [{1}]'.format(self.suggested, self.reason) )
        else:
            self.tx_suggested.setText( str(self.suggested) )
            
    def get_suggested_cost(self):
        return self.suggested
        
    def get_manual_cost(self):
        return self.manual

    def set_manual_cost(self, value):
        self.tx_manual.setText( str(value) )
        
    def set_manual_only(self, flag):
        self.rb_manual.setChecked(flag)
        #self.tx_manual.setEnabled(flag)

        self.rb_suggested.setChecked(not flag)
        self.rb_suggested.setEnabled(not flag)
        #self.tx_suggested.setEnabled(not flag)   

    def on_manual_text_change(self, text):
        try:
            self.manual = int(text)
        except:
            self.manual = 0
        
    def get_cost(self):
        if self.rb_manual.isChecked():
            return self.manual
        else:
            return self.suggested
        
def utest():
    app = QtGui.QApplication(sys.argv)
    dlg = QtGui.QDialog()
    vbox = QtGui.QVBoxLayout(dlg)
    csel = CostSelection(dlg)
    csel.set_suggested_cost(3)
    csel.set_discount_reason('crab')
    vbox.addWidget( csel )
    dlg.show()
    app.exec_()
        
if __name__ == '__main__':
    utest()
    
        
