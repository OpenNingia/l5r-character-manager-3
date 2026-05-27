# -*- coding: utf-8 -*-
# Copyright (C) 2014-2026 Daniele Simonetti
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# Central notification bus for the API layer.
#
# The legacy QWidget UI updates itself by calling update_from_model()
# after every mutation -- a pull flow. The QML UI cannot do that: it
# needs Qt signals to drive property bindings. Rather than retrofit
# signals into every setter in l5r/api/character/*.py, a small set of
# API entry points emit on this shared bus and any UI (QML, future
# headless tools) can subscribe.
#
# The widget UI does not connect to the bus, so adding emit() calls
# here is a no-op for it.

from qtpy.QtCore import QObject, Signal


class _ModelBus(QObject):
    model_replaced = Signal()
    dirty_changed = Signal(bool)
    name_changed = Signal(str)
    family_changed = Signal(str)
    clan_changed = Signal(str)
    notes_changed = Signal(str)
    personal_info_changed = Signal()


_BUS = None


def bus():
    """Return the process-wide _ModelBus, creating it on first use.

    Lazy so that importing l5r.api.signals before a QApplication exists
    (e.g. in tests that never touch the bus) is safe.
    """
    global _BUS
    if _BUS is None:
        _BUS = _ModelBus()
    return _BUS
