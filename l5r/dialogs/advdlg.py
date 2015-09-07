# -*- coding: utf-8 -*-
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

import models.advances as advances
import api.data.skills
from util import log

from PySide import QtCore, QtGui


class SkillSelectInformativeWidget(QtGui.QWidget):

    currentIndexChanged = QtCore.Signal(str)

    def __init__(self, parent=None):
        super(SkillSelectInformativeWidget, self).__init__(parent)

        self.cb_skills = QtGui.QComboBox(self)
        self.lb_book = QtGui.QLabel(self)
        self.lb_desc = QtGui.QLabel(self)

        # build UI
        vb = QtGui.QVBoxLayout(self)
        vb.addWidget(self.cb_skills)

        fr_desc = QtGui.QFrame(self)
        fly = QtGui.QFormLayout(fr_desc)
        fly.addRow(self.lb_book, self.lb_desc)

        vb.addWidget(fr_desc)

        self.cb_skills.currentIndexChanged.connect(self.updateItem)

    def clear(self):
        self.cb_skills.clear()
        self.lb_book.clear()
        self.lb_desc.clear()

    def addItem(self, text, data):
        self.cb_skills.addItem(text, data)

    def currentIndex(self):
        return self.cb_skills.currentIndex()

    def setCurrentIndex(self, index):
        self.cb_skills.setCurrentIndex()

    def currentText(self):
        return self.cb_skills.currentText()

    def currentItem(self):
        return self.itemData(self.currentIndex())

    def itemText(self, index):
        return self.cb_skills.itemText(index)

    def itemData(self, index):
        return self.cb_skills.itemData(index)

    def updateItem(self, item):

        # the stored data could be the skill_id or a tuple (skill_id, skill_rank)
        item_ = self.currentItem()
        skill_id = None
        skill_rank = None
        if isinstance(item_, tuple):
            skill_id, skill_rank = item_
        elif isinstance(item_, list):
            skill_id, skill_rank = item_[0], item_[1]
        else:
            skill_id = item_

        skill_ = api.data.skills.get(skill_id)
        if skill_ and skill_.pack:
            self.lb_book.setText(skill_.pack.display_name)
        if skill_ and skill_.desc:
            self.lb_desc.setText(skill_.desc)

        self.currentIndexChanged.emit(item)


