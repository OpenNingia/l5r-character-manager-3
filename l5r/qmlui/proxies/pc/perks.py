# -*- coding: utf-8 -*-
# Copyright (C) 2014-2026 Daniele Simonetti
#
# Perks slice of PcProxy: the character's advantages (merits) and
# disadvantages (flaws), projected for PerksSection.qml.
#
# PerkAdv stores flaws with a negative `cost`. Display code wants the
# positive magnitude on both sides of the ledger, so this mixin
# normalises here: `cost` in the emitted dict is always >= 0, and the
# kind is implied by which list the entry appears in.
#
# A coarse `perksChanged` signal fires on character_refreshed and
# model_replaced, mirroring AdvancementsMixin. There is no per-perk
# signal in the bus.

from qtpy.QtCore import Property, Signal

import l5r.api as api
import l5r.api.character
import l5r.api.character.flaws
import l5r.api.character.merits
import l5r.api.character.rankadv
import l5r.api.data.flaws
import l5r.api.data.merits

from l5r.qmlui.proxies.pc.memo import invalidate, memoize


# 4e RAW caps disadvantage XP at 10. The app does not enforce it -- the
# cap is surfaced cosmetically in the section so the player can see the
# state, not so the app can block them. House rules vary widely.
_FLAWS_CAP = 10


def _suggested_cost(rule_id, rank_id, is_flaw):
    """Recompute the rulebook-suggested cost for (rule, rank), applying
    clan/tag discount exceptions the way api.data.merits.get_rank_cost
    does. Returns the positive magnitude; returns 0 if the datapack is
    not loaded (api.data.merits.get raises through a None ds).
    """
    try:
        if is_flaw:
            rank_row = api.data.flaws.get_rank(rule_id, rank_id)
        else:
            rank_row = api.data.merits.get_rank(rule_id, rank_id)
    except AttributeError:
        return 0
    if not rank_row:
        return 0
    cost = abs(rank_row.value)
    for ex in rank_row.exceptions or []:
        if api.character.has_tag_or_rule(ex.tag):
            cost = abs(ex.value)
    return int(cost)


def _resolve_perk(rule_id, is_flaw):
    """Look up the datapack row for a perk. Returns None when the
    datapack is not loaded -- can happen in tests, on a fresh install
    before any pack is imported, or if a character file references a
    rule from a pack the user removed."""
    try:
        if is_flaw:
            return api.data.flaws.get(rule_id)
        return api.data.merits.get(rule_id)
    except AttributeError:
        return None


def _resolve_name(rule_id, is_flaw):
    row = _resolve_perk(rule_id, is_flaw)
    return row.name if row else rule_id


def _resolve_category(perk_row):
    """Return the human-readable category name (Physical, Social, …)
    for a perk row. Looks up the perk's `type` field in
    `ctx.ds.perktypes`. Returns "" when nothing matches or when the
    datapack is not loaded."""
    if perk_row is None:
        return ""
    type_id = getattr(perk_row, "type", "") or ""
    if not type_id:
        return ""
    try:
        ds = api.data.model()
    except AttributeError:
        return type_id
    if ds is None:
        return type_id
    for t in getattr(ds, "perktypes", None) or []:
        if t.id == type_id:
            return t.name or type_id
    return type_id


def _project_entry(adv, is_flaw, is_starting):
    """Build the QVariantMap shape PerksSection.qml consumes."""
    magnitude = abs(int(adv.cost or 0))
    row = _resolve_perk(adv.perk, is_flaw)
    name = row.name if row else (adv.perk or "")
    suggested = _suggested_cost(adv.perk, adv.rank, is_flaw)
    category = _resolve_category(row)
    return {
        # `id(adv)` is a stable handle for as long as the proxy and the
        # PC model both live -- the only window we need it across.
        # Removal/edit slots resolve the adv by scanning pc.advans for
        # the matching id().
        "advId":         str(id(adv)),
        "ruleId":        adv.perk or "",
        "name":          name,
        "category":      category,
        "subtype":       getattr(adv, "extra", "") or "",
        "rank":          int(adv.rank) if adv.rank is not None else 0,
        "cost":          magnitude,
        # `suggestedCost` is the rulebook figure (with clan/tag
        # discounts applied) at the perk's current rank -- 0 when the
        # datapack is unavailable or the rank no longer exists in the
        # pack. The card surfaces a strikethrough comparison when this
        # differs from `cost` so the override stays visually auditable.
        "suggestedCost": suggested,
        "isCustom":      suggested != 0 and magnitude != suggested,
        "isStarting":    bool(is_starting),
    }


class PerksMixin:
    perksChanged = Signal()

    def _wire_perks(self, bus):
        bus.character_refreshed.connect(self._on_character_refreshed_perks)
        bus.model_replaced.connect(self._on_model_replaced_perks)

    def _on_character_refreshed_perks(self):
        invalidate(self, "merits", "flaws")
        self.perksChanged.emit()

    def _on_model_replaced_perks(self):
        invalidate(self, "merits", "flaws")
        self.perksChanged.emit()

    # ----- live registers ------------------------------------------

    @Property("QVariantList", notify=perksChanged)
    @memoize
    def merits(self):
        return self._collect("merit")

    @Property("QVariantList", notify=perksChanged)
    @memoize
    def flaws(self):
        return self._collect("flaw")

    def _collect(self, kind):
        pc = api.character.model()
        if not pc:
            return []
        is_flaw = kind == "flaw"

        # Starting-school grants -- no XP cost, can't be refunded.
        starting_ids = set()
        try:
            first = api.character.rankadv.get_first()
        except Exception:
            first = None
        if first:
            grants = first.flaws if is_flaw else first.merits
            for adv in grants or []:
                starting_ids.add(id(adv))

        rows = []
        for adv in pc.advans or []:
            if adv.type != "perk":
                continue
            # Flaws have negative cost; merits positive. Either tag also
            # works (the api layer sets both). Trust whichever is set.
            adv_kind = (getattr(adv, "tag", None)
                        or ("flaw" if (adv.cost or 0) < 0 else "merit"))
            if adv_kind != kind:
                continue
            rows.append(_project_entry(adv, is_flaw, id(adv) in starting_ids))

        # Also surface starting-school grants that don't live in the
        # advancement stack (rare but legal -- some datapacks attach
        # merits/flaws to the first rank directly).
        if first:
            grants = first.flaws if is_flaw else first.merits
            for adv in grants or []:
                if id(adv) in {id(a) for a in pc.advans or []}:
                    continue  # already in pc.advans, already projected
                rows.append(_project_entry(adv, is_flaw, True))
        return rows

    # ----- ledger totals -------------------------------------------

    @Property(int, notify=perksChanged)
    def meritsXp(self):
        return sum(r["cost"] for r in self._collect("merit"))

    @Property(int, notify=perksChanged)
    def flawsXp(self):
        return sum(r["cost"] for r in self._collect("flaw"))

    @Property(int, notify=perksChanged)
    def perksNetXp(self):
        return self.meritsXp - self.flawsXp

    @Property(int, constant=True)
    def flawsCap(self):
        return _FLAWS_CAP
