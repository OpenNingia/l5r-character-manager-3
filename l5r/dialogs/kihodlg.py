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
import l5r.api.data.powers
import l5r.api.character.powers

from PyQt5 import QtCore, QtGui, QtWidgets


class KihoDialog(QtWidgets.QDialog):

    # title bar
    header = None
    # frame layout
    vbox_lo = None
    # buttons
    bt_ok = None
    # controls
    cb_kiho = None
    tx_element = None
    tx_mastery = None
    tx_cost = None
    tx_pc_status = None
    tx_eligibility = None
    tx_detail = None

    def __init__(self, pc, parent=None):
        super(KihoDialog, self).__init__(parent)
        self.pc = pc
        self.item = None

        self.build_ui()
        self.connect_signals()
        self.setup()

    def build_ui(self):
        self.vbox_lo = QtWidgets.QVBoxLayout(self)
        self.bt_ok = QtWidgets.QPushButton(self.tr('Buy'), self)
        self.header = QtWidgets.QLabel(self)
        center_fr = QtWidgets.QFrame(self)
        center_fr.setFrameStyle(QtWidgets.QFrame.Sunken)
        cfr_fbox = QtWidgets.QFormLayout(center_fr)

        # bottom bar
        bottom_bar = QtWidgets.QFrame(self)
        hbox = QtWidgets.QHBoxLayout(bottom_bar)
        hbox.addStretch()
        hbox.addWidget(self.bt_ok)

        self.cb_kiho = QtWidgets.QComboBox(self)
        self.tx_element = QtWidgets.QLabel(self)
        self.tx_mastery = QtWidgets.QLabel(self)
        self.tx_cost = QtWidgets.QLabel(self)
        self.tx_pc_status = QtWidgets.QLabel(self)
        self.tx_eligibility = QtWidgets.QLabel(self)
        self.tx_detail = QtWidgets.QTextEdit(self)
        self.tx_detail.setReadOnly(True)

        cfr_fbox.addRow(self.tr("Kiho"), self.cb_kiho)
        cfr_fbox.addRow(self.tr("Element"), self.tx_element)
        cfr_fbox.addRow(self.tr("Mastery"), self.tx_mastery)
        cfr_fbox.addRow(self.tr("XP Cost"), self.tx_cost)
        cfr_fbox.addRow(self.tr("PG Status"), self.tx_pc_status)
        cfr_fbox.addRow(self.tr("Eligibility"), self.tx_eligibility)
        cfr_fbox.addRow(self.tr("Details"), self.tx_detail)

        cfr_fbox.setContentsMargins(120, 20, 120, 20)
        cfr_fbox.setVerticalSpacing(9)

        self.vbox_lo.addWidget(self.header)
        self.vbox_lo.addWidget(center_fr)
        self.vbox_lo.addWidget(bottom_bar)

        self.resize(600, 400)

    def connect_signals(self):
        self.bt_ok.clicked.connect(self.accept)
        self.cb_kiho.currentIndexChanged.connect(self.on_kiho_change)

    def setup(self):
        self.set_header_text(self.tr("""
        <center>
        <h1>Buy a kiho</h1>
        <p style="color: #666">Only certain classes are able to learn Kiho and at a different XP cost</p>
        </center>
        """))

        self.setWindowTitle(self.tr("L5RCM: Kiho"))
        self.load_kiho()

    def load_kiho(self):
        for kiho in api.data.powers.kiho():
            if kiho.type != 'tattoo' and not api.character.powers.has_kiho(kiho.id):
                self.cb_kiho.addItem(kiho.name, kiho.id)

    def set_header_text(self, text):
        self.header.setText(text)

    def on_kiho_change(self, idx):
        idx = self.cb_kiho.currentIndex()
        itm = self.cb_kiho.itemData(idx)

        kiho = api.data.powers.get_kiho(itm)
        if not kiho:
            return

        status_ok = [
            self.tr("You are a Monk of the Brotherhood of Shinsei"),
            self.tr("You are a Monk"),
            self.tr("You are a Ninja"),
            self.tr("You are a Shugenja")
        ]

        status_ko = self.tr("You have to be a Monk, Ninja or Shugenja")

        # save for later
        self.item = kiho

        ring_ = api.data.get_ring(kiho.element)
        kiho_cost = api.rules.calculate_kiho_cost(kiho.id)

        self.tx_element.setText(ring_.text)
        self.tx_mastery.setText(str(kiho.mastery))
        self.tx_cost.setText(str(kiho_cost))

        pc_status = None
        is_monk, is_brotherhood = api.character.is_monk()
        is_ninja = api.character.is_ninja()
        is_shugenja = api.character.is_shugenja()

        if is_brotherhood:
            pc_status = status_ok[0]
        elif is_monk:
            pc_status = status_ok[1]
        elif is_ninja:
            pc_status = status_ok[2]
        elif is_shugenja:
            pc_status = status_ok[3]
        else:
            pc_status = status_ko

        str_eligible = self.tr("You are eligible")

        if pc_status == status_ko:
            self.tx_pc_status.setText(
                u"""<span style="color:#A00">{0}</span>""".format(pc_status))
        else:
            self.tx_pc_status.setText(
                u"""<span style="color:#0A0">{0}</span>""".format(pc_status))

        is_eligible, reason = api.character.powers.check_kiho_eligibility(kiho.id)

        if is_eligible:
            self.tx_eligibility.setText(
                u"""<span style="color: #0A0">{0}</span>""".format(str_eligible))
        else:
            self.tx_eligibility.setText(
                u"""<span style="color: #A00">{0}</span>""".format(reason))

        self.tx_detail.setText(u"<p><em>{0}</em></p>".format(kiho.desc))
        self.bt_ok.setEnabled(is_eligible)

    def accept(self):
        # save item
        self.parent().do_buy_kiho(self.item)
        super(KihoDialog, self).accept()


