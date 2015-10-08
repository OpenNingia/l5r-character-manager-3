# -*- coding: utf-8 -*-
__author__ = 'Daniele Simonetti'

import unittest
import api
import api.character
import api.data

import dal

from tests.fakedata import *


class TestCharacterBll(unittest.TestCase):

    def setUp(self):
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
