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

import sys
import api.data.skills
import widgets
from widgets.searchbox import SearchBox

from PySide import QtCore, QtGui
from asq.initiators import query

class ChooseOneSkill(QtGui.QWidget):

    cb_category = None
    cb_skill = None
    sb_search = None

    def __init__(self, parent = None):
        super(ChooseOneSkill, self).__init__(parent)

        self.cb_categories = QtGui.QComboBox(self)
        self.cb_skills = QtGui.QComboBox(self)
        self.sb_search = SearchBox(self)

        #vbox = QtGui.QVBoxLayout(self)
        form = QtGui.QFormLayout(self)

        form.addRow("", self.sb_search)
        form.addRow(self.tr("Category"), self.cb_categories)
        form.addRow(self.tr("Skill"), self.cb_skills)

        #vbox.addWidget(self.sb_search)
        #vbox.addItem(form)

        #self.vbl = vbox
        self.fol = form

        self.connect_signals()

    def sizeHint(self):
       return QtCore.QSize(440, 320)

    def load(self):
        self.load_categories()
        self.load_skills()

        self.on_category_changed(0)
        self.on_skill_changed(0)

    def set(self, skill):
        self.cb_skills.clear()
        self.cb_skills.addItem(skill.name, skill.id)
        self.select_categ(skill.type)

    def connect_signals(self):
        self.cb_categories.currentIndexChanged.connect(self.on_category_changed)
        self.cb_skills.currentIndexChanged.connect(self.on_skill_changed)
        self.sb_search.newSearch.connect(self.on_search)

    def load_skills(self):
        self.cb_skills.clear()
        c = self.get_selected_category()

        # filter the skills by the selecter
        # category and order them by name
        skills_to_show = query(api.data.skills.get_skills()) \
                         .where(lambda x: x.type == c) \
                         .order_by(lambda x: x.name)
        for c in skills_to_show:
            self.cb_skills.addItem(c.name, c.id)

    def load_categories(self):
        self.cb_categories.clear()
        for c in api.data.skills.get_categories():
            print('add categ', c.name, c.id)
            self.cb_categories.addItem(c.name, c.id)

    def get_selected_category(self):
        return self.cb_categories.itemData( self.cb_categories.currentIndex() )

    def on_category_changed(self, idx):
        self.load_skills()

    def on_skill_changed(self, idx):
        print('skill', idx)

    def on_search(self, tx):

        # search skills
        found_skills = self.search_skill_by_text(tx.lower())
        if len(found_skills):
            self.cb_skills.clear()
            for c in found_skills:
                self.cb_skills.addItem(c.name, c.id)
            self.select_categ(found_skills[0].type)
            return

        found_categs = self.search_categ_by_text(tx.lower())
        if len(found_categs):
            self.cb_categories.clear()
            for c in found_categs:
                self.cb_categories.addItem(c.name, c.id)
            return

    def search_skill_by_text(self, tx):

        return query(api.data.skills.get_skills()) \
               .where( lambda x: tx in x.name.lower() ) \
               .to_list()

    def search_categ_by_text(self, tx):

        return query(api.data.skills.get_categories()) \
               .where( lambda x: tx in x.name.lower() ) \
               .to_list()

    def select_categ(self, categ):
        self.cb_categories.blockSignals(True)

        idx = self.cb_categories.findData(categ)
        self.cb_categories.setCurrentIndex(idx)

        self.cb_categories.blockSignals(False)
