# -*- coding: utf-8 -*-
# Copyright (C) 2014-2026 Daniele Simonetti
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# Tab 6 — Advancements history table. Extracted from l5r/main.py during
# the Phase 4 split — no behaviour changes.

from qtpy import QtCore, QtWidgets

import l5r.models

from l5r.util import log
from l5r.util.settings import L5RCMSettings


class AdvancementsSink(QtCore.QObject):
    """Qt slots for the Tab 6 Advancements panel + matching menu actions."""

    def __init__(self, window):
        super().__init__(window)
        self.window = window

    def reset_adv(self):
        window = self.window
        window.pc.advans = []
        window.update_from_model()

    def refund_last_adv(self):
        """pops last advancement"""
        window = self.window
        if len(window.pc.advans) > 0:
            adv = window.pc.advans.pop()
            log.ui.info(u"removed advancement: %s", adv.desc)
            window.update_from_model()

    def _warn_about_refund(self):
        window = self.window
        settings = L5RCMSettings()

        if not settings.app.warn_about_refund:
            return True

        msgBox = QtWidgets.QMessageBox(window)
        msgBox.setWindowTitle('L5R: CM')
        msgBox.setText(self.tr("Advancements refund."))
        msgBox.setInformativeText(self.tr(
            "If this advancement is required from other ones\n"
            "removing it might lean to incoherences in your character.\n"
            "Continue anyway?"))

        do_not_prompt_again = QtWidgets.QCheckBox(
            self.tr("Do not prompt again"), msgBox)
        # PREVENT MSGBOX TO CLOSE ON CLICK
        do_not_prompt_again.blockSignals(True)
        msgBox.addButton(QtWidgets.QMessageBox.Yes)
        msgBox.addButton(QtWidgets.QMessageBox.No)
        msgBox.addButton(do_not_prompt_again, QtWidgets.QMessageBox.ActionRole)
        msgBox.setDefaultButton(QtWidgets.QMessageBox.No)
        result = msgBox.exec_()
        if do_not_prompt_again.checkState() == QtCore.Qt.Checked:
            settings.app.warn_about_refund = False
        return result == QtWidgets.QMessageBox.Yes

    def refund_advancement(self):
        """refund the specified advancement"""
        window = self.window

        adv_idx = (len(window.pc.advans) -
                   window.adv_view.selectionModel().currentIndex().row() - 1)

        log.ui.debug(u"refund_advancement at index: %d", adv_idx)

        if adv_idx >= len(window.pc.advans) or adv_idx < 0:
            return self.refund_last_adv()

        if self._warn_about_refund():
            adv = window.pc.advans[adv_idx]
            if adv is not None:
                log.ui.info(u"removed advancement: %s", adv.desc)
                del window.pc.advans[adv_idx]
                window.update_from_model()
            return True
        return False


class AdvancementsTabMixin:
    """Tab 6: rank-advancement history with a Refund button."""

    def build_ui_page_6(self):
        mfr = QtWidgets.QFrame(self)
        vbox = QtWidgets.QVBoxLayout(mfr)

        fr_ = QtWidgets.QFrame(self)
        fr_h = QtWidgets.QHBoxLayout(fr_)
        fr_h.setContentsMargins(0, 0, 0, 0)
        fr_h.addWidget(
            QtWidgets.QLabel(self.tr("""<p><i>Select the advancement to refund and hit the button</i></p>"""), self))
        bt_refund_adv = QtWidgets.QPushButton(self.tr("Refund"), self)
        bt_refund_adv.setSizePolicy(QtWidgets.QSizePolicy.Maximum,
                                    QtWidgets.QSizePolicy.Preferred)
        bt_refund_adv.clicked.connect(self.advancements_sink.refund_advancement)
        fr_h.addWidget(bt_refund_adv)
        vbox.addWidget(fr_)

        self.adv_view_model = l5r.models.AdvancementViewModel(self)
        view = QtWidgets.QTableView(self)
        view.setSortingEnabled(False)
        view.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.Interactive)
        view.horizontalHeader().setStretchLastSection(True)
        view.horizontalHeader().setCascadingSectionResizes(True)

        self.table_views.append(view)
        view.setModel(self.adv_view_model)
        vbox.addWidget(view)

        self.adv_view = view

        self.tabs.addTab(mfr, self.tr("Advancements"))
