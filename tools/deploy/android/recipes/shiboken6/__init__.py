# Copyright (C) 2023 The Qt Company Ltd.
# SPDX-License-Identifier: LicenseRef-Qt-Commercial OR LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only
#
# Committed copy of the shiboken6 python-for-android recipe that
# pyside6-android-deploy generates on the fly. We drive a plain `buildozer`
# build from a committed buildozer.spec instead of the deploy tool, so this
# recipe lives in-tree (referenced via p4a.local_recipes). The ONLY change vs
# the generated original is that ``wheel_path`` is read from the environment
# (L5RCM_SHIBOKEN6_WHEEL) rather than hard-coded to a CI-absolute path, so the
# recipe is portable. Keep ``version`` in sync with the PySide6/shiboken6
# Android wheels downloaded by the Android workflow.
from __future__ import annotations

import os
import shutil
import zipfile
from pathlib import Path

from pythonforandroid.logger import info
from pythonforandroid.recipe import PythonRecipe


class ShibokenRecipe(PythonRecipe):
    version = '6.11.1'
    wheel_path = os.environ['L5RCM_SHIBOKEN6_WHEEL']

    call_hostpython_via_targetpython = False
    install_in_hostpython = False

    def build_arch(self, arch):
        '''Unzip the wheel and copy into site-packages of target.'''
        info('Installing {} into site-packages'.format(self.name))
        with zipfile.ZipFile(self.wheel_path, 'r') as zip_ref:
            info('Unzip wheels and copy into {}'.format(
                self.ctx.get_python_install_dir(arch.arch)))
            zip_ref.extractall(self.ctx.get_python_install_dir(arch.arch))

        lib_dir = Path(f"{self.ctx.get_python_install_dir(arch.arch)}/shiboken6")
        shutil.copyfile(lib_dir / "libshiboken6.abi3.so",
                        Path(self.ctx.get_libs_dir(arch.arch)) / "libshiboken6.abi3.so")


recipe = ShibokenRecipe()
