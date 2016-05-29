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

import l5r.models as models
import l5r.widgets as widgets
import l5r.api as api
import l5r.api.rules
import l5r.api.data
import l5r.api.data.skills
from PyQt5 import QtCore, QtGui, QtWidgets


class ModifierDialog(QtWidgets.QDialog):

    # title bar
    header = None
    # frame layout
    vbox_lo = None
    # buttons
    bt_ok = None
    # controls
    cb_modifier = None
    tx_value = None
    tx_detail = None
    tx_reason = None

    def __init__(self, pc, parent=None):
        super(ModifierDialog, self).__init__(parent)
        self.pc = pc
        self.item = None

        self.build_ui()
        self.connect_signals()
        self.setup()

    def build_ui(self):
        self.vbox_lo = QtWidgets.QVBoxLayout(self)
        self.bt_ok = QtWidgets.QPushButton(self.tr('Save'), self)
        self.header = QtWidgets.QLabel(self)
        center_fr = QtWidgets.QFrame(self)
        center_fr.setFrameStyle(QtWidgets.QFrame.Sunken)
        cfr_fbox = QtWidgets.QFormLayout(center_fr)

        # bottom bar
        bottom_bar = QtWidgets.QFrame(self)
        hbox = QtWidgets.QHBoxLayout(bottom_bar)
        hbox.addStretch()
        hbox.addWidget(self.bt_ok)

        self.cb_modifier = QtWidgets.QComboBox(self)
        self.tx_detail = QtWidgets.QLineEdit(self)
        self.tx_value = QtWidgets.QLineEdit(self)
        self.tx_reason = QtWidgets.QLineEdit(self)

        cfr_fbox.addRow(self.tr("Modifier"), self.cb_modifier)
        cfr_fbox.addRow(self.tr("Detail"), self.tx_detail)
        cfr_fbox.addRow(self.tr("Value"), self.tx_value)
        cfr_fbox.addRow(self.tr("Reason"), self.tx_reason)

        cfr_fbox.setContentsMargins(160, 20, 160, 20)

        self.vbox_lo.addWidget(self.header)
        self.vbox_lo.addWidget(center_fr)
        self.vbox_lo.addWidget(bottom_bar)

        self.resize(600, 300)

    def connect_signals(self):
        self.bt_ok.clicked.connect(self.accept)
        self.cb_modifier.currentIndexChanged.connect(self.on_modifier_change)

    def setup(self):
        self.set_header_text(self.tr('''
        <center>
        <h1>Add or Edit a modifier</h1>
        <p style="color: #666">Modifiers represent the way your character performs better in some contexts</p>
        </center>
        '''))

        self.setWindowTitle(self.tr("L5RCM: Modifiers"))

        for i_key, i_value in models.MOD_TYPES.items():
            if i_key == 'none':
                continue
            self.cb_modifier.addItem(i_value, i_key)

    def set_modifier(self, item):
        '''
        :param ModifierModel item:
        '''
        if item:
            for i in range(self.cb_modifier.count()):
                key = self.cb_modifier.itemData(i)
                if key == item.type:
                    self.cb_modifier.setCurrentIndex(i)

            self.tx_reason.setText(item.reason)
            self.tx_value.setText(api.rules.format_rtk_t(item.value))
            self.tx_detail.setText(item.dtl or (models.MOD_DTLS[item.type][1] if item.type in models.MOD_DTLS else None))
        else:
            assert False, 'We should clean-up everything if accepting item == None.'

        self.item = item

    def set_header_text(self, text):
        self.header.setText(text)

    def on_modifier_change(self, idx):
        idx = self.cb_modifier.currentIndex()
        mod = self.cb_modifier.itemData(idx)

        def __skill_completer():
            all_skills = []
            for t in api.data.skills.all():
                all_skills.append(t.name)
            cmp = QtWidgets.QCompleter(all_skills)
            # cmp.setCompletionMode(QtWidgets.QCompleter.InlineCompletion)
            return cmp

        def __weap_completer():
            pc = self.pc
            aweaps = []
            for w in pc.get_weapons():
                aweaps.append(w.name)
            cmp = QtWidgets.QCompleter(aweaps)
            # cmp.setCompletionMode(QtWidgets.QCompleter.InlineCompletion)
            return cmp

        def __trait_completer():
            traits = [x.text for x in api.data.model().traits]
            cmp = QtWidgets.QCompleter(traits)
            # cmp.setCompletionMode(QtWidgets.QCompleter.InlineCompletion)
            return cmp

        def __ring_completer():
            rings = [x.text for x in api.data.model().rings]
            cmp = QtWidgets.QCompleter(rings)
            # cmp.setCompletionMode(QtWidgets.QCompleter.InlineCompletion)
            return cmp

        dtl = models.MOD_DTLS[mod] if mod else 'none'

        # set detail completer

        if dtl[0] == 'skill':
            self.tx_detail.setPlaceholderText(self.tr("Type skill name"))
            self.tx_detail.setCompleter(__skill_completer())
            self.tx_detail.setEnabled(True)
        elif dtl[0] == 'aweap':
            self.tx_detail.setPlaceholderText(self.tr("Type weapon name"))
            self.tx_detail.setCompleter(__weap_completer())
            self.tx_detail.setEnabled(True)
        elif dtl[0] == 'trait':
            self.tx_detail.setPlaceholderText(self.tr("Type trait name"))
            self.tx_detail.setCompleter(__trait_completer())
            self.tx_detail.setEnabled(True)
        elif dtl[0] == 'ring':
            self.tx_detail.setPlaceholderText(self.tr("Type ring name"))
            self.tx_detail.setCompleter(__ring_completer())
            self.tx_detail.setEnabled(True)
        else:
            self.tx_detail.setPlaceholderText("")
            self.tx_detail.setText("")
            self.tx_detail.setEnabled(False)

    def accept(self):
        # save item
        self.item.type = self.cb_modifier.itemData(
            self.cb_modifier.currentIndex())
        self.item.reason = self.tx_reason.text()
        self.item.dtl = self.tx_detail.text()
        self.item.value = api.rules.parse_rtk_with_bonus(self.tx_value.text())
        super(ModifierDialog, self).accept()
