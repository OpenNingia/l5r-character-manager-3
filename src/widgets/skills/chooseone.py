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
import api.data.schools
import api.character.skills
import api.character.rankadv

from widgets.searchbox import SearchBox

from PySide import QtCore, QtGui
from asq.initiators import query
from asq.selectors import a_


class ChooseOneSkill(QtGui.QWidget):
    valueChanged = QtCore.Signal(object)

    cb_category = None
    cb_skill = None
    sb_search = None
    filtered = None
    wildcards = None
    exclude_owned = False
    skills_to_show = []

    @property
    def skill(self):
        return api.data.skills.get(self.get_selected_skill())

    def __init__(self, parent=None):
        super(ChooseOneSkill, self).__init__(parent)

        self.cb_categories = QtGui.QComboBox(self)
        self.cb_skills = QtGui.QComboBox(self)
        self.sb_search = SearchBox(self)

        # vbox = QtGui.QVBoxLayout(self)
        form = QtGui.QFormLayout(self)

        form.addRow("", self.sb_search)
        form.addRow(self.tr("Category"), self.cb_categories)
        form.addRow(self.tr("Skill"), self.cb_skills)

        # vbox.addWidget(self.sb_search)
        #vbox.addItem(form)

        #self.vbl = vbox
        self.fol = form

        self.connect_signals()

    def sizeHint(self):
        return QtCore.QSize(440, 320)

    def set_filter(self, wildcards, skills):
        self.wildcards = wildcards
        self.filtered = skills

    def set_exclude_owned(self, flag):
        self.exclude_owned = flag

    def load(self):

        if self.wildcards:
            inclusive = api.data.skills.get_inclusive_tags(self.wildcards)
            exclusive = api.data.skills.get_exclusive_tags(self.wildcards)

            self.load_skills(inclusive, exclusive)
        else:
            self.load_skills()

    def set(self, skill):
        if not skill:
            return

        self.blockSignals(True)
        self.cb_skills.blockSignals(True)
        self.set_categ(skill.type)
        idx = self.cb_skills.findData(skill.id)
        self.cb_skills.setCurrentIndex(idx)
        self.cb_skills.blockSignals(False)
        self.blockSignals(False)

    def connect_signals(self):
        self.cb_categories.currentIndexChanged.connect(self.on_category_changed)
        self.cb_skills.currentIndexChanged.connect(self.on_skill_changed)
        self.sb_search.newSearch.connect(self.on_search)

    def load_skills(self, inclusive=None, exclusive=None):

        skills_to_show = api.data.skills.all()

        def intersect(a, b):
            return list(set(a) & set(b))

        if inclusive and inclusive[0] != 'any':
            skills_to_show = query(skills_to_show) \
                .where(lambda x: len(intersect(x.tags, inclusive)) > 0).to_list()

        if exclusive:
            skills_to_show = query(skills_to_show) \
                .where(lambda x: len(intersect(x.tags, exclusive)) == 0).to_list()

        if self.exclude_owned:
            # exclude owned skills
            skills_to_show = query(skills_to_show) \
                .where(lambda x: x.id not in api.character.skills.all()).to_list()

            # exclude skills already in advancement
            skills_to_show = query(skills_to_show) \
                .where(lambda x: x.id not in api.character.rankadv.get_current().skills).to_list()

            # exclude advancement school skills ( rank 1 only )
            if api.character.rankadv.get_current().rank == 1:
                print('advancement school', api.character.rankadv.get_current().school)
                rank1_school = api.data.schools.get(api.character.rankadv.get_current().school)
                school_skills = [x.id for x in rank1_school.skills]

                skills_to_show = query(skills_to_show) \
                    .where(lambda x: x.id not in school_skills).to_list()

        if self.filtered and len(self.filtered):
            skills_to_show = query(skills_to_show) \
                .where(lambda x: x.id not in self.filtered).to_list()

        self.skills_to_show = skills_to_show

        categories = query(skills_to_show) \
            .distinct(a_('type')) \
            .select(a_('type')).to_list()

        self.cb_categories.blockSignals(True)
        self.cb_categories.clear()
        for c in api.data.skills.categories():
            if c.id in categories:
                self.cb_categories.addItem(c.name, c.id)
        self.cb_categories.blockSignals(False)

        if self.cb_categories.count() > 0:
            self.on_category_changed(0)

    def update_skills(self):

        c = self.get_selected_category()

        skills = query(self.skills_to_show) \
            .where(lambda x: x.type == c) \
            .order_by(lambda x: x.name)

        self.cb_skills.blockSignals(True)
        self.cb_skills.clear()
        for c in skills:
            self.cb_skills.addItem(c.name, c.id)
        self.cb_skills.blockSignals(False)

        if self.cb_skills.count() > 0:
            self.on_skill_changed(0)

    def get_selected_category(self):
        return self.cb_categories.itemData(self.cb_categories.currentIndex())

    def get_selected_skill(self):
        return self.cb_skills.itemData(self.cb_skills.currentIndex())

    def on_category_changed(self, idx):
        self.update_skills()

    def on_skill_changed(self, idx):

        if self.signalsBlocked():
            return

        sk = self.get_selected_skill()
        self.valueChanged.emit(sk)

    def on_search(self, tx):

        # search skills
        found_skills = self.search_skill_by_text(tx.lower())
        if len(found_skills):
            self.set(found_skills[0])
            return

        found_categs = self.search_categ_by_text(tx.lower())
        if len(found_categs):
            self.set_categ(found_categs[0])
            return

    def search_skill_by_text(self, tx):

        return query(api.data.skills.all()) \
            .where(lambda x: tx in x.name.lower()) \
            .to_list()

    def search_categ_by_text(self, tx):

        return query(api.data.skills.categories()) \
            .where(lambda x: tx in x.name.lower()) \
            .to_list()

    def set_categ(self, categ):
        idx = self.cb_categories.findData(categ)
        self.cb_categories.setCurrentIndex(idx)
