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

    def _on_character_refreshed_combat(self):
        self.combatChanged.emit()

    def _on_model_replaced_combat(self):
        self.combatChanged.emit()

    @Property("QVariantMap", notify=combatChanged)
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
    def armorTn(self):
        pc = api.character.model()
        if not pc:
            return {"name": "", "baseTn": 0, "armorTn": 0,
                    "rd": 0, "currentTn": 0, "desc": ""}
        return {
            "name":      str(api.character.get_armor_name()),
            "baseTn":    int(api.character.get_base_tn()),
            "armorTn":   int(api.character.get_armor_tn()),
            "rd":        int(api.character.get_full_rd()),
            "currentTn": int(api.character.get_full_tn()),
            "desc":      str(api.character.get_armor_desc()),
        }

    @Property("QVariantList", notify=combatChanged)
    def wounds(self):
        pc = api.character.model()
        if not pc:
            return []
        table = api.rules.get_wounds_table() or []
        rows = []
        for idx, row in enumerate(table):
            inc, total, stacked, inc_w, total_w, stacked_w = row
            name = _WOUND_NAMES[idx] if idx < len(_WOUND_NAMES) else ""
            rows.append({
                "label":   _wound_label(idx, name),
                "value":   int(stacked),
                "taken":   int(stacked_w) if stacked_w else 0,
            })
        return rows

    @Property(int, notify=combatChanged)
    def healthMultiplier(self):
        pc = api.character.model()
        return int(pc.health_multiplier) if pc else 2
