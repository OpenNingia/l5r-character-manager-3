# -*- coding: utf-8 -*-
"""Controller-level tests for the QML AppController rank-advancement gate.

Regression coverage for the bug where advancing Insight Rank silently
discarded a pending opportunity (originally the school's 'choose skills').
The choice getters read only the last rank advancement, and advance_rank()
appended a fresh empty Rank that became the new last one, orphaning the
grants. The fix blocks the rank-up while any *surfaced* opportunity is
unresolved (a reminder toast on the outer 'Advance Rank' button), driven by
the same _SURFACED_OPPORTUNITIES allow-list that powers the badges -- so it
scales as flows are ported and never dead-locks on a grant with no QML CTA.
"""
__author__ = 'Daniele Simonetti'

import contextlib
import unittest
from unittest import mock

import l5r.api as api
import l5r.api.character
import l5r.api.character.rankadv
import l5r.api.character.schools
import l5r.api.character.skills
import l5r.api.character.spells
import l5r.api.data
from l5r.api.context import L5RCMContext, use

import l5rdal as dal
from l5rdal.school import SchoolSkillWildcardSet

from l5r.tests.fakedata import *

from l5r.qmlui.proxies.app_controller import AppController


def setUpModule():
    # AppController is a QObject; signal emission needs an application
    # instance. CI runs headless with QT_QPA_PLATFORM=offscreen.
    from qtpy.QtWidgets import QApplication
    global _app
    _app = QApplication.instance() or QApplication([])


class TestAdvanceRankGuard(unittest.TestCase):

    def setUp(self):
        # fresh, isolated context per test (see api.tests.test_character)
        self._stack = contextlib.ExitStack()
        self.addCleanup(self._stack.close)
        self._stack.enter_context(use(L5RCMContext()))

        data_ = dal.Data([], [])
        api.data.set_model(data_)
        data_.clans.append(test_clan_1)
        data_.families.append(test_family_1)
        data_.schools.append(test_school_1)
        data_.skcategs.append(test_skill_categ_1)
        data_.skills.append(test_skill_1)

        api.character.new()

        # the first school offers a wildcard skill choice -> this seeds
        # skills_to_choose on the rank-1 advancement (the opportunity)
        wildcard_set = SchoolSkillWildcardSet()
        wildcard_set.rank = 1
        test_school_1.skills_pc = [wildcard_set]
        # test_school_1 is a shared module-level fixture: restore it
        self.addCleanup(setattr, test_school_1, 'skills_pc', [])
        api.character.schools.set_first('test_school_1')

        self.ctrl = AppController()
        self._blocked = []
        self._ready = []
        self.ctrl.advanceRankBlocked.connect(
            lambda: self._blocked.append(True))
        self.ctrl.advanceRankReady.connect(
            lambda: self._ready.append(True))

    def _simulate_pending_rank_up(self):
        """Report a pending rank-up (potential rank 2 vs taken rank 1) so
        advanceRank clears its insight gate and reaches the opportunity
        guard, without hand-tuning traits/skills to cross insight 150."""
        def fake_insight_rank(strict=False):
            return 1 if strict else 2
        self._stack.enter_context(
            mock.patch.object(api.character, 'insight_rank',
                              fake_insight_rank))

    # --- outer 'Advance Rank' button (requestAdvanceRank) -------------

    def test_request_blocked_while_school_skills_pending(self):
        """The outer button must NOT open the dialog while school skills are
        unresolved: it emits advanceRankBlocked (toast), not advanceRankReady."""
        self.assertTrue(api.character.rankadv.has_granted_skills_to_choose())

        self.ctrl.requestAdvanceRank()

        self.assertEqual([True], self._blocked)
        self.assertEqual([], self._ready, "dialog would have opened")

    def test_request_ready_once_choices_resolved(self):
        """Once nothing is pending, the outer button signals the view to open
        the dialog (advanceRankReady) and does not block."""
        api.character.rankadv.clear_skills_to_choose()
        self.assertFalse(api.character.rankadv.has_granted_skills_to_choose())

        self.ctrl.requestAdvanceRank()

        self.assertEqual([True], self._ready)
        self.assertEqual([], self._blocked)

    def test_request_blocked_by_free_kiho_not_only_skills(self):
        """Scalability: the gate is not skills-only. A *different* surfaced
        opportunity (free kiho) blocks the rank-up just the same."""
        api.character.rankadv.clear_skills_to_choose()
        api.character.rankadv.set_gained_kiho_count(2)  # rank-granted free kiho
        self.assertFalse(api.character.rankadv.has_granted_skills_to_choose())

        self.ctrl.requestAdvanceRank()

        self.assertEqual([True], self._blocked)
        self.assertEqual([], self._ready)

    def test_request_blocked_by_pending_affinity(self):
        """The shugenja elemental-affinity choice now surfaces on the Spells
        section, so an unresolved one blocks the rank-up like any other."""
        api.character.rankadv.clear_skills_to_choose()
        api.character.rankadv.get_last().affinities_to_choose = ['nonvoid']

        self.ctrl.requestAdvanceRank()

        self.assertEqual([True], self._blocked)
        self.assertEqual([], self._ready)

    def test_choose_affinity_resolves_the_block(self):
        """chooseAffinity commits the ring and clears the pending choice, so
        the rank-up is no longer blocked afterwards."""
        api.character.rankadv.clear_skills_to_choose()
        rank_ = api.character.rankadv.get_last()
        rank_.affinities_to_choose = ['nonvoid']

        self.ctrl.chooseAffinity('fire')

        self.assertEqual([], rank_.affinities_to_choose)
        self.assertIn('fire', api.character.spells.affinities())

        self.ctrl.requestAdvanceRank()
        self.assertEqual([True], self._ready)
        self.assertEqual([], self._blocked)

    # --- dialog accept (advanceRank), defence in depth ----------------

    def test_advance_refuses_while_opportunities_pending(self):
        """Even if the dialog is somehow reached, advanceRank must refuse and
        append no new rank while an opportunity is unresolved."""
        self._simulate_pending_rank_up()
        ranks_before = len(api.character.rankadv.get_all())

        self.ctrl.advanceRank()

        self.assertEqual([True], self._blocked)
        self.assertEqual(
            ranks_before, len(api.character.rankadv.get_all()),
            "advancement happened despite a pending opportunity")

    def test_advance_proceeds_once_resolved(self):
        """After the opportunities are resolved, advanceRank advances normally
        and does not block."""
        self._simulate_pending_rank_up()
        api.character.rankadv.clear_skills_to_choose()
        ranks_before = len(api.character.rankadv.get_all())

        self.ctrl.advanceRank()

        self.assertEqual([], self._blocked, "advancement was wrongly blocked")
        self.assertEqual(
            ranks_before + 1, len(api.character.rankadv.get_all()),
            "advancement did not happen after resolving the choices")


