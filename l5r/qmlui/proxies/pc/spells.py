# -*- coding: utf-8 -*-
# Copyright (C) 2014-2026 Daniele Simonetti
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# Spells slice of PcProxy: the spells the character knows, projected for
# SpellsSection.qml. This replaces the spell half of the legacy
# l5r/ui/tabs/techniques.py (the tech half is the `techniques` section).
#
# A character knows a spell through one of three channels, which the row
# flags distinguish so the section can act on each correctly:
#   - isSchool    -- bound to a rank advancement (granted to shugenja as
#                    they advance). Not individually removable; managed on
#                    Advancements.
#   - isLearned   -- a free-form SpellAdv (cost 0). Removable.
#   - isMemorized -- a MemoSpellAdv (cost == mastery XP), the legacy
#                    "memorize" toggle. Carries an XP cost; forgetting it
#                    refunds that cost.
# A single spell may be more than one of these at once (e.g. a school
# spell can also be memorized), so the channels are flags on one deduped
# row, not separate lists.
#
# Affinity / deficiency are the elemental leanings the character's school
# grants -- shown as the header of the section, exactly as the legacy tab
# showed them above the spell table.
#
# Each spell row carries what SpellsSection's card consumes:
#   { id:           "the_fires_of_purity",   // also keys every action
#     name:         "The Fires of Purity",
#     element:      "fire",                   // ring key, or "multi"/"dragon"
#     elementLabel: "Fire",                   // localised; multi -> "Air, Fire"
#     mastery:      3,
#     masteryMod:   1,                         // affinity(+) / deficiency(-)
#     range:        "100 feet",
#     area:         "…",
#     duration:     "…",
#     raises:       "Range, Area",            // joined raise options
#     tags:         ["attack", "fire"],
#     source:       "Core p.182",
#     description:  "…",                       // prose; may be ""
#     isSchool:     true,
#     isLearned:    false,
#     isMemorized:  false,
#     cost:         0 }                         // XP paid (memo cost, else 0)
#
# Getters read live from api.character.model(); a coarse `spellsChanged`
# signal fires on character_refreshed / model_replaced, mirroring the
# other slices.

from qtpy.QtCore import Property, Signal

import l5r.api as api
import l5r.api.character
import l5r.api.character.spells
import l5r.api.data
import l5r.api.data.spells

from l5r.qmlui.proxies.pc.memo import invalidate, memoize
from l5r.util import log


# The five rings, in the canonical L5R order the rest of the sheet uses.
# A spell whose element is one of these gets the ring hue; "multi" /
# "dragon" spells fall outside the palette and the section renders them
# in gold (decided QML-side from this key).
_RING_KEYS = ("earth", "air", "water", "fire", "void")

# Sort rank for a spell's element ("magic school"): the canonical ring
# order above, with multi-element / dragon / anything off-palette sorted
# after the five rings.
_ELEMENT_ORDER = {key: idx for idx, key in enumerate(_RING_KEYS)}


def _element_sort_key(element):
    return _ELEMENT_ORDER.get(element, len(_RING_KEYS))


def _element_label(spell):
    """Localised element name for a spell. Multi-element spells join
    their constituent rings (mirrors the legacy SpellTableViewModel)."""
    def ring_text(key):
        ring_ = api.data.get_ring(key)
        return ring_.text if ring_ else (key or "").title()

    if api.data.spells.is_multi_element(spell.id):
        return u", ".join(ring_text(x) for x in (spell.elements or []))
    return ring_text(spell.element)


def _element_label_for_key(key):
    """Localised label for a bare affinity/deficiency key. Falls back to
    a title-cased form for compound keys ('maho fire', 'wards', …) that
    are not rings."""
    ring_ = api.data.get_ring(key)
    if ring_:
        return ring_.text
    return (key or "").replace("_", " ").title()


def _spell_source(spell):
    """'Pack p.NN' string for the spell, or '' when unavailable."""
    try:
        pack = getattr(spell, "pack", None)
        pack_name = pack.display_name if pack else ""
        page = getattr(spell, "page", 0) or 0
        if pack_name and page:
            return u"{0} p.{1}".format(pack_name, page)
        return pack_name or ""
    except Exception:
        return ""


