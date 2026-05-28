# -*- coding: utf-8 -*-
# Copyright (C) 2014-2026 Daniele Simonetti
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# QObject adapter exposing the active AdvancedPcModel to QML.
#
# PcProxy is intentionally a thin composition of per-area mixins in
# l5r.qmlui.proxies.pc.*. Each mixin owns a slice of the surface (its
# Signals, Properties, and bus listeners) and ships a _wire_<area>(bus)
# method called from __init__ to subscribe to the api signals bus.
#
# Getters always read live from get_context().pc -- the proxy holds no
# reference to the model, so model swaps (api.character.new /
# set_model) cannot leave it pointing at a stale instance.

from qtpy.QtCore import QObject

import l5r.api as api
import l5r.api.signals

from l5r.qmlui.proxies.pc.combat import CombatMixin
from l5r.qmlui.proxies.pc.flags import FlagsMixin
from l5r.qmlui.proxies.pc.identity import IdentityMixin
from l5r.qmlui.proxies.pc.notes import NotesMixin
from l5r.qmlui.proxies.pc.session import SessionMixin
from l5r.qmlui.proxies.pc.skills import SkillsMixin
from l5r.qmlui.proxies.pc.traits import TraitsMixin


class PcProxy(
    IdentityMixin,
    SessionMixin,
    TraitsMixin,
    FlagsMixin,
    CombatMixin,
    NotesMixin,
    SkillsMixin,
    QObject,
):
    def __init__(self, parent=None):
        QObject.__init__(self, parent)
        bus = api.signals.bus()
        self._wire_identity(bus)
        self._wire_session(bus)
        self._wire_traits(bus)
        self._wire_flags(bus)
        self._wire_combat(bus)
        self._wire_notes(bus)
        self._wire_skills(bus)
