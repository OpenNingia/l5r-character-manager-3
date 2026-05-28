# -*- coding: utf-8 -*-
# Copyright (C) 2014-2026 Daniele Simonetti
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# Character file load/save dialogs and the create-new-character entry
# point, plus the matching Qt-slot endpoints in PersistenceSink.
# Extracted from l5r/main.py / l5r/sinks/sink_1.py during Phase 4 / 4.5.

import os

from qtpy import QtCore, QtWidgets

from pyqtwaitingspinner import SpinnerParameters, WaitingSpinner

import l5r.api as api
import l5r.api.character
import l5r.api.character.books
import l5r.dialogs as dialogs

from l5r.l5rcmcore import DB_VERSION
from l5r.l5rcmcore.qtsignalsutils import QtSignalLock
from l5r.util import log
from l5r.util.settings import L5RCMSettings
from l5r.util.worker import Worker


class PersistenceSink(QtCore.QObject):
    """Qt signal/slot endpoints for character-file persistence and PDF export.

    Owned by L5RMain as ``self.persistence_sink``. Holds its own
    QThreadPool for the PDF export workers.
    """

    def __init__(self, window):
        super().__init__(window)
        self.window = window
        self.thread_pool = QtCore.QThreadPool()
        self.thread_pool.setMaxThreadCount(2)

    def _make_spinner(self):
        spin_pars = SpinnerParameters(disable_parent_when_spinning=True)
        spinner = WaitingSpinner(self.window.centralWidget(), spin_pars)
        return spinner

    def _on_pdf_export_error(self, err):
        exctype, value, tb = err
        log.app.error("PDF export failed: %s: %s\n%s", exctype.__name__, value, tb)
        self.window.advise_error(self.tr("Cannot save pdf sheet."))

    def new_character(self):
        window = self.window
        window.save_path = ''

        # create new character
        api.character.new()

        # backward compatibility, assign to form
        window.pc = api.character.model()

        window.tx_pc_notes.set_content('')
        window.update_from_model()

    def load_character(self):
        window = self.window
        path = window.select_load_path()
        window.load_character_from(path)

        # TODO. let the API handle the loading
        api.character.set_model(window.pc)

    def save_character(self):
        window = self.window
        if not window.save_path or not os.path.exists(window.save_path):
            window.save_path = window.select_save_path()

        if window.save_path:
            window.pc.version = DB_VERSION
            window.pc.extra_notes = window.tx_pc_notes.get_content()

            # set book dependencies
            api.character.books.set_dependencies()

            log.app.info("saving character file: %s", window.save_path)
            window.pc.save_to(window.save_path)

    def export_character_as_pdf(self):
        window = self.window

        file_ = window.select_export_file(".pdf")
        if not file_:
            return

        spinner = self._make_spinner()

        worker = Worker(window.export_as_pdf, file_)
        worker.signals.result.connect(lambda x: window.open_pdf_file_as_shell(file_))
        worker.signals.finished.connect(lambda: spinner.stop())
        worker.signals.error.connect(self._on_pdf_export_error)

        self.thread_pool.start(worker)
        spinner.start()

    def show_npc_export_dialog(self):
        window = self.window
        dlg = dialogs.NpcExportDialog(window)
        if dlg.exec_() != QtWidgets.QDialog.Accepted:
            return

        file_ = window.select_export_file(".pdf")
        if not file_:
            return

        spinner = self._make_spinner()

        worker = Worker(window.export_npc_characters, dlg.paths, file_)
        worker.signals.result.connect(lambda x: window.open_pdf_file_as_shell(file_))
        worker.signals.finished.connect(lambda: spinner.stop())
        worker.signals.error.connect(self._on_pdf_export_error)

        self.thread_pool.start(worker)
        spinner.start()


class PersistenceMixin:
    """Character file load/save dialogs and new-character creation."""

    def load_character_from(self, path):

        with QtSignalLock(self.pers_info_widgets + [self.tx_pc_name]):

            if not self.pc:
                self.create_new_character()

            if self.pc.load_from(path):
                self.save_path = path

                if not api.character.books.fulfills_dependencies():
                    # warn about missing dependencies
                    self.warn_about_missing_books()

                    # immediately create a new character
                    self.create_new_character()
                    return False

                log.app.info('successfully loaded character from {0}'.format(self.save_path))

                self.tx_pc_notes.set_content(self.pc.extra_notes)
                self.update_from_model()
            else:
                log.app.error('character load failure')

    def select_save_path(self):
        settings = L5RCMSettings()
        last_dir = settings.app.last_open_dir
        char_name = self.get_character_full_name()
        proposed = os.path.join(last_dir, char_name)

        fileName = QtWidgets.QFileDialog.getSaveFileName(
            self,
            self.tr("Save Character"),
            proposed,
            self.tr("L5R Character files (*.l5r)"))

        # user pressed cancel or didn't enter a name
        if not fileName:
            return None

        # on pyqt5 it returns a tuple (fname, filter)
        if type(fileName) is tuple:
            fileName = fileName[0]

        if fileName:
            settings.app.last_open_dir = os.path.dirname(fileName)

        if fileName.endswith('.l5r'):
            return fileName
        return fileName + '.l5r'

    def select_load_path(self):
        settings = L5RCMSettings()
        last_dir = settings.app.last_open_dir
        fileName = QtWidgets.QFileDialog.getOpenFileName(
            self,
            self.tr("Load Character"),
            last_dir,
            self.tr("L5R Character files (*.l5r)"))

        # user pressed cancel or didn't enter a name
        if not fileName:
            return None

        # on pyqt5 it returns a tuple (fname, filter)
        if type(fileName) is tuple:
            fileName = fileName[0]

        if fileName:
            settings.app.last_open_dir = os.path.dirname(fileName)
        return fileName

    def select_export_file(self, file_ext='.txt'):
        supported_filters = [self.tr("PDF Files(*.pdf)")]

        settings = L5RCMSettings()
        last_dir = settings.app.last_open_dir
        char_name = self.get_character_full_name()
        proposed = os.path.join(last_dir, char_name)

        fileName = QtWidgets.QFileDialog.getSaveFileName(
            self,
            self.tr("Export Character"),
            proposed,
            ";;".join(supported_filters))

        # user pressed cancel or didn't enter a name
        if not fileName:
            return None

        # on pyqt5 it returns a tuple (fname, filter)
        if type(fileName) is tuple:
            fileName = fileName[0]

        if fileName:
            settings.app.last_open_dir = os.path.dirname(fileName)

        if fileName.endswith(file_ext):
            return fileName
        return fileName + file_ext

    def select_import_data_pack(self):
        supported_filters = [self.tr("L5R:CM Data Pack(*.l5rcmpack *.zip)"),
                             self.tr("Zip Archive(*.zip)")]

        settings = L5RCMSettings()
        last_data_dir = settings.app.last_open_data_dir

        files = QtWidgets.QFileDialog.getOpenFileNames(
            self,
            self.tr("Load data pack"),
            last_data_dir,
            ";;".join(supported_filters))

        if type(files) is tuple:
            files = files[0]

        if not files:
            return None

        if files[0]:
            settings.app.last_open_data_dir = os.path.dirname(files[0])

        return files

    def create_new_character(self):
        self.persistence_sink.new_character()
        self.pc.unsaved = False
