#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Copyright (C) 2014-2026 Daniele Simonetti
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
"""Android / mobile entry point (QML UI only).

This is a deliberately *thin* alternative to the desktop ``main.py``. It
does **not** import :mod:`l5r.main`, because that module pulls in the whole
legacy QWidget UI (``from l5r.ui... import`` at module top), which in turn
drags in desktop-only dependencies (``lxml`` via ``l5r/dialogs/spelldlg.py``,
``pyqtwaitingspinner``, ``darkdetect``) that are neither needed nor shippable
on Android.

Instead it calls :func:`l5r.qmlui.run_qml_app` directly after a minimal
``QApplication`` + settings bootstrap, mirroring the QML branch of
``l5r.main.main()`` (the part after the ``ui_mode == "qml"`` gate).

The binding is forced to PySide6 (the only Qt-for-Python binding that targets
Android; PyQt6 ships no Android wheels), and the front-end is forced to QML.
"""

import os

# Force the mobile-capable Qt binding and the QML front-end. Must be set
# before any qtpy import so qtpy selects PySide6.
os.environ.setdefault("QT_API", "pyside6")
os.environ.setdefault("L5RCM_UI", "qml")
# Fusion accepts the background/contentItem customization our QML relies on
# (see l5r/qmlui/app.py for the full rationale). run_qml_app sets this too,
# but setting it here as well is harmless and explicit.
os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "Fusion")

from qtpy import QtCore, QtGui

import l5r.api as api  # noqa: F401  (kept explicit; run_qml_app reads the ctx)
from l5r.qmlui import run_qml_app
from l5r.util.settings import L5RCMSettings
from l5r.l5rcmcore import APP_NAME, APP_ORG, APP_VERSION


def _configure_ca_certs():
    """Point stdlib ``ssl`` at certifi's CA bundle on Android.

    The python-for-android CPython ships no accessible system CA store, so
    ssl's default certificate verification fails app-wide with
    ``CERTIFICATE_VERIFY_FAILED: unable to get local issuer certificate``
    (e.g. the in-app datapack download over HTTPS). Exporting
    ``SSL_CERT_FILE`` before any TLS handshake makes
    ``ssl.create_default_context()`` -- and therefore urllib and everything
    built on it -- trust certifi's bundled roots. certifi is vendored into
    the APK (see the Android workflow); ``certifi.where()`` resolves to that
    bundled ``cacert.pem`` on device.

    No-op off Android (the desktop has a real system trust store) and
    best-effort: a failure here must never stop the app from starting.
    """
    if not api.is_android():
        return
    try:
        import certifi

        cafile = certifi.where()
        # setdefault: respect an env already set by the platform/launcher.
        os.environ.setdefault("SSL_CERT_FILE", cafile)
    except Exception:  # noqa: BLE001 -- never block startup on this
        from l5r.util import log
        log.app.warning("could not configure certifi CA bundle", exc_info=True)


def main():
    # QML-only UI: a QGuiApplication is enough (no QtWidgets). Using
    # QApplication here would pull in the QtWidgets binding, which on Android
    # makes pyside6-android-deploy add Widgets to --qt-libs; the Java QtLoader
    # then tries to preload QtWidgets.abi3.so from lib/arm64 before Python
    # starts and SIGSEGV/exits because that module is only bundled under
    # site-packages. The desktop entry point (l5r/main.py) keeps QApplication
    # for the legacy QWidget UI.

    # Trust certifi's CA roots on Android (no-op off Android). Must run
    # before any TLS handshake (e.g. the datapack download), so do it first.
    _configure_ca_certs()

    # NOTE: the APK is intentionally portrait-locked (p4a's default). Runtime
    # auto-rotation via setRequestedOrientation didn't take on device and
    # isn't worth chasing for a POC -- the responsive QML UI already targets
    # portrait phones (width < Theme.bpCompact -> the nav sidebar collapses
    # behind a hamburger drawer). If rotation is wanted later, the lever is
    # the Android activity's setRequestedOrientation (try SCREEN_ORIENTATION_
    # SENSOR, on the UI thread).
    app = QtGui.QGuiApplication([])

    QtCore.QCoreApplication.setApplicationName(APP_NAME)
    QtCore.QCoreApplication.setApplicationVersion(APP_VERSION)
    QtCore.QCoreApplication.setOrganizationName(APP_ORG)

    settings = L5RCMSettings()
    settings.load_defaults()
    settings.sync()

    if settings.app.use_system_locale:
        app_locale = QtCore.QLocale.system().name()
    else:
        app_locale = settings.app.user_locale

    # No CLI startup action on mobile: session resume inside run_qml_app
    # restores the last character (or creates a fresh one).
    return run_qml_app(app, app_locale, None)


if __name__ == "__main__":
    raise SystemExit(main())
