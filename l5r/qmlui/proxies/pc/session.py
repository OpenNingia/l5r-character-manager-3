# -*- coding: utf-8 -*-
# Copyright (C) 2014-2026 Daniele Simonetti
#
# Session slice of PcProxy: the unsaved-changes flag and the
# model-replaced fan-out signal that QML listens to when a new character
# is loaded or created.

from qtpy.QtCore import Property, Signal

import l5r.api as api
import l5r.api.character


class SessionMixin:
    dirtyChanged = Signal()
    modelReplaced = Signal()

    def _wire_session(self, bus):
        bus.dirty_changed.connect(self._on_dirty_changed)
        bus.model_replaced.connect(self._on_model_replaced_session)

    def _on_dirty_changed(self, _value):
        self.dirtyChanged.emit()

    def _on_model_replaced_session(self):
        self.modelReplaced.emit()
        self.dirtyChanged.emit()

    @Property(bool, notify=dirtyChanged)
    def dirty(self):
        pc = api.character.model()
        return bool(pc.unsaved) if pc else False
