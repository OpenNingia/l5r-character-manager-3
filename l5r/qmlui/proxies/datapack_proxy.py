# -*- coding: utf-8 -*-
# Copyright (C) 2014-2026 Daniele Simonetti
#
# Bridge between the QML "Library" section and datapack management. Bound
# as the context property ``datapacks`` in l5r.qmlui.app.run_qml_app.
#
# Datapacks are *application* data (the game-rules content), not character
# state, so this lives here rather than on PcProxy -- the same reasoning as
# SettingsProxy. The split with the api layer:
#
#   * l5r.api.data.datapacks owns the filesystem work (validate/extract a
#     .l5rcmpack, delete a pack's directory). It is GUI- and i18n-free.
#   * this proxy owns the blacklist (enable/disable persisted in
#     L5RCMSettings), the async download/install plumbing, the QML-facing
#     records, and the localised toast messages.
#
# Async rule: network + extract run on a Worker thread (QThreadPool); the
# data store rebuild (api.data.reload) runs on the GUI thread in the
# result slot, because PcProxy getters read ctx.ds continuously and
# rebuilding it off-thread would race them. This mirrors AppController's
# PDF-export worker pattern.

import os

from qtpy.QtCore import QObject, Property, QThreadPool, Signal, Slot

# QtWidgets (QFileDialog) is imported LAZILY inside installFromFileDialog,
# never at module scope: the Android/QML build runs on a QGuiApplication with
# no QtWidgets binding (see app_controller's module note). On Android the
# file-picker install path is unavailable -- datapacks are installed by
# downloading them from the official repo instead.

import l5r.api as api
import l5r.api.character
import l5r.api.data
import l5r.api.data.datapacks as datapacks

from l5r.util import datapack_catalog
from l5r.util import log
from l5r.util.settings import L5RCMSettings
from l5r.util.worker import Worker

# Catalogue entry status (also the QML button-state key).
_INSTALLED = "installed"
_UPDATE = "update"
_AVAILABLE = "available"


def _norm_key(value):
    """Canonical key for matching a catalogue asset to an installed pack.

    Neither side is reliable on its own -- the official repo is internally
    inconsistent: some manifest ids keep ``_pack`` (``great_clan_pack``),
    some drop a ``_data_pack`` the filename has (``community`` vs
    ``community_data_pack``), and ``LBS`` is upper-case while its asset is
    ``lbs_pack``. So we normalise BOTH the asset filename and the manifest
    id the same way -- lower-case, strip the archive suffix and trailing
    ``-<version>``, then peel any trailing ``_pack`` / ``_data`` tokens --
    and compare the results. This is only used for the "installed?" badge;
    the import reads the real id from the archive and ``export_to`` guards
    the version, so a mislabel can never cause a bad install.
    """
    key = (value or "").lower()
    for suf in (".l5rcmpack", ".zip"):
        if key.endswith(suf):
            key = key[:-len(suf)]
            break
    # drop a trailing -<version> (e.g. "great_clan_pack-1.6")
    dash = key.rfind("-")
    if dash > 0 and dash + 1 < len(key) and key[dash + 1].isdigit():
        key = key[:dash]
    # peel trailing _pack / _data tokens (community_data_pack -> community)
    changed = True
    while changed:
        changed = False
        for tok in ("_pack", "_data"):
            if key.endswith(tok) and len(key) > len(tok):
                key = key[:-len(tok)]
                changed = True
    return key


def _download_and_import(url, name):
    """Worker body: download the asset to a temp file, import it, and
    clean up. Runs OFF the GUI thread -- it must not reload the store.
    Returns ``(code, pack_id, name)``."""
    path = datapack_catalog.download_to_temp(url)
    try:
        code, pid, _detail = datapacks.import_pack(path)
    finally:
        try:
            os.remove(path)
        except OSError:
            pass
    return (code, pid, name)


