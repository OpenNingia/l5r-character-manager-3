# -*- coding: utf-8 -*-
# Copyright (C) 2014-2026 Daniele Simonetti
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# Modal message-box helpers used by the main window. Extracted from
# l5r/main.py during the Phase 4 split — no behaviour changes.
# Mixed into L5RMain via class L5RMain(L5RCMCore, ..., AdviseMixin).

from qtpy import QtCore, QtWidgets

import l5r.api.character.books
from l5r.util.settings import L5RCMSettings


class AdviseMixin:
    """Modal advisory / question dialogs (Qt message boxes)."""

    def advise_successfull_import(self, count):
        settings = L5RCMSettings()
        if not settings.app.advise_successful_import:
            return
        msgBox = QtWidgets.QMessageBox(self)
        msgBox.setWindowTitle('L5R: CM')
        msgBox.setText(
            self.tr("{0} data pack(s) imported succesfully.").format(count))
        do_not_prompt_again = QtWidgets.QCheckBox(
            self.tr("Do not prompt again"), msgBox)
        # PREVENT MSGBOX TO CLOSE ON CLICK
        do_not_prompt_again.blockSignals(True)
        msgBox.addButton(QtWidgets.QMessageBox.Ok)
        msgBox.addButton(do_not_prompt_again, QtWidgets.QMessageBox.ActionRole)
        msgBox.setDefaultButton(QtWidgets.QMessageBox.Ok)
        msgBox.setIcon(QtWidgets.QMessageBox.Information)
        msgBox.exec_()
        if do_not_prompt_again.checkState() == QtCore.Qt.Checked:
            settings.app.advise_successful_import = False

    def advise_error(self, message, dtl=None):
        msgBox = QtWidgets.QMessageBox(self)
        msgBox.setWindowTitle('L5R: CM')
        msgBox.setTextFormat(QtCore.Qt.RichText)
        msgBox.setText(message)
        if dtl:
            msgBox.setInformativeText(dtl)
        msgBox.setIcon(QtWidgets.QMessageBox.Critical)
        msgBox.setDefaultButton(QtWidgets.QMessageBox.Ok)
        msgBox.exec_()

    def advise_warning(self, message, dtl=None):
        msgBox = QtWidgets.QMessageBox(self)
        msgBox.setTextFormat(QtCore.Qt.RichText)
        msgBox.setWindowTitle('L5R: CM')
        msgBox.setText(message)
        if dtl:
            msgBox.setInformativeText(dtl)
        msgBox.setIcon(QtWidgets.QMessageBox.Warning)
        msgBox.setDefaultButton(QtWidgets.QMessageBox.Ok)
        msgBox.exec_()

    def ask_warning(self, message, dtl=None):
        msgBox = QtWidgets.QMessageBox(self)
        msgBox.setTextFormat(QtCore.Qt.RichText)
        msgBox.setWindowTitle('L5R: CM')
        msgBox.setText(message)
        if dtl:
            msgBox.setInformativeText(dtl)
        msgBox.setIcon(QtWidgets.QMessageBox.Warning)
        msgBox.addButton(QtWidgets.QMessageBox.Ok)
        msgBox.addButton(QtWidgets.QMessageBox.Cancel)
        msgBox.setDefaultButton(QtWidgets.QMessageBox.Cancel)
        return msgBox.exec_() == QtWidgets.QMessageBox.Ok

    def ask_to_save(self):
        msgBox = QtWidgets.QMessageBox(self)
        msgBox.setWindowTitle('L5R: CM')
        msgBox.setText(self.tr("The character has been modified."))
        msgBox.setInformativeText(self.tr("Do you want to save your changes?"))
        msgBox.addButton(QtWidgets.QMessageBox.Save)
        msgBox.addButton(QtWidgets.QMessageBox.Discard)
        msgBox.addButton(QtWidgets.QMessageBox.Cancel)
        msgBox.setDefaultButton(QtWidgets.QMessageBox.Save)
        return msgBox.exec_()

    def ask_to_upgrade(self, target_version):
        msgBox = QtWidgets.QMessageBox(self)
        msgBox.setWindowTitle('L5R: CM')
        msgBox.setText(
            self.tr("L5R: CM v%s is available for download.") % target_version)
        msgBox.setInformativeText(
            self.tr("Do you want to open the download page?"))
        msgBox.addButton(QtWidgets.QMessageBox.Yes)
        msgBox.addButton(QtWidgets.QMessageBox.No)
        msgBox.setDefaultButton(QtWidgets.QMessageBox.No)
        return msgBox.exec_()

    def not_enough_xp_advise(self, parent=None):
        if parent is None:
            parent = self
        QtWidgets.QMessageBox.warning(parent, self.tr("Not enough XP"),
                                      self.tr("Cannot purchase.\nYou've reached the XP Limit."))
        return

    def warn_about_missing_books(self):
        text = self.tr("<h3>Missing books</h3>")
        text += self.tr("<p>To load this character you need this additional books:</p>")
        dtl_text = u"<ul>"
        for b in l5r.api.character.books.get_missing_dependencies():
            dtl_text += "<li>{book_nm} &gt;= {book_ver}</li>".format(
                book_nm=b.name, book_ver=b.version)
        dtl_text += u"</ul>"

        self.advise_error(text, dtl_text)