class BuyAdvDialog(QtGui.QDialog):

    def __init__(self, pc, tag, parent=None):
        super(BuyAdvDialog, self).__init__(parent)
        self.tag = tag
        self.adv = None
        self.pc = pc
        self.quit_on_accept = True
        self.build_ui()
        self.load_data()

        self.connect_signals()

    def build_ui(self):
        grid = QtGui.QGridLayout(self)

        titles = dict(
            skill=self.tr('Buy Skill rank'),
            emph=self.tr('Buy Skill emphasys'))

        labels = dict(
            skill=(
                self.tr(
                    'Choose Skill Type'), self.tr('Choose Skill')),
            emph= (self.tr('Choose Skill'), self.tr('Choose Emphasis')))

        self.setWindowTitle(titles[self.tag])

        self.widgets = dict(
            skill=(
                #QtGui.QComboBox(self), QtGui.QComboBox(self)),
                QtGui.QComboBox(self), SkillSelectInformativeWidget(self)),
            emph =(QtGui.QComboBox(self), QtGui.QLineEdit(self)))

        for t in self.widgets.itervalues():
            if t[0]:
                t[0].setVisible(False)
            if t[1]:
                t[1].setVisible(False)

        if self.tag in self.widgets:
            for i in xrange(0, 2):
                if labels[self.tag][i] is not None:
                    lb = QtGui.QLabel(labels[self.tag][i], self)
                    wd = self.widgets[self.tag][i]
                    wd.setVisible(True)
                    grid.addWidget(lb, i, 0)
                    grid.addWidget(wd, i, 1, 1, 3)

        self.lb_from = QtGui.QLabel(self.tr('Make your choice'), self)
        self.lb_cost = QtGui.QLabel(self.tr('Cost: 0'), self)

        self.bt_buy = QtGui.QPushButton(self.tr('Buy'), self)
        self.bt_close = QtGui.QPushButton(self.tr('Close'), self)

        grid.addWidget(self.lb_from, 3, 0, 1, 3)
        grid.addWidget(self.lb_cost, 4, 0, 1, 3)
        grid.addWidget(self.bt_buy, 5, 2, 1, 1)
        grid.addWidget(self.bt_close, 5, 3, 1, 1)

    def cleanup(self):
        self.widgets = {}

    def load_data(self):
        print('load data')
        if self.tag == 'skill':
            cb = self.widgets[self.tag][0]
            for t in api.data.skills.categories():
                cb.addItem(t.name, t.id)
        elif self.tag == 'emph':
            cb = self.widgets[self.tag][0]
            for id in self.pc.get_skills():
                sk = api.data.skills.get(id)
                cb.addItem(sk.name, sk.id)

            self.lb_cost.setText(self.tr('Cost: 2 exp'))
            self.lb_from.setVisible(False)

    def fix_skill_id(self, uuid):
        if self.tag == 'emph':
            cb = self.widgets[self.tag][0]
            sk = api.data.skills.get(uuid)
            cb.addItem(sk.name, sk.id)
            cb.setCurrentIndex(cb.count() - 1)
            cb.setEnabled(False)

    def connect_signals(self):
        print('connect_signals')
        if self.tag == 'skill':
            cb1 = self.widgets[self.tag][0]
            cb2 = self.widgets[self.tag][1]

            cb1.setCurrentIndex(-1)
            cb1.currentIndexChanged.connect(self.on_skill_type_select)
            cb2.currentIndexChanged.connect(self.on_skill_select)
            cb1.setCurrentIndex(0)

        self.bt_buy.clicked.connect(self.buy_advancement)
        self.bt_close.clicked.connect(self.close)

    def on_skill_type_select(self, text=''):
        cb1 = self.widgets['skill'][0]
        cb2 = self.widgets['skill'][1]
        idx = cb1.currentIndex()
        type_ = cb1.itemData(idx)

        avail_skills = api.data.skills.get_by_category(type_)

        cb2.clear()

        can_buy_skill = [
            x for x in avail_skills if x.id not in self.pc.get_skills()]

        # no more skills available for this category
        # player bought them all?
        if len(can_buy_skill) == 0:
            self.bt_buy.setEnabled(False)
            # try the next category
            if (idx + 1) < cb1.count():
                cb1.setCurrentIndex(idx + 1)
        else:
            self.bt_buy.setEnabled(True)
            for sk in can_buy_skill:
                cb2.addItem(sk.name, sk.id)

    def on_skill_select(self, text=''):
        cb2 = self.widgets['skill'][1]
        idx = cb2.currentIndex()

        uuid = cb2.itemData(idx)
        text = cb2.itemText(idx)

        cb1 = self.widgets['skill'][0]
        type_ = cb1.itemData(cb1.currentIndex())

        cur_value = self.pc.get_skill_rank(uuid)
        new_value = cur_value + 1

        cost = new_value

        print('pc is obtuse? {0}'.format(self.pc.has_rule('obtuse')))
        print('skill type: {0}'.format(type_))
        print('skill uuid: {0}'.format(uuid))

        if (self.pc.has_rule('obtuse') and
                type_ == 'high' and
                uuid != 'investigation' and  # investigation
                uuid != 'medicine'):        # medicine

            # double the cost for high skill
            # other than medicine and investigation
            cost *= 2

        self.lb_from.setText(
            self.tr('From {0} to {1}').format(cur_value, new_value))
        self.lb_cost.setText(self.tr('Cost: {0} exp').format(cost))

        self.adv = advances.SkillAdv(uuid, cost)

        mastery_ability_ = api.data.skills.get_mastery_ability(uuid, new_value)
        if mastery_ability_:
            self.adv.rule = mastery_ability_.rule

        self.adv.desc = (self.tr('{0}, Rank {1} to {2}. Cost: {3} xp')
                         .format(text, cur_value, new_value, self.adv.cost))

    def buy_advancement(self):

        if self.adv and ((self.adv.cost + self.pc.get_px()) >
                         self.pc.exp_limit):
            QtGui.QMessageBox.warning(self, self.tr("Not enough XP"),
                                      self.tr("Cannot purchase.\nYou've reached the XP Limit."))
            self.close()
            return

        if self.tag == 'skill':
            self.pc.add_advancement(self.adv)
            self.on_skill_select()
        elif self.tag == 'emph':
            cb = self.widgets[self.tag][0]
            tx = self.widgets[self.tag][1]
            sk_name = cb.itemText(cb.currentIndex())
            sk_uuid = cb.itemData(cb.currentIndex())
            self.adv = advances.SkillEmph(sk_uuid, tx.text(), 2)
            self.adv.desc = (self.tr('{0}, Skill {1}. Cost: {2} xp')
                             .format(tx.text(), sk_name, self.adv.cost))
            self.pc.add_advancement(self.adv)
            tx.setText('')

        if self.quit_on_accept:
            self.accept()

    def closeEvent(self, event):
        self.cleanup()


