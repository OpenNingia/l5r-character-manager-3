# -*- coding: utf-8 -*-
# Copyright (C) 2014-2026 Daniele Simonetti
#
# Combat slice of PcProxy: initiative roll, armor TN/RD, wound table,
# and the health-rank multiplier. All four bundles are derived from
# advancements + equipment + rules, so a single coarse `combatChanged`
# is sufficient.

from qtpy.QtCore import Property, Signal

import l5r.api as api
import l5r.api.character
import l5r.api.rules

from l5r.qmlui.proxies.pc.memo import invalidate, memoize


def _wound_label(idx, name):
    """Friendly label string for one row of the wound table. Mirrors
    the QWidget ui.health.HealthDisplayMixin output: '+3 Nicked',
    '+5 Grazed', ..., or just 'Out' for the last (8th) row."""
    if name == "out":
        return api.tr("Out")
    penalty = api.rules.get_wound_penalties(idx)
    label = api.tr(name)
    if penalty:
        return "+{0} {1}".format(penalty, label)
    return label


_WOUND_NAMES = [
    "healthy", "nicked", "grazed", "hurt",
    "injured", "crippled", "down", "out",
]


class CombatMixin:
    combatChanged = Signal()

    def _wire_combat(self, bus):
        bus.character_refreshed.connect(self._on_character_refreshed_combat)
        bus.model_replaced.connect(self._on_model_replaced_combat)
        # Wounds / health-multiplier changes use a narrow signal so a
        # wounds +/- click refreshes only this slice, not the whole sheet.
        bus.wounds_changed.connect(self._on_character_refreshed_combat)

    def _on_character_refreshed_combat(self):
        invalidate(self, "initiative", "armorTn", "wounds")
        self.combatChanged.emit()

    def _on_model_replaced_combat(self):
        invalidate(self, "initiative", "armorTn", "wounds")
        self.combatChanged.emit()

    @Property("QVariantMap", notify=combatChanged)
    @memoize
    def initiative(self):
        pc = api.character.model()
        if not pc:
            return {"base": "", "mod": "", "current": ""}
        return {
            "base":    api.rules.format_rtk_t(api.rules.get_base_initiative()),
            "mod":     api.rules.format_rtk_t(api.rules.get_init_modifiers()),
            "current": api.rules.format_rtk_t(api.rules.get_tot_initiative()),
        }

    @Property("QVariantMap", notify=combatChanged)
    @memoize
    def armorTn(self):
        pc = api.character.model()
        if not pc:
            return {"name": "", "baseTn": 0, "armorTn": 0, "armorTnMod": 0,
                    "rd": 0, "currentTn": 0, "desc": ""}
        return {
            "name":       str(api.character.get_armor_name()),
            "baseTn":     int(api.character.get_base_tn()),
            "armorTn":    int(api.character.get_armor_tn()),
            "armorTnMod": int(api.character.get_armor_tn_mod()),
            "rd":         int(api.character.get_full_rd()),
            "currentTn":  int(api.character.get_full_tn()),
            "desc":       str(api.character.get_armor_desc()),
        }

    @Property("QVariantList", notify=combatChanged)
    @memoize
    def wounds(self):
        pc = api.character.model()
        if not pc:
            return []
        table = api.rules.get_wounds_table() or []
        rows = []
        for idx, row in enumerate(table):
            inc, total, stacked, inc_w, total_w, stacked_w = row
            name = _WOUND_NAMES[idx] if idx < len(_WOUND_NAMES) else ""
            # get_wound_penalties only covers rows 0..6 (Healthy..Down);
            # OUT is fatal, not penalised. Report 0 for OUT so the QML
            # consumer can branch on the row index alone.
            penalty = int(api.rules.get_wound_penalties(idx)) if idx < 7 else 0
            rows.append({
                "key":     name,
                "label":   _wound_label(idx, name),
                "value":   int(stacked),
                "inc":     int(inc),
                "taken":   int(stacked_w) if stacked_w else 0,
                "penalty": penalty,
            })
        return rows

    @Property(int, notify=combatChanged)
    def healthMultiplier(self):
        pc = api.character.model()
        return int(pc.health_multiplier) if pc else 2

    @Property(int, notify=combatChanged)
    def currentWounds(self):
        pc = api.character.model()
        return int(pc.wounds) if pc else 0

    @Property(int, notify=combatChanged)
    def maxWounds(self):
        if not api.character.model():
            return 0
        return int(api.rules.get_max_wounds())

    @Property(int, notify=combatChanged)
    def currentWoundLevel(self):
        # Index 0..7 of the wound row the player is currently *at*.
        # Mirrors the rules layer: the last row where `stacked_wounds`
        # is non-zero is the player's level (see api.rules.get_wounds_table).
        # Defaults to 0 (Healthy) when no wounds have been taken.
        if not api.character.model():
            return 0
        table = api.rules.get_wounds_table() or []
        last = 0
        for idx, row in enumerate(table):
            stacked_w = row[5]
            if stacked_w:
                last = idx
        return last
