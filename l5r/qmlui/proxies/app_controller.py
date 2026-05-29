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
import l5r.api.character.powers
import l5r.api.character.rankadv
import l5r.api.character.schools
import l5r.api.character.skills
import l5r.api.data
import l5r.api.data.clans
import l5r.api.data.families
import l5r.api.data.flaws
import l5r.api.data.merits
import l5r.api.data.schools
import l5r.api.data.skills
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
    L5R_RPG_HOME_PAGE,
    PROJECT_PAGE_LINK,
    PROJECT_PAGE_NAME,
)
from l5r.util import log, names
from l5r.util.fsutil import get_app_file, get_app_icon_path
from l5r.util.settings import L5RCMSettings


# Single-kanji glyphs lean on the system CJK font (no bundled face) --
# the L5R setting is fantasy-Japan, so a kanji column reads as part of
# the document rather than UI chrome. Each pick is one kanji that maps
# to the tab's concept by L5R-idiomatic reading (ryū for techniques,
# mon for about/clan crest, etc.). On a host with no CJK font installed
# the fallback box is ugly -- that's the known trade vs. the previous
# universal Unicode symbols.
_TAB_DEFS = [
    ("pc_info",       "Character",     "侍"),  # samurai
    ("skills",        "Skills",        "技"),  # gi -- technique / skill
    ("perks",         "Merits/Flaws",  "縁"),  # en -- bond / karma (neutral)
    ("techniques",    "Techniques",    "流"),  # ryū -- school / style
    ("spells",        "Spells",        "呪"),  # ju -- spell / incantation
    ("kata",          "Kata",          "型"),  # kata -- form
    ("kiho",          "Kiho",          "気"),  # ki -- spirit / breath
    ("tattoo",        "Tattoos",       "彫"),  # chō -- carve / engrave (irezumi)
    ("advancements",  "Advancements",  "道"),  # dō -- way / path
    ("weapons",       "Weapons",       "刀"),  # tō -- katana / blade
    ("misc",          "Miscellanea",   "雑"),  # zatsu -- miscellaneous (modifiers + equipment)
    ("notes",         "Notes",         "記"),  # ki -- record / note
    ("settings",      "Settings",      "設"),  # setsu -- setup
    ("about",         "About",         "紋"),  # mon -- clan crest
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
        or (when on an alternate path) resume the former school. Multiclass
        ('join a new school') is not surfaced here yet, so when the only
        way forward is to join a new school -- on a path with no former
        school to return to -- `canContinue` is False and the dialog
        explains why advancing is unavailable."""
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
            "nextRank":      next_rank,
            "onPath":        on_path,
            "currentSchool": current_name,
            "formerSchool":  former_name,
            "canContinue":   can_continue,
        }

    @Slot()
    def advanceRank(self):
        """Advance in the current school, or resume the former school when
        on an alternate path -- the legacy NextRankDlg 'go on' branch.
        Multiclass is deferred. Guards on availability (advance_rank assumes
        a pending rank-up) and owns the dirty flag (the rankadv helpers
        append the advancement directly and do not)."""
        if api.character.model() is None:
            return
        if api.character.insight_rank() <= api.character.insight_rank(strict=True):
            return  # no pending rank-up; nothing to do

        current_id = api.character.schools.get_current()
        if api.data.schools.is_path(current_id):
            res = api.character.rankadv.leave_path()
        else:
            res = api.character.rankadv.advance_rank()
        if res:
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