class SpellsMixin:
    spellsChanged = Signal()

    def _wire_spells(self, bus):
        bus.character_refreshed.connect(self._on_character_refreshed_spells)
        bus.model_replaced.connect(self._on_model_replaced_spells)

    def _on_character_refreshed_spells(self):
        invalidate(self, "spells", "spellAffinities", "spellDeficiencies")
        self.spellsChanged.emit()

    def _on_model_replaced_spells(self):
        invalidate(self, "spells", "spellAffinities", "spellDeficiencies")
        self.spellsChanged.emit()

    @Property("QVariantList", notify=spellsChanged)
    @memoize
    def spells(self):
        pc = api.character.model()
        if not pc:
            return []

        school_ids = set(api.character.spells.get_school_spells())
        learned_ids = set(api.character.spells.get_learned_spells())
        memo_ids = set(api.character.spells.get_memorized_spells())

        # Preserve a stable enumeration order while de-duplicating: a
        # spell known through more than one channel must appear once.
        ordered = []
        seen = set()
        for sid in (api.character.spells.get_all()
                    + list(memo_ids)):
            if sid in seen:
                continue
            seen.add(sid)
            ordered.append(sid)

        rows = []
        for sid in ordered:
            spell = api.data.spells.get(sid)
            if not spell:
                # Character file references a spell from a pack the user
                # removed (or no datapack loaded). Skip rather than break
                # the whole register.
                log.api.debug(u"spells proxy: could not resolve spell %s", sid)
                continue

            element = (spell.element or "void").lower()
            try:
                mastery_mod = int(api.character.spells.get_mastery_modifier(spell))
            except Exception:
                mastery_mod = 0

            is_memorized = sid in memo_ids
            # Memorized spells carry an XP cost equal to mastery (the
            # MemoSpellAdv cost); every other channel is free.
            cost = int(spell.mastery) if (is_memorized and spell.mastery) else 0

            rows.append({
                "id":           spell.id,
                "name":         spell.name or spell.id,
                "element":      element,
                "elementLabel": _element_label(spell),
                "mastery":      int(spell.mastery) if spell.mastery is not None else 0,
                "masteryMod":   mastery_mod,
                "range":        spell.range or "",
                "area":         spell.area or "",
                "duration":     spell.duration or "",
                "raises":       u", ".join(spell.raises or []),
                "tags":         list(api.data.spells.tags(spell.id)),
                "source":       _spell_source(spell),
                "description":  getattr(spell, "desc", "") or "",
                "isSchool":     sid in school_ids,
                "isLearned":    sid in learned_ids,
                "isMemorized":  is_memorized,
                "cost":         cost,
            })

        # Mastery descending (the mightiest incantations first), then by
        # the spell's element ("magic school") in canonical ring order,
        # then alphabetically by name.
        rows.sort(key=lambda r: (-r["mastery"],
                                 _element_sort_key(r["element"]),
                                 (r["name"] or "").lower()))
        return rows

    @Property("QVariantList", notify=spellsChanged)
    @memoize
    def spellAffinities(self):
        """Localised elemental affinities granted by the character's
        school(s). Empty list when the character has none."""
        if not api.character.model():
            return []
        try:
            return [_element_label_for_key(k)
                    for k in api.character.spells.affinities()]
        except Exception:
            log.api.debug(u"spells proxy: affinities probe failed", exc_info=1)
            return []

    @Property("QVariantList", notify=spellsChanged)
    @memoize
    def spellDeficiencies(self):
        """Localised elemental deficiencies. Empty list when none."""
        if not api.character.model():
            return []
        try:
            return [_element_label_for_key(k)
                    for k in api.character.spells.deficiencies()]
        except Exception:
            log.api.debug(u"spells proxy: deficiencies probe failed", exc_info=1)
            return []

    @Property(bool, notify=spellsChanged)
    def isShugenja(self):
        """Whether the character follows a shugenja school -- tailors the
        empty-state copy (a shugenja's empty spellbook reads differently
        from a bushi who has merely memorized a scroll or two)."""
        if not api.character.model():
            return False
        try:
            return bool(api.character.is_shugenja())
        except Exception:
            return False
