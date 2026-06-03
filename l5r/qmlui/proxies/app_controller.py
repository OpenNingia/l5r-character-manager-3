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

import os
from pathlib import Path

from asq.initiators import query
from asq.selectors import a_
from qtpy.QtCore import QObject, Property, QT_TRANSLATE_NOOP, QThreadPool, QUrl, Signal, Slot
from qtpy.QtGui import QDesktopServices, QGuiApplication
from qtpy.QtWidgets import QFileDialog, QMessageBox

import l5r.api as api
import l5r.api.character
import l5r.api.character.merits
import l5r.api.character.powers
import l5r.api.character.rankadv
import l5r.api.character.schools
import l5r.api.character.skills
import l5r.api.character.spells
import l5r.api.character.weapons
import l5r.api.data
import l5r.api.data.clans
import l5r.api.data.families
import l5r.api.data.flaws
import l5r.api.data.merits
import l5r.api.data.outfit
import l5r.api.data.schools
import l5r.api.data.skills
import l5r.api.data.spells
import l5r.api.rules
import l5r.api.signals
import l5r.models
import l5r.models.advances

from l5r.api.data import CMErrors
from l5r.l5rcmcore import (
    COMPANY_HOME_PAGE,
    APP_DESC,
    APP_VERSION,
    AUTHOR_NAME,
    BUGTRAQ_LINK,
    DATA_PACKS_DOWNLOADS_LINK,
    DB_VERSION,
    DONATE_LINK,
    L5R_RPG_HOME_PAGE,
    PROJECT_PAGE_LINK,
    PROJECT_PAGE_NAME,
)
from l5r.qmlui.proxies.pc import opportunities
from l5r.exporters.model_form import ModelExportForm
from l5r.util import log, names
from l5r.util.fsutil import get_app_file, get_app_icon_path
from l5r.util.settings import L5RCMSettings
from l5r.util.worker import Worker


# Single-kanji glyphs lean on the system CJK font (no bundled face) --
# the L5R setting is fantasy-Japan, so a kanji column reads as part of
# the document rather than UI chrome. Each pick is one kanji that maps
# to the tab's concept by L5R-idiomatic reading (ryū for techniques,
# mon for about/clan crest, etc.). On a host with no CJK font installed
# the fallback box is ugly -- that's the known trade vs. the previous
# universal Unicode symbols.
#
# Titles are wrapped in QT_TRANSLATE_NOOP rather than left as bare
# literals: the `tabs` property translates them at runtime with
# self.tr(title), but `title` is a variable there, so pylupdate6 can't
# see the source text through that call. QT_TRANSLATE_NOOP marks each
# literal for extraction into the "AppController" context (it returns the
# string unchanged at runtime) -- the same context self.tr() resolves
# against, so the harvested translation is the one that gets used. Keep
# the context string in sync with this class's name.
_TAB_DEFS = [
    ("pc_info",       QT_TRANSLATE_NOOP("AppController", "Character"),    "侍"),  # samurai
    ("skills",        QT_TRANSLATE_NOOP("AppController", "Skills"),       "技"),  # gi -- technique / skill
    ("perks",         QT_TRANSLATE_NOOP("AppController", "Merits/Flaws"), "縁"),  # en -- bond / karma (neutral)
    ("techniques",    QT_TRANSLATE_NOOP("AppController", "Techniques"),   "流"),  # ryū -- school / style
    ("spells",        QT_TRANSLATE_NOOP("AppController", "Spells"),       "呪"),  # ju -- spell / incantation
    ("kata",          QT_TRANSLATE_NOOP("AppController", "Kata"),         "型"),  # kata -- form
    ("kiho",          QT_TRANSLATE_NOOP("AppController", "Kiho"),         "気"),  # ki -- spirit / breath
    ("tattoo",        QT_TRANSLATE_NOOP("AppController", "Tattoos"),      "彫"),  # chō -- carve / engrave (irezumi)
    ("advancements",  QT_TRANSLATE_NOOP("AppController", "Advancements"), "道"),  # dō -- way / path
    ("weapons",       QT_TRANSLATE_NOOP("AppController", "Weapons"),      "刀"),  # tō -- katana / blade
    ("misc",          QT_TRANSLATE_NOOP("AppController", "Miscellanea"),  "雑"),  # zatsu -- miscellaneous (modifiers + equipment)
    ("notes",         QT_TRANSLATE_NOOP("AppController", "Notes"),        "記"),  # ki -- record / note
    ("settings",      QT_TRANSLATE_NOOP("AppController", "Settings"),     "設"),  # setsu -- setup
    ("about",         QT_TRANSLATE_NOOP("AppController", "About"),        "紋"),  # mon -- clan crest
]


_FLAG_SETTERS = {
    "honor":  api.character.set_honor,
    "glory":  api.character.set_glory,
    "status": api.character.set_status,
    "taint":  api.character.set_taint,
    "infamy": api.character.set_infamy,
}


# Modifier kinds offered by the Miscellanea section's add/edit dialog.
# Mirrors l5r.models.modifiers.MOD_TYPES / MOD_DTLS (the legacy
# ModifierDialog source of truth) -- key, label, the kind of "detail" the
# modifier takes ("none" => the detail field is disabled), and the detail
# field's prompt. Labels are wrapped in QT_TRANSLATE_NOOP("AppController")
# -- the same trick _TAB_DEFS uses -- so pylupdate6 extracts them for the
# context self.tr() resolves against (the table values are read through a
# variable below, which the extractor cannot see). The "none"/spell-casting
# placeholder rows of MOD_TYPES are intentionally omitted (the legacy
# dialog skipped them too).
_MODIFIER_TYPE_DEFS = [
    # (key,    label,                                                detailKind, detailLabel)
    ("wdmg", QT_TRANSLATE_NOOP("AppController", "Damage Roll"),    "aweap", QT_TRANSLATE_NOOP("AppController", "Weapon")),
    ("anyr", QT_TRANSLATE_NOOP("AppController", "Any Roll"),       "none",  ""),
    ("skir", QT_TRANSLATE_NOOP("AppController", "Skill Roll"),     "skill", QT_TRANSLATE_NOOP("AppController", "Skill")),
    ("atkr", QT_TRANSLATE_NOOP("AppController", "Attack Roll"),    "aweap", QT_TRANSLATE_NOOP("AppController", "Weapon")),
    ("trat", QT_TRANSLATE_NOOP("AppController", "Trait Roll"),     "trait", QT_TRANSLATE_NOOP("AppController", "Trait")),
    ("ring", QT_TRANSLATE_NOOP("AppController", "Ring Roll"),      "ring",  QT_TRANSLATE_NOOP("AppController", "Ring")),
    ("hrnk", QT_TRANSLATE_NOOP("AppController", "Health Rank"),    "none",  ""),
    ("artn", QT_TRANSLATE_NOOP("AppController", "Armor TN"),       "none",  ""),
    ("arrd", QT_TRANSLATE_NOOP("AppController", "Armor RD"),       "none",  ""),
    ("init", QT_TRANSLATE_NOOP("AppController", "Initiative"),     "none",  ""),
    ("wpen", QT_TRANSLATE_NOOP("AppController", "Wound Penalty"),  "none",  ""),
]


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


def _wstr(value):
    """Stringify a datapack weapon stat for QML (None -> "")."""
    return "" if value is None else str(value)


