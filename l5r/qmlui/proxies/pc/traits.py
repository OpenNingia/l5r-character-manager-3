# -*- coding: utf-8 -*-
# Copyright (C) 2014-2026 Daniele Simonetti
#
# Traits slice of PcProxy: the five ring ranks, the eight attribute
# ranks, and the current Void points pool. Everything in this mixin
# recomputes from advancements, so a single coarse `traitsChanged`
# fires on character_refreshed / model_replaced rather than per-field.

from qtpy.QtCore import Property, Signal

import l5r.api as api
import l5r.api.character
import l5r.api.data

import l5r.models as models

from l5r.qmlui.proxies.pc.memo import invalidate, memoize


class TraitsMixin:
    traitsChanged = Signal()

    def _wire_traits(self, bus):
        bus.character_refreshed.connect(self._on_character_refreshed_traits)
        bus.model_replaced.connect(self._on_model_replaced_traits)

    def _on_character_refreshed_traits(self):
        invalidate(self, "rings", "attribs")
        self.traitsChanged.emit()

    def _on_model_replaced_traits(self):
        invalidate(self, "rings", "attribs")
        self.traitsChanged.emit()

    @Property("QVariantMap", notify=traitsChanged)
    @memoize
    def rings(self):
        pc = api.character.model()
        if not pc:
            return {}
        return {r: api.character.ring_rank(r) for r in models.chmodel.RINGS._ids}

    @Property("QVariantMap", notify=traitsChanged)
    @memoize
    def attribs(self):
        pc = api.character.model()
        if not pc:
            return {}
        return {
            a: api.character.trait_rank(a)
            for a in models.chmodel.ATTRIBS._ids
        }

    @Property(int, notify=traitsChanged)
    def voidPoints(self):
        pc = api.character.model()
        return int(pc.void_points) if pc else 0