class TestControllerActions(unittest.TestCase):
    """resetAdvancements slot, the File>Open missing-datapack gate, and the
    session-only Free Shopping toggle."""

    def setUp(self):
        self._stack = contextlib.ExitStack()
        self.addCleanup(self._stack.close)
        self._stack.enter_context(use(L5RCMContext()))

        data_ = dal.Data([], [])
        api.data.set_model(data_)
        data_.clans.append(test_clan_1)
        data_.families.append(test_family_1)
        data_.schools.append(test_school_1)
        data_.skcategs.append(test_skill_categ_1)
        data_.skills.append(test_skill_1)

        api.character.new()
        self.ctrl = AppController()

    # --- reset advancements ------------------------------------------

    def test_reset_advancements_clears_stack(self):
        """The slot delegates to api.character.reset_advancements: the
        chronicle is emptied and the model is left dirty."""
        import l5r.models.advances
        pc = api.character.model()
        pc.add_advancement(l5r.models.advances.AttribAdv('strength', 4))
        self.assertEqual(1, len(pc.advans))

        self.ctrl.resetAdvancements()

        self.assertEqual([], pc.advans)
        self.assertTrue(pc.unsaved)

    # --- File > Open missing-datapack gate ---------------------------

    def test_file_open_refused_on_missing_books(self):
        """A character whose referenced datapack is not loaded must NOT be
        opened: the controller emits loadFailedMissingBooks and leaves the
        working character untouched (never calls set_model)."""
        import l5r.models
        before = api.character.model()

        def fake_load(self_pc, path):
            self_pc.pack_refs = [
                {'id': 'ghost', 'name': 'Ghost Tome', 'version': '1.0'}]
            return True

        self._stack.enter_context(
            mock.patch.object(l5r.models.AdvancedPcModel, 'load_from',
                              fake_load))
        fired = []
        self.ctrl.loadFailedMissingBooks.connect(
            lambda books, path: fired.append((books, path)))

        self.ctrl.fileOpen('whatever.l5r')

        self.assertEqual(1, len(fired), "missing-books signal not emitted")
        books, path = fired[0]
        self.assertEqual('whatever.l5r', path)
        self.assertEqual(1, len(books))
        self.assertIs(before, api.character.model(),
                      "active model was swapped despite missing books")

    # --- Free Shopping (SettingsProxy, session-only) -----------------

    def test_buy_for_free_toggle(self):
        """setBuyForFree flips the global Advancement flag and the property
        reflects it; it is session-only, so the test resets it on teardown."""
        import l5r.models
        from l5r.qmlui.proxies.settings_proxy import SettingsProxy
        self.addCleanup(l5r.models.Advancement.set_buy_for_free, False)

        proxy = SettingsProxy()
        self.assertFalse(proxy.buyForFree)

        proxy.setBuyForFree(True)
        self.assertTrue(proxy.buyForFree)
        self.assertTrue(l5r.models.Advancement.get_buy_for_free())

        proxy.setBuyForFree(False)
        self.assertFalse(l5r.models.Advancement.get_buy_for_free())


