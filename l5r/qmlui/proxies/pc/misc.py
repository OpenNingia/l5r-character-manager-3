# -*- coding: utf-8 -*-
# Copyright (C) 2014-2026 Daniele Simonetti
#
# Miscellanea slice of PcProxy (雑 -- zatsu). Feeds the merged QML
# "Miscellanea" section, which gathers the three odds-and-ends the legacy
# UI scattered across the Modifiers tab and the Equipment tab:
#
#   modifiers  -- the character's custom roll/stat modifiers (the legacy
#                 ModifiersTableViewModel rows): what each one modifies,
#                 its detail, its roll-and-keep value, the player's note,
#                 and whether it is currently applied.
#   equipment  -- the carried gear, in reading order: the school-granted
#                 starting outfit first (kind "starting"), then the
#                 free-form items the player added (kind "personal"). Each
#                 row carries the (kind, index) pair the controller uses
#                 to edit / remove it in place.
#   money      -- the koku / bu / zeni purse (api.character.get_money(),
#                 which already folds in the school's starting money).
#
# Getters read live from api.character.model() -- the proxy holds no
# model reference, so model swaps cannot strand it. A single coarse
# `miscChanged` signal fires on character_refreshed / model_replaced,
# mirroring the other slices.
#
# Row shapes consumed by MiscSection.qml:
#   modifiers: { id:     str   (session-stable handle for edit/remove/toggle)
#                type:   str   (MOD_TYPES key, e.g. "atkr"; "" if none)
#                detail: str   (the per-modifier detail, e.g. a weapon name)
#                value:  str   (roll-and-keep + bonus, e.g. "+2" or "1k0 +1")
#                reason: str   (the player's free-text note)
#                active: bool  (whether the modifier is currently applied) }
#   equipment: { kind:  "starting" | "personal"
#                index: int    (position within its own list)
#                text:  str
#                isStarting: bool }
#   money:     { koku: int, bu: int, zeni: int }

from qtpy.QtCore import Property, Signal

import l5r.api as api
import l5r.api.character
import l5r.api.rules
import l5r.api.rules.modifiers


def _pretty_source(slug):
    """Human-ish label for a datapack record slug used as a fallback name."""
    return (slug or "").replace("_", " ").strip().title()


class MiscMixin:
    miscChanged = Signal()

    def _wire_misc(self, bus):
        bus.character_refreshed.connect(self._on_character_refreshed_misc)
        bus.model_replaced.connect(self._on_model_replaced_misc)

    def _on_character_refreshed_misc(self):
        self.miscChanged.emit()

    def _on_model_replaced_misc(self):
        self.miscChanged.emit()

    @Property("QVariantList", notify=miscChanged)
    def modifiers(self):
        pc = api.character.model()
        if not pc:
            return []
        rows = []
        for m in pc.get_modifiers() or []:
            # value is a (roll, keep, bonus) tuple (or a 2-tuple on older
            # data); format_rtk_t renders either as the table string.
            rows.append({
                "id":         str(id(m)),
                "type":       getattr(m, "type", "") or "",
                "detail":     getattr(m, "dtl", "") or "",
                "value":      api.rules.format_rtk_t(getattr(m, "value", (0, 0, 0))),
                "reason":     getattr(m, "reason", "") or "",
                "active":     bool(getattr(m, "active", False)),
                "readonly":   False,   # user modifier: editable / removable
                "toggleable": True,
                "source":     "",
            })
        # datapack-granted (dynamic) modifiers: read-only, never serialized.
        # Their `key` is the session-stable toggle handle; only `when`-gated
        # ones are toggleable, the rest are always-on.
        for dm in l5r.api.rules.modifiers.build_dynamic_modifiers():
            rows.append({
                "id":         dm.key,
                "type":       dm.type or "",
                "detail":     dm.dtl or "",
                "value":      api.rules.format_rtk_t(dm.value),
                "reason":     dm.reason or _pretty_source(getattr(dm, "source", "")),
                "active":     bool(dm.active),
                "readonly":   True,
                "toggleable": bool(dm.toggleable),
                "source":     _pretty_source(getattr(dm, "source", "")),
            })
        return rows

    @Property("QVariantList", notify=miscChanged)
    def equipment(self):
        pc = api.character.model()
        if not pc:
            return []
        rows = []
        for i, txt in enumerate(api.character.get_starting_outfit() or []):
            rows.append({"kind": "starting", "index": i,
                         "text": txt or "", "isStarting": True})
        for i, txt in enumerate(api.character.get_equipment() or []):
            rows.append({"kind": "personal", "index": i,
                         "text": txt or "", "isStarting": False})
        return rows

    @Property("QVariantMap", notify=miscChanged)
    def money(self):
        pc = api.character.model()
        if not pc:
            return {"koku": 0, "bu": 0, "zeni": 0}
        koku, bu, zeni = api.character.get_money()
        return {"koku": int(koku), "bu": int(bu), "zeni": int(zeni)}
