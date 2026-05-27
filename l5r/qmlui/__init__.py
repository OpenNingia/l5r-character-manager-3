# -*- coding: utf-8 -*-
# Copyright (C) 2014-2026 Daniele Simonetti
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# Optional QML UI entry point. The package is loaded only when
# l5r/main.py sees L5RCM_UI=qml; the legacy QWidget UI is unaffected.

from l5r.qmlui.app import run_qml_app  # noqa: F401