class TestOriginController(unittest.TestCase):
    """Controller-level guards for the origin flow (issue #448): the QML
    advanceRank slot must never crash on a school-less character, canEditOrigin
    tracks spent XP (not the advancement count), and a blocked purchase emits a
    notice toast instead of bubbling a QMessageBox."""

    def setUp(self):
        self._stack = contextlib.ExitStack()
        self.addCleanup(self._stack.close)
        self._stack.enter_context(use(L5RCMContext()))

        data_ = dal.Data([], [])
        api.data.set_model(data_)
        data_.clans.append(test_clan_1)
        data_.families.append(test_family_1)
        data_.schools.append(test_school_1)
        data_.skcategs.append(test_skill_categ_1)
        data_.skills.append(test_skill_1)

        api.character.new()
        api.character.model().exp_limit = 100
        self.ctrl = AppController()

    def test_advanceRank_slot_noop_without_school(self):
        """The original #448 crash: a rank-up offered on a school-less PC.
        The slot must not raise and must append no rank."""
        def fake_insight_rank(strict=False):
            return 1 if strict else 2
        self._stack.enter_context(
            mock.patch.object(api.character, 'insight_rank',
                              fake_insight_rank))

        self.ctrl.advanceRank()  # must not raise

        self.assertEqual([], api.character.rankadv.get_all())

    def test_canEditOrigin_tracks_spent_xp(self):
        self.assertTrue(self.ctrl.canEditOrigin())
        api.character.set_family('test_family_1')
        api.character.schools.set_first('test_school_1')
        self.assertTrue(self.ctrl.canEditOrigin(),
                        "school chosen but no XP spent -> still editable")
        api.character.skills.purchase_skill_rank('test_skill_1')
        self.assertFalse(self.ctrl.canEditOrigin())

    def test_blocked_purchase_emits_notice(self):
        notices = []
        self.ctrl.notice.connect(lambda m: notices.append(m))
        # no origin yet -> buying a skill is refused with a notice toast
        self.ctrl.buySkillRank('test_skill_1')
        self.assertEqual(1, len(notices))
        self.assertEqual([], api.character.model().advans)

    def test_setOrigin_slot_commits_family_and_school(self):
        """The unified OriginSelectionDialog entry point (#451)."""
        self.ctrl.setOrigin('test_family_1', 'test_school_1', '')
        self.assertEqual('test_family_1', api.character.get_family())
        self.assertEqual('test_school_1', api.character.schools.get_first())
        self.assertEqual(1, len(api.character.rankadv.get_all()))

    def test_inscribePerk_before_origin_is_refused_with_notice(self):
        """Merits/flaws must not be recorded before the origin is chosen --
        this path appends directly (bypassing purchase_advancement's gate), so
        it must enforce the same rule and nudge with a toast (#448/#450)."""
        notices = []
        self.ctrl.notice.connect(lambda m: notices.append(m))
        self.ctrl.inscribePerk('merit', 'test_merit_1', 1, '', -1)
        self.assertEqual(1, len(notices))
        self.assertEqual([], api.character.model().advans)
