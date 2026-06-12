#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (C) 2014-2026 Daniele Simonetti
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
"""Translation pipeline for L5RCM (both the legacy Python/QWidget UI and the QML UI).

The app has two translatable surfaces that need two different extractors:

  python  ``self.tr(...)`` / ``api.tr(...)`` strings in the ``.py`` sources
          (legacy QWidget UI + the api layer, which outlives it). Extracted by
          PyQt6's ``pylupdate6`` -- the only tool that reliably captures the
          custom ``api.tr()`` indirection the way the shipped .qm expect.
          Sources: all of ``l5r/`` minus tests and ``l5r/qmlui/``.
          .ts  -> l5r/i18n/<locale>.ts
          .qm  -> l5r/share/l5rcm/i18n/<locale>.qm

  qml     ``qsTr(...)`` strings in ``l5r/qmlui/qml/**/*.qml``. ``pylupdate6``
          cannot parse QML, so this uses the QML-capable lupdate (PySide6's
          ``pyside6-lupdate`` or a Qt SDK's ``lupdate``).
          .ts  -> l5r/i18n/qml/<locale>.ts
          .qm  -> l5r/share/l5rcm/i18n/qml_<locale>.qm  (a SECOND QTranslator,
                  installed by l5r/qmlui/app.py alongside the legacy one)

Keeping the two surfaces in separate .ts/.qm is deliberate: the Python and QML
extractors disagree on translation contexts, so a single merged file risks
orphaning (and ``lrelease`` then dropping) the existing translations -- whose
only copy lives in the compiled .qm.

Commands:
  extract   scan sources -> merge into per-locale .ts (existing translations
            preserved, new strings added, removed ones marked obsolete;
            pass --no-obsolete to drop the vanished/obsolete entries instead)
  compile   lrelease each per-locale .ts -> shipped .qm
  all       extract then compile
  pro       (re)generate l5r/l5rcm.pro from the current Python source scan

Use --surface {python,qml,both} (default both) to pick a surface.

Tooling. Python side needs ``pylupdate6`` (ships with PyQt6, already a project
dep). QML side and all ``lrelease`` need the PySide6 tools -- ``pip install
pyside6`` gives ``pyside6-lupdate`` / ``pyside6-lrelease`` (no sudo, parse QML;
ideal in WSL) -- or a Qt SDK's native ``lupdate`` / ``lrelease`` on PATH.

Note: PyQt6's ``pylupdate6`` does NOT read l5rcm.pro; this script passes sources
explicitly. The .pro is regenerated as a human/Qt-Linguist-readable manifest only.

Typical use in WSL, after recovering the per-locale Python .ts into l5r/i18n/:
    pip install pyside6
    python3 tools/scripts/update_translations.py all
    # ...translate the unfinished entries in l5r/i18n/*.ts and l5r/i18n/qml/*.ts...
    python3 tools/scripts/update_translations.py compile
"""

import argparse
import os
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# tools/scripts/update_translations.py -> repo root is two levels up.
REPO_ROOT = Path(__file__).resolve().parents[2]
L5R_DIR = REPO_ROOT / "l5r"
QML_DIR = L5R_DIR / "qmlui" / "qml"
PY_TS_DIR = L5R_DIR / "i18n"
QML_TS_DIR = L5R_DIR / "i18n" / "qml"
QM_DIR = L5R_DIR / "share" / "l5rcm" / "i18n"
PRO_FILE = L5R_DIR / "l5rcm.pro"

# QML .qm are prefixed so they never collide with the legacy <locale>.qm in the
# same directory; app.py loads them as a second translator.
QML_QM_PREFIX = "qml_"

# Path components that exclude a .py from the Python translation surface.
# share holds only assets and __init__ stubs (no tr() strings).
#
# Note we do NOT exclude "qmlui": only the QML *markup* (qsTr in .qml) is the
# QML surface -- the qmlui *Python* proxies (app_controller.py, settings_proxy.py,
# pc/*.py, ...) use self.tr() and so belong to this Python/pylupdate6 surface,
# compiled into the legacy <locale>.qm the first QTranslator loads. Only .py
# files are scanned and l5r/qmlui/qml/ holds none, so the QML markup can't leak
# in here. (Excluding qmlui wholesale silently dropped every proxy string --
# the QML sidebar tab titles among them.)
PY_EXCLUDE_PARTS = {"__pycache__", "tests", "share"}

# Tool resolution order matters: on Debian/Ubuntu /usr/bin/lupdate is often a Qt5
# qtchooser shim (or a broken alternatives symlink) that fails to exec, while the
# real Qt6 tool lives unversioned under /usr/lib/qt6/bin/. So we try the explicit
# version-suffixed / PySide6 names first, then absolute Qt6 install dirs, and only
# fall back to the bare name last. Absolute paths in the list are used as-is.
QT6_BIN_DIRS = [
    "/usr/lib/qt6/bin",
    "/usr/lib/x86_64-linux-gnu/qt6/bin",
    "/usr/lib/qt6/libexec",
    "/opt/qt6/bin",
]


