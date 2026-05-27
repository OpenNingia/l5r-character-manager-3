# -*- coding: utf-8 -*-
# Copyright (C) 2014-2026 Daniele Simonetti
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# Per-area mixin classes that compose into l5r.qmlui.proxies.pc_proxy.PcProxy.
# Each mixin owns a slice of the character surface (identity, session,
# notes, ...) -- its Signals, Properties, and bus listeners. PcProxy is
# just `class PcProxy(IdentityMixin, ..., QObject)` plus a single __init__
# that calls each mixin's _wire_<area>(bus). Keeps the QML contract
# unchanged (one `pcProxy` context property) while letting the
# implementation grow tab-by-tab without crowding a single file.
