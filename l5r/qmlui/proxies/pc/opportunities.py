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
# `_compute_opportunities` builds the *complete* truth (every opportunity
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

from l5r.util import log


# tabIds whose opportunity has a working destination CTA today. Grow this
# as flows are ported: "skills" (granted skills picker), "spells" (free
# spells). Until a tabId is listed here its opportunity is computed but
# not badged -- no dead-end badges.
#   pc_info  -- rank advancement (Character section "Advance Rank" CTA)
#   kiho     -- rank-granted free kiho (Kiho section)
_SURFACED_OPPORTUNITIES = {"pc_info", "kiho"}


class OpportunitiesMixin:
    opportunitiesChanged = Signal()

    def _wire_opportunities(self, bus):
        bus.character_refreshed.connect(self._on_opportunities_changed)
        bus.model_replaced.connect(self._on_opportunities_changed)

    def _on_opportunities_changed(self):
        self.opportunitiesChanged.emit()

    def _can_advance_rank(self):
        """True when the character's potential Insight Rank outruns the
        rank actually taken -- i.e. a rank-up is waiting. Shared by the
        badge map and the `canAdvanceRank` property so both agree."""
        try:
            return api.character.insight_rank() > api.character.insight_rank(strict=True)
        except Exception:
            return False

    def _compute_opportunities(self):
        """Full map of pending opportunities, keyed by the tabId of the
        section that resolves each, to a count. Pure reads; mirrors the
        legacy NiceBar checks in l5r/ui/advance.py. (Affinity/deficiency
        choice has no ported home section yet, so it is omitted here
        rather than badged nowhere.)"""
        pc = api.character.model()
        if not pc:
            return {}

        out = {}
        try:
            # Reached a new Insight Rank -> the ROOT opportunity, resolved
            # in the Character section. Every grant below (free kiho /
            # spells / skills / affinity) is applied *by* this rank-up, so
            # it is listed first. It lives on Character -- a forward-looking
            # "decide your destiny" choice belongs on the dashboard, not
            # the Advancements ledger (which is history).
            if self._can_advance_rank():
                out["pc_info"] = out.get("pc_info", 0) + 1

            rank_ = api.character.rankadv.get_last()

            # School-granted skills / emphases to choose -> Skills.
            if rank_:
                wc = len(rank_.skills_to_choose or []) + len(rank_.emphases_to_choose or [])
                if wc:
                    out["skills"] = out.get("skills", 0) + wc

            # School-granted free spells (shugenja) -> Spells.
            if api.character.rankadv.has_granted_free_spells():
                out["spells"] = out.get("spells", 0) + 1

            # Rank-granted free kiho (monks) -> Kiho.
            free_kiho = int(api.character.rankadv.get_gained_kiho_count() or 0)
            if free_kiho:
                out["kiho"] = out.get("kiho", 0) + free_kiho
        except Exception:
            # An opportunity probe should never break the whole sheet;
            # degrade to whatever was computed before the failure.
            log.api.debug(u"opportunity probe failed", exc_info=1)

        return out

    @Property("QVariantMap", notify=opportunitiesChanged)
    def opportunityBadges(self):
        full = self._compute_opportunities()
        return {k: v for k, v in full.items() if k in _SURFACED_OPPORTUNITIES}

    @Property(bool, notify=opportunitiesChanged)
    def canAdvanceRank(self):
        """Whether a rank-up is waiting -- drives the Character section's
        'Advance Rank' callout. A dedicated flag (not the pc_info badge
        count) so the callout stays correct if another opportunity is ever
        mapped to the Character section too."""
        if api.character.model() is None:
            return False
        return self._can_advance_rank()

    @Property(int, notify=opportunitiesChanged)
    def freeKihoCount(self):
        """Free kiho the character may learn without spending XP (granted
        by a School rank). Drives the Kiho section's 'N FREE' pill and the
        zero-cost display in BuyKihoDialog; the discount itself is applied
        by api.character.powers.buy_kiho."""
        return int(api.character.rankadv.get_gained_kiho_count() or 0)
