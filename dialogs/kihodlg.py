# Copyright (C) 2011 Daniele Simonetti
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
import rules
from PySide import QtCore, QtGui

class KihoDialog(QtGui.QDialog):

    # data storage
    dstore         = None
    # title bar
    header         = None
    # frame layout
    vbox_lo        = None
    # buttons
    bt_ok          = None
    # controls
    cb_kiho        = None
    tx_element     = None
    tx_mastery     = None
    tx_cost        = None
    tx_pc_status   = None
    tx_eligibility = None
    tx_detail      = None

    def __init__(self, pc, dstore, parent = None):
        super(KihoDialog, self).__init__(parent)
        self.pc     = pc
        self.dstore = dstore
        self.item   = None

        self.build_ui       ()
        self.connect_signals()
        self.setup          ()

    def build_ui(self):
        self.vbox_lo  = QtGui.QVBoxLayout(self)
        self.bt_ok    = QtGui.QPushButton(self.tr('Buy'), self)
        self.header   = QtGui.QLabel(self)
        center_fr     = QtGui.QFrame(self)
        center_fr.setFrameStyle(QtGui.QFrame.Sunken)
        cfr_fbox      = QtGui.QFormLayout(center_fr)

        # bottom bar
        bottom_bar     = QtGui.QFrame(self)
        hbox = QtGui.QHBoxLayout(bottom_bar)
        hbox.addStretch()
        hbox.addWidget(self.bt_ok)

        self.cb_kiho        = QtGui.QComboBox(self)
        self.tx_element     = QtGui.QLabel(self)
        self.tx_mastery     = QtGui.QLabel(self)
        self.tx_cost        = QtGui.QLabel(self)
        self.tx_pc_status   = QtGui.QLabel(self)
        self.tx_eligibility = QtGui.QLabel(self)
        self.tx_detail      = QtGui.QLabel(self)
        self.tx_detail.setWordWrap(True)


        cfr_fbox.addRow(self.tr("Kiho"          ), self.cb_kiho        )
        cfr_fbox.addRow(self.tr("Element"       ), self.tx_element     )
        cfr_fbox.addRow(self.tr("Mastery"       ), self.tx_mastery     )
        cfr_fbox.addRow(self.tr("XP Cost"       ), self.tx_cost        )
        cfr_fbox.addRow(self.tr("PG Status"     ), self.tx_pc_status   )
        cfr_fbox.addRow(self.tr("Eligibility"   ), self.tx_eligibility )
        cfr_fbox.addRow(self.tr("Details"       ), self.tx_detail      )

        cfr_fbox.setContentsMargins(120, 20, 120, 20)

        self.vbox_lo.addWidget(self.header)
        self.vbox_lo.addWidget(center_fr  )
        self.vbox_lo.addWidget(bottom_bar )

        self.resize( 600, 300 )

    def connect_signals(self):
        self.bt_ok.clicked.connect( self.accept )
        self.cb_kiho.currentIndexChanged.connect( self.on_kiho_change )

    def setup(self):
        self.set_header_text(self.tr('''
        <center>
        <h1>Buy a kiho</h1>
        <p style="color: #666">Only certain classes are able to learn Kiho and at a different XP cost</p>
        </center>
        '''))

        self.setWindowTitle(self.tr("L5RCM: Kiho"))
        self.load_kiho()

    def load_kiho(self):
        for kiho in self.dstore.kihos:
            if kiho.type != 'tattoo' and not self.pc.has_kiho(kiho.id):
                self.cb_kiho.addItem( kiho.name, kiho.id )

    def set_header_text(self, text):
        self.header.setText(text)

    def on_kiho_change(self, idx):
        idx = self.cb_kiho.currentIndex()
        itm = self.cb_kiho.itemData(idx)

        kiho = dal.query.get_kiho(self.dstore, itm)
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

        ring_name = dal.query.get_ring(self.dstore, kiho.element)

        self.tx_element.setText(ring_name.text)
        self.tx_mastery.setText(str(kiho.mastery))
        self.tx_cost.setText(str( self.parent().calculate_kiho_cost(kiho) ))

        pc_status = None
        is_monk, is_brotherhood = self.parent().pc_is_monk()
        is_ninja, is_shugenja   = self.parent().pc_is_ninja(), self.parent().pc_is_shugenja()

        if   is_brotherhood: pc_status = status_ok[0]
        elif is_monk:        pc_status = status_ok[1]
        elif is_ninja:       pc_status = status_ok[2]
        elif is_shugenja:    pc_status = status_ok[3]
        else:                pc_status = status_ko

        str_eligible    = self.tr("You are eligible")
        str_no_eligible = [
            self.tr("Your {0} Ring or School Rank are not enough"), # monk
            self.tr("Your {0} Ring Rank is not enough"), # shugenja
            self.tr("Your School Rank is not enough"), # ninja
            self.tr("You are not eligible"), # n/a
            ]

        if pc_status == status_ko:
            self.tx_pc_status.setText( u"""<span style="color:#A00">{0}</span>""".format(pc_status) )
        else:
            self.tx_pc_status.setText( u"""<span style="color:#0A0">{0}</span>""".format(pc_status) )

        is_eligible = self.parent().check_kiho_eligibility(kiho)
        if is_eligible:
            self.tx_eligibility.setText("""<span style="color: #0A0">{0}</span>""".format(str_eligible))
        else:
            tmp = "N/A"
            if is_monk:        tmp = str_no_eligible[0].format(ring_name.text)
            elif is_shugenja:  tmp = str_no_eligible[1].format(ring_name.text)
            elif is_ninja:     tmp = str_no_eligible[2]
            else:              tmp = str_no_eligible[3]

            self.tx_eligibility.setText( u"""<span style="color: #A00">{0}</span>""".format(tmp))

        self.tx_detail.setText( u"<p><em>{0}</em></p>".format(kiho.desc))
        self.bt_ok.setEnabled( is_eligible )

    def accept(self):
        # save item
        self.parent().do_buy_kiho(self.item)
        super(KihoDialog, self).accept()