def _weapon_catalogue_record(weapon):
    """Serialise a datapack weapon for the QML weapon dialogs -- both the
    AddWeaponDialog catalogue and the CustomWeaponDialog base-template
    prefill consume this shape. `categories` mirrors the proxy's combat
    partition so the dialog can show a melee/ranged/arrow dot."""
    try:
        sk = api.data.skills.get(weapon.skill)
        skill_name = sk.name if sk else ""
    except Exception:
        skill_name = ""
    effect_ = api.data.outfit.get_effect(weapon.effectid)
    effect_tx = effect_.text if effect_ is not None else ""
    tags = list(getattr(weapon, "tags", None) or [])
    categories = [c for c in ("melee", "ranged", "arrow") if c in tags]
    return {
        "name":       weapon.name,
        "skill":      skill_name,
        "categories": categories,
        "tags":       tags,
        "dr":         _wstr(weapon.dr),
        "drAlt":      _wstr(weapon.dr2),
        "range":      _wstr(weapon.range),
        "strength":   _wstr(weapon.strength),
        "minStr":     _wstr(weapon.min_strength),
        "cost":       _wstr(weapon.cost),
        "effect":     effect_tx,
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


def _spell_catalogue_record(spell):
    """Serialise a spell DAL row for BuySpellDialog, resolving its
    eligibility against the active character. Mirrors the gate the
    legacy free-form SpellAdvDialog applied: a spell is learnable when
    the character's Insight Rank -- adjusted by elemental affinity and
    deficiency -- meets the spell's mastery. Ineligible spells are still
    returned (dimmed in the dialog) with the figures behind the gate."""
    def ring_text(key):
        ring_ = api.data.get_ring(key)
        return ring_.text if ring_ else (key or "").replace("_", " ").title()

    if api.data.spells.is_multi_element(spell.id):
        element_label = u", ".join(ring_text(x) for x in (spell.elements or []))
    else:
        element_label = ring_text(spell.element)

    try:
        insight = int(api.character.insight_rank())
        affinity = int(api.character.spells.affinity(spell))
        deficiency = int(api.character.spells.deficiency(spell))
    except Exception:
        insight, affinity, deficiency = 0, 0, 0
    reach = insight - deficiency + affinity

    try:
        pack = getattr(spell, "pack", None)
        pack_name = pack.display_name if pack else ""
        page = getattr(spell, "page", 0) or 0
        source = u"{0} p.{1}".format(pack_name, page) if (pack_name and page) else (pack_name or "")
    except Exception:
        source = ""

    mastery = int(spell.mastery) if spell.mastery is not None else 0
    return {
        "id":           spell.id,
        "name":         spell.name or spell.id,
        "element":      (spell.element or "void").lower(),
        "elementLabel": element_label,
        "mastery":      mastery,
        "masteryMod":   affinity - deficiency,
        "range":        spell.range or "",
        "area":         spell.area or "",
        "duration":     spell.duration or "",
        "raises":       u", ".join(spell.raises or []),
        "tags":         list(api.data.spells.tags(spell.id)),
        "source":       source,
        "description":  getattr(spell, "desc", "") or "",
        # `reach` is the highest mastery the character can presently
        # learn; the dialog shows it in the unmet-requirement line.
        "reach":        reach,
        "eligible":     reach >= mastery,
    }


def _ring_element_text(key):
    """Localised display name for a ring key, falling back to a Title-cased
    key (the same convention _spell_catalogue_record uses)."""
    ring_ = api.data.get_ring(key)
    return ring_.text if ring_ else (key or "").replace("_", " ").title()


def _spell_slot_specs():
    """Expand the pending free-spell grants on the current rank advancement
    into per-slot specs, mirroring the legacy SpellAdvDialog.setup(): each
    `spells_to_choose` entry -- a tuple (element, qty[, tag]) copied from the
    school's <PlayerChoose> spells -- yields `qty` restricted slots; then
    unrestricted slots are appended until the total reaches
    `gained_spells_count` (the legacy max(idx, page_count)).

    `element` is matched as a substring, exactly as the legacy did:
      - 'maho' present  -> Maho-only slot, no element restriction
      - 'any' present   -> no element restriction
      - 'nodefic'       -> ignore the caster's deficiency when judging reach
      - '!x'            -> any element but x
      - otherwise       -> that exact element
    """
    slots = []
    for wc in api.character.rankadv.get_starting_spells_to_choose() or []:
        element = wc[0] if len(wc) >= 1 else None
        qty = wc[1] if len(wc) >= 2 else 0
        tag = wc[2] if len(wc) >= 3 else None
        only_maho = bool(element) and 'maho' in element
        no_defic = bool(element) and 'nodefic' in element
        # No element restriction for any/maho slots (mirrors setup()).
        restriction = (None if (only_maho or not element or 'any' in element)
                       else element)
        for _ in range(int(qty or 0)):
            slots.append({
                "element": restriction,
                "maho":    only_maho,
                "noDefic": no_defic,
                "tag":     tag,
            })
    free = int(api.character.rankadv.get_pending_spells_count() or 0)
    while len(slots) < free:
        slots.append({"element": None, "maho": False,
                      "noDefic": False, "tag": None})
    return slots


def _spell_slot_options(spec):
    """Eligible, not-yet-known spells for one bounded slot, as catalogue
    records. Mirrors SpellItemSelection.update_spell_list + can_learn: filter
    by element / Maho / tag restriction and by learnability (honouring the
    slot's no-deficiency flag), excluding spells the character already knows.
    Every returned record is `eligible: True` -- it has already passed the
    slot's mastery-reach gate, so the dialog never dims a pickable spell."""
    known = set(api.character.spells.get_all())
    current_school = api.character.schools.get_current()
    try:
        insight = int(api.character.insight_rank())
    except Exception:
        insight = 0

    elem = spec.get("element")          # exact ring, "!x", or None
    only_maho = bool(spec.get("maho"))
    no_defic = bool(spec.get("noDefic"))
    tag = spec.get("tag")

    out = []
    for spell in api.data.spells.all() or []:
        if spell.id in known:
            continue
        # element restriction (exact, or "!x" exclusion)
        if elem:
            if elem[0] == '!':
                if spell.element == elem[1:]:
                    continue
            elif spell.element != elem:
                continue
        # Maho restriction
        if only_maho and not api.data.spells.has_tag(spell.id, 'maho', current_school):
            continue
        # tag restriction
        if tag and not api.data.spells.has_tag(spell.id, tag, current_school):
            continue
        # learnability -- Insight + affinity, minus deficiency unless waived
        try:
            aff = int(api.character.spells.affinity(spell))
            dfc = 0 if no_defic else int(api.character.spells.deficiency(spell))
        except Exception:
            aff = dfc = 0
        if insight + aff - dfc < (int(spell.mastery) if spell.mastery is not None else 0):
            continue
        rec = _spell_catalogue_record(spell)
        rec["eligible"] = True
        out.append(rec)
    out.sort(key=lambda r: (r["mastery"], (r["name"] or "").lower()))
    return out


class AppController(QObject):
    """Top-level controller exposed to QML."""

    saveRequested = Signal(str)
    # PDF export outcome -- (ok, path). Drives the QML toast; the file is
    # opened from here on success (see _on_export_ok).
    exportFinished = Signal(bool, str)
    # Emitted when a rank-up is requested but the current rank still has
    # unresolved opportunities (school skills, free kiho, ...). Drives a
    # reminder toast (the message is built QML-side, where the rest of the
    # QML strings live).
    advanceRankBlocked = Signal()
    # Emitted when a requested rank-up is clear to proceed -- the QML side
    # then opens the AdvanceRankDialog. Keeps the "may I advance?" decision
    # in the controller while the dialog stays a pure view concern.
    advanceRankReady = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._save_path = ""
        # Holds the running export Worker so the QRunnable + its signals
        # outlive exportPdf's stack frame until the thread finishes.
        self._export_worker = None
        self._export_path = ""

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
            "donateUrl": DONATE_LINK,
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

    @Slot()
    def exportPdfDialog(self):
        """Pick a destination and export the active character sheet to PDF.

        The fill / flatten / merge is the shared l5r.exporters.sheet path
        (one implementation for both front-ends). It runs on a worker thread
        so the sheet stays responsive; exportFinished(ok, path) drives the
        QML toast, and the finished file is opened on success.
        """
        settings = L5RCMSettings()
        last_dir = settings.app.last_open_dir or ""
        # Pre-fill "<Family> <Name>.pdf" in the last-used directory, like the
        # QWidget's select_export_file / get_character_full_name.
        full_name = self._character_full_name()
        suggested = "{}.pdf".format(full_name) if full_name else ""
        proposed = os.path.join(last_dir, suggested)

        path, _ = QFileDialog.getSaveFileName(
            None,
            self.tr("Export Character Sheet"),
            proposed,
            self.tr("PDF Documents (*.pdf);;All Files (*)"),
        )
        if not path:
            return
        if not path.lower().endswith(".pdf"):
            path += ".pdf"
        settings.app.last_open_dir = os.path.dirname(path)

        # Build the form on the GUI thread (it constructs Qt view-models);
        # the worker only reads their items + does file IO.
        form = ModelExportForm()
        worker = Worker(self._run_pdf_export, path, form)
        worker.signals.result.connect(self._on_export_ok)
        worker.signals.error.connect(self._on_export_error)
        self._export_path = path
        self._export_worker = worker
        QThreadPool.globalInstance().start(worker)

    @staticmethod
    def _run_pdf_export(path, form):
        from l5r.exporters import sheet
        sheet.export_pdf(path, form)
        return path

    def _on_export_ok(self, path):
        self._export_worker = None
        log.app.info(u"QML UI: exported character sheet to %s", path)
        self.exportFinished.emit(True, path)
        QDesktopServices.openUrl(QUrl.fromLocalFile(path))

    def _on_export_error(self, err):
        self._export_worker = None
        log.app.error(u"QML UI: PDF export failed: %s", err)
        self.exportFinished.emit(False, self._export_path)

    @staticmethod
    def _character_full_name():
        """`<Family Name> <name>` (e.g. "Hida Hiroshi"), or just the name
        when the character has no family -- mirrors L5RCMCore."""
        pc = api.character.model()
        name = pc.name if pc else ""
        family_ = api.data.families.get(api.character.get_family())
        if family_:
            return "{} {}".format(family_.name, name)
        return name

    @Slot()
    def exportNpcDialog(self):
        """Pick up to two .l5r character files and render them onto a single
        two-NPC sheet (l5r.exporters.sheet.export_npc).

        FDFExporterTwoNPC swaps the active model to each NPC as it fills the
        fields, so the export runs inside an ISOLATED api context (see
        _run_npc_export) -- otherwise it would leave the session showing the
        last NPC instead of the player's character.
        """
        settings = L5RCMSettings()
        last_dir = settings.app.last_open_dir or ""

        paths, _ = QFileDialog.getOpenFileNames(
            None,
            self.tr("Select NPC Characters (up to two)"),
            last_dir,
            self.tr("L5R Character (*.l5r);;All Files (*)"),
        )
        paths = [p for p in paths if p]
        if not paths:
            return
        if len(paths) > 2:
            QMessageBox.information(
                None,
                self.tr("NPC Sheet"),
                self.tr("Only the first two characters fit on an NPC sheet."))
            paths = paths[:2]

        out, _ = QFileDialog.getSaveFileName(
            None,
            self.tr("Export NPC Sheet"),
            os.path.join(last_dir, "npc.pdf"),
            self.tr("PDF Documents (*.pdf);;All Files (*)"),
        )
        if not out:
            return
        if not out.lower().endswith(".pdf"):
            out += ".pdf"
        settings.app.last_open_dir = os.path.dirname(out)

        worker = Worker(self._run_npc_export, paths, out)
        worker.signals.result.connect(self._on_export_ok)
        worker.signals.error.connect(self._on_export_error)
        self._export_path = out
        self._export_worker = worker
        QThreadPool.globalInstance().start(worker)

    @staticmethod
    def _run_npc_export(paths, out_path):
        # Isolate the per-NPC model swaps from the live session: a throwaway
        # context shares the data store / locale but gets its own `pc`, so
        # set_model inside FDFExporterTwoNPC never touches the production
        # context the QML proxies read.
        import l5r.api.context as ctxmod
        from l5r.exporters import sheet

        cur = ctxmod.get_context()
        iso = ctxmod.L5RCMContext()
        iso.ds = cur.ds
        iso.locale = cur.locale
        iso.blacklist = cur.blacklist
        iso.translation_provider = cur.translation_provider
        with ctxmod.use(iso):
            sheet.export_npc(paths, out_path)
        return out_path

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

    @Slot(int)
    def damageHealth(self, delta):
        api.character.damage_health(int(delta))
        api.character.notify_character_refreshed()

    @Slot(int)
    def setWoundsTotal(self, value):
        api.character.set_wounds_taken(int(value))
        api.character.notify_character_refreshed()

    @Slot()
    def resetWounds(self):
        api.character.set_wounds_taken(0)
        api.character.notify_character_refreshed()

    # --- skills ------------------------------------------------------

    @Slot(str)
    def buySkillRank(self, skill_id):
        """Purchase the next rank of `skill_id`. Buying when the
        character doesn't yet own the skill walks rank 0 -> 1 -- so
        this slot serves both 'add new skill' and 'level up' paths."""
        if not skill_id:
            return
        res = api.character.skills.purchase_skill_rank(skill_id)
        if res == CMErrors.NOT_ENOUGH_XP:
            self._show_not_enough_xp()
            return
        api.character.notify_character_refreshed()

    @Slot(str, str)
    def buySkillEmphasis(self, skill_id, text):
        """Add an emphasis to `skill_id`. Emphases cost a flat 2 XP
        (mirrors the legacy advdlg.py SkillEmph cost)."""
        text = (text or "").strip()
        if not skill_id or not text:
            return
        sk = api.data.skills.get(skill_id)
        if not sk:
            log.api.warning(u"QML UI: unknown skill for emphasis: %r", skill_id)
            return
        adv = l5r.models.advances.SkillEmph(skill_id, text, 2)
        adv.desc = self.tr("{0}, Skill {1}. Cost: {2} xp").format(
            text, sk.name, adv.cost)
        if api.character.purchase_advancement(adv) == CMErrors.NOT_ENOUGH_XP:
            self._show_not_enough_xp()
            return
        api.character.notify_character_refreshed()

    @Slot(result="QVariantList")
    def availableSkillsToBuy(self):
        """Skills the character does NOT yet own -- feeds BuySkillDialog.
        Sorted by category, then name, matching the legacy chooser."""
        owned = set(api.character.skills.get_all() or [])
        out = []
        for sk in api.data.skills.all():
            if sk.id in owned:
                continue
            try:
                categ_row = api.data.skills.get_category(sk.type)
                categ_name = categ_row.name if categ_row else (sk.type or "")
            except Exception:
                categ_name = sk.type or ""
            trait_row = api.data.get_trait_or_ring(sk.trait)
            trait_label = trait_row.text if trait_row else (sk.trait or "")
            out.append({
                "id":       sk.id,
                "name":     sk.name,
                "category": categ_name,
                "trait":    trait_label,
            })
        out.sort(key=lambda r: (r["category"].lower(), r["name"].lower()))
        return out

    # --- school skill choices (PlayerChoose) -------------------------
    # When a character joins their first school, the datapack may grant a
    # set of *wildcard* skill picks (the school XML's <PlayerChoose>, parsed
    # by l5rdal into school.skills_pc and copied onto the rank-1 advancement
    # as rank_.skills_to_choose). The player must resolve each set by
    # choosing one concrete skill that matches it. These two slots replace
    # the legacy SelWcSkills dialog (l5r/dialogs/advdlg.py) + the
    # AdvanceMixin.act_choose_skills / clear_skills_to_choose flow.

    def _wildcard_prompt(self, wc_set):
        """Human prompt for one wildcard set, e.g. 'Any High skill (rank 1):'
        or 'Any High, but Lore (rank 1):'. Ported verbatim from
        SelWcSkills.build_ui -- the wildcard value is read as a skill
        *category* id for the label (get_category), while option resolution
        below reads it as a skill *tag* (get_by_tag)."""
        wl = wc_set.wildcards or []
        rank = int(wc_set.rank or 1)
        if not wl:
            return self.tr("Any skill (rank {0}):").format(rank)

        inclusive = api.data.skills.get_inclusive_tags(wl)
        exclusive = api.data.skills.get_exclusive_tags(wl)
        inc_names = [c.name for c in
                     (api.data.skills.get_category(t) for t in inclusive)
                     if c is not None]
        exc_names = [c.name for c in
                     (api.data.skills.get_category(t) for t in exclusive)
                     if c is not None]
        sw1 = u", ".join(inc_names)
        sw2 = u", ".join(exc_names)
        if wl[0].value == 'any':
            sw1 = self.tr("skill")
        if exclusive:
            return self.tr("Any {0}, but {1} (rank {2}):").format(sw1, sw2, rank)
        return self.tr("Any {0} skill (rank {1}):").format(sw1, rank)

    def _wildcard_options(self, wc_set):
        """Concrete, still-unowned skills that satisfy one wildcard set --
        the chooser's option list. Ported from SelWcSkills.load_data:
        'any' opens the whole catalogue, an 'or' wildcard unions its tag's
        skills in, a 'not' wildcard removes them. Owned skills are dropped
        (you can't pick what you already have) and the result deduped."""
        owned = set(api.character.skills.get_all() or [])
        outcome = []
        for w_ in (wc_set.wildcards or []):
            if w_.value == 'any':
                outcome += api.data.skills.all()
            else:
                by_tag = api.data.skills.get_by_tag(w_.value)
                if not w_.modifier or w_.modifier == 'or':
                    outcome += by_tag
                elif w_.modifier == 'not':
                    outcome = [x for x in outcome if x not in by_tag]

        out, seen = [], set()
        for sk in outcome:
            if sk.id in owned or sk.id in seen:
                continue
            seen.add(sk.id)
            out.append({"id": sk.id, "name": sk.name})
        out.sort(key=lambda r: (r["name"] or "").lower())
        return out

    @Slot(result="QVariantMap")
    def schoolSkillChoices(self):
        """Resolve the pending school-granted wildcard skill/emphasis picks
        into a QML-friendly structure for ChooseSchoolSkillsDialog:
            { skills:   [{label, rank, options:[{id, name}, ...]}, ...],
              emphases: [{skillId, skillName}, ...] }
        one entry per wildcard set, plus one per emphasis-to-choose.
        Mirrors SelWcSkills.build_ui / load_data."""
        if api.character.model() is None:
            return {"skills": [], "emphases": []}

        skills = []
        for wc_set in api.character.rankadv.get_starting_skills_to_choose():
            skills.append({
                "label":   self._wildcard_prompt(wc_set),
                "rank":    int(wc_set.rank or 1),
                "options": self._wildcard_options(wc_set),
            })

        emphases = []
        for sid in api.character.rankadv.get_starting_emphases_to_choose():
            sk = api.data.skills.get(sid)
            if sk is None:
                continue
            emphases.append({"skillId": sk.id, "skillName": sk.name})

        return {"skills": skills, "emphases": emphases}

    @Slot("QVariantList", "QVariantList")
    def applySchoolSkillChoices(self, skill_picks, emph_picks):
        """Apply the player's school-skill choices: grant each picked skill
        at its set's rank, add each chosen emphasis, then clear the pending
        list so the opportunity resolves. Mirrors SelWcSkills.on_accept +
        AdvanceMixin.act_choose_skills. The api helpers (add_starting_skill,
        clear_skills_to_choose) append to the rank advancement but do not own
        the dirty flag, so set it here (like learnSpell / inscribePerk).

        Distinctness / unowned validation is enforced by the dialog
        (acceptEnabled); the options were already filtered to unowned, so
        this trusts the picks and applies them faithfully."""
        if api.character.model() is None:
            return

        for pick in (skill_picks or []):
            sid = pick.get("id")
            if not sid:
                continue
            rank = int(pick.get("rank", 1) or 1)
            api.character.skills.add_starting_skill(sid, rank)

        for pick in (emph_picks or []):
            sid = pick.get("skillId")
            text = (pick.get("text") or "").strip()
            if sid and text:
                api.character.skills.add_starting_skill(sid, emph=text)

        api.character.rankadv.clear_skills_to_choose()
        api.character.set_dirty_flag(True)
        api.character.notify_character_refreshed()

    # --- spells -------------------------------------------------------

    @Slot(str)
    def learnSpell(self, spell_id):
        """Learn a spell free-form -- a SpellAdv (cost 0), the legacy
        'Add new spell' action. Free-form spells are not bound to a
        rank, so there is no XP gate; a missing/unknown id is the only
        failure mode. The api helper appends the advancement but does
        not own the dirty flag, so set it here (mirrors inscribePerk)."""
        if not spell_id:
            return
        if api.character.spells.add_spell(spell_id):
            api.character.set_dirty_flag(True)
            api.character.notify_character_refreshed()

    @Slot(str)
    def removeSpell(self, spell_id):
        """Forget a free-form learned spell by id. Only the free-form
        SpellAdv is removed: school-granted spells live on a rank
        advancement (unwound on Advancements) and a memorized spell must
        be dropped via forgetSpell first. Re-resolves the advancement by
        scanning the live list, mirroring removePerk."""
        if not spell_id:
            return
        pc = api.character.model()
        if not pc:
            return
        target = None
        for adv in pc.advans or []:
            if adv.type == "spell" and getattr(adv, "spell", None) == spell_id:
                target = adv
                break
        if target is None:
            log.api.warning(u"QML UI: removeSpell: no learned spell %r", spell_id)
            return
        if api.character.remove_advancement(target):
            api.character.set_dirty_flag(True)
            api.character.notify_character_refreshed()

    @Slot(str)
    def memorizeSpell(self, spell_id):
        """Memorize a spell -- a MemoSpellAdv costing XP equal to the
        spell's mastery (the legacy 'Memorize' toggle). Surfaces the
        not-enough-XP notice when the character can't afford it; the
        purchase helper appends the advancement but does not own the
        dirty flag, so set it on success."""
        if not spell_id:
            return
        res = api.character.spells.purchase_memo_spell(spell_id)
        if res == CMErrors.NOT_ENOUGH_XP:
            self._show_not_enough_xp()
            return
        if res == CMErrors.NO_ERROR:
            api.character.set_dirty_flag(True)
            api.character.notify_character_refreshed()

    @Slot(str)
    def forgetSpell(self, spell_id):
        """Drop a memorized spell by id, refunding its XP -- the 'Forget'
        half of the legacy memorize toggle. Scans for the MemoSpellAdv
        rather than touching pc directly."""
        if not spell_id:
            return
        pc = api.character.model()
        if not pc:
            return
        target = None
        for adv in pc.advans or []:
            if adv.type == "memo_spell" and getattr(adv, "spell", None) == spell_id:
                target = adv
                break
        if target is None:
            log.api.warning(u"QML UI: forgetSpell: no memorized spell %r", spell_id)
            return
        if api.character.remove_advancement(target):
            api.character.set_dirty_flag(True)
            api.character.notify_character_refreshed()

    @Slot(result="QVariantList")
    def availableSpellsToBuy(self):
        """Catalogue feed for BuySpellDialog -- every spell the character
        does not already know, each marked eligible/ineligible (the gate
        the legacy free-form SpellAdvDialog put on 'Finish'). Ineligible
        spells are included (dimmed) so the player can see what lies just
        beyond their reach. Slot rather than Property so mid-session
        datapack imports show up without a restart."""
        if api.character.model() is None:
            return []
        known = set(api.character.spells.get_all())
        out = []
        for spell in api.data.spells.all() or []:
            if spell.id in known:
                continue
            out.append(_spell_catalogue_record(spell))
        # Within-reach first, then by mastery, then name -- the same
        # reading order the section uses for the known register.
        out.sort(key=lambda r: (not r["eligible"], r["mastery"],
                                (r["name"] or "").lower()))
        return out

    # --- school spell grant (shugenja) -------------------------------

    @Slot(result="QVariantMap")
    def schoolSpellChoices(self):
        """Per-slot feed for ChooseSchoolSpellsDialog -- the bounded version
        of the spell catalogue. Replaces the legacy 'bounded' SpellAdvDialog
        wizard: each free spell the school grants becomes one slot, with its
        own pre-filtered list of legal, learnable, not-yet-known spells (the
        dialog's tabs let the player fill them in any order). Restricted slots
        (a specific element, Maho-only, a tag) carry only the spells that
        satisfy them; unrestricted slots carry every learnable spell.

        Shape: { "slots": [ { index, elementLabel, excludeLabel, maho,
                              noDefic, tag, options:[catalogue record,...] } ] }
        elementLabel/excludeLabel are localised ring names ("" when not
        applicable); the QML composes the player-facing restriction copy from
        these flags so all wording stays on the QML translation surface."""
        if api.character.model() is None:
            return {"slots": []}
        slots = []
        for i, spec in enumerate(_spell_slot_specs()):
            elem = spec.get("element")
            exact = elem if (elem and not elem.startswith('!')) else None
            excl = elem[1:] if (elem and elem.startswith('!')) else None
            slots.append({
                "index":        i,
                "elementLabel": _ring_element_text(exact) if exact else "",
                "excludeLabel": _ring_element_text(excl) if excl else "",
                "maho":         bool(spec.get("maho")),
                "noDefic":      bool(spec.get("noDefic")),
                "tag":          spec.get("tag") or "",
                "options":      _spell_slot_options(spec),
            })
        return {"slots": slots}

    @Slot("QVariantList")
    def applySchoolSpellChoices(self, spell_ids):
        """Commit the player's bounded spell picks and clear the pending grant
        -- the legacy 'learn_next_school_spells' accept path (add_school_spell
        per pick, then clear_spells_to_choose). Validates that there is one
        distinct pick per granted slot; bails (committing nothing) otherwise,
        so a malformed call cannot half-resolve the grant. add_school_spell /
        clear_spells_to_choose mutate the rank directly and do not own the
        dirty flag, so this slot does (like advanceRank / joinNewSchool)."""
        if api.character.model() is None:
            return
        ids = [str(x) for x in (spell_ids or []) if x]
        expected = len(_spell_slot_specs())
        if not ids or len(ids) != expected or len(set(ids)) != len(ids):
            log.api.error(
                u"applySchoolSpellChoices: rejected picks "
                u"(%d given, %d expected, distinct=%s)",
                len(ids), expected, len(set(ids)) == len(ids))
            return
        for sid in ids:
            api.character.spells.add_school_spell(sid)
        api.character.rankadv.clear_spells_to_choose()
        api.character.set_dirty_flag(True)
        api.character.notify_character_refreshed()

    # --- elemental affinity / deficiency choice (shugenja) -----------

    @Slot(str, result="QVariantMap")
    def elementChoice(self, kind):
        """The element options for the affinity OR deficiency choice a school
        grants as `any`/`nonvoid` (kind is "affinity" or "deficiency"). Feeds
        ChooseElementDialog. Mirrors the legacy show_select_affinity /
        show_select_deficiency: all five rings, minus Void when the school's
        spec says `nonvoid`. Returns { pending, kind, options:[{id,name}] }."""
        empty = {"pending": False, "kind": kind, "options": []}
        if api.character.model() is None:
            return empty
        rank_ = api.character.rankadv.get_last()
        if not rank_:
            return empty
        specs = (rank_.affinities_to_choose if kind == "affinity"
                 else rank_.deficiencies_to_choose)
        if not specs:
            return empty
        # choose_* pops the last spec, so the last one is the next to resolve.
        spec = specs[-1]
        exclude_void = isinstance(spec, str) and 'nonvoid' in spec
        options = []
        for r in api.data.rings() or []:
            if exclude_void and r == 'void':
                continue
            options.append({"id": r, "name": _ring_element_text(r)})
        return {"pending": True, "kind": kind, "options": options}

    @Slot(str)
    def chooseAffinity(self, ring_id):
        """Commit the chosen elemental affinity (the legacy
        show_select_affinity). rankadv.choose_affinity mutates the rank and
        does not own the dirty flag, so this slot does."""
        if api.character.model() is None or not ring_id:
            return
        if api.character.rankadv.choose_affinity(ring_id):
            api.character.set_dirty_flag(True)
            api.character.notify_character_refreshed()

    @Slot(str)
    def chooseDeficiency(self, ring_id):
        """Commit the chosen elemental deficiency (the legacy
        show_select_deficiency)."""
        if api.character.model() is None or not ring_id:
            return
        if api.character.rankadv.choose_deficiency(ring_id):
            api.character.set_dirty_flag(True)
            api.character.notify_character_refreshed()

    # --- advancements ------------------------------------------------

    @Slot()
    def refundLastAdvancement(self):
        """Pop the head of the advancement stack. Refund is stack-LIFO
        because each entry's XP cost depends on the rank reached by the
        ones beneath it (see project-advancement-stack-semantics).
        The api setter owns the dirty-flag + refresh contract."""
        api.character.refund_last_advancement()

    @Slot(result=bool)
    def refundWarningEnabled(self):
        """True when the QML side should pop the refund-confirmation
        dialog before refunding. False after the user ticks 'Do not
        prompt again' (mirrors the legacy QMessageBox flow)."""
        return bool(L5RCMSettings().app.warn_about_refund)

    @Slot()
    def suppressRefundWarning(self):
        """Persist the 'Do not prompt again' choice from the QML refund
        dialog -- writes through QSettings so the preference outlives
        this session."""
        L5RCMSettings().app.warn_about_refund = False

    # --- rank advancement --------------------------------------------

    @Slot(result="QVariantMap")
    def advanceRankInfo(self):
        """Drives the QML AdvanceRankDialog's confirmation copy -- the
        legacy NextRankDlg 'go on' branch: advance in the current school,
        or (when on an alternate path) resume the former school.
        `canContinue` is False only on a path with no former (non-path)
        school to fall back to -- the dialog then disables Advance but
        still offers the join-a-new-school path (`canJoinNewSchool`),
        which is always available."""
        pc = api.character.model()
        if pc is None:
            return {}

        current_id = api.character.schools.get_current()
        on_path = bool(api.data.schools.is_path(current_id))
        current = api.data.schools.get(current_id)
        current_name = current.name if current else ""

        former_adv = api.character.rankadv.get_former_school()
        former = api.data.schools.get(former_adv.school) if former_adv else None
        former_name = former.name if former else ""

        try:
            next_rank = int(api.character.insight_rank())
        except Exception:
            next_rank = 0

        # "Continue" is impossible only when on a path with no former
        # (non-path) school to fall back to -- that case requires the
        # deferred multiclass join.
        can_continue = (not on_path) or (former is not None)

        return {
            "nextRank":         next_rank,
            "onPath":           on_path,
            "currentSchool":    current_name,
            "formerSchool":     former_name,
            "canContinue":      can_continue,
            # Multiclass is always an option at a rank boundary -- the
            # dialog offers it as a secondary path even in the dead-end
            # case above (a path with no former school to resume).
            "canJoinNewSchool": True,
        }

    @Slot()
    def requestAdvanceRank(self):
        """Entry point for the outer 'Advance Rank' button. Decides whether
        the rank-up may proceed BEFORE the dialog opens: if the player still
        has unresolved opportunities (school skills, free kiho, ...) it
        nudges with a reminder toast (advanceRankBlocked) and stops;
        otherwise it signals the view to open the dialog (advanceRankReady).

        The blocking set is the surfaced opportunities minus the rank-up
        itself (see opportunities.has_blocking_opportunities) -- so it scales
        with the allow-list and never dead-locks on a grant that has no QML
        resolution yet."""
        if api.character.model() is None:
            return
        if opportunities.has_blocking_opportunities():
            self.advanceRankBlocked.emit()
            return
        self.advanceRankReady.emit()

    @Slot()
    def advanceRank(self):
        """Advance in the current school, or resume the former school when
        on an alternate path -- the legacy NextRankDlg 'go on' branch.
        Guards on availability (advance_rank assumes a pending rank-up)
        and owns the dirty flag (the rankadv helpers append the
        advancement directly and do not)."""
        if api.character.model() is None:
            return
        if api.character.insight_rank() <= api.character.insight_rank(strict=True):
            return  # no pending rank-up; nothing to do

        # Defence in depth: the outer button (requestAdvanceRank) already
        # gates on this, but refuse here too so advancing can never silently
        # orphan an unresolved opportunity. Advancing appends a new Rank that
        # becomes the 'last' one and the choice getters read only the last
        # rank, so the pending grant would be lost. Nudge with a toast.
        if opportunities.has_blocking_opportunities():
            self.advanceRankBlocked.emit()
            return

        current_id = api.character.schools.get_current()
        if api.data.schools.is_path(current_id):
            res = api.character.rankadv.leave_path()
        else:
            res = api.character.rankadv.advance_rank()
        if res:
            api.character.set_dirty_flag(True)
            api.character.notify_character_refreshed()

    @Slot(str, str, result="QVariantList")
    def schoolsForJoin(self, clan_id, category):
        """School records for the QML JoinSchoolDialog, bucketed by the
        category the player chose: 'base' (a new school), 'advanced' (an
        advanced school) or 'path' (an alternate path). Mirrors the legacy
        SchoolChooserWidget.get_filtered_school_list, but the QML flow
        picks ONE category up front rather than toggling three checkboxes.
        Filtered by clan when one is given and serialised with
        _school_record (the same shape FirstSchoolChooserDialog consumes)."""
        if api.character.model() is None:
            return []
        if category == "advanced":
            schools = api.data.schools.get_advanced()
        elif category == "path":
            schools = api.data.schools.get_paths()
        else:
            schools = api.data.schools.get_base()
        if clan_id:
            schools = [s for s in schools if s.clanid == clan_id]
        return [_school_record(s)
                for s in sorted(schools, key=lambda x: x.name)]

    @Slot(str, result="QVariantList")
    def schoolRequirements(self, school_id):
        """The join requirements for a school, as a checklist for the QML
        JoinSchoolDialog: each entry is {text, satisfied, rolePlay}. Hard
        requirements (a prior school rank, a trait minimum, ...) are
        evaluated read-only against the live character (✓/✗); 'more'
        requirements are role-play notes the player must acknowledge by
        hand (rolePlay True, satisfied starts False so the dialog can gate
        Accept on the player ticking them). Same evaluation as
        RequirementsWidget.set_requirements -- Requirement.match(snapshot,
        datastore) over a CharacterSnapshot."""
        pc = api.character.model()
        if pc is None or not school_id:
            return []
        snap = l5r.models.CharacterSnapshot(pc)
        ds = api.data.model()
        out = []
        for r in api.data.schools.get_requirements(school_id) or []:
            role_play = (r.type == 'more')
            out.append({
                "text":      r.text or "",
                "rolePlay":  role_play,
                "satisfied": False if role_play else bool(r.match(snap, ds)),
            })
        return out

    @Slot(result="QVariantMap")
    def multipleSchoolsInfo(self):
        """Cost + affordability of the optional 'Multiple Schools'
        advantage the player may buy alongside a multiclass join (the
        legacy SchoolChooserWidget option). Soft data only: the QML shows
        the cost and a gentle 'not enough XP' note but, per the
        house-rules-friendly philosophy of the QML UI (same as
        inscribePerk and spell memorization), does not block the join."""
        cost = int(api.data.merits.get_rank_cost('multiple_schools', 1) or 0)
        return {
            "cost":       cost,
            "affordable": api.character.xp_left() >= cost,
        }

    @Slot(str, bool)
    def joinNewSchool(self, school_id, buy_multiple_schools):
        """Join a new school (multiclass) -- the legacy SchoolChooserDialog
        'Join a new school' branch. rankadv.join_new grants the new
        school's rank-1 technique plus its spell/kiho bonus and
        affinity/deficiency (and, for an alternate path, records the school
        it replaces); the optional 'Multiple Schools' advantage is bought
        alongside it. The rankadv helper appends the advancement but does
        not own the dirty flag (like advanceRank), so set it here once both
        mutations are in."""
        if api.character.model() is None or not school_id:
            return
        api.character.rankadv.join_new(school_id)
        if buy_multiple_schools:
            api.character.merits.add('multiple_schools')
        api.character.set_dirty_flag(True)
        api.character.notify_character_refreshed()

    # --- merits / flaws ----------------------------------------------

    @Slot(result="QVariantList")
    def availableMerits(self):
        """Catalogue feed for InscribePerkDialog in merit mode. Slot
        rather than constant Property so datapack imports mid-session
        are reflected without restarting the app."""
        return self._catalogue(is_flaw=False)

    @Slot(result="QVariantList")
    def availableFlaws(self):
        """Catalogue feed for InscribePerkDialog in flaw mode."""
        return self._catalogue(is_flaw=True)

    @Slot(result="QVariantList")
    def perkCategories(self):
        """Categories used to bucket merits/flaws -- Physical, Social,
        Mental, Spiritual, Material in the stock datapack. Drives the
        category-filter strip in InscribePerkDialog (mirrors the
        legacy BuyPerkDialog's subtype combobox)."""
        ds = api.data.model()
        if ds is None:
            return []
        out = []
        for t in getattr(ds, "perktypes", None) or []:
            out.append({"id": t.id, "name": t.name})
        out.sort(key=lambda r: (r["name"] or "").lower())
        return out

    def _catalogue(self, is_flaw):
        rows_src = (api.data.flaws.all() if is_flaw
                    else api.data.merits.all())
        out = []
        for p in rows_src or []:
            ranks = []
            for r in getattr(p, "ranks", None) or []:
                # The rank value is signed in the datapack (flaws are
                # negative); the QML side wants the positive magnitude.
                # Clan/tag exceptions are applied for the active PC so
                # the suggested cost reflects discounts the player
                # actually qualifies for.
                cost = abs(int(r.value))
                for ex in r.exceptions or []:
                    if api.character.has_tag_or_rule(ex.tag):
                        cost = abs(int(ex.value))
                ranks.append({"rank": int(r.id), "cost": cost})
            ranks.sort(key=lambda x: x["rank"])

            suggested = ranks[0]["cost"] if ranks else 0

            try:
                pack_name = (p.source_pack.display_name
                             if p.source_pack else "")
            except Exception:
                pack_name = ""
            # book_page may be an int, a numeric string, or a range
            # like "157-158" -- the datapack format does not constrain
            # it. Render whatever non-empty string we get.
            page_raw = getattr(p, "book_page", "") or ""
            page = str(page_raw).strip()
            if pack_name and page and page != "0":
                source = "{} p.{}".format(pack_name, page)
            else:
                source = pack_name

            out.append({
                "ruleId":        p.id,
                "name":          p.name or p.id,
                "type":          getattr(p, "type", "") or "",
                "description":   getattr(p, "desc", "") or "",
                "source":        source,
                "suggestedCost": suggested,
                "ranks":         ranks,
            })
        out.sort(key=lambda r: (r["name"] or "").lower())
        return out

    @Slot(str, str, int, str, int)
    def inscribePerk(self, kind, rule_id, rank, extra, override_cost):
        """Buy a merit or flaw. `override_cost == -1` means use the
        rulebook suggestion (with clan/tag discounts); any non-negative
        value is the player's manual XP -- house rules are common in
        L5R, so the slot accepts whatever the player picks without an
        XP-affordability gate.

        Mirrors BuyPerkDialog.on_accept: builds a PerkAdv directly and
        routes through append_advancement rather than the
        merits.add/flaws.add convenience APIs (those don't support
        cost overrides)."""
        if not rule_id:
            return
        is_flaw = kind == "flaw"

        if is_flaw:
            perk_row = api.data.flaws.get(rule_id)
        else:
            perk_row = api.data.merits.get(rule_id)
        if perk_row is None:
            log.api.warning(u"QML UI: unknown %s id %r", kind, rule_id)
            return

        rank_row = (api.data.flaws.get_rank(rule_id, rank) if is_flaw
                    else api.data.merits.get_rank(rule_id, rank))
        if rank_row is None:
            log.api.warning(u"QML UI: %s %r has no rank %s",
                            kind, rule_id, rank)
            return

        # Resolve cost: suggestion (with discount) or manual override.
        if override_cost is None or int(override_cost) < 0:
            cost = (api.data.flaws.get_rank_gain(rule_id, rank) if is_flaw
                    else api.data.merits.get_rank_cost(rule_id, rank))
            cost = abs(int(cost))
        else:
            cost = abs(int(override_cost))

        # Sign convention: flaws are stored with negative cost so the
        # global XP math (xp(), xp_limit(), get_xp_gained_from_flaws)
        # works as written.
        stored_cost = -cost if is_flaw else cost

        adv = l5r.models.advances.PerkAdv(rule_id, rank_row.id,
                                          stored_cost, kind)
        adv.rule = rule_id
        adv.extra = (extra or "").strip()
        if is_flaw:
            adv.desc = self.tr("{0} Rank {1}, XP Gain: {2}").format(
                perk_row.name, rank_row.id, cost)
        else:
            adv.desc = self.tr("{0} Rank {1}, XP Cost: {2}").format(
                perk_row.name, rank_row.id, cost)

        api.character.append_advancement(adv)
        api.character.set_dirty_flag(True)
        api.character.notify_character_refreshed()

    @Slot(str)
    def removePerk(self, adv_id):
        """Remove a previously-inscribed merit or flaw by stable id.
        `adv_id` is the str(id(adv)) value the PcProxy emitted for that
        entry; we re-resolve to the actual PerkAdv by scanning the
        live advancement list."""
        if not adv_id:
            return
        pc = api.character.model()
        if not pc:
            return
        target = None
        for adv in pc.advans or []:
            if str(id(adv)) == adv_id:
                target = adv
                break
        if target is None:
            log.api.warning(u"QML UI: removePerk: no adv with id %r", adv_id)
            return
        if api.character.remove_advancement(target):
            api.character.set_dirty_flag(True)
            api.character.notify_character_refreshed()

    @Slot(str, str, int)
    def editPerk(self, adv_id, extra, override_cost):
        """Edit an existing merit/flaw entry. Mirrors the legacy
        BuyPerkDialog edit mode: rule and rank stay fixed (changing
        those is semantically a remove+rebuy), but the player can
        re-key the notes (`extra`) and the XP figure. `override_cost`
        carries the same convention as inscribePerk: -1 = "use the
        rulebook suggestion (with discounts)"; any non-negative value
        is an explicit manual cost."""
        if not adv_id:
            return
        pc = api.character.model()
        if not pc:
            return
        target = None
        for adv in pc.advans or []:
            if str(id(adv)) == adv_id:
                target = adv
                break
        if target is None:
            log.api.warning(u"QML UI: editPerk: no adv with id %r", adv_id)
            return

        is_flaw = (getattr(target, "tag", None) == "flaw"
                   or (target.cost or 0) < 0)
        rule_id = target.perk
        rank = target.rank

        # Resolve cost: suggestion (with discount) or manual override.
        if override_cost is None or int(override_cost) < 0:
            try:
                cost = (api.data.flaws.get_rank_gain(rule_id, rank) if is_flaw
                        else api.data.merits.get_rank_cost(rule_id, rank))
            except AttributeError:
                cost = abs(int(target.cost or 0))
            cost = abs(int(cost))
        else:
            cost = abs(int(override_cost))

        target.extra = (extra or "").strip()
        # Keep the sign convention: flaws are stored with negative cost.
        target.cost = -cost if is_flaw else cost

        # Refresh the human-readable description so the advancements
        # chronicle stays in sync with the new figure.
        try:
            perk_row = (api.data.flaws.get(rule_id) if is_flaw
                        else api.data.merits.get(rule_id))
        except AttributeError:
            perk_row = None
        perk_name = perk_row.name if perk_row else rule_id
        if is_flaw:
            target.desc = self.tr("{0} Rank {1}, XP Gain: {2}").format(
                perk_name, rank, cost)
        else:
            target.desc = self.tr("{0} Rank {1}, XP Cost: {2}").format(
                perk_name, rank, cost)

        api.character.set_dirty_flag(True)
        api.character.notify_character_refreshed()

    # --- kata --------------------------------------------------------

    @Slot(str)
    def buyKata(self, kata_id):
        """Purchase a kata by id. Delegates to the api setter (which
        owns the dirty flag); surfaces the not-enough-XP notice and
        refreshes derived state on success."""
        if not kata_id:
            return
        res = api.character.powers.buy_kata(kata_id)
        if res == CMErrors.NOT_ENOUGH_XP:
            self._show_not_enough_xp()
            return
        api.character.notify_character_refreshed()

    @Slot(str)
    def removeKata(self, kata_id):
        """Unlearn a kata by id. Delegates to the api setter (which owns
        the dirty flag), then refreshes derived state on success."""
        if not kata_id:
            return
        if api.character.powers.remove_kata(kata_id):
            api.character.notify_character_refreshed()

    @Slot(result="QVariantList")
    def availableKataToBuy(self):
        """Catalogue feed for BuyKataDialog -- the kata the character may
        still learn, each with its element / mastery / cost / eligibility
        (see api.character.powers.get_all_buyable_kata). Slot rather than
        Property so mid-session datapack imports show up without a
        restart."""
        return api.character.powers.get_all_buyable_kata()

    # --- kiho --------------------------------------------------------

    @Slot(str)
    def buyKiho(self, kiho_id):
        """Purchase a kiho by id. Delegates to the api setter (which owns
        the dirty flag and applies the free-kiho discount); surfaces the
        not-enough-XP notice and refreshes derived state on success."""
        if not kiho_id:
            return
        res = api.character.powers.buy_kiho(kiho_id)
        if res == CMErrors.NOT_ENOUGH_XP:
            self._show_not_enough_xp()
            return
        api.character.notify_character_refreshed()

    @Slot(str)
    def removeKiho(self, kiho_id):
        """Unlearn a kiho by id. Delegates to the api setter (which owns
        the dirty flag), then refreshes derived state on success."""
        if not kiho_id:
            return
        if api.character.powers.remove_kiho(kiho_id):
            api.character.notify_character_refreshed()

    @Slot(result="QVariantList")
    def availableKihoToBuy(self):
        """Catalogue feed for BuyKihoDialog -- the kiho the character may
        still learn, each with its element / type / mastery / class-scaled
        cost / path standing / eligibility (see
        api.character.powers.get_all_buyable_kiho). Slot rather than
        Property so mid-session datapack imports show up without a
        restart."""
        return api.character.powers.get_all_buyable_kiho()

    # --- tattoo ------------------------------------------------------

    @Slot(str)
    def buyTattoo(self, tattoo_id):
        """Receive a tattoo by id. Delegates to the api setter (which
        owns the dirty flag); refreshes derived state on success.
        Tattoos are free, so there is no XP gate -- a missing id is the
        only failure mode."""
        if not tattoo_id:
            return
        if api.character.powers.buy_tattoo(tattoo_id) == CMErrors.NO_ERROR:
            api.character.notify_character_refreshed()

    @Slot(str)
    def removeTattoo(self, tattoo_id):
        """Remove a tattoo by id. Delegates to the api setter (which owns
        the dirty flag), then refreshes derived state on success."""
        if not tattoo_id:
            return
        if api.character.powers.remove_tattoo(tattoo_id):
            api.character.notify_character_refreshed()

    @Slot(result="QVariantList")
    def availableTattooToBuy(self):
        """Catalogue feed for BuyTattooDialog -- the tattoos the
        character may still receive (see
        api.character.powers.get_all_buyable_tattoo). Slot rather than
        Property so mid-session datapack imports show up without a
        restart."""
        return api.character.powers.get_all_buyable_tattoo()

    # --- weapons -----------------------------------------------------
    # A weapon is a plain WeaponOutfit on pc.weapons (no XP, no rank
    # history), so these slots delegate to api.character.weapons -- which
    # owns the dirty flag + refresh -- rather than to the advancement
    # machinery. The proxy emits a session-stable str(id(weapon)) handle
    # for each row; edit / remove / qty re-resolve the live item by
    # scanning the list (mirrors removePerk). Replaces the legacy
    # WeaponsSink (add / add-custom / edit / remove / qty).

    @Slot(result="QVariantList")
    def availableWeapons(self):
        """Catalogue feed for AddWeaponDialog (browse) and the
        CustomWeaponDialog base-template dropdown, sorted by skill then
        name. Slot rather than Property so mid-session datapack imports
        show up without a restart."""
        out = [_weapon_catalogue_record(w)
               for w in (api.data.outfit.get_weapons() or [])]
        out.sort(key=lambda r: ((r["skill"] or "").lower(),
                                (r["name"] or "").lower()))
        return out

    @Slot(str)
    def addWeapon(self, weapon_name):
        """Add a catalogue weapon by name (the legacy ChooseItemDialog
        weapon path). weapon_outfit_from_db resolves all of its stats,
        skill and tags from the datapack, so the category partition and
        roll calculations land correctly with no further input."""
        if not weapon_name:
            return
        if api.data.outfit.get_weapon(weapon_name) is None:
            log.api.warning(u"QML UI: addWeapon: unknown weapon %r",
                            weapon_name)
            return
        item = l5r.models.weapon_outfit_from_db(weapon_name)
        if item is not None:
            api.character.weapons.add(item)

    @Slot("QVariantMap")
    def addCustomWeapon(self, data):
        """Add a custom weapon (the legacy CustomWeaponDialog add path).
        `data.base` is the catalogue weapon the build started from -- it
        seeds the skill, trait and category tags so the new weapon still
        rolls and files correctly; the editable fields then override the
        stats. Mirrors CustomWeaponDialog, which always begins from a
        base template."""
        base = (data.get("base") or "").strip()
        if base and api.data.outfit.get_weapon(base) is not None:
            item = l5r.models.weapon_outfit_from_db(base)
        else:
            item = l5r.models.WeaponOutfit()
        self._apply_weapon_fields(item, data)
        if not item.name:
            log.api.warning(u"QML UI: addCustomWeapon: refused unnamed weapon")
            return
        api.character.weapons.add(item)

    @Slot(str, "QVariantMap")
    def editWeapon(self, weapon_id, data):
        """Edit a weapon's stats in place (the legacy CustomWeaponDialog
        edit mode). Skill, trait and category tags stay fixed -- changing
        those is semantically a remove + re-add -- so only the editable
        fields are rewritten, then the character is flagged dirty and
        re-projected."""
        item = self._resolve_weapon(weapon_id)
        if item is None:
            log.api.warning(u"QML UI: editWeapon: no weapon %r", weapon_id)
            return
        self._apply_weapon_fields(item, data)
        api.character.weapons.touch()

    @Slot(str)
    def removeWeapon(self, weapon_id):
        """Remove a weapon by its session-stable id."""
        item = self._resolve_weapon(weapon_id)
        if item is None:
            log.api.warning(u"QML UI: removeWeapon: no weapon %r", weapon_id)
            return
        api.character.weapons.remove(item)

    @Slot(str, int)
    def changeWeaponQty(self, weapon_id, delta):
        """Bump a weapon's quantity by `delta` (the arrow stepper). The
        api setter clamps to [1, 9999]."""
        item = self._resolve_weapon(weapon_id)
        if item is None:
            return
        current = int(getattr(item, "qty", 1) or 1)
        api.character.weapons.set_quantity(item, current + int(delta))

    def _resolve_weapon(self, weapon_id):
        """Re-resolve the live WeaponOutfit for a proxy-emitted id."""
        if not weapon_id:
            return None
        pc = api.character.model()
        if not pc:
            return None
        for w in pc.get_weapons() or []:
            if str(id(w)) == weapon_id:
                return w
        return None

    def _apply_weapon_fields(self, item, data):
        """Write the editable custom-weapon fields onto `item`, mirroring
        CustomWeaponDialog.on_accept: ints for strength / min-strength,
        DR coerced through the roll-and-keep parser, name / range / notes
        verbatim."""
        def _int(v):
            try:
                return int(v)
            except (TypeError, ValueError):
                return 0

        def _dr(v):
            r, k = api.rules.parse_rtk(str(v or ""))
            return api.rules.format_rtk(r, k)

        item.strength = _int(data.get("strength"))
        item.min_str = _int(data.get("minStr"))
        item.dr = _dr(data.get("dr")) or self.tr("N/A")
        item.dr_alt = _dr(data.get("drAlt")) or self.tr("N/A")
        item.range = data.get("range") or ""
        item.name = (data.get("name") or "").strip()
        item.desc = data.get("notes") or ""

    # --- armor -------------------------------------------------------
    # A character wears at most one armour (the model's single pc.armor),
    # so these slots set/clear that one item via api.character.set_armor /
    # clear_armor (which own the dirty flag) rather than poking pc. Armour
    # is grouped with weapons in the QML "Arms & Armor" section. Replaces
    # the legacy ChooseItemDialog('armor') + CustomArmorDialog.

    @Slot(result="QVariantList")
    def availableArmors(self):
        """Catalogue feed for AddArmorDialog (browse) and the
        CustomArmorDialog base-template dropdown. Slot rather than Property
        so mid-session datapack imports show up without a restart."""
        out = []
        for a in (api.data.outfit.get_armors() or []):
            effect_ = api.data.outfit.get_effect(a.effectid)
            out.append({
                "name":   a.name,
                "tn":     int(a.tn or 0),
                "rd":     int(a.rd or 0),
                "cost":   _wstr(a.cost),
                "effect": effect_.text if effect_ is not None else "",
            })
        out.sort(key=lambda r: (r["name"] or "").lower())
        return out

    @Slot(str)
    def wearArmor(self, armor_name):
        """Wear a catalogue armour by name (the legacy 'Wear Armor' path).
        armor_outfit_from_db resolves its TN / RD / effect from the
        datapack."""
        if not armor_name:
            return
        if api.data.outfit.get_armor(armor_name) is None:
            log.api.warning(u"QML UI: wearArmor: unknown armor %r", armor_name)
            return
        item = l5r.models.armor_outfit_from_db(armor_name)
        if item is not None:
            api.character.set_armor(item)
            api.character.notify_character_refreshed()

    @Slot("QVariantMap")
    def wearCustomArmor(self, data):
        """Wear a custom armour (the legacy CustomArmorDialog add path)."""
        item = l5r.models.ArmorOutfit()
        self._apply_armor_fields(item, data)
        if not item.name:
            log.api.warning(u"QML UI: wearCustomArmor: refused unnamed armor")
            return
        api.character.set_armor(item)
        api.character.notify_character_refreshed()

    @Slot("QVariantMap")
    def editArmor(self, data):
        """Re-stat the worn armour in place (the legacy CustomArmorDialog
        edit path -- it pre-loaded pc.armor). Re-sets the same item so the
        dirty flag is owned by the api setter."""
        item = api.character.get_armor()
        if item is None:
            log.api.warning(u"QML UI: editArmor: no armor worn")
            return
        self._apply_armor_fields(item, data)
        api.character.set_armor(item)
        api.character.notify_character_refreshed()

    @Slot()
    def removeArmor(self):
        """Take off the worn armour."""
        api.character.clear_armor()
        api.character.notify_character_refreshed()

    def _apply_armor_fields(self, item, data):
        """Write the editable custom-armour fields onto `item`, mirroring
        CustomArmorDialog.on_accept: ints for TN / RD, name / notes
        verbatim."""
        def _int(v):
            try:
                return int(v)
            except (TypeError, ValueError):
                return 0

        item.tn = _int(data.get("tn"))
        item.rd = _int(data.get("rd"))
        item.name = (data.get("name") or "").strip()
        item.desc = data.get("notes") or ""

    # --- miscellanea: modifiers --------------------------------------
    # Custom roll/stat modifiers (the legacy ModifiersTableViewModel +
    # ModifierDialog). A modifier is a plain ModifierModel on pc.modifiers
    # (no XP, no rank history), so these slots delegate to the
    # api.character modifier setters -- which own the dirty flag -- rather
    # than poking pc directly. The proxy emits a session-stable
    # str(id(modifier)) handle per row; edit / remove / toggle re-resolve
    # the live item by scanning the list (mirrors removeWeapon).

    @Slot(result="QVariantList")
    def modifierTypes(self):
        """The modifier kinds offered by the add/edit dialog -- key, the
        translated label, the detail field's kind ("none" => disabled),
        and its prompt. Mirrors the legacy ModifierDialog combo."""
        return [{"key": key,
                 "label": self.tr(label),
                 "detailKind": detail_kind,
                 "detailLabel": self.tr(detail_label) if detail_label else ""}
                for (key, label, detail_kind, detail_label) in _MODIFIER_TYPE_DEFS]

    @Slot(str, str, str, str, bool)
    def addModifier(self, type_key, detail, value, reason, active):
        """Add a custom modifier. `value` is a roll-and-keep+bonus string
        (e.g. "+2", "1k0", "2k1+3"), parsed to the (roll, keep, bonus)
        tuple the rules engine sums; an unparseable value collapses to
        the zero tuple, same as the legacy dialog."""
        item = l5r.models.ModifierModel()
        item.type = type_key or "none"
        item.dtl = (detail or "").strip()
        item.value = api.rules.parse_rtk_with_bonus(value or "0k0")
        item.reason = (reason or "").strip()
        item.active = bool(active)
        api.character.add_modifier(item)
        api.character.notify_character_refreshed()

    @Slot(str, str, str, str, str, bool)
    def editModifier(self, mod_id, type_key, detail, value, reason, active):
        """Re-key an existing modifier in place (the legacy dialog's edit
        path). Re-resolves the live ModifierModel by its session id."""
        item = self._resolve_modifier(mod_id)
        if item is None:
            log.api.warning(u"QML UI: editModifier: no modifier %r", mod_id)
            return
        item.type = type_key or "none"
        item.dtl = (detail or "").strip()
        item.value = api.rules.parse_rtk_with_bonus(value or "0k0")
        item.reason = (reason or "").strip()
        item.active = bool(active)
        api.character.touch_modifiers()
        api.character.notify_character_refreshed()

    @Slot(str, bool)
    def setModifierActive(self, mod_id, active):
        """Toggle whether a modifier is currently applied (the legacy
        table's checkbox column)."""
        item = self._resolve_modifier(mod_id)
        if item is None:
            return
        item.active = bool(active)
        api.character.touch_modifiers()
        api.character.notify_character_refreshed()

    @Slot(str)
    def removeModifier(self, mod_id):
        """Remove a modifier by its session-stable id."""
        item = self._resolve_modifier(mod_id)
        if item is None:
            log.api.warning(u"QML UI: removeModifier: no modifier %r", mod_id)
            return
        api.character.remove_modifier(item)
        api.character.notify_character_refreshed()

    def _resolve_modifier(self, mod_id):
        """Re-resolve the live ModifierModel for a proxy-emitted id."""
        if not mod_id:
            return None
        pc = api.character.model()
        if not pc:
            return None
        for m in pc.get_modifiers() or []:
            if str(id(m)) == mod_id:
                return m
        return None

    # --- miscellanea: equipment + money ------------------------------
    # The starting outfit (school-granted) and the free-form equipment
    # list are both flat lists of plain strings; the proxy addresses each
    # entry by (kind, index). The api setters own the dirty flag, so these
    # slots rebuild the target list and hand it back rather than mutating
    # pc directly. Money is a (koku, bu, zeni) tuple via set_money (which
    # stores it as a delta from the school's starting money).

    @Slot(str)
    def addEquipment(self, text):
        """Append one free-form equipment entry."""
        api.character.add_equipment(text or self.tr("New item"))
        api.character.notify_character_refreshed()

    @Slot(str, int, str)
    def setEquipmentText(self, kind, index, text):
        """Re-key one equipment entry in place (inline edit)."""
        text = text or ""
        if kind == "starting":
            items = list(api.character.get_starting_outfit() or [])
            if 0 <= index < len(items):
                items[index] = text
                api.character.set_starting_outfit(items)
        else:
            items = list(api.character.get_equipment() or [])
            if 0 <= index < len(items):
                items[index] = text
                api.character.set_equipment(items)
        api.character.notify_character_refreshed()

    @Slot(str, int)
    def removeEquipment(self, kind, index):
        """Drop one equipment entry by its (kind, index)."""
        if kind == "starting":
            items = list(api.character.get_starting_outfit() or [])
            if 0 <= index < len(items):
                del items[index]
                api.character.set_starting_outfit(items)
        else:
            items = list(api.character.get_equipment() or [])
            if 0 <= index < len(items):
                del items[index]
                api.character.set_equipment(items)
        api.character.notify_character_refreshed()

    @Slot(int, int, int)
    def setMoney(self, koku, bu, zeni):
        """Set the character's purse. set_money stores the figure as a
        delta from the school's starting money and owns the dirty flag."""
        api.character.set_money((int(koku), int(bu), int(zeni)))
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
