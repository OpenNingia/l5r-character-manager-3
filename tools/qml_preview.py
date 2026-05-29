# -*- coding: utf-8 -*-
# Copyright (C) 2014-2026 Daniele Simonetti
#
# Reusable offscreen renderer for the QML UI: instantiates a single QML
# component (typically a dialog) inside a throwaway ApplicationWindow,
# opens it, and grabs the window to a PNG -- no datapacks, no real app
# bootstrap. Lets us eyeball a dialog's layout/chrome in CI or during
# development without a display.
#
# It binds NULL `appCtrl` / `pcProxy` context properties so the proxy
# getters (which all null-guard) return empty data; the visual chrome
# and layout still render. For a fuller render, point --qml at a custom
# host file that provides its own stubs.
#
# Usage (see tools/qml_preview.ps1 for the env wrapper):
#   python tools/qml_preview.py --dialog InscribePerkDialog \
#       --call 'present("merit")' --size 980x720 --out preview.png
#   python tools/qml_preview.py --dialog FamilyChooserDialog --call open --out fam.png
#   python tools/qml_preview.py --qml some/Standalone.qml --out s.png
#
# Requires QT_QPA_PLATFORM=offscreen and (for offscreen grabbing)
# QT_QUICK_BACKEND=software -- the wrapper sets both.
import argparse
import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("QT_API", "pyqt6")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QUICK_BACKEND", "software")
os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "Fusion")

from qtpy.QtCore import QUrl, QTimer  # noqa: E402
from qtpy.QtGui import QGuiApplication, QFontDatabase  # noqa: E402
from qtpy.QtQml import QQmlApplicationEngine  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
QML_DIR = REPO / "l5r" / "qmlui" / "qml"
FONTS_DIR = REPO / "l5r" / "share" / "fonts"


def _load_fonts():
    for f in sorted(list(FONTS_DIR.glob("*.ttf")) + list(FONTS_DIR.glob("*.otf"))):
        QFontDatabase.addApplicationFont(str(f))


def _grab(window, out_path):
    # rootObjects() returns the ApplicationWindow typed as QWindow; the
    # grabWindow() slot lives on QQuickWindow, so cast across.
    from PyQt6 import sip
    from PyQt6.QtQuick import QQuickWindow
    qw = sip.cast(window, QQuickWindow)
    img = qw.grabWindow()
    ok = img.save(out_path)
    print("[qml_preview] saved={} {} {}x{}".format(ok, out_path, img.width(), img.height()))


def _host_qml(dialog_name, call, width, height):
    # `call` is a QML method invocation on the dialog, e.g. present("merit")
    # or open. Bare names get () appended.
    if "(" not in call:
        call = call + "()"
    return """
import QtQuick
import QtQuick.Controls
import "dialogs" as Dialogs
ApplicationWindow {{
    visible: true
    width: {w}; height: {h}
    color: "#6f6f6f"
    Dialogs.{name} {{
        id: dlg
        Component.onCompleted: dlg.{call}
    }}
}}
""".format(w=width, h=height, name=dialog_name, call=call)


def main():
    ap = argparse.ArgumentParser(description="Offscreen-render a QML component to a PNG.")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--dialog", help="component name in l5r/qmlui/qml/dialogs/ (e.g. InscribePerkDialog)")
    g.add_argument("--qml", help="path to a standalone host QML file to render directly")
    ap.add_argument("--call", default="open", help="method to invoke on the dialog (default: open). e.g. 'present(\"merit\")'")
    ap.add_argument("--size", default="900x640", help="window size WxH (default 900x640)")
    ap.add_argument("--out", default="qml_preview.png", help="output PNG path")
    ap.add_argument("--delay", type=int, default=900, help="ms to wait before grabbing (default 900)")
    args = ap.parse_args()

    width, height = (int(x) for x in args.size.lower().split("x"))

    app = QGuiApplication(sys.argv)
    _load_fonts()

    engine = QQmlApplicationEngine()
    engine.addImportPath(str(QML_DIR))
    # Null stubs so proxy-guarded getters return empty rather than ReferenceError.
    engine.rootContext().setContextProperty("appCtrl", None)
    engine.rootContext().setContextProperty("pcProxy", None)

    tmp = None
    if args.dialog:
        tmp = QML_DIR / "_qml_preview_host.qml"
        tmp.write_text(_host_qml(args.dialog, args.call, width, height), encoding="utf-8")
        target = tmp
    else:
        target = Path(args.qml)

    engine.load(QUrl.fromLocalFile(str(target)))
    roots = engine.rootObjects()
    if not roots:
        print("[qml_preview] ERROR: failed to load", target, file=sys.stderr)
        if tmp:
            tmp.unlink(missing_ok=True)
        return 2
    window = roots[0]

    rc = {"code": 0}

    def grab():
        try:
            _grab(window, args.out)
        except Exception as exc:  # noqa: BLE001
            print("[qml_preview] grab failed:", exc, file=sys.stderr)
            rc["code"] = 3
        finally:
            if tmp:
                tmp.unlink(missing_ok=True)
            app.quit()

    QTimer.singleShot(args.delay, grab)
    app.exec()
    return rc["code"]


if __name__ == "__main__":
    sys.exit(main())
