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

import os
import sys
import dal
import dal.query
import models
import widgets
from PySide import QtCore, QtGui

def new_horiz_line(parent = None):
    line = QtGui.QFrame(parent)
    line.setObjectName("hline")
    line.setGeometry(QtCore.QRect(3, 3, 3, 3))
    line.setFrameShape(QtGui.QFrame.Shape.HLine)
    line.setFrameShadow(QtGui.QFrame.Sunken)
    line.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed)
    return line
    
class WizardPage (QtGui.QWidget):

    def __init__(self, widget=None, parent=None):
        super(WizardPage, self).__init__(parent)

        self._skippable = False
        self._first = False
        self._final = False      
        
        self.widget = None

    @property
    def skippable(self):
        return self._skippable

    @skippable.setter
    def skippable(self, value):
        self._skippable = value

    @property
    def first(self):
        return self._first

    @first.setter
    def first(self, value):
        self._first = value

    @property
    def final(self):
        return self._final

    @final.setter
    def final(self, value):
        self._final = value

    def get_summary_widget(self):
        return QtGui.QWidget(self)
        
    def get_h1_text(self):
        return "placeholder"
        
    def _set_ui(self, w):
        self.widget = w        
        hbox = QtGui.QHBoxLayout(self)
        hbox.addStretch()
        hbox.addWidget(w)
        hbox.addStretch()
        
class WizardDialog(QtGui.QDialog):

    def __init__(self, parent=None):
        super(WizardDialog, self).__init__(parent)

        self.pages = {}  # tag => widget
        self.h1 = QtGui.QLabel(self)
        
        self.stack = QtGui.QStackedWidget(self)
        self.stack.currentChanged.connect(self.on_page_change)
               
        vbox = QtGui.QVBoxLayout(self)
        vbox.addWidget(self.h1)
        vbox.addWidget(new_horiz_line(self))
        vbox.addWidget(self.stack)       
        vbox.addSpacing(32)
        
        self.make_bottom_bar()
    
    def resizeEvent(self, ev):
        self.bottom_bar.resize( 
            QtCore.QSize(self.width(), 32))
        self.bottom_bar.move(
            0, self.height() - 32)
        
    def make_bottom_bar(self):
        fr = QtGui.QFrame(self)
        
        self.bt_back = QtGui.QPushButton(self.tr("<Back"), self)
        self.bt_skip = QtGui.QPushButton(self.tr("Skip"), self)
        self.bt_next = QtGui.QPushButton(self.tr("Next>"), self)
        
        hbox = QtGui.QHBoxLayout(fr)        
        hbox.addStretch()
        hbox.addWidget(self.bt_back)
        hbox.addWidget(self.bt_skip)
        hbox.addWidget(self.bt_next)
        
        hbox.setContentsMargins(0,0,3,0)
        fr.setStyleSheet("QFrame {background: #CCC; border-top: 1px solid #333;}")        
        
        self.bottom_bar = fr

    def add_page(self, tag, page, skippable=False, first=False, last=False):        
        page.skippable = skippable
        page.first = first
        page.last = last

        if tag not in self.pages:
            self.pages[tag] = page
            self.stack.addWidget(page)
            
    def begin(self):
        self.stack.setCurrentIndex(0)
        
    def on_page_change(self, index):
        page = self.pages.values()[index]
        self.h1.setText(page.get_h1_text())
        
        # buttons
        self.bt_back.setEnabled(not page.first)
        self.bt_skip.setEnabled(page.skippable)
        self.bt_next.setText(self.tr("Finish") if page.last else self.tr("Next>"))           


class ClanAndFamilyPage(WizardPage):
    def __init__(self, parent=None):
        super(ClanAndFamilyPage, self).__init__(parent)        
        self._set_ui(widgets.FamilyChooserWidget(parent.dstore, self))
                        
    def get_h1_text(self):
        return '''
        <center>
        <h1>Select Clan and Family</h1>
        <p style="color: #666">a Samurai should serve its clan first and foremost</p>
        </center>
        '''        

class FirstSchoolPage(WizardPage):
    def __init__(self, parent=None):
        super(FirstSchoolPage, self).__init__(parent)


class NewSchoolPage(WizardPage):
    def __init__(self, parent=None):
        super(NewSchoolPage, self).__init__(parent)


class AlternatePathPage(WizardPage):

    def __init__(self, parent=None):
        super(AlternatePathPage, self).__init__(parent)


class SkillsPage(WizardPage):
    def __init__(self, parent=None):
        super(SkillsPage, self).__init__(parent)

        
class SummaryPage(WizardPage):
    def __init__(self, pages, parent=None):
        super (SummaryPage, self).__init__(parent)
        self.pages = pages

        
class SpellsPage(WizardPage):
    def __init__(self, parent=None):
        super(SpellsPage, self).__init__(parent)


class KihoPage(WizardPage):
    def __init__(self, parent=None):
        super(KihoPage, self).__init__(parent)


class RankAdvDialog(WizardDialog):

    def __init__(self, pc, dstore, rank, parent=None):
        super(RankAdvDialog, self).__init__(parent)

        self.pc = pc
        self.dstore = dstore
        self.rank = rank

        self.build_ui()

    def build_ui(self):

        # on first rank the Player should choose the Clan and the Family
        if self.rank == 1:
            self.add_page('family', ClanAndFamilyPage(self), first=True)
            self.add_page('school', FirstSchoolPage(self))
            # to choose a Rank 1 alternate path
            self.add_page('path', AlternatePathPage(self))
            self.add_page('skills', SkillsPage(self))  # get those starting skills
        else:
            # to choose a different school
            self.add_page('school', NewSchoolPage(self), skippable=True)

        if self.can_get_new_spells():
            self.add_page('spells', SpellsPage(self))

        if self.can_get_new_kiho():
            self.add_page('kiho', KihoPage(self))

        self.add_page('summary', SummaryPage(self.pages, self), last=True)
        
        self.resize( 600, 400 )
        self.begin()
        
    def can_get_new_spells(self):
        return True

    def can_get_new_kiho(self):
        return True
        
# ## MAIN ## #


def main():
    app = QtGui.QApplication(sys.argv)

    user_data_dir = os.environ['APPDATA'].decode('latin-1')
    pack_data_dir = os.path.join(user_data_dir, 'openningia', 'l5rcm')

    dstore = dal.Data(
        [os.path.join(pack_data_dir, 'core.data'),
         os.path.join(pack_data_dir, 'data')],
        [])
    
    dlg = RankAdvDialog(None, dstore, 1)
    dlg.exec_()
    
if __name__ == '__main__':
    main()
        
