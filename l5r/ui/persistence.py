# -*- coding: utf-8 -*-
# Copyright (C) 2014-2026 Daniele Simonetti
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# Character file load/save dialogs and the create-new-character entry
# point. Extracted from l5r/main.py during the Phase 4 split — no
# behaviour changes. Expects self.sink1, self.pc, self.save_path,
# self.tx_pc_notes, self.pers_info_widgets, self.tx_pc_name plus
# self.warn_about_missing_books and self.update_from_model from other
# mixins / the host class.

import os

from qtpy import QtWidgets

import l5r.api as api
import l5r.api.character
import l5r.api.character.books

from l5r.l5rcmcore.qtsignalsutils import QtSignalLock
from l5r.util import log
from l5r.util.settings import L5RCMSettings


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
        self.sink1.new_character()
        self.pc.unsaved = False
