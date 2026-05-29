# -*- coding: utf-8 -*-
# Copyright (C) 2014-2026 Daniele Simonetti
#
# Weapons slice of PcProxy: the character's carried weapons, each row
# bundled with the data WeaponsSection.qml needs to render and act on.
#
# A weapon belongs to one or more of the three combat categories
# (melee / ranged / arrow) by virtue of those strings appearing in its
# `tags` -- the same partition the legacy WeaponTableViewModel used to
# split the three tables. The attack / damage rolls are recomputed live
# from api.rules (they depend on traits + skill rank + modifiers, so
# they must not be cached) and formatted in roll-and-keep notation.
#
# Row identity is str(id(weapon)) -- stable within a session, mirroring
# the perks slice. It keys edit / remove / quantity actions back through
# AppController, which re-resolves the live WeaponOutfit by scanning the
# list. Getters read live from api.character.model(); a coarse
# `weaponsChanged` signal fires on character_refreshed / model_replaced.
#
# Row shape consumed by WeaponsSection.qml:
#   { id:          str    (session-stable handle for edit/remove/qty)
#     name:        str
#     skill:       str    (weapon skill display name, e.g. "Kenjutsu")
#     categories:  [str]  (subset of ["melee", "ranged", "arrow"]; a
#                          throwable weapon files on every rail it names)
#     tags:        [str]  (the weapon's full tag set -- categories plus
#                          descriptors like small/large/samurai/peasant)
#     dr:          str    (primary damage rating, e.g. "3k2" or "N/A")
#     drAlt:       str    (secondary damage rating)
#     range:       str    (ranged weapons; e.g. "250'")
#     strength:    str    (ranged weapon strength)
#     minStr:      str    (minimum Strength to wield)
#     qty:         int    (stack size; meaningful for arrows)
#     baseAtk:     str    modAtk: str   (attack roll, pre/post modifiers)
#     baseDmg:     str    modDmg: str   (damage roll, pre/post modifiers)
#     description: str    (effect / notes prose) }

from qtpy.QtCore import Property, Signal

import l5r.api as api
import l5r.api.character
import l5r.api.character.weapons
import l5r.api.rules

from l5r.util import log

# The three combat categories, in reading order. A weapon shows on every
# rail its tags name -- a throwable melee weapon (tagged melee+ranged,
# e.g. the wakizashi) appears under both Melee (with its DR/ATK/DMG) and
# Ranged (with its thrown range/ATK), the same way the legacy three-table
# UI presented it. That is the weapon in two combat modes, not a
# duplicate; identical-name duplicates were a separate DAL bug, fixed in
# l5rdal.
_CATEGORIES = ("melee", "ranged", "arrow")


def _s(value):
    """Stringify a weapon stat for display. Stats arrive as ints, the
    sentinel "N/A", or None depending on whether they came from the DB or
    a custom build; the QML side wants a plain string either way."""
    if value is None:
        return ""
    return str(value)


class WeaponsMixin:
    weaponsChanged = Signal()

    def _wire_weapons(self, bus):
        bus.character_refreshed.connect(self._on_character_refreshed_weapons)
        bus.model_replaced.connect(self._on_model_replaced_weapons)

    def _on_character_refreshed_weapons(self):
        self.weaponsChanged.emit()

    def _on_model_replaced_weapons(self):
        self.weaponsChanged.emit()

    @Property("QVariantList", notify=weaponsChanged)
    def weapons(self):
        pc = api.character.model()
        if not pc:
            return []

        rows = []
        for w in api.character.weapons.get_all():
            tags = list(getattr(w, "tags", None) or [])
            categories = [c for c in _CATEGORIES if c in tags]

            # Rolls depend on live trait/skill/modifier state -- compute
            # them per projection rather than trusting any cached value.
            try:
                base_atk = api.rules.format_rtk_t(
                    api.rules.calculate_base_attack_roll(pc, w))
                mod_atk = api.rules.format_rtk_t(
                    api.rules.calculate_mod_attack_roll(pc, w))
                base_dmg = api.rules.format_rtk_t(
                    api.rules.calculate_base_damage_roll(pc, w))
                mod_dmg = api.rules.format_rtk_t(
                    api.rules.calculate_mod_damage_roll(pc, w))
            except Exception:
                log.api.debug(u"weapons proxy: roll calc failed for %s",
                              getattr(w, "name", "?"), exc_info=True)
                base_atk = mod_atk = base_dmg = mod_dmg = ""

            rows.append({
                "id":          str(id(w)),
                "name":        w.name or "",
                "skill":       getattr(w, "skill_nm", "") or "",
                "categories":  categories,
                "tags":        tags,
                "dr":          _s(w.dr),
                "drAlt":       _s(w.dr_alt),
                "range":       _s(w.range),
                "strength":    _s(w.strength),
                "minStr":      _s(w.min_str),
                "qty":         int(getattr(w, "qty", 1) or 1),
                "baseAtk":     base_atk,
                "modAtk":      mod_atk,
                "baseDmg":     base_dmg,
                "modDmg":      mod_dmg,
                "description": getattr(w, "desc", "") or "",
            })
        return rows
