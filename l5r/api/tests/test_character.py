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
