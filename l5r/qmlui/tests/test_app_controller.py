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