class TattooDialog(QtGui.QDialog):

    # data storage
    dstore         = None
    # title bar
    header         = None
    # frame layout
    vbox_lo        = None
    # buttons
    bt_ok          = None
    # controls
    cb_tattoo      = None
    tx_pc_status   = None
    tx_detail      = None

    def __init__(self, pc, dstore, parent = None):
        super(TattooDialog, self).__init__(parent)
        self.pc     = pc
        self.dstore = dstore
        self.item   = None

        self.build_ui       ()
        self.connect_signals()
        self.setup          ()

    def build_ui(self):
        self.vbox_lo  = QtGui.QVBoxLayout(self)
        self.bt_ok    = QtGui.QPushButton(self.tr('Buy'), self)
        self.header   = QtGui.QLabel(self)
        center_fr     = QtGui.QFrame(self)
        center_fr.setFrameStyle(QtGui.QFrame.Sunken)
        cfr_fbox      = QtGui.QFormLayout(center_fr)

        # bottom bar
        bottom_bar     = QtGui.QFrame(self)
        hbox = QtGui.QHBoxLayout(bottom_bar)
        hbox.addStretch()
        hbox.addWidget(self.bt_ok)

        self.cb_tattoo      = QtGui.QComboBox(self)
        self.tx_pc_status   = QtGui.QLabel(self)
        self.tx_detail      = QtGui.QLabel(self)
        self.tx_detail.setWordWrap(True)

        cfr_fbox.addRow(self.tr("Tattoo"        ), self.cb_tattoo      )
        cfr_fbox.addRow(self.tr("PG Status"     ), self.tx_pc_status   )
        cfr_fbox.addRow(self.tr("Details"       ), self.tx_detail      )

        cfr_fbox.setContentsMargins(120, 20, 120, 20)

        self.vbox_lo.addWidget(self.header)
        self.vbox_lo.addWidget(center_fr  )
        self.vbox_lo.addWidget(bottom_bar )

        self.resize( 600, 300 )

    def connect_signals(self):
        self.bt_ok.clicked.connect( self.accept )
        self.cb_tattoo.currentIndexChanged.connect( self.on_tattoo_change )

    def setup(self):
        self.set_header_text(self.tr('''
        <center>
        <h1>Acquire a Tattoo</h1>
        <p style="color: #666">Only members of the Togashi Order can acquire tattoos</p>
        </center>
        '''))

        self.setWindowTitle(self.tr("L5RCM: Tattoo"))
        self.load_kiho()

    def load_kiho(self):
        for kiho in self.dstore.kihos:
            if kiho.type == 'tattoo' and not self.pc.has_kiho(kiho.id):
                self.cb_tattoo.addItem( kiho.name, kiho.id )

    def set_header_text(self, text):
        self.header.setText(text)

    def on_tattoo_change(self, idx):
        idx = self.cb_tattoo.currentIndex()
        itm = self.cb_tattoo.itemData(idx)

        kiho = dal.query.get_kiho(self.dstore, itm)
        if not kiho:
            return

        status_ok = self.tr("You are a member of the Togashi Order")
        status_ko = self.tr("You have to be a member of the Togashi Order")

        # save for later
        self.item = kiho

        is_eligible = ( self.pc.has_tag('dragon_togashi_tattooed_order') or
                        self.pc.has_tag('dragon_ob_hoshi_tsurui_zumi') or
                        self.pc.has_tag('dragon_ob_hitomi_kikage_zumi') )
        if not is_eligible:
            self.tx_pc_status.setText( u"""<span style="color:#A00">{0}</span>""".format(status_ko) )
        else:
            self.tx_pc_status.setText( u"""<span style="color:#0A0">{0}</span>""".format(status_ok) )

        self.tx_detail.setText(u"<p><em>{0}</em></p>".format(kiho.desc))
        self.bt_ok.setEnabled( is_eligible )

    def accept(self):
        # save item
        self.parent().do_buy_kiho(self.item)
        super(TattooDialog, self).accept()

