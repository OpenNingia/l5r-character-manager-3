# -*- coding: utf-8 -*-
# Copyright (C) 2014-2026 Daniele Simonetti
#
# Skills slice of PcProxy: the character's full skill list, each row
# bundled with the data SkillsSection.qml needs to render and act on
# (rank, trait label, ring key, base/mod roll, emphases, mastery
# ladder, school-skill flag, description). Recomputes from the
# advancement history -- a single coarse `skillsChanged` signal fires
# on character_refreshed / model_replaced, mirroring TraitsMixin.

from qtpy.QtCore import Property, Signal

import l5r.api as api
import l5r.api.character
import l5r.api.character.skills
import l5r.api.data
import l5r.api.data.skills
import l5r.api.rules

import l5r.models.chmodel as chmodel


# Attribute -> ring key map. The api side keeps trait_id -> ring lookup
# in l5r.api.data.get_trait_ring(), but that returns the localised ring
# DAL row; QML wants the canonical key ("earth"/"air"/...). The map
# below is the same partition expressed in QML-friendly form.
_ATTR_TO_RING = {
    "stamina":      "earth",
    "willpower":    "earth",
    "reflexes":     "air",
    "awareness":    "air",
    "strength":     "water",
    "perception":   "water",
    "agility":      "fire",
    "intelligence": "fire",
    "void":         "void",
}


def _ring_key_for_trait(trait_id):
    """Map a skill's trait id ('agility', 'void', ...) to its ring key.
    Falls back to 'void' for unknown ids so the row still renders."""
    if not trait_id:
        return "void"
    return _ATTR_TO_RING.get(trait_id.lower(), "void")


class SkillsMixin:
    skillsChanged = Signal()

    def _wire_skills(self, bus):
        bus.character_refreshed.connect(self._on_character_refreshed_skills)
        bus.model_replaced.connect(self._on_model_replaced_skills)

    def _on_character_refreshed_skills(self):
        self.skillsChanged.emit()

    def _on_model_replaced_skills(self):
        self.skillsChanged.emit()

    @Property("QVariantList", notify=skillsChanged)
    def skills(self):
        pc = api.character.model()
        if not pc:
            return []

        rows = []
        for sid in api.character.skills.get_all():
            sk = api.data.skills.get(sid)
            if not sk:
                continue

            # Trait display label: prefer the localised DAL row so the
            # row's small-caps caption matches the rest of the sheet.
            trait_row = api.data.get_trait_or_ring(sk.trait)
            trait_label = trait_row.text if trait_row else (sk.trait or "")

            rank = api.character.skills.get_skill_rank(sid)
            base_pool = api.rules.calculate_base_skill_roll(pc, sk)
            mod_pool = api.rules.calculate_mod_skill_roll(pc, sk)

            mastery = []
            for ma in (sk.mastery_abilities or []):
                mastery.append({
                    "rank": int(ma.rank),
                    "desc": ma.desc or "",
                })

            rows.append({
                "id":          sk.id,
                "name":        sk.name,
                "rank":        int(rank),
                "trait":       trait_label,
                "ringKey":     _ring_key_for_trait(sk.trait),
                "baseRoll":    str(base_pool),
                "modRoll":     str(mod_pool),
                "isSchool":    bool(api.character.skills.is_starter(sid)),
                "emph":        list(api.character.skills.get_skill_emphases(sid)),
                "mastery":     mastery,
                "description": getattr(sk, "desc", "") or "",
            })

        return rows
