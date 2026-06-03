# -*- coding: utf-8 -*-
"""Tests for the QML autosave / crash-recovery session store.

Covers the contract between l5r.util.session (the UI-agnostic recovery
file + pointer storage) and the AppController policy that drives it:

  * a debounced autosave mirrors the working character to the recovery
    file WITHOUT committing it to the real .l5r (the dirty flag survives);
  * an explicit Save / Open cleans the recovery snapshot and records the
    real path so the next launch reopens it;
  * File > New is gated on unsaved changes (it discards the recovery
    file) and clears the session store when it proceeds;
  * restore_session resumes the last working character -- the unsaved
    recovery snapshot when dirty, otherwise the .l5r last open.
"""
__author__ = 'Daniele Simonetti'

import contextlib
import os
import tempfile
import unittest
from unittest import mock

import l5r.api as api
import l5r.api.character
import l5r.models
from l5r.api.context import L5RCMContext, use
from l5r.util import osutil, session

from l5r.qmlui.proxies.app_controller import AppController


def setUpModule():
    # AppController is a QObject (signals + a QTimer); both need a running
    # QApplication. CI runs headless with QT_QPA_PLATFORM=offscreen.
    from qtpy.QtWidgets import QApplication
    global _app
    _app = QApplication.instance() or QApplication([])


class _AutosaveTestBase(unittest.TestCase):

    def setUp(self):
        self._stack = contextlib.ExitStack()
        self.addCleanup(self._stack.close)
        # Fresh, isolated api context per test (see test_app_controller).
        self._stack.enter_context(use(L5RCMContext()))

        # Redirect the session store into a throwaway dir so reads/writes
        # never touch the real user config. session.* resolves paths
        # through osutil.get_user_data_path at call time, so patching it
        # here covers recovery_path() and the pointer alike.
        self._cfg = tempfile.mkdtemp(prefix="l5rcm-autosave-")
        self.addCleanup(self._rmtree, self._cfg)
        self._stack.enter_context(mock.patch.object(
            osutil, "get_user_data_path",
            side_effect=lambda rel="": os.path.join(self._cfg, rel)))

        api.character.new()
        api.character.set_dirty_flag(False)
        self.ctrl = AppController()

    @staticmethod
    def _rmtree(path):
        import shutil
        shutil.rmtree(path, ignore_errors=True)

    def _tmp_l5r(self):
        path = os.path.join(self._cfg, "hero.l5r")
        self.addCleanup(lambda: os.path.exists(path) and os.remove(path))
        return path


class TestAutosaveFlush(_AutosaveTestBase):

    def test_flush_writes_recovery_and_pointer_without_clearing_dirty(self):
        api.character.set_name("Hida Test")
        self.assertTrue(api.character.model().unsaved)

        self.ctrl._flush_autosave()

        # recovery snapshot exists; pointer says "unsaved, no real path".
        self.assertTrue(os.path.exists(session.recovery_path()))
        ptr = session.read_pointer()
        self.assertEqual({"path": "", "dirty": True}, ptr)
        # autosave must NOT clear the dirty flag: the work is recovered,
        # not committed to a real .l5r.
        self.assertTrue(api.character.model().unsaved)

    def test_flush_is_noop_when_clean(self):
        # clean model -> nothing to recover
        self.ctrl._flush_autosave()
        self.assertFalse(os.path.exists(session.recovery_path()))
        self.assertIsNone(session.read_pointer())

    def test_dirty_change_starts_debounce_timer(self):
        self.assertFalse(self.ctrl._autosave_timer.isActive())
        api.character.set_name("Doji Test")
        self.assertTrue(self.ctrl._autosave_timer.isActive())
        # going clean stops it again
        api.character.set_dirty_flag(False)
        self.assertFalse(self.ctrl._autosave_timer.isActive())


class TestExplicitSaveCleansSession(_AutosaveTestBase):

    def test_save_removes_recovery_and_marks_clean(self):
        api.character.set_name("Akodo Test")
        # simulate a prior autosave snapshot
        self.ctrl._flush_autosave()
        self.assertTrue(os.path.exists(session.recovery_path()))

        path = self._tmp_l5r()
        self.ctrl._save(path)

        self.assertTrue(os.path.exists(path), "real .l5r was not written")
        self.assertFalse(os.path.exists(session.recovery_path()),
                         "stale recovery snapshot not dropped after Save")
        self.assertEqual({"path": path, "dirty": False},
                         session.read_pointer())
        self.assertFalse(api.character.model().unsaved)
        self.assertEqual(path, self.ctrl._save_path)


