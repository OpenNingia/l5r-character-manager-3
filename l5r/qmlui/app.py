# -*- coding: utf-8 -*-
# Copyright (C) 2014-2026 Daniele Simonetti
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# QML UI bootstrap. Mirrors the minimum work done by the legacy
# L5RCMCore.__init__ (translation context, datapack reload) and hands
# control to a QQmlApplicationEngine rooted at qml/Main.qml.

import os
from pathlib import Path

from qtpy.QtCore import QTranslator, QUrl
from qtpy.QtGui import QFont, QFontDatabase
from qtpy.QtQml import QQmlApplicationEngine

import l5r.api as api
import l5r.api.data
from l5r.qmlui.proxies.app_controller import AppController
from l5r.qmlui.proxies.pc_proxy import PcProxy
from l5r.qmlui.proxies.settings_proxy import SettingsProxy
from l5r.util import log
from l5r.util.fsutil import get_app_file
from l5r.util.settings import L5RCMSettings


def _bootstrap_data(locale):
    """Replicate the data-init that L5RCMCore.__init__ does for the QWidget UI."""
    settings = L5RCMSettings()
    api.data.set_locale(locale)
    api.data.set_blacklist(settings.app.data_pack_blacklist)
    api.data.reload()


def _load_bundled_fonts():
    """Register the display fonts shipped in ``l5r/share/fonts/`` so
    ``Theme.fontDisplay`` resolves to the same face on every install.

    QML's ``font.family`` grouped property takes a single family name
    and does *not* parse CSS-style comma fallback chains, so we can't
    rely on the user having Cinzel installed -- we ship it. Each .ttf
    is added via ``QFontDatabase.addApplicationFont`` and registered
    against the running QGuiApplication; missing files are warned but
    don't abort bootstrap (the Theme would fall back to Qt's serif).
    """
    fonts_dir = Path(__file__).parent.parent / "share" / "fonts"
    if not fonts_dir.is_dir():
        log.app.warning(u"QML UI: bundled fonts dir missing at %s", fonts_dir)
        return
    # Accept both TrueType and OpenType -- the brush-style CJK faces we
    # ship for the kanji slots come as .otf.
    candidates = sorted(list(fonts_dir.glob("*.ttf")) + list(fonts_dir.glob("*.otf")))
    for face in candidates:
        font_id = QFontDatabase.addApplicationFont(str(face))
        if font_id < 0:
            log.app.warning(u"QML UI: failed to load font %s", face.name)
            continue
        families = QFontDatabase.applicationFontFamilies(font_id)
        log.app.debug(u"QML UI: registered %s -> %s", face.name, families)


def _apply_body_font(qapp):
    """Make IM Fell English the app-wide default body font.

    This is the ``Theme.fontBody`` face (design system §3.1). Cinzel
    stays the display face (``Theme.fontDisplay`` -- headers, ring
    labels, dialog titles, the watermark) and EB Garamond is the stat
    face (``Theme.fontStat`` -- numerals). IM Fell English becomes the
    body face by overriding the QApplication's default ``QFont``, which
    every Quick Controls item -- TextField, ComboBox, SpinBox, plain
    Label without an explicit family -- inherits at construction. That
    avoids touching dozens of consumer files for the same effect.

    The family string is the .ttf's exact internal name, the ALL-CAPS
    ``IM FELL English`` (see _load_bundled_fonts output). Qt matches
    family names case-insensitively, so ``"IM Fell English"`` resolves
    too, but pinning the exact name makes ``QFont.exactMatch()`` true
    and keeps the value identical to ``Theme.fontBody``.

    IM Fell English's optical width is narrower than a typical UI sans,
    so we bump the size by one point to keep on-screen body text
    legible at parity with the system font. The legacy QWidget path's
    ``settings.ui.use_system_font`` preference is a QWidget-era setting
    and intentionally not honoured here -- the QML UI's body face is
    part of its designed identity.
    """
    base = qapp.font()
    body = QFont("IM FELL English")
    base_size = base.pointSizeF()
    if base_size > 0:
        body.setPointSizeF(base_size + 1.0)
    qapp.setFont(body)


