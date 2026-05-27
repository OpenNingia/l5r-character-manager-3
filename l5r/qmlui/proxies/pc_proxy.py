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
# Getters always read live from get_context().pc -- the proxy holds no
# reference to the model, so model swaps (api.character.new /
# set_model) cannot leave it pointing at a stale instance. When the bus
# fires model_replaced, every *Changed signal is re-emitted so QML
# Bindings re-evaluate.

from qtpy.QtCore import QObject, Property, Signal

import l5r.api as api
import l5r.api.character
import l5r.api.signals

from l5r.l5rcmcore import APP_DESC, APP_VERSION


class PcProxy(QObject):
    nameChanged = Signal()
    clanChanged = Signal()
    familyChanged = Signal()
    dirtyChanged = Signal()
    modelReplaced = Signal()
    displayTitleChanged = Signal()
    notesChanged = Signal()
    personalInfoChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        bus = api.signals.bus()
        bus.model_replaced.connect(self._on_model_replaced)
        bus.dirty_changed.connect(self._on_dirty_changed)
        bus.name_changed.connect(self._on_name_changed)
        bus.family_changed.connect(self._on_family_changed)
        bus.clan_changed.connect(self._on_clan_changed)
        bus.notes_changed.connect(self._on_notes_changed)
        bus.personal_info_changed.connect(self._on_personal_info_changed)

    # --- bus listeners ------------------------------------------------

    def _on_model_replaced(self):
        self.modelReplaced.emit()
        self.nameChanged.emit()
        self.familyChanged.emit()
        self.clanChanged.emit()
        self.dirtyChanged.emit()
        self.displayTitleChanged.emit()
        self.notesChanged.emit()
        self.personalInfoChanged.emit()

    def _on_dirty_changed(self, _value):
        self.dirtyChanged.emit()
        self.displayTitleChanged.emit()

    def _on_name_changed(self, _value):
        self.nameChanged.emit()
        self.displayTitleChanged.emit()

    def _on_family_changed(self, _value):
        self.familyChanged.emit()

    def _on_clan_changed(self, _value):
        self.clanChanged.emit()

    def _on_notes_changed(self, _value):
        self.notesChanged.emit()

    def _on_personal_info_changed(self):
        self.personalInfoChanged.emit()

    # --- properties ---------------------------------------------------

    @Property(str, notify=nameChanged)
    def name(self):
        pc = api.character.model()
        return pc.name if pc else ""

    @Property(str, notify=familyChanged)
    def family(self):
        return api.character.get_family() or ""

    @Property(str, notify=clanChanged)
    def clan(self):
        return api.character.get_clan() or ""

    @Property(bool, notify=dirtyChanged)
    def dirty(self):
        pc = api.character.model()
        return bool(pc.unsaved) if pc else False

    @Property(str, notify=displayTitleChanged)
    def displayTitle(self):
        pc = api.character.model()
        base = "{} v{}".format(APP_DESC, APP_VERSION)
        if not pc or not pc.name:
            return base
        clan = api.character.get_clan() or ""
        body = "{} [{}]".format(pc.name, clan) if clan else pc.name
        suffix = " *" if pc.unsaved else ""
        return "{} — {}{}".format(base, body, suffix)

    @Property(str, notify=notesChanged)
    def notesHtml(self):
        return api.character.get_notes()

    @Property("QVariantMap", notify=personalInfoChanged)
    def personalInfo(self):
        return {k: api.character.get_personal_info(k)
                for k in api.character.personal_info_keys()}