def _candidates(tool):
    """Ordered probe list for a Qt linguist tool (e.g. 'lupdate'): version-suffixed
    and PySide6 names, then absolute Qt6 paths, then the bare name as last resort."""
    names = [f"pyside6-{tool}", f"{tool}6", f"{tool}-qt6"]
    names += [str(Path(d) / tool) for d in QT6_BIN_DIRS]
    names += [tool]
    return names


# pylupdate6 (PyQt6) is the only Python extractor; it has no shim ambiguity.
PYLUPDATE_CANDIDATES = ["pylupdate6"]
LUPDATE_CANDIDATES = _candidates("lupdate")
LRELEASE_CANDIDATES = _candidates("lrelease")


def _resolve(name):
    """Resolve `name` to an executable: an absolute/relative path is checked for
    existence + exec bit; a bare name is looked up on PATH."""
    if os.sep in name or (os.altsep and os.altsep in name):
        return name if (os.path.isfile(name) and os.access(name, os.X_OK)) else None
    return shutil.which(name)


def find_tool(candidates, kind, env_var=None, hint="pip install pyside6"):
    # An explicit override (e.g. L5R_LUPDATE=/path/to/lupdate) wins outright.
    if env_var and os.environ.get(env_var):
        override = os.environ[env_var]
        path = _resolve(override)
        if path:
            return path
        sys.exit(f"error: {env_var}={override!r} is not an executable file")
    for name in candidates:
        path = _resolve(name)
        if path:
            return path
    sys.exit(
        f"error: no {kind} found (tried: {', '.join(candidates)}).\n"
        f"       Install it with:  {hint}\n"
        f"       Or point the script at it:  {env_var or 'L5R_<TOOL>'}=/path/to/{kind} <command>"
    )


def run(cmd):
    print("+ " + " ".join(cmd))
    subprocess.run(cmd, check=True)


def discover_locales():
    """Mirror the locales the app already ships (one legacy .qm each), minus our
    own qml_*.qm outputs. Override with --locales for a subset."""
    locales = [qm.stem for qm in sorted(QM_DIR.glob("*.qm"))
               if not qm.stem.startswith(QML_QM_PREFIX)]
    if not locales:
        sys.exit(f"error: no legacy .qm under {QM_DIR} to derive locales from; "
                 f"pass --locales (e.g. --locales it_IT,fr,es_ES)")
    return locales


def python_sources():
    files = []
    for path in sorted(L5R_DIR.rglob("*.py")):
        if PY_EXCLUDE_PARTS & set(path.relative_to(L5R_DIR).parts):
            continue
        files.append(path)
    if not files:
        sys.exit(f"error: no .py sources found under {L5R_DIR}")
    return files


def qml_sources():
    files = sorted(QML_DIR.rglob("*.qml"))
    if not files:
        sys.exit(f"error: no .qml files under {QML_DIR}")
    return files


def ts_stats(ts_path):
    """(total, untranslated) message counts. An entry is untranslated when its
    <translation> is marked unfinished or has no text."""
    total = untranslated = 0
    for msg in ET.parse(ts_path).getroot().iter("message"):
        total += 1
        tr = msg.find("translation")
        text = (tr.text or "").strip() if tr is not None else ""
        type_ = tr.get("type") if tr is not None else None
        if type_ == "unfinished" or not text:
            untranslated += 1
    return total, untranslated


def _print_stats(label, locales, ts_dir):
    print(f"\n{label}: per-locale status")
    for loc in locales:
        ts = ts_dir / f"{loc}.ts"
        if not ts.exists():
            continue
        total, untr = ts_stats(ts)
        print(f"  {loc:<8} {total - untr:>4}/{total:<4} translated "
              f"({untr} to do)  {ts.relative_to(REPO_ROOT)}")


def extract_python(locales, no_obsolete=False):
    pylupdate = find_tool(PYLUPDATE_CANDIDATES, "pylupdate6",
                          env_var="L5R_PYLUPDATE", hint="pip install pyqt6")
    PY_TS_DIR.mkdir(parents=True, exist_ok=True)
    sources = [str(f) for f in python_sources()]
    # pylupdate6 spells it with a double dash, unlike Qt's lupdate.
    extra = ["--no-obsolete"] if no_obsolete else []
    ts_args = []
    for loc in locales:
        ts_args += ["-ts", str(PY_TS_DIR / f"{loc}.ts")]
    run([pylupdate, *extra, *sources, *ts_args])
    _print_stats("python", locales, PY_TS_DIR)


