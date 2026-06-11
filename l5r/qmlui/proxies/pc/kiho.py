# -*- coding: utf-8 -*-
# Copyright (C) 2014-2026 Daniele Simonetti
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# Kiho slice of PcProxy: the spiritual techniques (気) the character has
# learned, projected for KihoSection.qml.
#
# A kiho shares storage with a tattoo -- both are KihoAdv advancements
# (adv.type == 'kiho') -- but they are mechanically distinct: a tattoo is
# free and carries no element/mastery, and its DAL row has
# type == 'tattoo'. This slice projects only the *proper* kiho (every
# kiho whose power type is not 'tattoo'); the tattoo slice does the
# inverse. Both are read-only here -- the purchase / removal actions live
# on AppController (buyKiho / removeKiho).
#
# Each row carries exactly what the section's card consumes:
#   { id:           "the_touch_of_the_void",  // also keys removal
#     name:         "The Touch of the Void",
#     element:      "void",                   // ring key -> Theme.ringColor
#     elementLabel: "Void",                   // localised ring name
#     mastery:      3,
#     type:         "mystical",               // kiho kind, lower-cased key
#     typeLabel:    "Mystical",               // display label
#     cost:         6,                         // XP actually paid (0 if free)
#     description:  "…" }                      // prose; may be ""
#
# Getters read live from api.character.model(); a coarse `kihoChanged`
# signal fires on character_refreshed / model_replaced, mirroring
# KataMixin / TattooMixin.

from qtpy.QtCore import Property, Signal

import l5r.api as api
import l5r.api.character
import l5r.api.data
import l5r.api.data.powers

from l5r.qmlui.proxies.pc.memo import invalidate, memoize


class KihoMixin:
    kihoChanged = Signal()

    def _wire_kiho(self, bus):
        bus.character_refreshed.connect(self._on_character_refreshed_kiho)
        bus.model_replaced.connect(self._on_model_replaced_kiho)

    def _on_character_refreshed_kiho(self):
        invalidate(self, "kiho")
        self.kihoChanged.emit()

    def _on_model_replaced_kiho(self):
        invalidate(self, "kiho")
        self.kihoChanged.emit()

    @Property("QVariantList", notify=kihoChanged)
    @memoize
    def kiho(self):
        pc = api.character.model()
        if not pc:
            return []

        rows = []
        for adv in pc.advans or []:
            if adv.type != "kiho":
                continue
            kiho_id = getattr(adv, "kiho", None)
            kiho_ = api.data.powers.get_kiho(kiho_id) if kiho_id else None
            # Skip tattoos (handled by the tattoo slice) and any kiho
            # whose power lives in a pack the user removed -- degrade
            # gracefully rather than break the whole list.
            if not kiho_ or kiho_.type == "tattoo":
                continue

            element = (kiho_.element or "void").lower()
            ring_ = api.data.get_ring(kiho_.element)
            element_label = ring_.text if ring_ else (kiho_.element or "")
            kind = (kiho_.type or "").strip()

            rows.append({
                "id":           kiho_.id,
                "name":         kiho_.name or kiho_.id,
                "element":      element,
                "elementLabel": element_label,
                "mastery":      int(kiho_.mastery) if kiho_.mastery is not None else 0,
                "type":         kind.lower(),
                "typeLabel":    kind.title(),
                "cost":         int(adv.cost or 0),
                "description":  getattr(kiho_, "desc", "") or "",
            })

        rows.sort(key=lambda r: (r["mastery"], (r["name"] or "").lower()))
        return rows
