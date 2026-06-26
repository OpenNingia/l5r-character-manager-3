# Copyright (C) 2023 The Qt Company Ltd.
# SPDX-License-Identifier: LicenseRef-Qt-Commercial OR LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only
#
# Committed copy of the PySide6 python-for-android recipe that
# pyside6-android-deploy generates on the fly. We drive a plain `buildozer`
# build from a committed buildozer.spec instead of the deploy tool, so this
# recipe lives in-tree (referenced via p4a.local_recipes).
#
# Changes vs the generated original (kept minimal):
#   - ``wheel_path`` is read from the environment (L5RCM_PYSIDE6_WHEEL) rather
#     than a CI-absolute path, so the recipe is portable.
#   - the per-module ``QtX.abi3.so`` copies (which the deploy tool emits as a
#     long unrolled block keyed off the detected --qt-libs) are folded into a
#     loop over QT_MODULES. That list MUST match the --qt-libs in
#     buildozer.spec's p4a.extra_args (minus OpenGL, which ships no QtOpenGL
#     top-level .abi3.so binding but a real libQt6OpenGL.so under Qt/lib that
#     the copytree below already carries).
#
# Keep ``version`` and QT_MODULES in sync with the Android wheels / extra_args
# when bumping PySide6.
from __future__ import annotations

import os
import shutil
import zipfile
from pathlib import Path

from pythonforandroid.logger import info
from pythonforandroid.recipe import PythonRecipe

# Top-level PySide6 binding modules to load on startup. Mirrors the
# --qt-libs list in buildozer.spec (Core first for JNI_OnLoad ordering).
QT_MODULES = [
    "QtCore",
    "QtGui",
    "QtNetwork",
    "QtQml",
    "QtQuick",
    "QtQuickControls2",
    "QtOpenGL",
]


class PySideRecipe(PythonRecipe):
    version = '6.11.1'
    wheel_path = os.environ['L5RCM_PYSIDE6_WHEEL']
    depends = ["shiboken6"]
    call_hostpython_via_targetpython = False
    install_in_hostpython = False

    def build_arch(self, arch):
        """Unzip the wheel and copy into site-packages of target."""

        info("Copying libc++_shared.so from SDK to be loaded on startup")
        libcpp_path = (f"{self.ctx.ndk.sysroot_lib_dir}/"
                       f"{arch.command_prefix}/libc++_shared.so")
        shutil.copyfile(libcpp_path,
                        Path(self.ctx.get_libs_dir(arch.arch)) / "libc++_shared.so")

        info(f"Installing {self.name} into site-packages")
        with zipfile.ZipFile(self.wheel_path, "r") as zip_ref:
            info("Unzip wheels and copy into {}".format(
                self.ctx.get_python_install_dir(arch.arch)))
            zip_ref.extractall(self.ctx.get_python_install_dir(arch.arch))

        pyside_dir = Path(f"{self.ctx.get_python_install_dir(arch.arch)}/PySide6")
        lib_dir = pyside_dir / "Qt" / "lib"
        libs_out = Path(self.ctx.get_libs_dir(arch.arch))

        info("Copying Qt libraries to be loaded on startup")
        shutil.copytree(lib_dir, libs_out, dirs_exist_ok=True)

        # PySide6's own shared objects + the per-module bindings.
        for so in ["libpyside6.abi3.so", "libpyside6qml.abi3.so"]:
            shutil.copyfile(pyside_dir / so, libs_out / so)
        for mod in QT_MODULES:
            src = pyside_dir / f"{mod}.abi3.so"
            if src.exists():
                shutil.copyfile(src, libs_out / f"{mod}.abi3.so")

        # The Android platform integration plugin.
        plugin_path = (lib_dir.parent / "plugins" / "platforms" /
                       f"libplugins_platforms_qtforandroid_{arch.arch}.so")
        if plugin_path.exists():
            shutil.copyfile(
                plugin_path,
                libs_out / f"libplugins_platforms_qtforandroid_{arch.arch}.so")


recipe = PySideRecipe()
