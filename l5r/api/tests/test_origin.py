# -*- coding: utf-8 -*-
"""Origin-selection rules (issue #448).

The character's clan/family/school grant the starting trait bonuses, so the
origin must be locked in *before* any XP is spent -- otherwise a player could
buy a trait cheaply and then collect the bonus on top. These tests pin the
API contract that enforces it:

  - no advancement may be purchased until the origin (family + school) is
    complete (CMErrors.MISSING_ORIGIN);
  - the origin stays editable until the first *paid* advancement (gated on
    spent XP, not the advancement count, so picking the school -- which
    appends a cost-0 rank-1 advancement -- doesn't lock out the family);
  - set_origin replaces a previous origin atomically and refuses once frozen;
  - clear_origin resets to the freshly-created baseline while preserving the
    identity the player typed;
  - a school-less character is never offered (and never crashes on) a rank-up.
"""
__author__ = 'Daniele Simonetti'

import contextlib
import unittest

import l5r.api as api
import l5r.api.character
import l5r.api.character.rankadv
import l5r.api.character.schools
import l5r.api.character.skills
import l5r.api.data
from l5r.api.context import L5RCMContext, use

import l5rdal as dal
from l5rdal.school import School, SchoolKiho, SchoolTattoo

from l5r.tests.fakedata import *


def _make_school(sid, clanid):
    s = School()
    s.id = sid
    s.name = sid
    s.clanid = clanid
    s.trait = 'willpower'
    s.affinity = None
    s.deficiency = None
    s.honor = 0.0
    s.kihos = SchoolKiho()
    s.tattoos = SchoolTattoo()
    s.tags = []
    s.skills = []
    s.skills_pc = []
    s.techs = []
    s.spells = []
    s.spells_pc = []
    s.outfit = []
    s.money = [0, 0, 0]
    s.require = []
    s.perks = []
    return s


class TestOrigin(unittest.TestCase):

    def setUp(self):
        self._stack = contextlib.ExitStack()
        self.addCleanup(self._stack.close)
        self._stack.enter_context(use(L5RCMContext()))

        data_ = dal.Data([], [])
        api.data.set_model(data_)
        data_.clans.append(test_clan_1)
        data_.clans.append(test_clan_2)
        data_.families.append(test_family_1)
        data_.families.append(test_family_2)
        # a second school (clan_2) for the replace-origin tests
        self.school_2 = _make_school('test_school_2', 'test_clan_2')
        data_.schools.append(test_school_1)
        data_.schools.append(self.school_2)
        data_.skcategs.append(test_skill_categ_1)
        data_.skills.append(test_skill_1)

        api.character.new()
        api.character.model().exp_limit = 100

    # --- can_buy_advancements ----------------------------------------

    def test_cannot_buy_without_origin(self):
        self.assertFalse(api.character.can_buy_advancements())
        self.assertEqual(
            api.data.CMErrors.MISSING_ORIGIN,
            api.character.skills.purchase_skill_rank('test_skill_1'))
        self.assertEqual([], api.character.model().advans)

    def test_cannot_buy_with_only_family(self):
        api.character.set_family('test_family_1')
        self.assertFalse(api.character.can_buy_advancements())

    def test_cannot_buy_with_only_school(self):
        api.character.schools.set_first('test_school_1')
        self.assertFalse(api.character.can_buy_advancements())
        self.assertEqual(
            api.data.CMErrors.MISSING_ORIGIN,
            api.character.skills.purchase_skill_rank('test_skill_1'))

    def test_can_buy_once_origin_complete(self):
        api.character.set_family('test_family_1')
        api.character.schools.set_first('test_school_1')
        self.assertTrue(api.character.can_buy_advancements())
        self.assertEqual(
            api.data.CMErrors.NO_ERROR,
            api.character.skills.purchase_skill_rank('test_skill_1'))

    # --- can_edit_origin (xp()==0, not len(advans)==0) ----------------

    def test_edit_origin_open_after_school_chosen(self):
        """Choosing the school appends the cost-0 rank-1 advancement, but the
        origin must stay editable (the bug was locking on advancement count)."""
        api.character.schools.set_first('test_school_1')
        self.assertTrue(len(api.character.model().advans) > 0)
        self.assertTrue(api.character.can_edit_origin())

    def test_edit_origin_freezes_after_paid_advancement(self):
        api.character.set_family('test_family_1')
        api.character.schools.set_first('test_school_1')
        self.assertTrue(api.character.can_edit_origin())
        api.character.skills.purchase_skill_rank('test_skill_1')
        self.assertFalse(api.character.can_edit_origin())

    # --- set_origin / clear_origin ------------------------------------

    def test_set_origin_sets_family_and_school(self):
        self.assertTrue(api.character.set_origin('test_family_1',
                                                 'test_school_1'))
        self.assertEqual('test_family_1', api.character.get_family())
        self.assertEqual('test_clan_1', api.character.get_clan())
        self.assertEqual('test_school_1', api.character.schools.get_first())
        # exactly one rank advancement (the rank-1)
        self.assertEqual(1, len(api.character.rankadv.get_all()))

    def test_set_origin_replaces_previous_atomically(self):
        api.character.set_origin('test_family_1', 'test_school_1')
        api.character.set_origin('test_family_2', 'test_school_2')
        self.assertEqual('test_family_2', api.character.get_family())
        self.assertEqual('test_school_2', api.character.schools.get_first())
        # no leftover rank advancement from the first origin
        self.assertEqual(1, len(api.character.rankadv.get_all()))

    def test_set_origin_refused_after_xp_spent(self):
        api.character.set_origin('test_family_1', 'test_school_1')
        api.character.skills.purchase_skill_rank('test_skill_1')
        self.assertFalse(api.character.set_origin('test_family_2',
                                                  'test_school_2'))
        # unchanged
        self.assertEqual('test_family_1', api.character.get_family())
        self.assertEqual('test_school_1', api.character.schools.get_first())

    def test_set_first_is_idempotent(self):
        """Re-selecting the first school replaces it -- no second rank-1."""
        api.character.schools.set_first('test_school_1')
        api.character.schools.set_first('test_school_1')
        self.assertEqual(1, len(api.character.rankadv.get_all()))

    def test_clear_origin_preserves_identity(self):
        pc = api.character.model()
        api.character.set_name('Hida Kisada')
        api.character.set_notes('a stout defender')
        pc.exp_limit = 175
        api.character.set_origin('test_family_1', 'test_school_1')

        api.character.clear_origin()

        # origin gone
        self.assertIsNone(api.character.get_family())
        self.assertIsNone(pc.clan)
        self.assertEqual([], pc.advans)
        self.assertEqual(0.0, pc.honor)
        # identity preserved
        self.assertEqual('Hida Kisada', pc.name)
        self.assertEqual('a stout defender', pc.extra_notes)
        self.assertEqual(175, pc.exp_limit)

    # --- school-less rank-up: no crash --------------------------------

    def test_advance_rank_refuses_without_school(self):
        self.assertFalse(api.character.rankadv.advance_rank())
        self.assertEqual([], api.character.rankadv.get_all())


if __name__ == '__main__':
    unittest.main()
