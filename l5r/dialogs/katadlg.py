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


import l5r.models as models
import l5r.api as api
import l5r.api.data
import l5r.api.data.powers
import l5r.widgets as widgets

from l5r.util import log
from PyQt5 import QtCore, QtGui, QtWidgets


def em(text):
    return u'<em>{}</em>'.format(text)

class KataDialog(QtWidgets.QDialog):

    # title bar
    header = None
    # frame layout
    vbox_lo = None
    # buttons
    bt_ok = None
    # controls
    cb_kata = None
    tx_element = None
    tx_mastery = None
    tx_cost = None
    req_list = None
    tx_detail = None
    tx_ring_need = None

    def __init__(self, pc, parent=None):
        super(KataDialog, self).__init__(parent)
        self.pc = pc
        self.item = None

        self.build_ui()
        self.connect_signals()
        self.setup()

    def build_ui(self):
        self.vbox_lo = QtWidgets.QVBoxLayout(self)
        self.bt_ok = QtWidgets.QPushButton(self.tr('Buy'), self)
        self.header = QtWidgets.QLabel(self)
        self.lb_book = QtWidgets.QLabel(self)
        center_fr = QtWidgets.QFrame(self)
        center_fr.setFrameStyle(QtWidgets.QFrame.Sunken)
        cfr_fbox = QtWidgets.QFormLayout(center_fr)

        # bottom bar
        bottom_bar = QtWidgets.QFrame(self)
        hbox = QtWidgets.QHBoxLayout(bottom_bar)
        hbox.addStretch()
        hbox.addWidget(self.bt_ok)

        self.cb_kata = QtWidgets.QComboBox(self)
        self.req_list = widgets.RequirementsWidget(self)
        self.tx_element = QtWidgets.QLabel(self)
        self.tx_mastery = QtWidgets.QLabel(self)
        self.tx_ring_need = QtWidgets.QLabel(self)
        self.tx_cost = QtWidgets.QLabel(self)        
        self.tx_detail = QtWidgets.QTextEdit(self)
        self.tx_detail.setReadOnly(True)
        # self.tx_detail.setWordWrap(True)

        # this should display as "Mastery 3 - you need at least 3 in your Air
        # Ring"
        fr_mastery = QtWidgets.QFrame(self)
        fr_hbox = QtWidgets.QHBoxLayout(fr_mastery)
        fr_hbox.setContentsMargins(0, 0, 0, 0)
        fr_hbox.addWidget(self.tx_mastery)
        fr_hbox.addWidget(self.tx_ring_need)

        cfr_fbox.addRow(self.tr("Kata"), self.cb_kata)
        cfr_fbox.addRow(self.tr("Element"), self.tx_element)
        cfr_fbox.addRow(self.tr("Mastery"), fr_mastery)
        cfr_fbox.addRow(self.tr("XP Cost"), self.tx_cost)
        cfr_fbox.addRow(self.tr("Requirements"), self.req_list)
        cfr_fbox.addRow(self.tr("Details"), self.tx_detail)
        cfr_fbox.addRow(self.tr("Source"), self.lb_book)

        cfr_fbox.setContentsMargins(120, 20, 120, 20)
        cfr_fbox.setVerticalSpacing(9)

        self.vbox_lo.addWidget(self.header)
        self.vbox_lo.addWidget(center_fr)
        self.vbox_lo.addWidget(bottom_bar)

        self.setMinimumSize(600, 400)

    def connect_signals(self):
        self.bt_ok.clicked.connect(self.accept)
        self.cb_kata.currentIndexChanged.connect(self.on_kata_change)

    def setup(self):
        self.set_header_text(self.tr("""
        <center>
        <h1>Buy a Kata</h1>
        <p style="color: #666">You can only buy Kata if you match at least one requirement</p>
        </center>
        """))

        self.setWindowTitle(self.tr("L5RCM: Kata"))
        self.load_kata()

    def load_kata(self):
        for kata in api.data.powers.kata():
            if not api.character.powers.has_kata(kata.id):
                self.cb_kata.addItem(kata.name, kata.id)

    def set_header_text(self, text):
        self.header.setText(text)

    def on_kata_change(self, idx):
        idx = self.cb_kata.currentIndex()
        itm = self.cb_kata.itemData(idx)

        kata = api.data.powers.get_kata(itm)
        if not kata:
            return

        self.update_book(kata)

        # save for later
        self.item = kata

        ring_ = api.data.get_ring(kata.element)

        self.tx_element.setText(ring_.text)
        self.tx_mastery.setText(str(kata.mastery))
        self.tx_cost.setText(str(kata.mastery))
        self.tx_detail.setText(u"<p><em>{0}</em></p>".format(kata.desc))
        self.req_list.set_requirements(self.pc, api.data.model(), kata.require)

        self.tx_ring_need.setText(
            self.tr("""<span style="color: #A00">You need at value of {0} in your {1} ring.</span>""")
            .format(kata.mastery, ring_.text))

        def check_ring_value():
            ring_val = api.character.ring_rank(kata.element)
            return ring_val >= kata.mastery

        def check_eligibility():
            has_requirements = self.req_list.match_at_least_one()
            return has_requirements and check_ring_value()

        self.tx_ring_need.setVisible(not check_ring_value())
        self.bt_ok.setEnabled(check_eligibility())

    def accept(self):
        # save item
        self.parent().do_buy_kata(self.item)
        super(KataDialog, self).accept()


    def update_book(self, kata_data):
        try:
            source_book = kata_data.pack
            page_number = kata_data.page

            if not source_book:
                self.lb_book.setText("")
            elif not page_number:                
                self.lb_book.setText(em(source_book.display_name))
            else:
                self.lb_book.setText(em(self.tr(f"{source_book.display_name}, page {page_number}")))
        except:
            log.ui.error(f'cannot load source book for tattoo: {kata_data.id}', exc_info=1)