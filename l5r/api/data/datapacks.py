# -*- coding: utf-8 -*-
# Copyright (C) 2014-2026 Daniele Simonetti
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# Datapack install / delete -- the GUI-free, synchronous core of datapack
# management. Both the QML DatapackProxy and the legacy QWidget
# L5RCMCore.import_data_pack drive these (the headless CLI ``--import`` in
# l5r.qmlui.proxies.app_controller routes here too), so there is one place
# that knows how a .l5rcmpack lands on disk and how it comes off.
#
# This module deliberately:
#   * never touches L5RCMSettings -- the datapack *blacklist* (enable/
#     disable) is a settings concern that stays in the proxy/UI layer,
#     which then calls api.data.set_blacklist(...) + api.data.reload().
#     Here we only validate, extract, and remove files.
#   * never reloads the data store -- the caller decides when to
#     ``api.data.reload()`` (so a batch can reload once at the end).
#   * carries no dirty flag -- datapacks are application data, not
#     character state.

import os
import shutil
import zipfile

import l5rdal as dal
import l5rdal.dataimport
from l5rdal.dataimport import (
    InvalidDataPack,
    ManifestNotFound,
    VersionMismatch,
)

import l5r.api as api
import l5r.api.data
from l5r.l5rcmcore import APP_VERSION
from l5r.util import log


# import_pack result codes. The api layer is i18n-free: it returns one of
# these and the proxy maps it to a localised, user-facing message.
OK = 'ok'
INVALID = 'invalid'                      # not a datapack / missing manifest
CM_VERSION = 'cm_version'                # min-cm-version newer than APP_VERSION
ALREADY_INSTALLED = 'already_installed'  # an equal-or-newer copy is on disk
ERROR = 'error'                          # unexpected failure


def dest_for(pack):
    """Return the install root for ``pack`` under the user data dir.

    Routing mirrors L5RCMCore.import_data_pack: the ``core`` pack lives in
    ``core.data``; a language-tagged pack in ``data.<language>``; anything
    else in the shared ``data``. ``l5rdal.dataimport.DataPack.export_to``
    then appends the pack id beneath this and extracts there.
    """
    base = api.get_user_data_path()
    if pack.id == 'core':
        return os.path.join(base, 'core.data')
    if pack.language:
        return os.path.join(base, 'data.' + pack.language)
    return os.path.join(base, 'data')


def import_pack(path):
    """Validate and extract a .l5rcmpack/.zip onto disk.

    Returns ``(code, pack_id, detail)`` where ``code`` is one of the
    module constants, ``pack_id`` is the manifest id on success (else
    None), and ``detail`` is a short non-localised string for logging.

    Does NOT reload the data store -- the caller reloads when ready.

    Security note: ``DataPack.export_to`` uses ``zipfile.extractall`` on
    archive-controlled paths (a known ZIP-slip in l5rdal). For the in-app
    downloader this is mitigated by the host allow-list (downloads only
    come from the official GitHub repo); a locally-picked file is the
    user's own trust decision, exactly as on the legacy import path.
    """
    dal.dataimport.CM_VERSION = APP_VERSION
    try:
        pack = dal.dataimport.DataPack(path)
    except ManifestNotFound:
        log.api.warning(u"datapack import: no manifest in %s", path)
        return (INVALID, None, 'manifest-not-found')
    except (zipfile.BadZipFile, OSError):
        # Not a zip / unreadable file -- the user picked the wrong thing.
        log.api.warning(u"datapack import: not a valid archive: %s", path)
        return (INVALID, None, 'bad-archive')
    except Exception:
        log.api.exception(u"datapack import: cannot open %s", path)
        return (ERROR, None, 'open-failed')

    if not pack.good():
        return (INVALID, None, 'not-good')

    dest = dest_for(pack)
    try:
        pack.export_to(dest)
    except VersionMismatch:
        # export_to raises the SAME exception for two distinct cases:
        # the pack needs a newer L5R:CM than we are, or an equal/newer
        # copy is already installed. check_cm_version() (False => the
        # former) disambiguates -- it is evaluated first inside export_to.
        if not pack.check_cm_version():
            log.api.warning(u"datapack import: needs CM >= %s (have %s)",
                            pack.min_cm_ver, APP_VERSION)
            return (CM_VERSION, pack.id, 'cm-version')
        log.api.info(u"datapack import: %s already installed (>= %s)",
                     pack.id, pack.version)
        return (ALREADY_INSTALLED, pack.id, 'already-installed')
    except InvalidDataPack:
        log.api.warning(u"datapack import: invalid archive %s", path)
        return (INVALID, None, 'invalid-archive')
    except Exception:
        log.api.exception(u"datapack import: extract failed for %s", path)
        return (ERROR, None, 'extract-failed')

    log.api.info(u"datapack import: installed %s to %s", pack.id, dest)
    return (OK, pack.id, None)


def delete_pack(pack_id):
    """Remove an installed datapack's files from disk.

    Deletes the pack's own directory (``DataManifest.path`` -- the folder
    l5rdal found the manifest in), guarded so it can never escape the user
    data dir. Does NOT prune the shared ``data``/``core.data`` roots, and
    does NOT reload the data store. Returns True on success.
    """
    pack = api.data.pack_by_id(pack_id)
    if pack is None:
        log.api.warning(u"datapack delete: unknown pack %r", pack_id)
        return False

    target = getattr(pack, 'path', None)
    if not target:
        log.api.warning(u"datapack delete: pack %r has no path", pack_id)
        return False

    base = os.path.realpath(api.get_user_data_path())
    target = os.path.realpath(target)
    # Path-traversal guard: a malformed manifest path must not let rmtree
    # escape the data dir. commonpath raises ValueError on mixed drives.
    try:
        if os.path.commonpath([base, target]) != base or target == base:
            log.api.error(u"datapack delete: refusing unsafe path %s", target)
            return False
    except ValueError:
        log.api.error(u"datapack delete: refusing cross-volume path %s", target)
        return False

    if not os.path.isdir(target):
        log.api.warning(u"datapack delete: %s is not a directory", target)
        return False

    try:
        shutil.rmtree(target)
    except OSError:
        # Windows can briefly hold a handle on a just-read XML file. Retry
        # once before giving up so the common case succeeds.
        log.api.warning(u"datapack delete: first rmtree failed for %s, retrying",
                        target)
        try:
            shutil.rmtree(target)
        except OSError:
            log.api.exception(u"datapack delete: could not remove %s", target)
            return False

    log.api.info(u"datapack delete: removed %s (%s)", pack_id, target)
    return True


def installed():
    """Return the list of installed packs (DataManifest objects).

    Thin pass-through of ``api.data.packs()`` so callers can read pack
    metadata (id, display_name, language, version, authors, active, path)
    without importing the data submodule directly.
    """
    return api.data.packs()
