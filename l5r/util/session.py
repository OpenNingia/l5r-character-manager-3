# -*- coding: utf-8 -*-
# Copyright (C) 2014-2026 Daniele Simonetti
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# Autosave / crash-recovery session store.
#
# A character editor autosaves the working character to a *recovery*
# file in the user config dir -- never to the character's real .l5r,
# which is only written on an explicit Save. A small JSON *pointer*
# alongside it records the real path the session maps to (empty for a
# never-saved character) and whether the recovery snapshot holds unsaved
# edits, so the next launch can resume exactly where the user left off:
#
#   pointer.dirty == True   -> the recovery file holds unsaved edits;
#                              load it and re-mark the session dirty.
#   pointer.dirty == False  -> the work is safely committed to `path` on
#                              disk; reload that file instead.
#
# File > New clears the store (the recovery file IS the unsaved work it
# discards) and writes a fresh empty pointer. An explicit Save / Open
# does the same (the work now lives in the real .l5r) but records the
# associated path so the next launch reopens it.
#
# This module is UI-agnostic (no Qt import): only file IO + JSON against
# the user config dir, like its osutil/fsutil/settings neighbours. The
# front-end (currently the QML AppController) owns the *policy* -- when
# to autosave, what to restore -- and calls in here for the *storage*.

import json
import os

from l5r.util import log
from l5r.util import osutil

_RECOVERY_NAME = "session.l5r"
_POINTER_NAME = "session.json"


def recovery_path():
    """Absolute path of the recovery .l5r snapshot in the user config dir."""
    return osutil.get_user_data_path(_RECOVERY_NAME)


def _pointer_path():
    return osutil.get_user_data_path(_POINTER_NAME)


def _ensure_dir(path):
    folder = os.path.dirname(path)
    if folder and not os.path.isdir(folder):
        os.makedirs(folder, exist_ok=True)


def write_pointer(real_path, dirty):
    """Persist the session pointer: the real .l5r path this session maps
    to (empty for a never-saved character) and whether the recovery file
    holds unsaved edits."""
    target = _pointer_path()
    try:
        _ensure_dir(target)
        with open(target, "wt") as fp:
            json.dump({"path": real_path or "", "dirty": bool(dirty)}, fp)
    except OSError:
        log.app.exception(u"autosave: could not write session pointer")


def write_recovery(pc, real_path, dirty=True):
    """Mirror the working character to the recovery file and update the
    pointer. Uses save_to(clear_dirty=False) so the in-memory unsaved
    flag survives -- the work is recovered, not committed to the real
    file. Returns True on success."""
    if pc is None:
        return False
    rec = recovery_path()
    try:
        _ensure_dir(rec)
        if pc.save_to(rec, clear_dirty=False):
            write_pointer(real_path, dirty)
            log.app.debug(u"autosave: recovery snapshot written (path=%r)",
                          real_path)
            return True
    except OSError:
        log.app.exception(u"autosave: could not write recovery file")
    return False


def read_pointer():
    """Return the session pointer as {"path": str, "dirty": bool}, or
    None when it is absent or unreadable."""
    target = _pointer_path()
    if not os.path.exists(target):
        return None
    try:
        with open(target, "rt") as fp:
            data = json.load(fp)
        return {
            "path": data.get("path") or "",
            "dirty": bool(data.get("dirty")),
        }
    except (OSError, ValueError):
        log.app.exception(u"autosave: could not read session pointer")
        return None


def remove_recovery():
    """Delete the recovery file if present (e.g. after an explicit Save,
    when the work now lives in the real .l5r)."""
    rec = recovery_path()
    try:
        if os.path.exists(rec):
            os.remove(rec)
    except OSError:
        log.app.exception(u"autosave: could not remove recovery file")


def clear():
    """Drop the whole session store -- recovery file and pointer. Used by
    File > New, which discards the unsaved recovery snapshot."""
    remove_recovery()
    target = _pointer_path()
    try:
        if os.path.exists(target):
            os.remove(target)
    except OSError:
        log.app.exception(u"autosave: could not remove session pointer")
