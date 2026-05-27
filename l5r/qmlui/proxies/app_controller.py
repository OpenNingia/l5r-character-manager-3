# -*- coding: utf-8 -*-
# Copyright (C) 2014-2026 Daniele Simonetti
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# Glue between QML actions (File menu) and the Python API. Lives as a
# context property called ``appCtrl`` and exposes Q_INVOKABLE slots for
# every action the QML side needs to drive.

from pathlib import Path

from qtpy.QtCore import QObject, Property, Signal, Slot
from qtpy.QtGui import QGuiApplication
from qtpy.QtWidgets import QFileDialog

import l5r.api as api
import l5r.api.character
import l5r.models

from l5r.l5rcmcore import (
    COMPANY_HOME_PAGE,
    APP_DESC,
    APP_VERSION,
    AUTHOR_NAME,
    BUGTRAQ_LINK,
    DATA_PACKS_DOWNLOADS_LINK,
    DB_VERSION,
    L5R_RPG_HOME_PAGE,
    PROJECT_PAGE_LINK,
    PROJECT_PAGE_NAME,
)
from l5r.util import log
from l5r.util.fsutil import get_app_icon_path


_TAB_DEFS = [
    ("pc_info",       "Character",     "✴"),  # 8-pointed star -- profile
    ("advancements",  "Advancements",  "★"),  # filled star
    ("skills",        "Skills",        "◆"),  # filled diamond
    ("perks",         "Merits/Flaws",  "◉"),  # fisheye -- yin/yang feel
    ("techniques",    "Techniques",    "☯"),  # taijitu
    ("powers",        "Powers",        "✨"),  # sparkles
    ("modifiers",     "Modifiers",     "✚"),  # heavy greek cross
    ("weapons",       "Weapons",       "⚔"),  # crossed swords
    ("equipment",     "Equipment",     "⚺"),  # atom
    ("notes",         "Notes",         "✎"),  # lower right pencil
    ("settings",      "Settings",      "⚙"),  # gear
    ("about",         "About",         "ⓘ"),  # circled i
]


class AppController(QObject):
    """Top-level controller exposed to QML."""

    saveRequested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._save_path = ""

    # --- tab list -----------------------------------------------------

    @Property("QVariantList", constant=True)
    def tabs(self):
        return [
            {"id": tid, "title": self.tr(title), "icon": icon}
            for tid, title, icon in _TAB_DEFS
        ]

    # --- about page ---------------------------------------------------

    @Property("QVariantMap", constant=True)
    def aboutInfo(self):
        icon_path = get_app_icon_path((64, 64))
        return {
            "appDesc": APP_DESC,
            "version": APP_VERSION,
            "projectPage": PROJECT_PAGE_LINK,
            "projectPageName": PROJECT_PAGE_NAME,
            "bugtraq": BUGTRAQ_LINK,
            "l5rRpgHome": L5R_RPG_HOME_PAGE,
            "companyHome": COMPANY_HOME_PAGE,
            "dataPacks": DATA_PACKS_DOWNLOADS_LINK,
            "author": AUTHOR_NAME,
            "iconUrl": Path(icon_path).as_uri() if icon_path else "",
        }

    # --- file menu ----------------------------------------------------

    @Slot()
    def fileNew(self):
        log.app.info(u"QML UI: File > New")
        self._save_path = ""
        api.character.new()
        api.character.set_dirty_flag(False)

    @Slot()
    def fileOpenDialog(self):
        path, _ = QFileDialog.getOpenFileName(
            None,
            self.tr("Open Character"),
            "",
            self.tr("L5R Character (*.l5r);;All Files (*)"),
        )
        if path:
            self.fileOpen(path)

    @Slot(str)
    def fileOpen(self, path):
        log.app.info(u"QML UI: File > Open: %s", path)
        pc = l5r.models.AdvancedPcModel()
        if not pc.load_from(path):
            log.app.warning(u"QML UI: failed to load character: %s", path)
            return
        api.character.set_model(pc)
        api.character.set_dirty_flag(False)
        self._save_path = path

    @Slot()
    def fileSave(self):
        if not self._save_path:
            self.fileSaveAs()
            return
        self._save(self._save_path)

    @Slot()
    def fileSaveAs(self):
        path, _ = QFileDialog.getSaveFileName(
            None,
            self.tr("Save Character"),
            "",
            self.tr("L5R Character (*.l5r);;All Files (*)"),
        )
        if path:
            if not path.lower().endswith(".l5r"):
                path += ".l5r"
            self._save(path)

    def _save(self, path):
        pc = api.character.model()
        if pc is None:
            return
        pc.version = DB_VERSION
        if pc.save_to(path):
            self._save_path = path
            api.character.set_dirty_flag(False)
            log.app.info(u"QML UI: saved character to %s", path)
        else:
            log.app.warning(u"QML UI: failed to save character to %s", path)

    @Slot()
    def fileQuit(self):
        QGuiApplication.instance().quit()

    # --- startup hooks ------------------------------------------------

    def apply_startup(self, action, path):
        """Apply the CLI-resolved action after the QML window is up."""
        if action == "open" and path:
            self.fileOpen(path)
        elif action == "import" and path:
            _import_data_pack(path)
            QGuiApplication.instance().quit()


def _import_data_pack(data_pack_file):
    """Headless datapack import; mirrors L5RCMCore.import_data_pack
    without the QWidget advise_error calls."""
    import os
    import l5rdal as dal
    import l5rdal.dataimport
    from l5r.l5rcmcore import APP_VERSION
    from l5r.util import osutil

    try:
        dal.dataimport.CM_VERSION = APP_VERSION
        pack = dal.dataimport.DataPack(data_pack_file)
        if not pack.good():
            log.app.warning(u"QML UI: invalid data pack: %s", data_pack_file)
            return False
        dest = osutil.get_user_data_path()
        if pack.id == 'core':
            dest = os.path.join(dest, 'core.data')
        elif pack.language:
            dest = os.path.join(dest, 'data.' + pack.language)
        else:
            dest = os.path.join(dest, 'data')
        pack.export_to(dest)
        log.app.info(u"QML UI: imported data pack to %s", dest)
        return True
    except Exception:
        log.app.exception(u"QML UI: failed to import data pack")
        return False
