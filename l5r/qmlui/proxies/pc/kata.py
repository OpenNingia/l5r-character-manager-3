# -*- coding: utf-8 -*-
# Copyright (C) 2014-2026 Daniele Simonetti
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# Kata slice of PcProxy: the martial forms the character has learned,
# projected for KataSection.qml.
#
# A kata is bought directly (unlike a technique, which is granted by
# school rank) -- so this slice is read-only here, while the purchase /
# removal actions live on AppController (buyKata / removeKata). Each row
# carries the data the section needs to render a card and to drive its
# remove handle: the kata's id (which also keys removal -- a character
# owns any kata at most once, so no opaque advancement handle is
# needed), name, element (a ring key + localised label), mastery, the XP
# actually paid, and the prose description.
#
# Getters read live from api.character.model(); a coarse `kataChanged`
# signal fires on character_refreshed / model_replaced, mirroring
# SkillsMixin / PerksMixin.

from qtpy.QtCore import Property, Signal

import l5r.api as api
import l5r.api.character
import l5r.api.data
import l5r.api.data.powers

from l5r.qmlui.proxies.pc.memo import invalidate, memoize
from l5r.util import log


class KataMixin:
    kataChanged = Signal()

    def _wire_kata(self, bus):
        bus.character_refreshed.connect(self._on_character_refreshed_kata)
        bus.model_replaced.connect(self._on_model_replaced_kata)

    def _on_character_refreshed_kata(self):
        invalidate(self, "kata")
        self.kataChanged.emit()

    def _on_model_replaced_kata(self):
        invalidate(self, "kata")
        self.kataChanged.emit()

    @Property("QVariantList", notify=kataChanged)
    @memoize
    def kata(self):
        pc = api.character.model()
        if not pc:
            return []

        rows = []
        for adv in pc.advans or []:
            if adv.type != "kata":
                continue
            kata_id = getattr(adv, "kata", None)
            kata_ = api.data.powers.get_kata(kata_id) if kata_id else None
            if not kata_:
                # Character file references a kata from a pack the user
                # removed (or no datapack loaded). Skip rather than break
                # the whole list.
                log.api.debug(u"kata proxy: could not resolve kata %s", kata_id)
                continue

            element = (kata_.element or "void").lower()
            ring_ = api.data.get_ring(kata_.element)
            element_label = ring_.text if ring_ else (kata_.element or "")

            rows.append({
                "id":          kata_.id,
                "name":        kata_.name or kata_.id,
                "element":     element,
                "elementLabel": element_label,
                "mastery":     int(kata_.mastery) if kata_.mastery is not None else 0,
                "cost":        int(adv.cost or 0),
                "description": getattr(kata_, "desc", "") or "",
            })

        rows.sort(key=lambda r: (r["mastery"], (r["name"] or "").lower()))
        return rows