class DatapackProxy(QObject):
    """QML bridge for installing / enabling / deleting / downloading
    datapacks."""

    packsChanged = Signal()
    catalogChanged = Signal()
    busyChanged = Signal()
    # (ok, message) -> the MainSheet toast.
    operationFinished = Signal(bool, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._settings = L5RCMSettings()
        self._busy = False
        self._catalog_state = "idle"
        self._catalog_entries = []   # QML records, status already resolved
        self._catalog_worker = None
        self._install_worker = None
        # downloadCore() may need the catalogue first; this remembers to
        # fire the core install once a pending refresh lands.
        self._pending_core = False

    # --- serialisation ------------------------------------------------

    @staticmethod
    def _pack_record(pack):
        authors = pack.authors or []
        return {
            "id": pack.id,
            "displayName": pack.display_name or pack.id,
            "language": pack.language or "",
            "version": pack.version or "",
            "authors": ", ".join(authors),
            "active": bool(pack.active),
            "isCore": pack.id == "core",
        }

    # --- installed packs ----------------------------------------------

    @Property("QVariantList", notify=packsChanged)
    def installedPacks(self):
        packs = list(datapacks.installed())
        # Core first, then by display name -- stable, scannable order.
        packs.sort(key=lambda p: (p.id != "core",
                                   (p.display_name or p.id or "").lower()))
        return [self._pack_record(p) for p in packs]

    @Property(bool, notify=packsChanged)
    def hasPacks(self):
        """True when at least one pack is *loaded* (active). Disabling
        every pack makes the app unusable too, so this keys off active
        packs -- the empty-state nudge then re-fires in that case."""
        return any(p.active for p in datapacks.installed())

    # --- catalogue ----------------------------------------------------

    @Property("QVariantList", notify=catalogChanged)
    def catalogEntries(self):
        return list(self._catalog_entries)

    @Property(str, notify=catalogChanged)
    def catalogState(self):
        return self._catalog_state

    @Property(bool, notify=busyChanged)
    def busy(self):
        return self._busy

    # --- internal helpers ---------------------------------------------

    def _set_busy(self, value):
        value = bool(value)
        if value != self._busy:
            self._busy = value
            self.busyChanged.emit()

    def _set_catalog_state(self, state):
        if state != self._catalog_state:
            self._catalog_state = state
            self.catalogChanged.emit()

    def _reload_and_notify(self):
        """Rebuild the data store and fan a refresh out to the open
        character. MUST run on the GUI thread."""
        api.data.reload()
        api.character.notify_character_refreshed()
        self.packsChanged.emit()

    def _resolve_status(self, raw_entries):
        """Tag each raw catalogue entry with installed/update/available
        and the installed version, matching on the normalised key (see
        _norm_key -- the repo's filenames and manifest ids don't line up)."""
        by_key = {}
        for p in datapacks.installed():
            by_key[_norm_key(p.id)] = p.version or ""
        records = []
        for e in raw_entries:
            installed_ver = by_key.get(_norm_key(e["name"]))
            status = _AVAILABLE
            if installed_ver is not None:
                status = _INSTALLED
                if e["version"] and installed_ver:
                    try:
                        if api.ver_cmp(e["version"], installed_ver) > 0:
                            status = _UPDATE
                    except Exception:
                        pass
            records.append({
                "name": e["name"],
                "version": e["version"],
                "url": e["url"],
                "size": e["size"],
                "status": status,
                "installedVersion": installed_ver or "",
            })
        self._catalog_entries = records

    def _core_entry(self):
        for e in self._catalog_entries:
            if e["name"].lower().startswith("core"):
                return e
        return None

    def _failure_message(self, code, label):
        if code == datapacks.ALREADY_INSTALLED:
            return self.tr("\"{0}\" is already installed (same or newer "
                           "version).").format(label)
        if code == datapacks.CM_VERSION:
            return self.tr("\"{0}\" needs a newer version of L5R: CM.").format(label)
        if code == datapacks.INVALID:
            return self.tr("That file is not a valid datapack.")
        return self.tr("Could not install the datapack.")

    # --- slots: local management (synchronous) ------------------------

    @Slot()
    def installFromFileDialog(self):
        if api.is_android():
            # No native file picker on Android: datapacks are installed by
            # downloading them from the official repo (see the download flow).
            log.app.info(
                u"QML UI: install-from-file unavailable on Android (use download)")
            return
        from qtpy.QtWidgets import QFileDialog  # desktop-only; see module note
        start_dir = self._settings.app.last_open_data_dir or ""
        path, _ = QFileDialog.getOpenFileName(
            None,
            self.tr("Install Datapack"),
            start_dir,
            self.tr("L5R Datapack (*.l5rcmpack *.zip);;All Files (*)"),
        )
        if not path:
            return
        self._settings.app.last_open_data_dir = os.path.dirname(path)
        self._settings.sync()

        label = os.path.basename(path)
        code, _pid, _detail = datapacks.import_pack(path)
        if code == datapacks.OK:
            self._reload_and_notify()
            self._resolve_status(self._raw_from_records())
            self.catalogChanged.emit()
            self.operationFinished.emit(
                True, self.tr("Installed \"{0}\".").format(label))
        else:
            self.operationFinished.emit(False, self._failure_message(code, label))

    @Slot(str, bool)
    def setPackActive(self, pack_id, active):
        if not pack_id:
            return
        blacklist = [x for x in (self._settings.app.data_pack_blacklist or [])]
        if active:
            blacklist = [x for x in blacklist if x != pack_id]
        elif pack_id not in blacklist:
            blacklist.append(pack_id)

        self._settings.app.data_pack_blacklist = blacklist
        self._settings.sync()
        api.data.set_blacklist(blacklist)
        self._reload_and_notify()
        # Catalogue install/update badges depend on the active set.
        self._resolve_status(self._raw_from_records())
        self.catalogChanged.emit()
        self.operationFinished.emit(
            True,
            self.tr("Datapack enabled.") if active
            else self.tr("Datapack disabled."))

    @Slot(str)
    def deletePack(self, pack_id):
        pack = api.data.pack_by_id(pack_id)
        label = (pack.display_name or pack.id) if pack else pack_id
        if datapacks.delete_pack(pack_id):
            self._reload_and_notify()
            self._resolve_status(self._raw_from_records())
            self.catalogChanged.emit()
            self.operationFinished.emit(
                True, self.tr("Removed \"{0}\".").format(label))
        else:
            self.operationFinished.emit(
                False, self.tr("Could not remove \"{0}\".").format(label))

    # --- slots: catalogue + download (async) --------------------------

    @Slot()
    def refreshCatalog(self):
        if self._busy:
            return
        self._set_busy(True)
        self._set_catalog_state("loading")
        worker = Worker(datapack_catalog.fetch_catalog)
        worker.signals.result.connect(self._on_catalog_ok)
        worker.signals.error.connect(self._on_catalog_error)
        self._catalog_worker = worker  # keep alive until it fires
        QThreadPool.globalInstance().start(worker)

    @Slot(str, str)
    def downloadAndInstall(self, name, url):
        if self._busy:
            return
        if not datapack_catalog.host_allowed(url):
            self.operationFinished.emit(
                False,
                self.tr("That download is not from the official repository."))
            return
        self._set_busy(True)
        worker = Worker(_download_and_import, url, name)
        worker.signals.result.connect(self._on_install_ok)
        worker.signals.error.connect(self._on_install_error)
        self._install_worker = worker  # keep alive until it fires
        QThreadPool.globalInstance().start(worker)

    @Slot()
    def downloadCore(self):
        if self._busy:
            return
        entry = self._core_entry()
        if entry:
            self.downloadAndInstall(entry["name"], entry["url"])
            return
        # No catalogue yet -- fetch it, then auto-install Core when it lands.
        self._pending_core = True
        self.refreshCatalog()

    # --- worker result/error slots (run on the GUI thread) ------------

    def _on_catalog_ok(self, raw_entries):
        self._catalog_worker = None
        self._resolve_status(raw_entries)
        self._set_busy(False)
        self._catalog_state = "ready"
        self.catalogChanged.emit()
        if self._pending_core:
            self._pending_core = False
            entry = self._core_entry()
            if entry:
                self.downloadAndInstall(entry["name"], entry["url"])
            else:
                self.operationFinished.emit(
                    False, self.tr("The Core datapack is not available right now."))

    def _on_catalog_error(self, err):
        self._catalog_worker = None
        self._pending_core = False
        self._set_busy(False)
        state, msg = self._classify_network_error(err)
        self._catalog_state = state
        self.catalogChanged.emit()
        self.operationFinished.emit(False, msg)

    def _on_install_ok(self, result):
        self._install_worker = None
        code, _pid, name = result
        self._set_busy(False)
        if code == datapacks.OK:
            self._reload_and_notify()
            self._resolve_status(self._raw_from_records())
            self.catalogChanged.emit()
            self.operationFinished.emit(
                True, self.tr("Installed \"{0}\".").format(name))
        else:
            self.operationFinished.emit(False, self._failure_message(code, name))

    def _on_install_error(self, err):
        self._install_worker = None
        self._set_busy(False)
        _state, msg = self._classify_network_error(err)
        self.operationFinished.emit(False, msg)

    def _classify_network_error(self, err):
        """Map a Worker error tuple (exctype, value, tb) to a
        (catalogState, message) pair."""
        exctype = err[0] if err else None
        if exctype is not None and issubclass(exctype, datapack_catalog.RateLimitError):
            return ("ratelimited",
                    self.tr("GitHub is rate-limiting requests right now. "
                            "Please try again later."))
        if exctype is not None and issubclass(exctype, datapack_catalog.OfflineError):
            return ("offline",
                    self.tr("Couldn't reach the datapack repository. "
                            "Check your connection."))
        return ("error", self.tr("Couldn't load the datapack list."))

    def _raw_from_records(self):
        """Re-derive the raw {name,version,url,size} list from the cached
        records so a status recompute (after install/toggle/delete) doesn't
        need another network round-trip."""
        return [{"name": e["name"], "version": e["version"],
                 "url": e["url"], "size": e["size"]}
                for e in self._catalog_entries]
