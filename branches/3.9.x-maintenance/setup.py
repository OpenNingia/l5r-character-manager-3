# Copyright (C) 2011 Daniele Simonetti
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
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
from distutils.core import setup
import py2exe

setup(
    windows = [
        {
            "script": "l5rcm.py",
            "icon_resources": [(0, "windows/l5rcm.ico"), (1, "windows/l5rcmpack.ico")]
        }
    ],
    options={"py2exe": {"includes": ["PySide.QtGui"]}},
    )