def check_all_done(cb_list):
    # check that all the choice have been made
    for cb in cb_list:
        if cb.currentIndex() < 0:
            return False
    return True


def check_all_done_2(le_list):
    for le in le_list:
        if len(le.text()) == 0:
            return False
    return True


def check_all_different(cb_list):
    # check that all the choices are different
    for i in xrange(0, len(cb_list) - 1):
        cb = cb_list[i]
        id = cb.itemData(cb.currentIndex())
        for j in xrange(i + 1, len(cb_list)):
            cb2 = cb_list[j]
            id2 = cb2.itemData(cb2.currentIndex())

            if id2 == id:
                return False
    return True


def check_already_got(list1, list2):
    # check if you already got this item
    for id in list1:
        if id in list2:
            return True
    return False


class SelWcSkills(QtGui.QDialog):

    def __init__(self, pc, parent=None):
        super(SelWcSkills, self).__init__(parent)
        self.pc = pc
        self.cbs = []
        self.les = []
        self.error_bar = None
        self.build_ui()
        self.connect_signals()
        self.load_data()

    def build_ui(self):
        self.setWindowTitle(self.tr('Choose School Skills'))

        vb = QtGui.QVBoxLayout(self)

        self.header = QtGui.QLabel(self.tr("<i>Your school has granted you \
                                             the right to choose some skills.</i> \
                                             <br/><b>Choose with care.</b>"), self)

        vb.addWidget(self.header)

        self.bt_ok = QtGui.QPushButton(self.tr('Ok'), self)
        self.bt_cancel = QtGui.QPushButton(self.tr('Cancel'), self)

        row_ = 2
        for ws in self.pc.get_pending_wc_skills():
            lb = ''
            wl = ws.wildcards
            if len(ws.wildcards):
                or_wc = [
                    x.value for x in wl if not x.modifier or x.modifier == 'or']
                not_wc = [
                    x.value for x in wl if x.modifier and x.modifier == 'not']

                or_categories = [
                    api.data.skills.get_category(x).name for x in or_wc if api.data.skills.get_category(x) is not None
                ]

                nor_categories = [
                    api.data.skills.get_category(x).name for x in not_wc if api.data.skills.get_category(x) is not None
                ]

                sw1 = ', '.join(or_categories)
                sw2 = ', '.join(nor_categories)

                if wl[0].value == 'any':
                    sw1 = self.tr('skill')

                if len(not_wc):
                    lb = self.tr('Any {0}, but {1} (rank {2}):').format(
                        sw1, sw2, ws.rank)
                else:
                    lb = self.tr(
                        'Any {0} skill (rank {1}):').format(sw1, ws.rank)

            vb.addWidget(QtGui.QLabel(lb, self))

            cb = SkillSelectInformativeWidget(self)
            self.cbs.append(cb)
            vb.addWidget(cb)

            row_ += 1

        for s in self.pc.get_pending_wc_emphs():

            skill_ = api.data.skills.get(s)
            if not skill_:
                continue

            lb = self.tr("{0}'s Emphases: ").format(skill_.name)

            vb.addWidget(QtGui.QLabel(lb, self))

            le = QtGui.QLineEdit(self)
            self.les.append(le)
            vb.addWidget(le)

            row_ += 1

        self.error_bar = QtGui.QLabel(self)
        self.error_bar.setVisible(False)

        vb.addWidget(self.error_bar)

        fr_bottom = QtGui.QFrame(self)
        hb = QtGui.QHBoxLayout(fr_bottom)
        hb.addWidget(self.bt_ok)
        hb.addWidget(self.bt_cancel)

        vb.addWidget(fr_bottom)

    def cleanup(self):
        self.cbs = []
        self.les = []
        self.error_bar = None

    def load_data(self):

        log.ui.debug(u"User can choose some starting skills")

        i = 0
        for ws in self.pc.get_pending_wc_skills():
            outcome = []
            wl = ws.wildcards

            for w_ in wl:
                if w_.value == 'any':
                    outcome += api.data.skills.all()
                else:
                    log.ui.debug(u"query skills with tag: %s", w_.value)

                    skills_by_tag = api.data.skills.get_by_tag(w_.value)

                    if not w_.modifier or w_.modifier == 'or':
                        outcome += skills_by_tag
                    elif w_.modifier == 'not':
                        outcome = [
                            x for x in outcome if x not in skills_by_tag]

            for sk in outcome:
                if sk.id not in self.pc.get_skills():
                    self.cbs[i].addItem(sk.name, (sk.id, ws.rank))

            i += 1

    def connect_signals(self):
        self.bt_cancel.clicked.connect(self.close)
        self.bt_ok    .clicked.connect(self.on_accept)

    def on_accept(self):

        # check if all selected
        done = check_all_done(self.cbs) and check_all_done_2(self.les)

        if not done:
            self.error_bar.setText('''<p style='color:#FF0000'>
                                      <b>
                                      You need to choose all the skills
                                      e/o emphases
                                      </b>
                                      </p>
                                      ''')
            self.error_bar.setVisible(True)
            return

        # check if all different
        all_different = check_all_different(self.cbs)

        if not all_different:
            self.error_bar.setText('''<p style='color:#FF0000'>
                                      <b>
                                      You can't select the same skill more than once
                                      </b>
                                      </p>
                                      ''')
            self.error_bar.setVisible(True)
            return

        # check if already got
        already_got = check_already_got(
            [x.itemData(x.currentIndex())[0] for x in self.cbs], self.pc.get_skills())

        if already_got:
            self.error_bar.setText('''<p style='color:#FF0000'>
                                      <b>
                                      You already possess some of these skills
                                      </b>
                                      </p>
                                      ''')
            self.error_bar.setVisible(True)
            return

        self.error_bar.setVisible(False)

        for cb in self.cbs:
            idx = cb.currentIndex()
            uuid, rank = cb.itemData(idx)

            api.character.skills.add_starting_skill(uuid, rank)

            #self.pc.add_school_skill(uuid, rank)

        for i in xrange(0, len(self.les)):
            emph = self.les[i].text()
            s_id = self.pc.get_pending_wc_emphs()[i]

            api.character.skills.add_starting_skill(uuid, emph=emph)

        self.accept()

    def closeEvent(self, event):
        self.cleanup()
