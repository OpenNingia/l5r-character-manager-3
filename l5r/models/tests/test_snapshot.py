# -*- coding: utf-8 -*-

import unittest
import l5rdal as dal
import l5r.api as api
import l5r.api.data
import l5r.api.character
from l5r.models import CharacterSnapshot
from l5r.tests.fakedata import *

__author__ = 'Daniele Simonetti'


class TestCharacterSnapshot(unittest.TestCase):

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
        api.character.schools.set_first('test_school_1')

        # set starting school

    def tearDown(self):
        pass

    def test_rings(self):
        """
        check ring values
        :return:
        """

        # create snapshot
        snap = CharacterSnapshot(api.character.model())

        self.assertEqual(
            api.character.ring_rank('air'),
            snap.get_ring_rank('air'))

        self.assertEqual(
            api.character.ring_rank('fire'),
            snap.get_ring_rank('fire'))

        self.assertEqual(
            api.character.ring_rank('water'),
            snap.get_ring_rank('water'))

        self.assertEqual(
            api.character.ring_rank('earth'),
            snap.get_ring_rank('earth'))

        self.assertEqual(
            api.character.ring_rank('void'),
            snap.get_ring_rank('void'))

    def test_traits(self):
        """
        check trait values
        :return:
        """

        # create snapshot
        snap = CharacterSnapshot(api.character.model())

        self.assertEqual(
            api.character.trait_rank('strength'),
            snap.get_trait_rank('strength'))

        self.assertEqual(
            api.character.trait_rank('willpower'),
            snap.get_trait_rank('willpower'))

        self.assertEqual(
            api.character.trait_rank('reflexes'),
            snap.get_trait_rank('reflexes'))

        self.assertEqual(
            api.character.trait_rank('agility'),
            snap.get_trait_rank('agility'))

        self.assertEqual(
            api.character.trait_rank('awareness'),
            snap.get_trait_rank('awareness'))

        self.assertEqual(
            api.character.trait_rank('perception'),
            snap.get_trait_rank('perception'))

        self.assertEqual(
            api.character.trait_rank('stamina'),
            snap.get_trait_rank('stamina'))

        self.assertEqual(
            api.character.trait_rank('intelligence'),
            snap.get_trait_rank('intelligence'))

    def test_starting_skills(self):
        """
        test starting skill rank
        :return:
        """

        # set starting skill
        api.character.skills.add_starting_skill('test_skill_1', rank=1)

        # create snapshot
        snap = CharacterSnapshot(api.character.model())

        self.assertEqual(1, snap.get_skill_rank('test_skill_1'))
        self.assertEqual(0, snap.get_skill_rank('test_skill_2'))

    def test_purchased_skills(self):
        """
        test purchased skill rank
        :return:
        """

        # purchase skill rank
        self.assertTrue(
            api.character.skills.purchase_skill_rank('test_skill_2'))

        # create snapshot
        snap = CharacterSnapshot(api.character.model())

        self.assertEqual(0, snap.get_skill_rank('test_skill_1'))
        self.assertEqual(1, snap.get_skill_rank('test_skill_2'))
