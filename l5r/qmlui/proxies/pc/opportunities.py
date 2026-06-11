# -*- coding: utf-8 -*-
# Copyright (C) 2014-2026 Daniele Simonetti
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# Opportunities slice of PcProxy: the "you have unlocked something"
# prompts the legacy UI surfaced through its NiceBar (l5r/ui/advance.py).
#
# These are *pending state*, not transient events: a granted free kiho, a
# rank-up choice, school-granted skills, free spells -- each stays true
# until the player acts on it (and survives save/reload because it lives
# on the rank advancement). So they are modelled declaratively here and
# re-emitted on every refresh, rather than fired as one-shot toasts.
#
# The QML side renders these as a count badge on the relevant section's
# TOC entry (the section it is resolved in); the section itself carries
# the actual call-to-action button. So the map is keyed by **tabId** ->
# count.
#
# `compute_opportunities` builds the *complete* truth (every opportunity
# with a home section). `opportunityBadges` then surfaces only those whose
# destination section already has a working CTA in the QML UI, via the
# `_SURFACED_OPPORTUNITIES` allow-list -- so we never badge a section that
# has no button yet. As each flow is ported, add its tabId to that set
# (the matching in-section CTA should land in the same change).
#
# Getters read live from api.character.model(); a coarse
# `opportunitiesChanged` signal fires on character_refreshed /
# model_replaced, mirroring the other slices.

from qtpy.QtCore import Property, Signal

import l5r.api as api
import l5r.api.character
import l5r.api.character.rankadv

from l5r.qmlui.proxies.pc.memo import invalidate, memoize
from l5r.util import log


# tabIds whose opportunity has a working destination CTA today. Until a
# tabId is listed here its opportunity is computed but not badged -- no
# dead-end badges.
#   pc_info  -- rank advancement (Character section "Advance Rank" CTA)
#   kiho     -- rank-granted free kiho (Kiho section)
#   skills   -- school-granted wildcard skill/emphasis picks (Skills section
#               "Choose Skills" CTA + ChooseSchoolSkillsDialog)
#   spells   -- school-granted free spells AND the elemental affinity/
#               deficiency choice (Spells section CTAs + ChooseSchoolSpells
#               Dialog / ChooseElementDialog). All three resolve there.
_SURFACED_OPPORTUNITIES = {"pc_info", "kiho", "skills", "spells"}


def _can_advance_rank():
    """True when the character's potential Insight Rank outruns the rank
    actually taken -- i.e. a rank-up is waiting. Shared by the badge map and
    the `canAdvanceRank` property so both agree."""
    try:
        return api.character.insight_rank() > api.character.insight_rank(strict=True)
    except Exception:
        return False


def compute_opportunities():
    """Full map of pending opportunities, keyed by the tabId of the section
    that resolves each, to a count. Pure reads; mirrors the legacy NiceBar
    checks in l5r/ui/advance.py. The shugenja choices (free spells, elemental
    affinity, elemental deficiency) all resolve on the Spells section, so they
    accumulate into a single "spells" count."""
    pc = api.character.model()
    if not pc:
        return {}

    out = {}
    try:
        # Reached a new Insight Rank -> the ROOT opportunity, resolved in
        # the Character section. Every grant below (free kiho / spells /
        # skills / affinity) is applied *by* this rank-up, so it is listed
        # first. It lives on Character -- a forward-looking "decide your
        # destiny" choice belongs on the dashboard, not the Advancements
        # ledger (which is history).
        if _can_advance_rank():
            out["pc_info"] = out.get("pc_info", 0) + 1

        rank_ = api.character.rankadv.get_last()

        # School-granted skills / emphases to choose -> Skills.
        if rank_:
            wc = len(rank_.skills_to_choose or []) + len(rank_.emphases_to_choose or [])
            if wc:
                out["skills"] = out.get("skills", 0) + wc

        # Shugenja choices, all resolved on the Spells section:
        #   - free spells granted by the school rank,
        #   - an elemental affinity to choose (school grants `any`/`nonvoid`),
        #   - an elemental deficiency to choose.
        # They share the "spells" tabId so the TOC badge counts every pending
        # shugenja decision at once. Resolving any one re-fires this probe.
        if api.character.rankadv.has_granted_free_spells():
            out["spells"] = out.get("spells", 0) + 1
        if rank_:
            elem = len(rank_.affinities_to_choose or []) + len(rank_.deficiencies_to_choose or [])
            if elem:
                out["spells"] = out.get("spells", 0) + elem

        # Rank-granted free kiho (monks) -> Kiho.
        free_kiho = int(api.character.rankadv.get_gained_kiho_count() or 0)
        if free_kiho:
            out["kiho"] = out.get("kiho", 0) + free_kiho
    except Exception:
        # An opportunity probe should never break the whole sheet; degrade
        # to whatever was computed before the failure.
        log.api.debug(u"opportunity probe failed", exc_info=1)

    return out


def surfaced_opportunities():
    """compute_opportunities() filtered to those whose destination section
    has a working CTA today (the _SURFACED_OPPORTUNITIES allow-list) -- so we
    never surface a dead-end."""
    full = compute_opportunities()
    return {k: v for k, v in full.items() if k in _SURFACED_OPPORTUNITIES}


