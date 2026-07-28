# -*- coding: utf-8 -*-
# Regression tests for issue #282: the Topaz Champion path (and, more
# generally, "join at any rank" rank-0 alternate paths).
#
# Two behaviours are covered:
#   1. A rank-0 alternate path grants its OWN technique -- broken since
#      commit 22b28a1 whose ``school_rank or rank`` fallback turned the
#      path's legitimate school_rank==0 into the insight rank, so a rank-0
#      tech never matched (all the Imperial champion/magistrate/legionnaire
#      paths were affected).
#   2. A path tagged ``keep_replaced_tech`` (the Topaz Champion) ALSO grants
#      the technique the replaced school would have provided at that rank --
#      "you gain the Technique it would normally replace".
__author__ = 'Daniele Simonetti'

import contextlib
import unittest

import l5rdal as dal
import l5r.api as api
import l5r.api.character
import l5r.api.character.rankadv
import l5r.api.character.schools
import l5r.api.data
from l5r.api.context import L5RCMContext, use

from l5rdal.school import School, SchoolKiho, SchoolTattoo, SchoolTech
from l5rdal.clan import Clan
from l5rdal.family import Family


def _tech(tid, rank):
    t = SchoolTech()
    t.id = tid
    t.rank = rank
    return t


def _school(sid, techs, tags):
    s = School()
    s.id = sid
    s.name = sid
    s.clanid = 'test_clan'
    s.trait = 'willpower'
    s.affinity = None
    s.deficiency = None
    s.honor = 0.0
    s.kihos = SchoolKiho()
    s.tattoos = SchoolTattoo()
    s.tags = list(tags)
    s.skills = []
    s.skills_pc = []
    s.techs = techs
    s.spells = []
    s.spells_pc = []
    s.outfit = []
    s.money = [0] * 3
    s.require = []
    s.perks = []
    return s


class TestTopazPath(unittest.TestCase):

    def setUp(self):
        self._stack = contextlib.ExitStack()
        self.addCleanup(self._stack.close)
        self._stack.enter_context(use(L5RCMContext()))

        data_ = dal.Data([], [])
        api.data.set_model(data_)

        clan = Clan()
        clan.id = 'test_clan'
        clan.name = u'test_clan'
        data_.clans.append(clan)

        fam = Family()
        fam.id = 'test_family'
        fam.name = u'test_family'
        fam.clanid = 'test_clan'
        fam.trait = 'strength'
        data_.families.append(fam)

        # a base bushi school with the usual rank 1..5 techniques
        base = _school('base_school',
                       [_tech('base_tech_%d' % r, r) for r in range(1, 6)],
                       ['bushi'])
        data_.schools.append(base)

        # the Topaz Champion: a rank-0 "join at any rank" path that keeps
        # the technique it replaces
        topaz = _school('topaz_path', [_tech('soul_of_promise', 0)],
                        ['champion', 'alternate', 'keep_replaced_tech'])
        data_.schools.append(topaz)

        # a plain rank-0 path WITHOUT the tag (an Imperial champion) --
        # grants only its own technique
        emerald = _school('emerald_path', [_tech('emperors_hand', 0)],
                          ['champion', 'alternate'])
        data_.schools.append(emerald)

        api.character.new()

    def _to_rank(self, n):
        """put the character in base_school and advance to insight rank n."""
        api.character.schools.set_first('base_school')
        for _ in range(n - 1):
            api.character.rankadv.advance_rank()

    # ------------------------------------------------------------------

    def test_rank0_path_grants_own_technique(self):
        """A rank-0 path's own technique is granted (was lost since 22b28a1)."""
        self._to_rank(3)
        api.character.rankadv.join_new('emerald_path')  # insight rank 4
        self.assertEqual(['emperors_hand'],
                         api.character.schools.get_techs_by_rank(4))

    def test_topaz_keeps_replaced_technique(self):
        """The Topaz Champion grants its own technique AND the rank-4
        technique the base school would otherwise have provided."""
        self._to_rank(3)
        api.character.rankadv.join_new('topaz_path')  # insight rank 4
        techs = api.character.schools.get_techs_by_rank(4)
        self.assertIn('soul_of_promise', techs)
        self.assertIn('base_tech_4', techs)
        self.assertEqual(2, len(techs))

    def test_topaz_replaced_technique_tracks_join_rank(self):
        """The kept technique is the one for the rank the path replaces --
        joining at insight rank 3 keeps the rank-3 base technique."""
        self._to_rank(2)
        api.character.rankadv.join_new('topaz_path')  # insight rank 3
        techs = api.character.schools.get_techs_by_rank(3)
        self.assertIn('soul_of_promise', techs)
        self.assertIn('base_tech_3', techs)

    def test_topaz_techniques_are_active_rules(self):
        """Both techniques become active rules (has_rule), which is what
        drives the technique's mechanical effects."""
        self._to_rank(3)
        api.character.rankadv.join_new('topaz_path')  # insight rank 4
        self.assertTrue(api.character.has_rule('soul_of_promise'))
        self.assertTrue(api.character.has_rule('base_tech_4'))

    def test_base_school_techniques_unaffected(self):
        """A plain school still grants exactly one technique per rank."""
        self._to_rank(5)
        for r in range(1, 6):
            self.assertEqual(['base_tech_%d' % r],
                             api.character.schools.get_techs_by_rank(r))

    def test_get_tech_by_rank_returns_primary(self):
        """The single-value helper still returns the path's own technique."""
        self._to_rank(3)
        api.character.rankadv.join_new('topaz_path')  # insight rank 4
        self.assertEqual('soul_of_promise',
                         api.character.schools.get_tech_by_rank(4))


if __name__ == '__main__':
    unittest.main()