class TestDiscardChangesGate(_AutosaveTestBase):
    """File > New and File > Open are destructive (they discard the
    recovery snapshot), so a dirty model must confirm first."""

    def setUp(self):
        super().setUp()
        self._confirm = []
        self.ctrl.confirmDiscardChanges.connect(
            lambda action: self._confirm.append(action))

    def test_dirty_new_asks_for_confirmation_and_keeps_model(self):
        api.character.set_name("Bayushi Test")

        self.ctrl.requestFileNew()

        self.assertEqual(["new"], self._confirm,
                         "dirty New must request confirmation")
        # fileNew must NOT have run: the work is untouched.
        self.assertEqual("Bayushi Test", api.character.model().name)
        self.assertTrue(api.character.model().unsaved)

    def test_dirty_open_asks_for_confirmation_and_keeps_model(self):
        api.character.set_name("Ide Test")

        self.ctrl.requestFileOpen()

        self.assertEqual(["open"], self._confirm,
                         "dirty Open must request confirmation")
        self.assertEqual("Ide Test", api.character.model().name)
        self.assertTrue(api.character.model().unsaved)

    def test_clean_new_proceeds_without_confirmation(self):
        self.assertFalse(api.character.model().unsaved)

        self.ctrl.requestFileNew()

        self.assertEqual([], self._confirm, "clean New must not prompt")
        # the session store is reset to a fresh, clean pointer.
        self.assertEqual({"path": "", "dirty": False},
                         session.read_pointer())

    def test_clean_open_proceeds_to_picker_without_confirmation(self):
        self.assertFalse(api.character.model().unsaved)

        # stub the native file dialog so the clean path runs headless and
        # the user "cancels" (no selection) -- we only assert that no
        # confirmation was raised and the picker was reached.
        from l5r.qmlui.proxies import app_controller as ac
        with mock.patch.object(ac.QFileDialog, "getOpenFileName",
                               return_value=("", "")) as picker:
            self.ctrl.requestFileOpen()

        self.assertEqual([], self._confirm, "clean Open must not prompt")
        picker.assert_called_once()

    def test_filenew_clears_recovery_and_resets_pointer(self):
        # leave a stale recovery snapshot behind, then run New
        api.character.set_name("Shosuro Test")
        self.ctrl._flush_autosave()
        self.assertTrue(os.path.exists(session.recovery_path()))

        self.ctrl.fileNew()

        self.assertFalse(os.path.exists(session.recovery_path()),
                         "File > New must discard the recovery snapshot")
        self.assertEqual({"path": "", "dirty": False},
                         session.read_pointer())
        self.assertEqual("", self.ctrl._save_path)


class TestRestoreSession(_AutosaveTestBase):

    def test_no_pointer_returns_false(self):
        self.assertIsNone(session.read_pointer())
        self.assertFalse(self.ctrl.restore_session())

    def test_restore_unsaved_recovery_snapshot(self):
        # author an unsaved working character and autosave it
        api.character.set_name("Moto Test")
        session.write_recovery(api.character.model(), "C:/some/hero.l5r",
                               dirty=True)

        # fresh context + controller simulate a relaunch
        with use(L5RCMContext()):
            api.character.new()
            ctrl = AppController()
            self.assertTrue(ctrl.restore_session())
            self.assertEqual("Moto Test", api.character.model().name)
            self.assertEqual("C:/some/hero.l5r", ctrl._save_path)
            # not yet committed to the real .l5r -> still dirty
            self.assertTrue(api.character.model().unsaved)

    def test_restore_reopens_clean_saved_character(self):
        # a saved character: real .l5r on disk, clean pointer, no recovery
        path = self._tmp_l5r()
        api.character.set_name("Kuni Test")
        api.character.model().save_to(path)          # writes + clears dirty
        session.remove_recovery()
        session.write_pointer(path, dirty=False)

        with use(L5RCMContext()):
            api.character.new()
            ctrl = AppController()
            self.assertTrue(ctrl.restore_session())
            self.assertEqual("Kuni Test", api.character.model().name)
            self.assertEqual(path, ctrl._save_path)
            self.assertFalse(api.character.model().unsaved)

    def test_restore_clean_pointer_missing_file_falls_back(self):
        session.write_pointer("C:/gone/missing.l5r", dirty=False)
        self.assertFalse(self.ctrl.restore_session())


if __name__ == "__main__":
    unittest.main()
