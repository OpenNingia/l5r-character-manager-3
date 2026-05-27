# -*- coding: utf-8 -*-
# Copyright (C) 2014-2026 Daniele Simonetti
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# Glue between QML actions (File menu, character mutations) and the
# Python api layer. Lives as a context property called ``appCtrl`` and
# exposes Q_INVOKABLE slots for every action the QML side needs to
# drive. Splitting AppController into per-area files is a follow-up if
# the surface keeps growing -- for now organised by `# --- section`
# comment blocks.

from pathlib import Path

from asq.initiators import query
from asq.selectors import a_
from qtpy.QtCore import QObject, Property, Signal, Slot
from qtpy.QtGui import QGuiApplication
from qtpy.QtWidgets import QFileDialog, QMessageBox

import l5r.api as api
import l5r.api.character
import l5r.api.character.schools
import l5r.api.data
import l5r.api.data.clans
import l5r.api.data.families
import l5r.api.data.schools
import l5r.models

from l5r.api.data import CMErrors
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
from l5r.util import log, names
from l5r.util.fsutil import get_app_file, get_app_icon_path


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


_FLAG_SETTERS = {
    "honor":  api.character.set_honor,
    "glory":  api.character.set_glory,
    "status": api.character.set_status,
    "taint":  api.character.set_taint,
    "infamy": api.character.set_infamy,
}


def _school_record(school_dal):
    """Serialise a school DAL row for QML consumption."""
    if school_dal is None:
        return None
    try:
        pack_name = school_dal.pack.display_name if school_dal.pack else ""
    except Exception:
        pack_name = ""
    return {
        "id":     school_dal.id,
        "name":   school_dal.name,
        "clanId": getattr(school_dal, "clanid", "") or "",
        "trait":  getattr(school_dal, "trait", "") or "",
        "book":   pack_name,
        "page":   int(getattr(school_dal, "page", 0) or 0),
    }


def _family_record(family_dal):
    if family_dal is None:
        return None
    try:
        pack_name = family_dal.pack.display_name if family_dal.pack else ""
    except Exception:
        pack_name = ""
    return {
        "id":     family_dal.id,
        "name":   family_dal.name,
        "clanId": getattr(family_dal, "clanid", "") or "",
        "trait":  getattr(family_dal, "trait", "") or "",
        "book":   pack_name,
        "page":   int(getattr(family_dal, "page", 0) or 0),
    }


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

    # --- notes / personal info ---------------------------------------

    @Slot(str)
    def setNotes(self, html):
        api.character.set_notes(html)

    @Slot(str, str)
    def setPersonalInfoField(self, key, value):
        api.character.set_personal_info(key, value)

    # --- identity ----------------------------------------------------

    @Slot(str)
    def generateName(self, gender):
        """Pick a random male/female name and apply it to the model."""
        src = "male.txt" if gender == "male" else "female.txt"
        name = names.get_random_name(get_app_file(src))
        api.character.set_name(name)

    @Slot(str)
    def setName(self, value):
        api.character.set_name(value or "")

    @Slot(int)
    def setExpLimit(self, value):
        api.character.set_exp_limit(int(value))

    # --- traits / void -----------------------------------------------

    @Slot(str)
    def increaseTrait(self, trait_name):
        """Buy the next rank in a trait. Surfaces a QMessageBox if the
        character is short on XP. TODO: replace the message box with a
        proper QML notification surface (see project memory)."""
        idx = l5r.models.chmodel.attrib_from_name(trait_name)
        if idx < 0:
            log.api.warning(u"QML UI: unknown trait %r", trait_name)
            return
        res = api.character.purchase_trait_rank(idx)
        if res == CMErrors.NOT_ENOUGH_XP:
            self._show_not_enough_xp()
            return
        api.character.notify_character_refreshed()

    @Slot()
    def increaseVoid(self):
        res = api.character.purchase_void_rank()
        if res == CMErrors.NOT_ENOUGH_XP:
            self._show_not_enough_xp()
            return
        api.character.notify_character_refreshed()

    @Slot(int)
    def setVoidPoints(self, value):
        api.character.set_void_points(int(value))

    def _show_not_enough_xp(self):
        # Stopgap: QMessageBox bubbled out of the QML window. Slated for
        # replacement with a QML toast/dialog -- see the
        # `project-qmlui-msgbox-refactor` memory.
        QMessageBox.warning(
            None,
            self.tr("Not enough XP"),
            self.tr("You don't have enough experience points "
                    "to complete this purchase."),
        )

    # --- social/spiritual flags --------------------------------------

    @Slot(str, float)
    def setFlag(self, flag_name, value):
        setter = _FLAG_SETTERS.get(flag_name)
        if setter is None:
            log.api.warning(u"QML UI: unknown flag %r", flag_name)
            return
        setter(float(value))

    # --- health ------------------------------------------------------

    @Slot(int)
    def setHealthMultiplier(self, value):
        try:
            api.character.set_health_multiplier(int(value))
        except ValueError:
            log.api.warning(u"QML UI: invalid health multiplier %r", value)
            return
        api.character.notify_character_refreshed()

    # --- clan / family / school choosers -----------------------------

    @Slot(result="QVariantList")
    def clansList(self):
        return [{"id": c.id, "name": c.name}
                for c in query(api.data.clans.all()).order_by(a_("name"))]

    @Slot(str, result="QVariantList")
    def familiesForClan(self, clan_id):
        all_families = api.data.families.get_all()
        if clan_id:
            filtered = query(all_families).where(lambda x: x.clanid == clan_id)
        else:
            filtered = query(all_families)
        return [_family_record(f) for f in filtered.order_by(a_("name"))]

    @Slot(str, result="QVariantList")
    def basicSchoolsForClan(self, clan_id):
        base = api.data.schools.get_base()
        if clan_id:
            base = [s for s in base if s.clanid == clan_id]
        return [_school_record(s)
                for s in sorted(base, key=lambda x: x.name)]

    @Slot(str, result="QVariantList")
    def rank1PathsForClan(self, clan_id):
        paths = api.data.schools.get_paths_with_rank(1)
        if clan_id:
            paths = [s for s in paths if s.clanid == clan_id]
        return [_school_record(s)
                for s in sorted(paths, key=lambda x: x.name)]

    @Slot(result=str)
    def currentFamilyId(self):
        return api.character.get_family() or ""

    @Slot(result=str)
    def currentClanId(self):
        return api.character.get_clan() or ""

    @Slot(result=str)
    def currentFirstSchoolId(self):
        return api.character.schools.get_first() or ""

    @Slot(result=bool)
    def canEditOrigin(self):
        """Origin (family/school) edits are blocked once XP has been
        spent -- mirrors the QWidget side's disabled edit buttons."""
        pc = api.character.model()
        return bool(pc and len(pc.advans) == 0)

    @Slot(str)
    def setFamily(self, family_id):
        if not family_id:
            return
        api.character.set_family(family_id)
        api.character.notify_character_refreshed()

    @Slot(str, str)
    def setFirstSchool(self, school_id, path_id):
        if not school_id:
            return
        if path_id:
            api.character.schools.set_first_with_path(school_id, path_id)
        else:
            api.character.schools.set_first(school_id)
        api.character.set_dirty_flag(True)
        api.character.notify_character_refreshed()

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
