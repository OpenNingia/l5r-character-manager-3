# -*- coding: utf-8 -*-
# Copyright (C) 2014-2026 Daniele Simonetti
#
# Flags slice of PcProxy: the five "social/spiritual" gauges -- Honor,
# Glory, Status, Shadowland Taint, Infamy. Each is stored as a float
# whose integer part is the rank (0-9) and decimal part is the number
# of points within that rank (0-9 tenths).

from qtpy.QtCore import Property, Signal

import l5r.api as api
import l5r.api.character

from l5r.qmlui.proxies.pc.memo import invalidate, memoize


class FlagsMixin:
    flagsChanged = Signal()

    def _wire_flags(self, bus):
        bus.character_refreshed.connect(self._on_character_refreshed_flags)
        bus.model_replaced.connect(self._on_model_replaced_flags)

    def _on_character_refreshed_flags(self):
        invalidate(self, "flags")
        self.flagsChanged.emit()

    def _on_model_replaced_flags(self):
        invalidate(self, "flags")
        self.flagsChanged.emit()

    @Property("QVariantMap", notify=flagsChanged)
    @memoize
    def flags(self):
        pc = api.character.model()
        if not pc:
            return {}
        return {
            "honor":  float(api.character.honor()),
            "glory":  float(api.character.glory()),
            "status": float(api.character.status()),
            "taint":  float(api.character.taint()),
            "infamy": float(api.character.infamy()),
        }
