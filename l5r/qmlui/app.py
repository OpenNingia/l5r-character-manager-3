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

from pathlib import Path

from qtpy.QtCore import QUrl
from qtpy.QtQml import QQmlApplicationEngine

import l5r.api as api
import l5r.api.data
from l5r.qmlui.proxies.app_controller import AppController
from l5r.qmlui.proxies.pc_proxy import PcProxy
from l5r.util import log
from l5r.util.settings import L5RCMSettings


def _bootstrap_data(locale):
    """Replicate the data-init that L5RCMCore.__init__ does for the QWidget UI."""
    settings = L5RCMSettings()
    api.data.set_locale(locale)
    api.data.set_blacklist(settings.app.data_pack_blacklist)
    api.data.reload()


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

    api.set_translation_context(qapp)
    _bootstrap_data(locale)

    pc_proxy = PcProxy()
    controller = AppController()

    # Start with a fresh, in-memory character so pcProxy.* getters never
    # see ctx.pc == None. The QWidget path does the same via
    # L5RMain.create_new_character().
    api.character.new()
    api.character.set_dirty_flag(False)

    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("pcProxy", pc_proxy)
    engine.rootContext().setContextProperty("appCtrl", controller)

    qml_main = Path(__file__).parent / "qml" / "MainSheet.qml"
    engine.load(QUrl.fromLocalFile(str(qml_main)))
    if not engine.rootObjects():
        log.app.error(u"QML UI: engine failed to load %s", qml_main)
        return 1

    # Keep the proxies/engine alive on the QApplication so they outlive
    # this function's stack frame.
    qapp._l5r_qml_engine = engine
    qapp._l5r_pc_proxy = pc_proxy
    qapp._l5r_app_controller = controller

    if startup_action is not None:
        controller.apply_startup(*startup_action)

    return qapp.exec()
