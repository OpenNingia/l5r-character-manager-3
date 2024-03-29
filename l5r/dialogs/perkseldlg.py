# -*- coding: utf-8 -*-
# Copyright (C) 2014-2022 Daniele Simonetti
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

import l5r.api as api
import l5r.models as models
import l5r.widgets as widgets
import l5r.api.character

from l5r.util import log
from PyQt5 import QtCore, QtGui, QtWidgets

def em(text):
    return u'<em>{}</em>'.format(text)

class BuyPerkDialog(QtWidgets.QDialog):

    tag = None
    adv = None
    pc = None
    perk_id = 0
    perk_nm = ''
    perk_rule = None
    item = None
    edit_mode = False

    def __init__(self, pc, tag, parent=None):
        super(BuyPerkDialog, self).__init__(parent)
        self.tag = tag
        self.pc = pc
        self.build_ui()
        self.load_data()

    def build_ui(self):
        if self.tag == 'merit':
            self.setWindowTitle(self.tr("Add Advantage"))
        else:
            self.setWindowTitle(self.tr("Add Disadvantage"))

        self.setMinimumSize(600, 0)

        self.bt_accept = QtWidgets.QPushButton(self.tr("Ok"), self)
        self.bt_cancel = QtWidgets.QPushButton(self.tr("Cancel"), self)

        lvbox = QtWidgets.QVBoxLayout(self)

        grp = QtWidgets.QGroupBox(self.tr("SubType"), self)
        vbox = QtWidgets.QVBoxLayout(grp)
        self.cb_subtype = QtWidgets.QComboBox(self)
        self.cb_subtype.currentIndexChanged.connect(self.on_subtype_select)
        vbox.addWidget(self.cb_subtype)
        lvbox.addWidget(grp)

        grp = None
        if self.tag == 'merit':
            grp = QtWidgets.QGroupBox(self.tr("Advantage"), self)
        else:
            grp = QtWidgets.QGroupBox(self.tr("Disadvantage"), self)
        vbox = QtWidgets.QVBoxLayout(grp)
        self.cb_perk = QtWidgets.QComboBox(self)
        self.cb_perk.currentIndexChanged.connect(self.on_perk_select)
        vbox.addWidget(self.cb_perk)
        lvbox.addWidget(grp)

        grp = QtWidgets.QGroupBox(self.tr("Rank"), self)
        vbox = QtWidgets.QVBoxLayout(grp)
        self.cb_rank = QtWidgets.QComboBox(self)
        self.cb_rank.currentIndexChanged.connect(self.on_rank_select)
        vbox.addWidget(self.cb_rank)
        lvbox.addWidget(grp)

        grp = QtWidgets.QGroupBox(self.tr("Notes"), self)
        vbox = QtWidgets.QVBoxLayout(grp)
        self.tx_notes = QtWidgets.QTextEdit(self)
        self.lb_book = QtWidgets.QLabel(self)
        vbox.addWidget(self.tx_notes)
        vbox.addWidget(self.lb_book)
        lvbox.addWidget(grp)

        if self.tag == 'merit':
            grp = QtWidgets.QGroupBox(self.tr("XP Cost"), self)
        else:
            grp = QtWidgets.QGroupBox(self.tr("XP Gain"), self)
        vbox = QtWidgets.QVBoxLayout(grp)
        self.cost_widget = widgets.CostSelection(self)
        vbox.addWidget(self.cost_widget)
        lvbox.addWidget(grp)

        self.btbox = QtWidgets.QDialogButtonBox(QtCore.Qt.Horizontal)
        self.btbox.addButton(self.bt_accept, QtWidgets.QDialogButtonBox.AcceptRole)
        self.btbox.addButton(self.bt_cancel, QtWidgets.QDialogButtonBox.RejectRole)

        self.btbox.accepted.connect(self.on_accept)
        self.btbox.rejected.connect(self.close)

        lvbox.addWidget(self.btbox)

    def load_data(self):
        # load subtypes
        for typ in api.data.model().perktypes:
            self.cb_subtype.addItem(typ.name, typ.id)

    def set_edit_mode(self, flag):
        self.edit_mode = flag

        self.cb_subtype.setEnabled(not flag)
        self.cb_perk.setEnabled(not flag)
        self.cb_rank.setEnabled(not flag)

        self.cb_subtype.parent().setVisible(not flag)

        self.cb_rank   .blockSignals(flag)
        self.cb_perk   .blockSignals(flag)
        self.cb_subtype.blockSignals(flag)

        self.cost_widget.set_manual_only(flag)
        self.tx_notes.setReadOnly(not flag)

    def load_item(self, perk):
        self.cb_perk.clear()

        perk_id = perk.adv.perk
        perk_itm = api.data.merits.get(perk_id) or api.data.flaws.get(perk_id)

        if not perk_itm:
            log.ui.error(u"BuyPerkDialog. perk not found: %s", perk)
            return

        self.cb_perk.addItem(perk.name, perk_itm)
        self.cb_perk.setCurrentIndex(0)

        self.item = perk.adv

        self.cost_widget.set_manual_cost(abs(self.item.cost))

        if self.item.extra:
            self.tx_notes.setPlainText(self.item.extra)
        elif perk_itm.desc:
            self.tx_notes.setPlainText(perk_itm.desc)
        else:
            self.tx_notes.setPlainText("")


    def on_subtype_select(self, text=''):
        if self.edit_mode:
            return

        self.item = None
        self.cb_perk.clear()

        selected = self.cb_subtype.currentIndex()
        if selected < 0:
            return
        type_ = self.cb_subtype.itemData(selected)

        # populate perks
        perks = api.data.merits.all() if (
            self.tag == 'merit') else api.data.flaws.all()
        perks = [x for x in perks if x.type == type_]

        for p in perks:
            self.cb_perk.addItem(p.name, p)

    def on_perk_select(self, text=''):
        if self.edit_mode:
            return

        self.item = None
        self.cb_rank.clear()

        selected = self.cb_perk.currentIndex()
        if selected < 0:
            return
        perk = self.cb_perk.itemData(selected)

        self.update_book(perk)

        self.perk_id = perk.id
        self.perk_nm = perk.name

        # get perk rule
        self.perk_rule = perk.rule

        # fill description
        if perk.desc:
            self.tx_notes.setPlainText(perk.desc)

        # populate ranks
        for rank in perk.ranks:
            self.cb_rank.addItem(self.tr("Rank %d") % rank.id, rank)

    def on_rank_select(self, text=''):
        selected = self.cb_rank.currentIndex()
        if selected < 0:
            return
        rank = self.cb_rank.itemData(selected)
        cost = rank.value
        tag = None
        self.cost_widget.set_manual_only(cost == 0)
        # self.set_manual_cost(0)
        if cost != 0:
            # look for exceptions
            cost = abs(cost)
            for discount in rank.exceptions:
                t = discount.tag
                discounted = discount.value

                if api.character.has_tag(t):
                    cost = int(discounted)
                    tag = t
                    break

            if cost <= 0:
                cost = 1

        self.item = models.PerkAdv(self.perk_id, rank.id, cost, tag)
        if tag:
            self.cost_widget.set_discount_reason(tag)
        self.cost_widget.set_suggested_cost(self.item.cost)

    def update_perk(self):
        self.item.extra = self.tx_notes.toPlainText()
        self.item.cost = abs(self.cost_widget.get_cost())
        if self.tag == 'flaw':
            self.item.cost *= -1

    def on_accept(self):
        if self.edit_mode:
            self.update_perk()
            self.accept()
            return

        if not self.item:
            QtWidgets.QMessageBox.warning(self, self.tr("Perk not found"),
                                      self.tr("Please select a perk."))
            return

        self.item.rule = self.perk_rule
        self.item.extra = self.tx_notes.toPlainText()
        self.item.cost = abs(self.cost_widget.get_cost())

        if self.tag == 'merit':
            self.item.desc = self.tr("%s Rank %d, XP Cost: %d") % (
                self.perk_nm, self.item.rank, self.item.cost)

            if self.item.cost > api.character.xp_left():
                QtWidgets.QMessageBox.warning(self, self.tr("Not enough XP"),
                                          self.tr("Cannot purchase.\nYou've reached the XP Limit."))
                return
        else:
            self.item.desc = self.tr("%s Rank %d, XP Gain: %d") % (
                self.perk_nm, self.item.rank, abs(self.item.cost))

        if self.tag == 'flaw':
            self.item.cost *= -1

        self.item.tag = self.tag
        api.character.append_advancement(self.item)

        self.accept()

    def update_book(self, perk_data):
        try:
            source_book = perk_data.source_pack
            page_number = perk_data.book_page

            if not source_book:
                self.lb_book.setText("")
            elif not page_number:                
                self.lb_book.setText(em(source_book.display_name))
            else:
                self.lb_book.setText(em(self.tr(f"{source_book.display_name}, page {page_number}")))
        except:
            log.ui.error(f'cannot load source book for perk: {perk_data.id}', exc_info=1)
            print('perk data:', perk_data.__dict__)