def _install_qml_translator(qapp, locale):
    """Install the QML UI's translations.

    QML ``qsTr()`` strings resolve against translators installed on the
    QApplication. ``l5r.main.main()`` already installed the legacy
    ``<locale>.qm`` (which covers the Python ``tr()`` / ``api.tr()``
    strings); this adds the QML-only ``qml_<locale>.qm`` produced by
    ``tools/scripts/update_translations.py``. The two are kept separate
    because their lupdate extractors disagree on translation contexts.

    A missing or empty file is harmless: ``load()`` returns False and
    ``qsTr`` falls back to the source (English) text. The translator is
    pinned on ``qapp`` so it outlives this call.
    """
    translator = QTranslator(qapp)
    if translator.load(get_app_file(u"i18n/qml_{0}".format(locale))):
        qapp.installTranslator(translator)
        qapp._l5r_qml_translator = translator
        log.app.debug(u"QML UI: loaded QML translations for %s", locale)
    else:
        log.app.debug(u"QML UI: no QML translations for %s (qsTr -> source)", locale)


def run_qml_app(qapp, locale, startup_action):
    """Launch the QML UI.

    Parameters
    ----------
    qapp : QApplication
        already constructed and translated by l5r.main.main().
    locale : str
        culture locale (e.g. ``en_GB``), already resolved.
    startup_action : tuple[str, str | None] | None
        result of ``l5r.main._resolve_startup_action(sys.argv)``: either
        ``("open", path)``, ``("import", path)``, ``("new", None)`` or
        ``None`` for "just show an empty window".
    """
    log.app.info(u"QML UI: bootstrap")

    # Force the Fusion style. The default on Windows is the native
    # Windows style, which refuses customization of `background` and
    # `contentItem` on Quick Controls (ItemDelegate, ComboBox, etc.)
    # -- every `background: Rectangle { ... }` override in our QML is
    # then silently no-op'd and Qt logs "The current style does not
    # support customization of this control".  Fusion ships with
    # PyQt6, is identical across platforms, and accepts customization,
    # which we lean on heavily for the parchment / ink-on-paper look.
    # We use the env var rather than ``QQuickStyle.setStyle()`` because
    # ``qtpy`` does not currently expose the QtQuickControls2 module
    # for PyQt6; the codebase invariant is that Qt is imported through
    # qtpy only. Quick Controls reads this env var when the first
    # control is instantiated, which happens during ``engine.load``
    # below, so setting it here is in time.
    os.environ["QT_QUICK_CONTROLS_STYLE"] = "Fusion"

    api.set_translation_context(qapp)
    _install_qml_translator(qapp, locale)
    _load_bundled_fonts()
    _apply_body_font(qapp)
    _bootstrap_data(locale)

    pc_proxy = PcProxy()
    controller = AppController()
    settings_proxy = SettingsProxy()

    # Start with a fresh, in-memory character so pcProxy.* getters never
    # see ctx.pc == None. The QWidget path does the same via
    # L5RMain.create_new_character().
    api.character.new()
    api.character.set_dirty_flag(False)

    engine = QQmlApplicationEngine()
    # Make `import Theme 1.0` resolvable everywhere via the qml/Theme
    # singleton module. addImportPath takes the *parent* of the module
    # directory.
    qml_dir = Path(__file__).parent / "qml"
    engine.addImportPath(str(qml_dir))
    engine.rootContext().setContextProperty("pcProxy", pc_proxy)
    engine.rootContext().setContextProperty("appCtrl", controller)
    engine.rootContext().setContextProperty("appSettings", settings_proxy)

    qml_main = qml_dir / "MainSheet.qml"
    engine.load(QUrl.fromLocalFile(str(qml_main)))
    if not engine.rootObjects():
        log.app.error(u"QML UI: engine failed to load %s", qml_main)
        return 1

    # Keep the proxies/engine alive on the QApplication so they outlive
    # this function's stack frame.
    qapp._l5r_qml_engine = engine
    qapp._l5r_pc_proxy = pc_proxy
    qapp._l5r_app_controller = controller
    qapp._l5r_settings_proxy = settings_proxy

    if startup_action is not None:
        controller.apply_startup(*startup_action)

    return qapp.exec()
