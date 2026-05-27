# -*- coding: utf-8 -*-
__author__ = 'Daniele Simonetti'

import contextlib
import unittest

import l5rdal as dal

import l5r.api as api
import l5r.api.character
import l5r.api.data
import l5r.api.rules
from l5r.api.context import L5RCMContext, use

from l5r.tests.fakedata import (
    test_clan_1,
    test_family_1,
    test_school_1,
    test_skill_categ_1,
    test_skill_1,
)


class TestHealthMultiplier(unittest.TestCase):
    """Cover the wound-level math driven by pc.health_multiplier and the
    api.character.set_health_multiplier setter."""

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
        # Default fresh character: stamina=2, willpower=2 -> earth=2,
        # health_multiplier=2, wounds=0.

    # --- model defaults ----------------------------------------------------

    def test_default_multiplier_is_two(self):
        """L5R 4e ships every PC with x2 wound increments by default."""
        self.assertEqual(2, api.character.model().health_multiplier)
        self.assertEqual(2, api.character.get_health_multiplier())

    def test_default_earth_rank(self):
        """Sanity check: a vanilla PC has Earth = min(stamina, willpower) = 2.
        The rest of the file relies on this baseline."""
        self.assertEqual(2, api.character.ring_rank('earth'))

    # --- get_health_rank ---------------------------------------------------

    def test_healthy_level_is_earth_times_five_regardless_of_multiplier(self):
        """The Healthy wound level (idx 0) is Earth * 5 in 4e — the
        multiplier scales only the seven penalty levels below it."""
        earth = api.character.ring_rank('earth')
        for mult in (1, 2, 3, 4, 5):
            api.character.model().health_multiplier = mult
            self.assertEqual(
                earth * 5,
                api.rules.get_health_rank(0),
                "healthy level should be Earth*5 with multiplier=%d" % mult,
            )

    def test_penalty_levels_use_multiplier(self):
        """Wound levels 1..7 each return Earth * multiplier."""
        earth = api.character.ring_rank('earth')
        for mult in (1, 2, 3, 4, 5):
            api.character.model().health_multiplier = mult
            for idx in range(1, 8):
                self.assertEqual(
                    earth * mult,
                    api.rules.get_health_rank(idx),
                    "level %d with multiplier=%d" % (idx, mult),
                )

    # --- get_max_wounds ---------------------------------------------------

    def test_max_wounds_default(self):
        """Earth=2, mult=2 -> 2*5 + 7*(2*2) = 10 + 28 = 38."""
        self.assertEqual(38, api.rules.get_max_wounds())

    def test_max_wounds_scales_with_multiplier(self):
        earth = api.character.ring_rank('earth')
        for mult in (1, 2, 3, 4, 5):
            api.character.model().health_multiplier = mult
            expected = earth * 5 + 7 * earth * mult
            self.assertEqual(
                expected,
                api.rules.get_max_wounds(),
                "max wounds with multiplier=%d" % mult,
            )

    # --- get_wounds_table -------------------------------------------------

    def test_wounds_table_increments_match_health_rank(self):
        """Each row of get_wounds_table starts with that level's increment,
        which must match get_health_rank for the same index."""
        api.character.model().health_multiplier = 3
        table = api.rules.get_wounds_table()
        self.assertEqual(8, len(table))
        for idx in range(8):
            self.assertEqual(
                api.rules.get_health_rank(idx),
                table[idx][0],
                "row %d increment" % idx,
            )

    def test_wounds_table_total_matches_max_wounds(self):
        """First row's 'total' column should equal get_max_wounds."""
        api.character.model().health_multiplier = 4
        table = api.rules.get_wounds_table()
        self.assertEqual(api.rules.get_max_wounds(), table[0][1])

    # --- api.character.set_health_multiplier ------------------------------

    def test_setter_updates_the_model(self):
        api.character.set_health_multiplier(3)
        self.assertEqual(3, api.character.model().health_multiplier)
        self.assertEqual(3, api.character.get_health_multiplier())

    def test_setter_marks_character_dirty(self):
        """Regression: changing the multiplier must trigger the save-on-close
        prompt. Until 2026-05 the L5RCMCore wrapper assigned the field
        directly and never set the dirty flag, so users could lose the
        change."""
        pc = api.character.model()
        pc.unsaved = False
        api.character.set_health_multiplier(3)
        self.assertTrue(pc.unsaved)

    def test_setter_no_op_does_not_dirty(self):
        """Setting the same value the model already has must not flag the
        character as modified — otherwise opening the dialog and pressing
        OK without changing the spinbox would prompt to save."""
        pc = api.character.model()
        current = pc.health_multiplier
        pc.unsaved = False
        api.character.set_health_multiplier(current)
        self.assertFalse(pc.unsaved)

    def test_setter_rejects_zero(self):
        with self.assertRaises(ValueError):
            api.character.set_health_multiplier(0)

    def test_setter_rejects_negative(self):
        with self.assertRaises(ValueError):
            api.character.set_health_multiplier(-3)

    def test_setter_coerces_int(self):
        """The Qt InputDialog gives us an int; if a caller passes a numeric
        string we should still accept it rather than silently storing junk."""
        api.character.set_health_multiplier("4")
        self.assertEqual(4, api.character.model().health_multiplier)

    def test_setter_affects_max_wounds(self):
        """End-to-end: pushing the setter recomputes the rules layer."""
        earth = api.character.ring_rank('earth')
        api.character.set_health_multiplier(5)
        self.assertEqual(earth * 5 + 7 * earth * 5, api.rules.get_max_wounds())
