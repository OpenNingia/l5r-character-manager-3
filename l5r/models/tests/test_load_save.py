# -*- coding: utf-8 -*-

import contextlib
import os
import tempfile
import unittest

import l5rdal as dal
from l5rdal.school import SchoolSkillWildcard, SchoolSkillWildcardSet

import l5r.api as api
import l5r.api.data
import l5r.api.data.families
import l5r.api.data.skills
import l5r.api.character
import l5r.api.character.rankadv
import l5r.api.character.schools
from l5r.api.context import L5RCMContext, use
from l5r.models.chmodel import AdvancedPcModel
from l5r.tests.fakedata import *


class TestLoadSavePendingChoices(unittest.TestCase):
    """Regression tests for the character save/load round-trip.

    A character saved with pending skill choices used to break on reload:
    the ``SchoolSkillWildcardSet`` objects stored in a rank advancement's
    ``skills_to_choose`` were serialised to plain dicts and never restored,
    so reading ``ws.wildcards`` raised ``AttributeError``.
    """

    def setUp(self):
        self._stack = contextlib.ExitStack()
        self.addCleanup(self._stack.close)
        self._stack.enter_context(use(L5RCMContext()))

        data_ = dal.Data([], [])
        api.data.set_model(data_)

        data_.clans.append(test_clan_1)
        data_.families.append(test_family_1)

        # A school that grants a pending wildcard skill choice
        # ("any skill from category test_skill_categ_1, rank 1").
        wildcard = SchoolSkillWildcard()
        wildcard.value = 'test_skill_categ_1'
        wildcard.modifier = 'or'

        wildcard_set = SchoolSkillWildcardSet()
        wildcard_set.rank = 1
        wildcard_set.wildcards = [wildcard]

        test_school_1.skills_pc = [wildcard_set]
        data_.schools.append(test_school_1)

        self.addCleanup(lambda: setattr(test_school_1, 'skills_pc', []))

        api.character.new()
        api.character.schools.set_first('test_school_1')

    def _get_rank_skills_to_choose(self, model):
        api.character.set_model(model)
        return api.character.rankadv.get_starting_skills_to_choose()

    def test_pending_choice_present_before_save(self):
        """Sanity check: the in-memory character has the wildcard set."""
        to_choose = api.character.rankadv.get_starting_skills_to_choose()
        self.assertEqual(1, len(to_choose))
        self.assertEqual('test_skill_categ_1', to_choose[0].wildcards[0].value)

    def test_round_trip_preserves_wildcard_objects(self):
        """Saving then loading must keep ``skills_to_choose`` as objects."""
        model = api.character.model()

        fd, path = tempfile.mkstemp(suffix='.l5r')
        os.close(fd)
        self.addCleanup(lambda: os.path.exists(path) and os.remove(path))

        self.assertTrue(model.save_to(path))

        loaded = AdvancedPcModel()
        self.assertTrue(loaded.load_from(path))

        to_choose = self._get_rank_skills_to_choose(loaded)

        # This attribute access used to raise:
        #   AttributeError: 'dict' object has no attribute 'wildcards'
        self.assertEqual(1, len(to_choose))
        wildcard_set = to_choose[0]
        self.assertIsInstance(wildcard_set, SchoolSkillWildcardSet)
        self.assertEqual(1, wildcard_set.rank)
        self.assertEqual(1, len(wildcard_set.wildcards))

        wildcard = wildcard_set.wildcards[0]
        self.assertIsInstance(wildcard, SchoolSkillWildcard)
        self.assertEqual('test_skill_categ_1', wildcard.value)
        self.assertEqual('or', wildcard.modifier)
