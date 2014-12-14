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

import api.character.rankadv
import api.character

from newrank.wizardpage import WizardPage
from newrank.alternatepath import AlternatePathPage
from newrank.clanandfamily import ClanAndFamilyPage
from newrank.firstschool import FirstSchoolPage
from newrank.kiho import KihoPage
from newrank.newschool import NewSchoolPage
from newrank.skills import SkillsPage
from newrank.spells import SpellsPage

from PySide import QtCore, QtGui


def new_horiz_line(parent=None):
    line = QtGui.QFrame(parent)
    line.setObjectName("hline")
    line.setGeometry(QtCore.QRect(3, 3, 3, 3))
    line.setFrameShape(QtGui.QFrame.Shape.HLine)
    line.setFrameShadow(QtGui.QFrame.Sunken)
    line.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed)
    return line


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
        self.current_page.load()

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

        # apply partial progress
        self.on_partial_progress(page)

        # activate next page
        self.stack.setCurrentIndex(index + 1)

        if page.last:
            self.on_finish()

    def on_skip(self):
        index = max(0, self.stack.currentIndex())
        page = self.pages[index]
        page.clear()

        # activate next page
        self.stack.setCurrentIndex(index + 1)

        if page.last:
            self.on_finish()

    def on_partial_progress(self, page):
        pass

class SummaryPage(WizardPage):
    def __init__(self, pages, parent=None):
        super(SummaryPage, self).__init__(parent)
        self.pages = pages


class RankAdvDialog(WizardDialog):
    def __init__(self, rank, parent=None):
        super(RankAdvDialog, self).__init__(parent)

        self.rank = rank

        # start rank advancement
        api.character.rankadv.start(rank)

        self.build_ui()

    def build_ui(self):

        self.begin_add_pages()

        # on first rank the Player should choose the Clan and the Family
        if self.rank == 1:
            self.add_page(ClanAndFamilyPage(self), first=True)
            self.add_page(FirstSchoolPage(self))
            # to choose a Rank 1 alternate path
            self.add_page(AlternatePathPage(self), skippable=True)
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

    def on_partial_progress(self, page):
        page.apply_rank_advancement()

# ## MAIN ## #


def main():
    import sys
    app = QtGui.QApplication(sys.argv)

    # pc = models.AdvancedPcModel()
    api.character.new()
    dlg = RankAdvDialog(1)
    dlg.exec_()


if __name__ == '__main__':
    main()
