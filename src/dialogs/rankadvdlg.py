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


def new_horiz_line(parent=None):
    line = QtGui.QFrame(parent)
    line.setObjectName("hline")
    line.setGeometry(QtCore.QRect(3, 3, 3, 3))
    line.setFrameShape(QtGui.QFrame.Shape.HLine)
    line.setFrameShadow(QtGui.QFrame.Sunken)
    line.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed)
    return line


class WizardPage (QtGui.QWidget):

    nextAllowed = QtCore.Signal(bool)

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

    def clear(self):
        pass

    def refresh_status(self):
        if hasattr(self.widget, 'refresh_status'):
            self.widget.refresh_status()


class WizardDialog(QtGui.QDialog):

    def __init__(self, parent=None):
        super(WizardDialog, self).__init__(parent)

        self.pages = []
        self.h1 = QtGui.QLabel(self)

        self.stack = QtGui.QStackedWidget(self)
        self.stack.currentChanged.connect(self.on_page_change)

        vbox = QtGui.QVBoxLayout(self)
        vbox.addWidget(self.h1)
        vbox.addWidget(new_horiz_line(self))
        vbox.addWidget(self.stack)
        vbox.addSpacing(32)

        self.current_page = None

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

        self.bt_cancel = QtGui.QPushButton(self.tr("Cancel"), self)

        hbox = QtGui.QHBoxLayout(fr)
        hbox.addWidget(self.bt_cancel)
        hbox.addStretch()
        hbox.addWidget(self.bt_back)
        hbox.addWidget(self.bt_skip)
        hbox.addWidget(self.bt_next)

        hbox.setContentsMargins(3, 0, 3, 0)
        fr.setStyleSheet("QFrame {background: #CCC; border-top: 1px solid #333;}")

        self.bt_cancel.clicked.connect(self.on_cancel)

        self.bt_back.clicked.connect(self.on_back)
        self.bt_skip.clicked.connect(self.on_skip)
        self.bt_next.clicked.connect(self.on_next)

        self.bottom_bar = fr

    def add_page(self, page, skippable=False, first=False, last=False):
        page.skippable = skippable
        page.first = first
        page.last = last

        if page not in self.pages:
            self.pages.append(page)
            self.stack.addWidget(page)

    def begin_add_pages(self):
        self.stack.blockSignals(True)

    def end_add_pages(self):
        self.stack.blockSignals(False)

        for p in self.pages:
            p.nextAllowed.connect(self.on_next_allowed)

        self.on_page_change(0)

    def on_page_change(self, index):
        page = self.pages[index]
        self.h1.setText(page.get_h1_text())

        # buttons
        self.bt_back.setEnabled(not page.first)
        self.bt_skip.setEnabled(page.skippable)
        self.bt_next.setText(self.tr("Finish") if page.last else self.tr("Next>"))
        self.current_page = page
        self.current_page.refresh_status()

    def on_next_allowed(self, allowed):
        if self.sender() == self.current_page:
            self.bt_next.setEnabled(allowed)

    def on_cancel(self):
        self.reject()

    def on_back(self):
        index = max(0, self.stack.currentIndex())
        page = self.pages[index]
        if page.first:
            return
        self.stack.setCurrentIndex(index - 1)

    def on_next(self):
        index = max(0, self.stack.currentIndex())
        page = self.pages[index]
        self.stack.setCurrentIndex(index + 1)
        if page.last:
            self.on_finish()

    def on_skip(self):
        index = max(0, self.stack.currentIndex())
        page = self.pages[index]
        page.clear()
        self.on_next()


class ClanAndFamilyPage(WizardPage):
    def __init__(self, parent=None):
        super(ClanAndFamilyPage, self).__init__(parent)
        self._set_ui(widgets.FamilyChooserWidget(parent.dstore, self))

    def get_h1_text(self):
        return self.tr('''
<center>
<h1>Select Clan and Family</h1>
<p style="color: #666">a Samurai should serve its clan first and foremost</p>
</center>
        ''')


