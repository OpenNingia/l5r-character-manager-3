# -*- coding: utf-8 -*-
# Copyright (C) 2014-2026 Daniele Simonetti
#
# Notes slice of PcProxy: rich-text notes HTML plus the anagraphic /
# family personal-info map. Both feed the Notes tab in QML.

from qtpy.QtCore import Property, Signal

import l5r.api as api
import l5r.api.character

from l5r.qmlui.proxies.pc.memo import invalidate, memoize


class NotesMixin:
    notesChanged = Signal()
    personalInfoChanged = Signal()

    def _wire_notes(self, bus):
        bus.notes_changed.connect(self._on_notes_changed)
        bus.personal_info_changed.connect(self._on_personal_info_changed)
        bus.model_replaced.connect(self._on_model_replaced_notes)

    def _on_notes_changed(self, _value):
        self.notesChanged.emit()

    def _on_personal_info_changed(self):
        invalidate(self, "personalInfo")
        self.personalInfoChanged.emit()

    def _on_model_replaced_notes(self):
        self.notesChanged.emit()
        invalidate(self, "personalInfo")
        self.personalInfoChanged.emit()

    @Property(str, notify=notesChanged)
    def notesHtml(self):
        return api.character.get_notes()

    @Property("QVariantMap", notify=personalInfoChanged)
    @memoize
    def personalInfo(self):
        return {k: api.character.get_personal_info(k)
                for k in api.character.personal_info_keys()}
