# -*- coding: utf-8 -*-
# Copyright (C) 2014-2026 Daniele Simonetti
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# Per-character sheet-section visibility store.
#
# The QML sheet lets the user hide sections they don't use (Spells for a
# bushi, Kiho/Kata/Tattoos for a samurai, ...). That choice is a *view*
# preference, not character data, so it is deliberately NOT written into
# the .l5r save file -- it lives here, in a single JSON map in the user
# config dir, keyed by a hash of the character's file path:
#
#   { "<sha1 of normcase(abspath(path))>": ["spells", "kiho", ...], ... }
#
# A never-saved character has no path to key on; the front-end keeps its
# hidden set in memory and flushes it here on the first Save (when a path
# finally exists). Save-As copies the set to the new file's key.
#
# Like its session/osutil/fsutil neighbours this module is UI-agnostic:
# only file IO + JSON against the user config dir. The front-end (the QML
# AppController) owns the policy -- which sections, when to load/store --
# and calls in here for the storage.

import hashlib
import json
import os

from l5r.util import log
from l5r.util import osutil

_STORE_NAME = "section_visibility.json"


def _store_path():
    return osutil.get_user_data_path(_STORE_NAME)


def _key(path):
    """Stable map key for a character file path, or None for a never-saved
    character (empty path) which can't be persisted yet."""
    if not path:
        return None
    norm = os.path.normcase(os.path.abspath(path))
    return hashlib.sha1(norm.encode("utf-8")).hexdigest()


def _ensure_dir(path):
    folder = os.path.dirname(path)
    if folder and not os.path.isdir(folder):
        os.makedirs(folder, exist_ok=True)


def _read_map():
    target = _store_path()
    if not os.path.exists(target):
        return {}
    try:
        with open(target, "rt") as fp:
            data = json.load(fp)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        log.app.exception(u"section visibility: could not read store")
        return {}


def load(path):
    """Return the set of hidden section ids for `path` (empty set when the
    path is empty/unknown or the store is absent/unreadable)."""
    key = _key(path)
    if key is None:
        return set()
    entry = _read_map().get(key)
    return set(entry) if isinstance(entry, list) else set()


def store(path, hidden_ids):
    """Persist the hidden section ids for `path`. No-op for a never-saved
    character (empty path). An empty set drops the key, keeping the store
    tidy."""
    key = _key(path)
    if key is None:
        return
    data = _read_map()
    hidden = sorted(hidden_ids)
    if hidden:
        data[key] = hidden
    else:
        data.pop(key, None)
    target = _store_path()
    try:
        _ensure_dir(target)
        with open(target, "wt") as fp:
            json.dump(data, fp)
    except OSError:
        log.app.exception(u"section visibility: could not write store")