class FirstSchoolPage(WizardPage):
    def __init__(self, parent=None):
        super(FirstSchoolPage, self).__init__(parent)

        w = widgets.SchoolChooserWidget(parent.pc, parent.dstore, self)
        w.allow_advanced_schools = False
        w.allow_alternate_paths = False
        w.allow_basic_schools = True
        w.show_filter_selection = False
        w.show_bonus_trait = True
        w.show_school_requirements = False

        w.statusChanged.connect(self.nextAllowed)

        self._set_ui(w)

    def get_h1_text(self):
        return self.tr('''
<center>
<h1>Join your First School</h1>
<p style="color: #666">In this phase you're limited to base schools,
        however you can replace this rank with an alternative path
        on the next step</p>
</center>
        ''')


class NewSchoolPage(WizardPage):
    def __init__(self, parent=None):
        super(NewSchoolPage, self).__init__(parent)

        w = widgets.SchoolChooserWidget(parent.pc, parent.dstore, self)
        w.allow_advanced_schools = True
        w.allow_alternate_paths = False
        w.allow_basic_schools = True
        w.show_filter_selection = True
        w.show_bonus_trait = False
        w.show_school_requirements = True

        # disable alternate path filter
        w.cx_path_schools.setEnabled(False)

        w.statusChanged.connect(self.nextAllowed)

        self._set_ui(w)

    def get_h1_text(self):
        return self.tr('''
<center>
<h1>Join a new School</h1>
<p style="color: #666">In this phase you can join either Base school
and Advanced ones</p>
<p style="color: #066">To follow an alternate path, skip this step</p>
</center>
        ''')


class AlternatePathPage(WizardPage):

    def __init__(self, parent=None):
        super(AlternatePathPage, self).__init__(parent)

        w = widgets.SchoolChooserWidget(parent.pc, parent.dstore, self)
        w.allow_advanced_schools = False
        w.allow_alternate_paths = True
        w.allow_basic_schools = False
        w.show_filter_selection = False
        w.show_bonus_trait = False
        w.show_school_requirements = True

        w.statusChanged.connect(self.nextAllowed)

        self._set_ui(w)

    def get_h1_text(self):
        return self.tr('''
<center>
<h1>Follow an Alternate Path</h1>
<p style="color: #666">If you don't like a certain school rank you can
replace it with another one</p>
</center>
        ''')


class SkillsPage(WizardPage):
    def __init__(self, parent=None):
        super(SkillsPage, self).__init__(parent)


class SpellsPage(WizardPage):
    def __init__(self, parent=None):
        super(SpellsPage, self).__init__(parent)


class KihoPage(WizardPage):
    def __init__(self, parent=None):
        super(KihoPage, self).__init__(parent)


class SummaryPage(WizardPage):
    def __init__(self, pages, parent=None):
        super(SummaryPage, self).__init__(parent)
        self.pages = pages


class RankAdvDialog(WizardDialog):

    def __init__(self, pc, dstore, rank, parent=None):
        super(RankAdvDialog, self).__init__(parent)

        self.pc = pc
        self.dstore = dstore
        self.rank = rank

        self.build_ui()

    def build_ui(self):

        self.begin_add_pages()

        # on first rank the Player should choose the Clan and the Family
        if self.rank == 1:
            self.add_page(ClanAndFamilyPage(self), first=True)
            self.add_page(FirstSchoolPage(self))
            # to choose a Rank 1 alternate path
            self.add_page(AlternatePathPage(self))
            self.add_page(SkillsPage(self))  # get those starting skills
        else:
            # to choose a different school
            self.add_page(NewSchoolPage(self), first=True, skippable=True)
            self.add_page(AlternatePathPage(self), skippable=True)

        if self.can_get_new_spells():
            self.add_page(SpellsPage(self))

        if self.can_get_new_kiho():
            self.add_page(KihoPage(self))

        self.add_page(SummaryPage(self.pages, self), last=True)

        self.resize(700, 600)

        self.end_add_pages()

    def can_get_new_spells(self):
        return True

    def can_get_new_kiho(self):
        return True

    def on_finish(self):
        pass

# ## MAIN ## #


def main():
    app = QtGui.QApplication(sys.argv)

    user_data_dir = os.environ['APPDATA'].decode('latin-1')
    pack_data_dir = os.path.join(user_data_dir, 'openningia', 'l5rcm')

    dstore = dal.Data(
        [os.path.join(pack_data_dir, 'core.data'),
         os.path.join(pack_data_dir, 'data')],
        [])

    pc = models.AdvancedPcModel()
    dlg = RankAdvDialog(pc, dstore, 2)
    dlg.exec_()

if __name__ == '__main__':
    main()
