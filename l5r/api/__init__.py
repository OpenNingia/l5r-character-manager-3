# -*- coding: utf-8 -*-
# Copyright (C) 2014-2022 Daniele Simonetti
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

import os
import re

from l5r.api.context import L5RCMContext, _current, get_context, use  # noqa: F401

ORG = 'openningia'
APP = 'l5rcm'


def get_user_data_path(rel_path=None):
    user_data = '.'
    if os.name == 'posix':  # Linux is ok but Macosx ???
        user_data = '%s/.config' % (os.environ['HOME'])
    elif os.name == 'nt':
        user_data = os.environ['APPDATA']
    if rel_path:
        return os.path.join(user_data, ORG, APP, rel_path)
    return os.path.join(user_data, ORG, APP)


def set_translation_context(obj):
    __api.translation_provider = obj


def cmp(a, b):
    return (a > b) - (a < b)


def ver_cmp(version1, version2):
    def normalize(v):
        return [int(x) for x in re.sub(r'(\.0+)*$', '', v).split(".")]
    return cmp(normalize(version1), normalize(version2))


def tr(*args, **kwargs):
    """translate text"""
    return __api.tr(*args, **kwargs)


# Back-compat alias. Pre-Phase-5 code referred to the class as
# L5RCMAPI; the new name is L5RCMContext (see l5r/api/context.py).
L5RCMAPI = L5RCMContext


# The production L5RCMContext. Bound to the _current ContextVar
# immediately below so that production code paths see it as the active
# context, while tests can override per-scope with l5r.api.context.use().
#
# ``__api`` is retained as a transitional alias so existing references
# (e.g. ``from l5r.api import get_context; __api.pc``) keep working while
# the find-and-replace to ``get_context()`` rolls through the codebase.
__api = L5RCMContext()
_current.set(__api)


# L5RCMContext.reload needs get_user_data_path, but that helper lives
# here (in l5r/api/__init__.py). Bind a wrapper that supplies it so
# existing callers can keep doing ``__api.reload()`` without args.
_original_reload = __api.reload
__api.reload = lambda: _original_reload(get_user_data_path)
