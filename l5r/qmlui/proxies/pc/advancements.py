# -*- coding: utf-8 -*-
# Copyright (C) 2014-2026 Daniele Simonetti
#
# Advancements slice of PcProxy: the character's advancement history
# (the rank-by-rank purchase stack) projected for AdvancementsSection.
# Returns the list newest-first with `isHead: true` on items[0], since
# the QML side affords refund only on the head of the stack -- mid-
# stack refund is unsafe because advancement costs depend on the rank
# reached by prior entries (see project-advancement-stack-semantics).
#
# A single coarse `advancementsChanged` signal fires on
# character_refreshed / model_replaced, mirroring SkillsMixin.

from qtpy.QtCore import Property, Signal

import l5r.api as api
import l5r.api.character

from l5r.qmlui.proxies.pc.memo import invalidate, memoize


class AdvancementsMixin:
    advancementsChanged = Signal()

    def _wire_advancements(self, bus):
        bus.character_refreshed.connect(self._on_character_refreshed_advancements)
        bus.model_replaced.connect(self._on_model_replaced_advancements)

    def _on_character_refreshed_advancements(self):
        invalidate(self, "advancements")
        self.advancementsChanged.emit()

    def _on_model_replaced_advancements(self):
        invalidate(self, "advancements")
        self.advancementsChanged.emit()

    @Property("QVariantList", notify=advancementsChanged)
    @memoize
    def advancements(self):
        pc = api.character.model()
        if not pc or not pc.advans:
            return []

        # Newest first -- matches the legacy AdvancementViewModel
        # (which iterates `reversed(model.advans)`) and lines the head
        # of the stack up with the top of the chronicle in QML.
        rows = []
        head_index = len(pc.advans) - 1
        for i in range(head_index, -1, -1):
            adv = pc.advans[i]
            rows.append({
                "type":      adv.type or "",
                "desc":      adv.desc or "",
                "cost":      int(adv.cost) if adv.cost is not None else 0,
                "timestamp": float(adv.timestamp) if adv.timestamp else 0.0,
                "isHead":    i == head_index,
            })
        return rows

    @Property(int, notify=advancementsChanged)
    def advancementsCount(self):
        pc = api.character.model()
        return len(pc.advans) if pc else 0

    @Property(int, notify=advancementsChanged)
    def advancementsXpSpent(self):
        # api.character.xp() already sums positive costs only -- the
        # canonical "XP spent" figure shown elsewhere on the sheet.
        # Reusing it keeps the ledger banner aligned with the
        # Character section's XP readout.
        return int(api.character.xp())