def extract_qml(locales, locations, no_obsolete=False):
    lupdate = find_tool(LUPDATE_CANDIDATES, "lupdate", env_var="L5R_LUPDATE")
    QML_TS_DIR.mkdir(parents=True, exist_ok=True)
    sources = [str(f) for f in qml_sources()]
    extra = ["-no-obsolete"] if no_obsolete else []
    ts_args = []
    for loc in locales:
        ts_args += ["-ts", str(QML_TS_DIR / f"{loc}.ts")]
    # -locations none keeps source line numbers out of the .ts so git diffs stay
    # about actual string changes, not churn from QML line shifts.
    run([lupdate, "-locations", locations, *extra, *sources, *ts_args])
    _print_stats("qml", locales, QML_TS_DIR)


def compile_surface(label, locales, ts_dir, qm_name):
    lrelease = find_tool(LRELEASE_CANDIDATES, "lrelease", env_var="L5R_LRELEASE")
    QM_DIR.mkdir(parents=True, exist_ok=True)
    built = 0
    for loc in locales:
        ts = ts_dir / f"{loc}.ts"
        if not ts.exists():
            print(f"skip {loc}: {ts.relative_to(REPO_ROOT)} missing -- run 'extract' first")
            continue
        run([lrelease, str(ts), "-qm", str(QM_DIR / qm_name(loc))])
        built += 1
    print(f"{label}: compiled {built} .qm into {QM_DIR.relative_to(REPO_ROOT)}/")


def regenerate_pro(locales):
    rel_sources = [str(f.relative_to(L5R_DIR)).replace("\\", "/") for f in python_sources()]
    rel_ts = [f"i18n/{loc}.ts" for loc in locales]
    body = (
        "# Auto-generated by tools/scripts/update_translations.py -- do not edit by hand.\n"
        "# Manifest of the Python sources scanned for tr()/api.tr() strings and the\n"
        "# per-locale .ts targets. NOTE: PyQt6's pylupdate6 does NOT read this file;\n"
        "# the script passes these paths explicitly. Kept for Qt Linguist compatibility.\n"
        "\n"
        "SOURCES = " + " \\\n          ".join(rel_sources) + "\n"
        "\n"
        "TRANSLATIONS = " + " \\\n               ".join(rel_ts) + "\n"
        "\n"
        "CODECFORTR = UTF-8\n"
    )
    PRO_FILE.write_text(body, encoding="utf-8")
    print(f"wrote {PRO_FILE.relative_to(REPO_ROOT)} "
          f"({len(rel_sources)} sources, {len(rel_ts)} translations)")


def cmd_extract(args):
    if args.surface in ("python", "both"):
        extract_python(args.locales, args.no_obsolete)
        if not args.no_pro:
            regenerate_pro(args.locales)
    if args.surface in ("qml", "both"):
        extract_qml(args.locales, args.locations, args.no_obsolete)


def cmd_compile(args):
    if args.surface in ("python", "both"):
        compile_surface("python", args.locales, PY_TS_DIR, lambda loc: f"{loc}.qm")
    if args.surface in ("qml", "both"):
        compile_surface("qml", args.locales, QML_TS_DIR, lambda loc: f"{QML_QM_PREFIX}{loc}.qm")


def cmd_all(args):
    cmd_extract(args)
    print()
    cmd_compile(args)


def cmd_pro(args):
    regenerate_pro(args.locales)


def main(argv=None):
    # Shared options live on a parent parser so they can be passed *after* the
    # subcommand, e.g. `extract --surface python`.
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--surface", choices=("python", "qml", "both"), default="both",
        help="which translatable surface to act on (default: both)",
    )
    common.add_argument(
        "--locales", metavar="CSV",
        help="comma-separated locales (default: discovered from share/l5rcm/i18n/*.qm). "
             "Example: it_IT,fr,es_ES",
    )
    common.add_argument(
        "--locations", choices=("none", "relative", "absolute"), default="none",
        help="how the QML lupdate records source locations in the .ts "
             "(default: none, for clean git diffs; ignored by pylupdate6)",
    )
    common.add_argument(
        "--no-pro", action="store_true",
        help="do not regenerate l5rcm.pro during a python extract",
    )
    common.add_argument(
        "--no-obsolete", action="store_true",
        help="during extract, drop vanished/obsolete entries from the .ts "
             "instead of keeping them parked (passes -no-obsolete to the "
             "extractors). Translations of removed strings are lost for good.",
    )

    parser = argparse.ArgumentParser(
        description="Extract and compile L5RCM translations (Python + QML surfaces).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("extract", parents=[common],
                   help="scan sources -> merge strings into per-locale .ts")
    sub.add_parser("compile", parents=[common],
                   help="lrelease per-locale .ts -> shipped .qm")
    sub.add_parser("all", parents=[common], help="extract then compile")
    sub.add_parser("pro", parents=[common],
                   help="(re)generate l5r/l5rcm.pro from the Python source scan")

    args = parser.parse_args(argv)
    args.locales = (
        [s.strip() for s in args.locales.split(",") if s.strip()]
        if args.locales else discover_locales()
    )

    {"extract": cmd_extract, "compile": cmd_compile,
     "all": cmd_all, "pro": cmd_pro}[args.command](args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
