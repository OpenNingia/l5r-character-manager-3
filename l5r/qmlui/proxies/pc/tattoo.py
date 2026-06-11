# -*- coding: utf-8 -*-
# Copyright (C) 2014-2026 Daniele Simonetti
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# Tattoo slice of PcProxy: the mystic marks of the Togashi Order the
# character bears, projected for TattooSection.qml.
#
# A tattoo shares storage with a kiho -- both are KihoAdv advancements
# (adv.type == 'kiho') -- but they are mechanically distinct: free
# (cost 0) and carrying no element, mastery or XP. They are told apart
# by the kind of power the advancement references: a tattoo's DAL row
# has type == 'tattoo'. So this slice keeps the proper kiho out and
# projects only the tattoos; the kiho slice (when ported) does the
# inverse. Both are read-only here -- the receive / remove actions live
# on AppController (buyTattoo / removeTattoo).
#
# Each row carries exactly what the section's card consumes:
#   { id:          "the_dragons_breath_tattoo",  // also keys removal
#     name:         "The Dragon's Breath",
#     description:  "…" }                         // prose; may be ""
#
# Getters read live from api.character.model(); a coarse `tattooChanged`
# signal fires on character_refreshed / model_replaced, mirroring
# KataMixin / SkillsMixin.

from qtpy.QtCore import Property, Signal

import l5r.api as api
import l5r.api.character
import l5r.api.data
import l5r.api.data.powers

from l5r.qmlui.proxies.pc.memo import invalidate, memoize


class TattooMixin:
    tattooChanged = Signal()

    def _wire_tattoo(self, bus):
        bus.character_refreshed.connect(self._on_character_refreshed_tattoo)
        bus.model_replaced.connect(self._on_model_replaced_tattoo)

    def _on_character_refreshed_tattoo(self):
        invalidate(self, "tattoo")
        self.tattooChanged.emit()

    def _on_model_replaced_tattoo(self):
        invalidate(self, "tattoo")
        self.tattooChanged.emit()

    @Property("QVariantList", notify=tattooChanged)
    @memoize
    def tattoo(self):
        pc = api.character.model()
        if not pc:
            return []

        rows = []
        for adv in pc.advans or []:
            if adv.type != "kiho":
                continue
            kiho_id = getattr(adv, "kiho", None)
            kiho_ = api.data.powers.get_kiho(kiho_id) if kiho_id else None
            # Skip proper kiho (handled by the kiho slice) and any mark
            # whose power lives in a pack the user removed -- degrade
            # gracefully rather than break the whole list.
            if not kiho_ or kiho_.type != "tattoo":
                continue

            rows.append({
                "id":          kiho_.id,
                "name":        kiho_.name or kiho_.id,
                "description": getattr(kiho_, "desc", "") or "",
            })

        rows.sort(key=lambda r: (r["name"] or "").lower())
        return rows
