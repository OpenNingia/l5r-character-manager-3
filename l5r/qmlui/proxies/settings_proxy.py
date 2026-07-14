# -*- coding: utf-8 -*-
# Copyright (C) 2014-2026 Daniele Simonetti
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# App-global preferences bridge for the QML Settings section. Bound as
# the context property ``appSettings`` in l5r.qmlui.app.run_qml_app.
#
# These are *application* settings (QSettings, via L5RCMSettings), not
# character state -- so they live here rather than on PcProxy. Only the
# preferences that are meaningful on the parchment sheet are surfaced:
# localization, the Insight-calculation method, the PDF "skills on first
# page" flag, and the new-UI switch. The QWidget-only chrome settings
# (table row colours, app font, banner) are intentionally NOT ported.
#
# Apply semantics:
#   * Insight calculation -- applied immediately: written as the global
#     default AND pushed onto the active character, then a refresh fans
#     the recompute out to every section.
#   * PDF first-page-skills -- persisted; the exporter reads it at export
#     time, so no live work is needed here.
#   * Language + new-UI switch -- can only be honoured at startup (the
#     translators / front-end are chosen once in l5r.main.main), so these
#     persist and emit ``reloadRequired`` for the QML side to surface a
#     restart toast.

from qtpy.QtCore import QObject, Property, QT_TRANSLATE_NOOP, Signal, Slot

import l5r.api as api
import l5r.api.character
import l5r.models

from l5r.util import log
from l5r.util.settings import L5RCMSettings


# Labels are wrapped in QT_TRANSLATE_NOOP rather than left as bare
# literals: the property translates them at runtime with
# self.tr(label), but `label` is a variable there, so pylupdate6 can't
# see the source text through that call. QT_TRANSLATE_NOOP marks each
# literal for extraction into the "SettingsProxy" context (it returns the
# string unchanged at runtime) -- the same context self.tr() resolves
# against, so the harvested translation is the one that gets used. Keep
# the context string in sync with this class's name.

# The locales the legacy SettingsWidget offered. Kept verbatim so the two
# front-ends present the same choices; the labels are tr()-wrapped at
# build time (see availableLocales).
_LOCALES = [
    ("en_US", QT_TRANSLATE_NOOP("SettingsProxy","US English")),
    ("en_GB", QT_TRANSLATE_NOOP("SettingsProxy","UK English")),
    ("it_IT", QT_TRANSLATE_NOOP("SettingsProxy","Italian")),
    ("es_ES", QT_TRANSLATE_NOOP("SettingsProxy","Spanish")),
    ("fr_FR", QT_TRANSLATE_NOOP("SettingsProxy","French")),
    ("pt_BR", QT_TRANSLATE_NOOP("SettingsProxy","Portuguese (Brazil)")),
    ("ru_RU", QT_TRANSLATE_NOOP("SettingsProxy","Russian"))
]

# Insight-calculation methods -- the int maps to api.rules.calculate_insight
# (which reads pc.insight_calculation). Mirrors the legacy combo in
# l5r/widgets/settings.py.
_INSIGHT_METHODS = [
    (1, QT_TRANSLATE_NOOP("SettingsProxy","Default")),
    (2, QT_TRANSLATE_NOOP("SettingsProxy","Ignore Rank 1 Skills")),
    (3, QT_TRANSLATE_NOOP("SettingsProxy","Account Rank 1 School Skills"))
]

# UI text-size choices. The id is the persisted key (settings.app
# ui_font_size); the scale is the multiplier pushed onto Theme.fontScale
# (see _FONT_SCALES). Only two choices are offered, per the design intent:
# "Standard" (1.0) and "Large" (1.25).
_FONT_SIZES = [
    ("standard", QT_TRANSLATE_NOOP("SettingsProxy","Standard")),
    ("large", QT_TRANSLATE_NOOP("SettingsProxy","Large")),
    ("larger", QT_TRANSLATE_NOOP("SettingsProxy","Larger")),
    ("huge", QT_TRANSLATE_NOOP("SettingsProxy","Huge"))
]

_FONT_SCALES = {
    "standard": 1.0,
    "large": 1.15,
    "larger": 1.25,
    "huge": 1.45
}