def blocking_opportunities():
    """The surfaced opportunities that must be resolved BEFORE advancing
    rank: every surfaced one except the rank-up itself (pc_info), which *is*
    the advancement. Advancing appends a new 'last' rank and the choice
    getters read only the last rank, so these would be silently orphaned.

    This reuses the same allow-list as the badges, so it scales: each flow
    added to _SURFACED_OPPORTUNITIES (as it gains a QML CTA) starts blocking
    automatically, and a grant with no resolution path yet (e.g. free
    spells, affinity/deficiency) is *not* in the list, so it never
    dead-locks the advance."""
    return {k: v for k, v in surfaced_opportunities().items() if k != "pc_info"}


def has_blocking_opportunities():
    """True if any surfaced opportunity other than the rank-up itself is
    still unresolved -- the rank-advance gate (see blocking_opportunities)."""
    return bool(blocking_opportunities())


class OpportunitiesMixin:
    opportunitiesChanged = Signal()

    def _wire_opportunities(self, bus):
        bus.character_refreshed.connect(self._on_opportunities_changed)
        bus.model_replaced.connect(self._on_opportunities_changed)

    def _on_opportunities_changed(self):
        invalidate(self, "opportunityBadges")
        self.opportunitiesChanged.emit()

    @Property("QVariantMap", notify=opportunitiesChanged)
    @memoize
    def opportunityBadges(self):
        return surfaced_opportunities()

    @Property(bool, notify=opportunitiesChanged)
    def canAdvanceRank(self):
        """Whether a rank-up is waiting -- drives the Character section's
        'Advance Rank' callout. A dedicated flag (not the pc_info badge
        count) so the callout stays correct if another opportunity is ever
        mapped to the Character section too."""
        if api.character.model() is None:
            return False
        return _can_advance_rank()

    @Property(bool, notify=opportunitiesChanged)
    def hasPendingOpportunities(self):
        """Whether the player still has surfaced opportunities to resolve
        before advancing rank (school skills, free kiho, ... -- everything
        except the rank-up itself). Drives the outer 'Advance Rank' button,
        which nudges with a reminder toast instead of opening the dialog
        while any remain, so advancing never silently orphans a grant."""
        if api.character.model() is None:
            return False
        return has_blocking_opportunities()

    @Property(int, notify=opportunitiesChanged)
    def schoolSkillChoiceCount(self):
        """School-granted skill/emphasis picks still pending -- drives the
        Skills section's 'Choose Skills' callout and the count it shows.
        A dedicated count (not the 'skills' badge) so the callout stays
        correct if another opportunity is ever mapped to the Skills section
        too. Mirrors the legacy AdvanceMixin.check_new_skills nicebar
        (api.character.rankadv.has_granted_skills_to_choose) and the same
        sum computed in compute_opportunities."""
        if api.character.model() is None:
            return 0
        rank_ = api.character.rankadv.get_last()
        if not rank_:
            return 0
        return len(rank_.skills_to_choose or []) + len(rank_.emphases_to_choose or [])

    @Property(int, notify=opportunitiesChanged)
    def freeKihoCount(self):
        """Free kiho the character may learn without spending XP (granted
        by a School rank). Drives the Kiho section's 'N FREE' pill and the
        zero-cost display in BuyKihoDialog; the discount itself is applied
        by api.character.powers.buy_kiho."""
        return int(api.character.rankadv.get_gained_kiho_count() or 0)

    # --- shugenja choices, all resolved on the Spells section ---------
    # Three dedicated flags (not the shared "spells" badge count) so each
    # Spells-section callout shows/hides independently. They are surfaced in
    # priority order in the QML (affinity -> deficiency -> free spells) so the
    # player fixes the elemental leanings -- which set which masteries are in
    # reach -- before choosing spells against them. Mirrors the legacy
    # AdvanceMixin.check_affinity_wc / check_school_new_spells nicebars.

    @Property(int, notify=opportunitiesChanged)
    def affinityChoiceCount(self):
        """Pending elemental-affinity choices on the current rank advancement
        (school grants `any`/`nonvoid`). Drives the Spells section's 'awakens
        an affinity' callout."""
        if api.character.model() is None:
            return 0
        rank_ = api.character.rankadv.get_last()
        return len(rank_.affinities_to_choose or []) if rank_ else 0

    @Property(int, notify=opportunitiesChanged)
    def deficiencyChoiceCount(self):
        """Pending elemental-deficiency choices on the current rank
        advancement. Drives the Spells section's 'exacts a deficiency'
        callout."""
        if api.character.model() is None:
            return 0
        rank_ = api.character.rankadv.get_last()
        return len(rank_.deficiencies_to_choose or []) if rank_ else 0

    @Property(bool, notify=opportunitiesChanged)
    def freeSpellChoicePending(self):
        """Whether the character has school-granted free spells still to
        choose (shugenja). Drives the Spells section's 'grants spells' callout
        and gates the ChooseSchoolSpellsDialog -- mirrors
        api.character.rankadv.has_granted_free_spells."""
        if api.character.model() is None:
            return False
        return api.character.rankadv.has_granted_free_spells()
