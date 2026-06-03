# -*- coding: utf-8 -*-
__author__ = 'Daniele Simonetti'

import contextlib
import unittest

import l5r.api as api
import l5r.api.character
import l5r.api.data
from l5r.api.context import L5RCMContext, use

import l5rdal as dal

from l5r.tests.fakedata import *


class TestCharacterBll(unittest.TestCase):

    def setUp(self):
        # Each test gets a fresh, isolated L5RCMContext so it never
        # mutates (or is contaminated by) the production singleton bound
        # in l5r/api/__init__.py.
        self._stack = contextlib.ExitStack()
        self.addCleanup(self._stack.close)
        self._stack.enter_context(use(L5RCMContext()))

        # inject some data
        data_ = dal.Data([], [])
        api.data.set_model(data_)

        # clans
        data_.clans.append(test_clan_1)
        data_.clans.append(test_clan_2)
        # families
        data_.families.append(test_family_1)
        data_.families.append(test_family_2)
        # schools
        data_.schools.append(test_school_1)
        # skills
        data_.skcategs.append(test_skill_categ_1)
        data_.skcategs.append(test_skill_categ_2)
        data_.skills.append(test_skill_1)
        data_.skills.append(test_skill_2)

        # create new character
        api.character.new()

    def tearDown(self):
        pass

    def test_set_family(self):
        """
        test the set_family method
        :return:
        """
        api.character.set_family('test_family_1')
        self.assertEqual('test_family_1', api.character.model().family)

    def test_get_family(self):
        """
        get_family should return 'test_family'
        :return:
        """
        api.character.model().family = 'test_family_2'
        self.assertEqual('test_family_2', api.character.get_family())

    def test_get_family_no_family(self):
        """
        get_family should return None
        :return:
        """
        self.assertEqual(None, api.character.get_family())

    def test_get_clan_no_family(self):
        """
        get_clan should return None
        :return:
        """
        self.assertEqual(None, api.character.get_clan())

    def test_get_clan(self):
        """
        get_clan should return test_clan
        :return:
        """

        api.character.set_family('test_family_1')
        self.assertEqual('test_clan_1', api.character.get_clan())

    def test_get_family_tags(self):
        """
        get_family_tags() should returns the family and the clan id
        :return:
        """

        api.character.set_family('test_family_1')
        self.assertEqual(['test_family_1', 'test_clan_1'], api.character.get_family_tags())

    def test_get_family_tags_no_family(self):
        """
        get_family_tags() should returns an empty list
        :return:
        """

        self.assertEqual([], api.character.get_family_tags())

    def test_family_trait_bonus(self):
        """
        check that the family trait bonus is applied
        :return:
        """

        # this family has trait bonus: strength
        api.character.set_family('test_family_1')
        self.assertEqual(3, api.character.trait_rank('strength'))

    def test_starting_trait_value(self):
        """
        check that the family trait bonus is applied
        :return:
        """

        self.assertEqual(2, api.character.trait_rank('strength'))

    def test_school_trait_bonus(self):
        """
        check that the school trait bonus is applied
        :return:
        """

        # this family has trait bonus: willpower
        api.character.schools.set_first('test_school_1')
        self.assertEqual(3, api.character.trait_rank('willpower'))

    def test_school_tags(self):
        """
        check that the school tags are applied
        :return:
        """

        test_school_1.tags = ['tag1', 'tag2']

        api.character.schools.set_first('test_school_1')
        self.assertEqual(['test_school_1', 'tag1', 'tag2'], api.character.get_school_tags())

    def test_get_school_rules(self):
        """
        check that upon joining a school you get the rules of the first school tech
        """
        self.assertEqual(
            api.character.get_school_rules(),
            []
        )
        api.character.schools.set_first('test_school_1')
        self.assertEqual(
            api.character.get_school_rules(),
            [
                'test_tech_1',
            ]
        )

    def test_join_new_school(self):
        """rankadv.join_new adds a SECOND school (multiclass): both schools
        are tracked, the current school becomes the newly joined one, and
        its school rank is 1. This is the branch the QML joinNewSchool slot
        drives -- joinNewSchool simply calls join_new (+ an optional merit).
        """
        import l5r.api.character.rankadv
        import l5r.api.character.schools

        # a second basic school the character can multiclass into
        second = School()
        second.id = 'test_school_2'
        second.name = u'test_school_2'
        second.clanid = 'test_clan_2'
        second.trait = 'reflexes'
        second.affinity = None
        second.deficiency = None
        second.honor = 0.0
        second.kihos = SchoolKiho()
        second.tattoos = SchoolTattoo()
        s2_tech = SchoolTech()
        s2_tech.id = 'test_tech_s2_1'
        s2_tech.rank = 1
        second.tags = []
        second.skills = []
        second.skills_pc = []
        second.techs = [s2_tech]
        second.spells = []
        second.spells_pc = []
        second.outfit = []
        second.money = [0] * 3
        second.require = []
        second.perks = []
        api.data.model().schools.append(second)

        api.character.schools.set_first('test_school_1')
        api.character.rankadv.join_new('test_school_2')

        self.assertEqual(
            sorted(['test_school_1', 'test_school_2']),
            sorted(api.character.schools.get_all()))
        self.assertEqual('test_school_2', api.character.schools.get_current())
        self.assertEqual(1, api.character.schools.get_school_rank('test_school_2'))
        self.assertEqual(1, api.character.schools.get_school_rank('test_school_1'))

    def test_choose_affinity(self):
        """choose_affinity commits the picked ring onto the rank advancement
        and consumes the pending `any`/`nonvoid` slot (the QML chooseAffinity
        slot path)."""
        import l5r.api.character.rankadv
        import l5r.api.character.schools
        import l5r.api.character.spells

        api.character.schools.set_first('test_school_1')
        rank_ = api.character.rankadv.get_last()
        rank_.affinities_to_choose = ['nonvoid']

        self.assertTrue(api.character.rankadv.choose_affinity('fire'))
        self.assertIn('fire', api.character.spells.affinities())
        self.assertEqual([], rank_.affinities_to_choose)

    def test_choose_affinity_nothing_pending(self):
        """choose_affinity is a no-op (returns False) when no choice is
        pending, so a stray call can't invent an affinity."""
        import l5r.api.character.rankadv
        import l5r.api.character.schools

        api.character.schools.set_first('test_school_1')
        api.character.rankadv.get_last().affinities_to_choose = []
        self.assertFalse(api.character.rankadv.choose_affinity('fire'))

    def test_choose_deficiency(self):
        """choose_deficiency is the deficiency counterpart of choose_affinity."""
        import l5r.api.character.rankadv
        import l5r.api.character.schools
        import l5r.api.character.spells

        api.character.schools.set_first('test_school_1')
        rank_ = api.character.rankadv.get_last()
        rank_.deficiencies_to_choose = ['any']

        self.assertTrue(api.character.rankadv.choose_deficiency('water'))
        self.assertIn('water', api.character.spells.deficiencies())
        self.assertEqual([], rank_.deficiencies_to_choose)

    def test_school_spell_commit(self):
        """The bounded spell-grant commit path (applySchoolSpellChoices):
        add_school_spell records each pick on the rank, and
        clear_spells_to_choose wipes the pending grant."""
        import l5r.api.character.rankadv
        import l5r.api.character.schools
        import l5r.api.character.spells
        from l5rdal.spell import Spell

        s1 = Spell()
        s1.id, s1.name, s1.element, s1.mastery = 'spell_a', 'Spell A', 'fire', 1
        s2 = Spell()
        s2.id, s2.name, s2.element, s2.mastery = 'spell_b', 'Spell B', 'water', 1
        api.data.model().spells.append(s1)
        api.data.model().spells.append(s2)

        api.character.schools.set_first('test_school_1')
        rank_ = api.character.rankadv.get_last()
        rank_.gained_spells_count = 2

        api.character.spells.add_school_spell('spell_a')
        api.character.spells.add_school_spell('spell_b')
        api.character.rankadv.clear_spells_to_choose()

        school_spells = api.character.spells.get_school_spells()
        self.assertIn('spell_a', school_spells)
        self.assertIn('spell_b', school_spells)
        self.assertEqual(0, api.character.rankadv.get_pending_spells_count())
        self.assertEqual([], api.character.rankadv.get_starting_spells_to_choose())