_EXP_DISPLAYS = [
    (1, QT_TRANSLATE_NOOP("SettingsProxy","Points Used / Earned")),
    (2, QT_TRANSLATE_NOOP("SettingsProxy","Points Available / Earned")),
    (3, QT_TRANSLATE_NOOP("SettingsProxy","Points Available / Points Used"))
]

_HEALTH_METHODS = [
    ('default', QT_TRANSLATE_NOOP("SettingsProxy","Default")),
    ('stacked', QT_TRANSLATE_NOOP("SettingsProxy","Health left")),
    ('wounds', QT_TRANSLATE_NOOP("SettingsProxy","Total wounds"))
]


class SettingsProxy(QObject):
    """Read/write bridge over L5RCMSettings for the QML Settings section."""

    # Coarse notify signals -- the section re-reads the matching getter.
    localeChanged = Signal()
    insightCalculationChanged = Signal()
    firstPageSkillsChanged = Signal()
    printCurrentArmorTnChanged = Signal()
    useQmlUiChanged = Signal()
    buyForFreeChanged = Signal()
    fontSizeChanged = Signal()
    expDisplayChanged = Signal()
    healthMethodChanged = Signal()


    # Emitted when a setting was persisted but cannot take effect until the
    # app is restarted (language, front-end switch). Carries the message
    # the QML toast shows.
    reloadRequired = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._settings = L5RCMSettings()

    # --- static option lists -----------------------------------------

    @Property("QVariantList", constant=True)
    def availableLocales(self):
        return [{"id": code, "name": self.tr(label)}
                for code, label in _LOCALES]

    @Property("QVariantList", constant=True)
    def insightMethods(self):
        return [{"id": value, "name": self.tr(label)}
                for value, label in _INSIGHT_METHODS]

    @Property("QVariantList", constant=True)
    def fontSizes(self):
        return [{"id": key, "name": self.tr(label)}
                for key, label in _FONT_SIZES]

    @Property("QVariantList", constant=True)
    def expDisplays(self):
        return [{"id": key, "name": self.tr(label)}
                for key, label in _EXP_DISPLAYS]

    @Property("QVariantList", constant=True)
    def healthMethods(self):
        return [{"id": key, "name": self.tr(label)}
                for key, label in _HEALTH_METHODS]

    # --- localization ------------------------------------------------

    @Property(bool, notify=localeChanged)
    def useSystemLocale(self):
        return bool(self._settings.app.use_system_locale)

    @Property(str, notify=localeChanged)
    def userLocale(self):
        return self._settings.app.user_locale or "en_US"

    @Slot(bool)
    def setUseSystemLocale(self, value):
        value = bool(value)
        if value == self.useSystemLocale:
            return
        self._settings.app.use_system_locale = value
        self._settings.sync()
        self.localeChanged.emit()
        self.reloadRequired.emit(
            self.tr("The language will change the next time you start the app."))

    @Slot(str)
    def setUserLocale(self, code):
        code = code or "en_US"
        if code == self.userLocale:
            return
        self._settings.app.user_locale = code
        self._settings.sync()
        self.localeChanged.emit()
        self.reloadRequired.emit(
            self.tr("The language will change the next time you start the app."))

    # --- insight calculation (applied immediately) -------------------

    @Property(int, notify=insightCalculationChanged)
    def insightCalculation(self):
        try:
            return int(self._settings.app.insight_calculation)
        except (TypeError, ValueError):
            return 1

    @Slot(int)
    def setInsightCalculation(self, value):
        try:
            value = int(value)
        except (TypeError, ValueError):
            log.app.warning(u"QML UI: invalid insight calculation %r", value)
            return
        if value == self.insightCalculation:
            return
        # Persist the global default and apply it to the active character
        # so the change is visible at once. Matches the legacy menu
        # handler (l5r/ui/menu.py on_change_insight_calculation), which
        # does not force the dirty flag for this preference.
        self._settings.app.insight_calculation = value
        self._settings.sync()
        if api.character.model() is not None:
            api.character.set_insight_calculation_method(value)
            api.character.notify_character_refreshed()
        self.insightCalculationChanged.emit()

    # --- free shopping (GM/build aid, session-only) ------------------
    # The legacy "Free Shopping" Options toggle: while on, every NEW
    # advancement is created at 0 XP (l5r.models.Advancement reads the
    # class flag in its __init__). It is a session-only switch -- NOT
    # persisted to QSettings -- matching the legacy menu, which defaults
    # off at every launch. Persisting "everything is free" across runs
    # would be a footgun, so the flag deliberately resets on restart.

    @Property(bool, notify=buyForFreeChanged)
    def buyForFree(self):
        return bool(l5r.models.Advancement.get_buy_for_free())

    @Slot(bool)
    def setBuyForFree(self, value):
        value = bool(value)
        if value == self.buyForFree:
            return
        l5r.models.Advancement.set_buy_for_free(value)
        self.buyForFreeChanged.emit()

    # --- UI text size (applied live via Theme.fontScale) -------------
    # Persisted preference that scales the whole type scale. The QML
    # root binds Theme.fontScale to `fontScale` below, so changing it
    # takes effect at once -- no restart needed.

    @Property(str, notify=fontSizeChanged)
    def fontSize(self):
        value = self._settings.app.ui_font_size or "standard"
        return value if value in _FONT_SCALES else "standard"

    @Property(float, notify=fontSizeChanged)
    def fontScale(self):
        return _FONT_SCALES.get(self.fontSize, 1.0)

    @Slot(str)
    def setFontSize(self, value):
        value = value if value in _FONT_SCALES else "standard"
        if value == self.fontSize:
            return
        self._settings.app.ui_font_size = value
        self._settings.sync()
        self.fontSizeChanged.emit()

    @Property(str, notify=healthMethodChanged)
    def healthMethod(self):
        return (self._settings.app.health_method or "default")
        
    @Slot(str)
    def setHealthMethod(self, value):
        if value == self.healthMethod:
            return
        self._settings.app.health_method = value
        self._settings.sync()
        api.signals.bus().wounds_changed.emit()
        self.healthMethodChanged.emit()

    # --- EXP display (applied live via Theme.expDisplay) -------------
    @Property(int, notify=expDisplayChanged)
    def expDisplay(self):
        try:
            return int(self._settings.app.ui_exp_display)
        except (TypeError, ValueError):
            return 1

    @Slot(int)
    def setExpDisplay(self, value):
        try:
            value = int(value)
        except (TypeError, ValueError):
            log.app.warning(u"QML UI: invalid experience display %r", value)
            return

        if value == self.expDisplay:
            return

        self._settings.app.ui_exp_display = value
        self._settings.sync()
        self.expDisplayChanged.emit()




    # --- PDF export (read by the exporter at export time) ------------

    @Property(bool, notify=firstPageSkillsChanged)
    def firstPageSkills(self):
        return bool(self._settings.pc_export.first_page_skills)

    @Slot(bool)
    def setFirstPageSkills(self, value):
        value = bool(value)
        if value == self.firstPageSkills:
            return
        self._settings.pc_export.first_page_skills = value
        self._settings.sync()
        self.firstPageSkillsChanged.emit()

    @Property(bool, notify=printCurrentArmorTnChanged)
    def printCurrentArmorTn(self):
        return bool(self._settings.pc_export.print_current_armor_tn)

    @Slot(bool)
    def setPrintCurrentArmorTn(self, value):
        value = bool(value)
        if value == self.printCurrentArmorTn:
            return
        self._settings.pc_export.print_current_armor_tn = value
        self._settings.sync()
        self.printCurrentArmorTnChanged.emit()

    # --- front-end switch (honoured at startup) ----------------------

    @Property(bool, notify=useQmlUiChanged)
    def useQmlUi(self):
        return bool(self._settings.ui.use_qml_ui)

    @Slot(bool)
    def setUseQmlUi(self, value):
        value = bool(value)
        if value == self.useQmlUi:
            return
        self._settings.ui.use_qml_ui = value
        self._settings.sync()
        self.useQmlUiChanged.emit()
        if value:
            msg = self.tr("Restart the app to keep using the new interface.")
        else:
            msg = self.tr("Restart the app to switch back to the classic interface.")
        self.reloadRequired.emit(msg)
