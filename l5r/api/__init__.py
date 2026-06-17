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

import functools
import os
import re

from l5r.api.context import L5RCMContext, _current, get_context, use  # noqa: F401

ORG = 'openningia'
APP = 'l5rcm'


def is_android():
    """True when running under python-for-android (the Android packaging
    used by pyside6-android-deploy). ``ANDROID_ARGUMENT`` is set by the p4a
    bootstrap and is the canonical "am I on Android" marker."""
    return 'ANDROID_ARGUMENT' in os.environ


def get_user_data_path(rel_path=None):
    user_data = '.'
    if is_android():
        # python-for-android exposes the app's private, always-writable
        # internal storage via ANDROID_PRIVATE (it also points HOME there).
        # There is no XDG/APPDATA equivalent on Android, so anchor our
        # config tree directly under it.
        base = os.environ.get('ANDROID_PRIVATE') or os.environ.get('HOME', '.')
        user_data = os.path.join(base, '.config')
    elif os.name == 'posix':  # Linux is ok but Macosx ???
        user_data = '%s/.config' % (os.environ['HOME'])
    elif os.name == 'nt':
        user_data = os.environ['APPDATA']
    if rel_path:
        return os.path.join(user_data, ORG, APP, rel_path)
    return os.path.join(user_data, ORG, APP)


def set_translation_context(obj):
    get_context().translation_provider = obj


def cmp(a, b):
    return (a > b) - (a < b)


def ver_cmp(version1, version2):
    def normalize(v):
        return [int(x) for x in re.sub(r'(\.0+)*$', '', v).split(".")]
    return cmp(normalize(version1), normalize(version2))


def tr(*args, **kwargs):
    """translate text"""
    return get_context().tr(*args, **kwargs)


# Bind the production L5RCMContext onto the _current ContextVar at
# import time so any get_context() call in production code returns it.
# Tests can override per-scope with l5r.api.context.use().
_current.set(L5RCMContext())


# L5RCMContext.reload needs get_user_data_path (which lives here in
# l5r/api/__init__.py, to avoid a circular import with l5r/api/context.py).
# Bind a partial on the production context that supplies it so callers
# can keep doing ``get_context().reload()`` without args. functools.partial
# (rather than a closure-capturing lambda) keeps the wrapper independent of
# the surrounding module namespace.
_ctx = get_context()
_ctx.reload = functools.partial(_ctx.reload, get_user_data_path)
del _ctx