class TattooDialog(QtWidgets.QDialog):

    # title bar
    header = None
    # frame layout
    vbox_lo = None
    # buttons
    bt_ok = None
    # controls
    cb_tattoo = None
    tx_pc_status = None
    tx_detail = None

    def __init__(self, pc, parent=None):
        super(TattooDialog, self).__init__(parent)
        self.pc = pc
        self.item = None

        self.build_ui()
        self.connect_signals()
        self.setup()

    def build_ui(self):
        self.vbox_lo = QtWidgets.QVBoxLayout(self)
        self.bt_ok = QtWidgets.QPushButton(self.tr('Buy'), self)
        self.header = QtWidgets.QLabel(self)
        center_fr = QtWidgets.QFrame(self)
        center_fr.setFrameStyle(QtWidgets.QFrame.Sunken)
        cfr_fbox = QtWidgets.QFormLayout(center_fr)

        # bottom bar
        bottom_bar = QtWidgets.QFrame(self)
        hbox = QtWidgets.QHBoxLayout(bottom_bar)
        hbox.addStretch()
        hbox.addWidget(self.bt_ok)

        self.cb_tattoo = QtWidgets.QComboBox(self)
        self.tx_pc_status = QtWidgets.QLabel(self)
        self.tx_detail = QtWidgets.QLabel(self)
        self.tx_detail.setWordWrap(True)

        cfr_fbox.addRow(self.tr("Tattoo"), self.cb_tattoo)
        cfr_fbox.addRow(self.tr("PG Status"), self.tx_pc_status)
        cfr_fbox.addRow(self.tr("Details"), self.tx_detail)

        cfr_fbox.setContentsMargins(120, 20, 120, 20)

        self.vbox_lo.addWidget(self.header)
        self.vbox_lo.addWidget(center_fr)
        self.vbox_lo.addWidget(bottom_bar)

        self.resize(600, 300)

    def connect_signals(self):
        self.bt_ok.clicked.connect(self.accept)
        self.cb_tattoo.currentIndexChanged.connect(self.on_tattoo_change)

    def setup(self):
        self.set_header_text(self.tr("""
        <center>
        <h1>Acquire a Tattoo</h1>
        <p style="color: #666">Only members of the Togashi Order can acquire tattoos</p>
        </center>
        """))

        self.setWindowTitle(self.tr("L5RCM: Tattoo"))
        self.load_kiho()

    def load_kiho(self):
        for kiho in api.data.powers.kiho():
            if kiho.type == 'tattoo' and not api.character.powers.has_kiho(kiho.id):
                self.cb_tattoo.addItem(kiho.name, kiho.id)

    def set_header_text(self, text):
        self.header.setText(text)

    def on_tattoo_change(self, idx):
        idx = self.cb_tattoo.currentIndex()
        itm = self.cb_tattoo.itemData(idx)

        kiho = api.data.powers.get_kiho(itm)
        if not kiho:
            return

        status_ok = self.tr("You are a member of the Togashi Order")
        status_ko = self.tr("You have to be a member of the Togashi Order")

        # save for later
        self.item = kiho

        is_eligible = True
        # is_eligible = (api.character.has_tag('dragon_togashi_tattooed_order') or
        #                api.character.has_tag('dragon_ob_hoshi_tsurui_zumi') or
        #                api.character.has_tag('dragon_ob_hitomi_kikage_zumi'))
        if not is_eligible:
            self.tx_pc_status.setText(
                u"""<span style="color:#A00">{0}</span>""".format(status_ko))
        else:
            self.tx_pc_status.setText(
                u"""<span style="color:#0A0">{0}</span>""".format(status_ok))

        self.tx_detail.setText(u"<p><em>{0}</em></p>".format(kiho.desc))
        self.bt_ok.setEnabled(is_eligible)

    def accept(self):
        # save item
        self.parent().do_buy_kiho(self.item)
        super(TattooDialog, self).accept()
