# -*- coding: utf-8 -*-
# Copyright (C) 2014-2026 Daniele Simonetti
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# Weapon mutators for the active character.
#
# A character's weapons are plain WeaponOutfit items on pc.weapons (NOT
# advancements -- they cost no XP and carry no rank history). The legacy
# WeaponsSink poked pc.weapons directly and called update_from_model;
# these helpers give the QML front-end (and any future caller) a single
# mutation path that owns the dirty flag and emits character_refreshed,
# per the CLAUDE.md setter contract. The proxy reads the live list via
# get_all(); reads are not duplicated here.

import l5r.api as api
import l5r.api.character
import l5r.api.signals

from l5r.api import get_context
from l5r.util import log

# Quantity is clamped to this range -- mirrors the legacy WeaponsSink
# arrow stepper, which refused to leave [1, 9999].
MIN_QTY = 1
MAX_QTY = 9999


def get_all():
    """Return the live list of the character's weapons (WeaponOutfit)."""
    pc = get_context().pc
    return pc.get_weapons() if pc else []


def add(item):
    """Append a weapon to the character and mark it dirty."""
    pc = get_context().pc
    if pc is None or item is None:
        return
    pc.add_weapon(item)
    api.character.set_dirty_flag(True)
    api.signals.bus().character_refreshed.emit()
    log.api.info(u"added weapon: %s", getattr(item, "name", "?"))


def remove(item):
    """Remove a weapon from the character. Returns True if it was present."""
    pc = get_context().pc
    if pc is None or item is None:
        return False
    if item not in pc.weapons:
        log.api.warning(u"remove weapon: item not owned: %s",
                        getattr(item, "name", "?"))
        return False
    pc.weapons.remove(item)
    api.character.set_dirty_flag(True)
    api.signals.bus().character_refreshed.emit()
    return True


def set_quantity(item, qty):
    """Set a weapon's quantity, clamped to [MIN_QTY, MAX_QTY]. Returns the
    clamped value actually stored. A no-op (no dirty/refresh) when the
    value is unchanged."""
    if item is None:
        return None
    qty = max(MIN_QTY, min(int(qty), MAX_QTY))
    if int(getattr(item, "qty", MIN_QTY) or MIN_QTY) == qty:
        return qty
    item.qty = qty
    api.character.set_dirty_flag(True)
    api.signals.bus().character_refreshed.emit()
    return qty


def touch():
    """Flag the character dirty and re-emit character_refreshed after an
    in-place edit of a weapon's fields (the proxy holds no reference to
    the mutated item, so it needs the coarse refresh to re-project)."""
    if get_context().pc is None:
        return
    api.character.set_dirty_flag(True)
    api.signals.bus().character_refreshed.emit()
