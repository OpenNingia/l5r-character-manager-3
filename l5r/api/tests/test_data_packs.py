# -*- coding: utf-8 -*-
# Tests for l5r.api.data.datapacks (install / delete of datapacks).
__author__ = 'Daniele Simonetti'

import contextlib
import json
import os
import tempfile
import unittest
import zipfile
from unittest import mock

import l5rdal as dal

import l5r.api as api
import l5r.api.data
import l5r.api.data.datapacks as dp
from l5r.api.context import L5RCMContext, use


def _make_pack(archive_path, pack_id, version="1.0", language=None,
               min_cm_version=None):
    """Build a minimal .l5rcmpack: a root ``manifest`` + one empty data
    file, exactly the shape l5rdal.dataimport.DataPack expects."""
    manifest = {"id": pack_id, "version": version}
    if language:
        manifest["language"] = language
    if min_cm_version:
        manifest["min-cm-version"] = min_cm_version
    with zipfile.ZipFile(archive_path, "w") as z:
        z.writestr("manifest", json.dumps(manifest))
        z.writestr("data.xml", "<L5RCM></L5RCM>")


class _FakePack(object):
    """Stand-in DataManifest for the path-traversal guard test."""
    def __init__(self, pack_id, path):
        self.id = pack_id
        self.path = path


class TestDataPacks(unittest.TestCase):

    def setUp(self):
        # Isolated context + a throwaway user-data dir, so nothing touches
        # the real %APPDATA% install or the production singleton.
        self._stack = contextlib.ExitStack()
        self.addCleanup(self._stack.close)
        self._stack.enter_context(use(L5RCMContext()))

        self.tmp = tempfile.mkdtemp(prefix="l5rcm_packs_")
        self.addCleanup(lambda: _rmtree(self.tmp))

        def fake_user_data_path(rel=None):
            return os.path.join(self.tmp, rel) if rel else self.tmp

        self._stack.enter_context(
            mock.patch("l5r.api.get_user_data_path", new=fake_user_data_path))

        # Empty store to begin with.
        api.data.set_model(dal.Data([], []))

    def _rebuild_store(self, blacklist=None):
        """Rebuild the data store from the temp install dirs and make it
        the active model (test contexts can't use the no-arg
        api.data.reload, which the production partial supplies)."""
        locations = [os.path.join(self.tmp, "core.data"),
                     os.path.join(self.tmp, "data")]
        api.data.set_model(dal.Data(locations, blacklist or []))

    # --- import_pack --------------------------------------------------

    def test_import_core_ok(self):
        archive = os.path.join(self.tmp, "core_pack-1.0.l5rcmpack")
        _make_pack(archive, "core", "1.0")

        code, pid, _detail = dp.import_pack(archive)
        self.assertEqual(dp.OK, code)
        self.assertEqual("core", pid)
        # core routes to core.data/<id>/manifest
        self.assertTrue(os.path.isfile(
            os.path.join(self.tmp, "core.data", "core", "manifest")))

        self._rebuild_store()
        self.assertIsNotNone(api.data.pack_by_id("core"))

    def test_import_language_pack_routes_to_data_locale(self):
        archive = os.path.join(self.tmp, "fr.l5rcmpack")
        _make_pack(archive, "fr_pack", "1.0", language="fr_FR")

        code, pid, _detail = dp.import_pack(archive)
        self.assertEqual(dp.OK, code)
        self.assertTrue(os.path.isdir(
            os.path.join(self.tmp, "data.fr_FR", "fr_pack")))

    def test_import_invalid_archive(self):
        bogus = os.path.join(self.tmp, "not_a_pack.l5rcmpack")
        with open(bogus, "wb") as fp:
            fp.write(b"this is not a zip")
        code, pid, _detail = dp.import_pack(bogus)
        self.assertEqual(dp.INVALID, code)
        self.assertIsNone(pid)

    def test_import_missing_manifest(self):
        archive = os.path.join(self.tmp, "no_manifest.l5rcmpack")
        with zipfile.ZipFile(archive, "w") as z:
            z.writestr("data.xml", "<L5RCM></L5RCM>")
        code, _pid, _detail = dp.import_pack(archive)
        self.assertEqual(dp.INVALID, code)

    def test_import_cm_version_too_new(self):
        archive = os.path.join(self.tmp, "future.l5rcmpack")
        _make_pack(archive, "future", "1.0", min_cm_version="999.0")
        code, pid, _detail = dp.import_pack(archive)
        self.assertEqual(dp.CM_VERSION, code)
        self.assertEqual("future", pid)

    def test_reimport_is_idempotent(self):
        archive = os.path.join(self.tmp, "core.l5rcmpack")
        _make_pack(archive, "core", "1.0")
        self.assertEqual(dp.OK, dp.import_pack(archive)[0])
        # Real packs carry the manifest at the zip root (no nested id
        # folder), so a re-import just overwrites and reports OK.
        self.assertEqual(dp.OK, dp.import_pack(archive)[0])

    # --- delete_pack --------------------------------------------------

    def test_delete_removes_files(self):
        archive = os.path.join(self.tmp, "great.l5rcmpack")
        _make_pack(archive, "great_clan", "1.0")
        self.assertEqual(dp.OK, dp.import_pack(archive)[0])
        self._rebuild_store()

        pack = api.data.pack_by_id("great_clan")
        self.assertIsNotNone(pack)
        path = pack.path
        self.assertTrue(os.path.isdir(path))

        self.assertTrue(dp.delete_pack("great_clan"))
        self.assertFalse(os.path.exists(path))

    def test_delete_unknown_pack(self):
        self._rebuild_store()
        self.assertFalse(dp.delete_pack("does_not_exist"))

    def test_delete_refuses_path_outside_data_dir(self):
        # A pack whose .path escapes the user data dir must never be
        # rmtree'd (path-traversal guard).
        outside = tempfile.mkdtemp(prefix="l5rcm_outside_")
        self.addCleanup(lambda: _rmtree(outside))
        store = dal.Data([], [])
        store.packs.append(_FakePack("evil", outside))
        api.data.set_model(store)

        self.assertFalse(dp.delete_pack("evil"))
        self.assertTrue(os.path.isdir(outside))  # untouched


def _rmtree(path):
    import shutil
    shutil.rmtree(path, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
