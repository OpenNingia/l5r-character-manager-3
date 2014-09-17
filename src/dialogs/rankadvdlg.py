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

import dal
import dal.query
import models
import widgets
from PySide import QtCore, QtGui


class WizardPage (QtGui.QWidget):

    def __init__(self, parent=None):
        super(WizardPage, self).__init__(parent)

        self._skippable = False
        self._first = False
        self._final = False

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


class WizardDialog(QtGui.QDialog):

    def __init__(self, parent=None):
        super(WizardDialog, self).__init__(parent)

        self.pages = {}  # tag => widget

    def add_page(self, tag, page, skippable=False, first=False, last=False):

        page.skippable = skippable
        page.first = first
        page.last = last

        if tag not in self.pages:
            self.pages[tag] = page

    def build_ui(self):

        self.stack = QtGui.QStackedWidgets(self)
        for k, p in self.pages:
            self.stack.addWidget(p)


class ClanAndFamilyPage(WizardPage):

    def __init__(self, parent=None):
        super(ClanAndFamilyPage, self).__init__(self)


class FirstSchoolPage(WizardPage):

    def __init__(self, parent=None):
        super(SchoolPage, self).__init__(self)


class NewSchoolPage(WizardPage):

    def __init__(self, parent=None):
        super(SchoolPage, self).__init__(self)


class AlternatePathPage(WizardPage):

    def __init__(self, parent=None):
        super(AlternatePathPage, self).__init__(self)


class SkillsPage(WizardPage):
    def __init__(self, parent=None):
        super(SkillsPage, self).__init__(self)

        
class SummaryPage(WizardPage):
    def __init__(self, pages, parent=None):
        super (SummaryPage, self).__init__(self)
        self.pages = pages

        
class SpellsPage(WizardPage):

    def __init__(self, parent=None):
        super(SpellsPage, self).__init__(self)


class KihoPage(WizardPage):

    def __init__(self, parent=None):
        super(KihoPage, self).__init__(self)


class RankAdvDialog(WizardDialog):

    def __init__(self, pc, dstore, rank, parent=None):
        super(RankAdvDialog, self).__init__(self)

        self.pc = pc
        self.dstore = dstore
        self.rank = rank

        self.build_ui()

    def build_ui(self):

        # on first rank the Player should choose the Clan and the Family
        if self.rank == 1:
            self.add_page(ClanAndFamilyPage(self), first=True)
            self.add_page(FirstSchoolPage(self))
            # to choose a Rank 1 alternate path
            self.add_page(AlternatePathPage(self))
            self.add_page(SkillsPage(self))  # get those starting skills
        else:
            # to choose a different school
            self.add_page(SchoolPage(self), skippable=True)

        if self.can_get_new_spells():
            self.add_page(SpellsPage(self))

        if self.can_get_new_kiho():
            self.add_page(KihoPage(self))

        self.add_page(SummaryPage(self.pages, self), final = True)
