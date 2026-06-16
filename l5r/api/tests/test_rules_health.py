# -*- coding: utf-8 -*-
__author__ = 'Daniele Simonetti'

import contextlib
import unittest

import l5rdal as dal

import l5r.api as api
import l5r.api.character
import l5r.api.data
# api.character.trait_rank reaches into api.data.families.get_family_trait;
# the parent package doesn't pull submodules in, so importing it here
# wires up the lookup before any rule that walks Earth/Stamina runs.
import l5r.api.data.families  # noqa: F401
import l5r.api.rules
import l5r.api.signals
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

    def test_setter_emits_wounds_changed_on_change(self):
        """The QML combat proxy listens on api.signals.bus().wounds_changed
        to rebroadcast combatChanged; without this emit, healthMultiplier
        would still update the model but the UI would freeze on the old
        wound table until something else refreshed it. The narrow signal
        (not the coarse character_refreshed) keeps the rest of the sheet
        from re-projecting."""
        events = _record_signal(self, api.signals.bus().wounds_changed)
        api.character.set_health_multiplier(3)
        self.assertEqual(1, len(events))

    def test_setter_no_op_does_not_emit(self):
        pc = api.character.model()
        events = _record_signal(self, api.signals.bus().wounds_changed)
        api.character.set_health_multiplier(pc.health_multiplier)
        self.assertEqual(0, len(events))

    # --- effects on wound table & resilience -----------------------------

    def test_changing_multiplier_resizes_buckets_below_healthy(self):
        """Bumping the multiplier widens NICKED..OUT (Earth*mult each)
        but must leave HEALTHY (Earth*5) untouched. Regression for the
        per-bucket increment that the WoundsBlock card grid shows in
        each card's corner -- the proxy reads it straight from the
        rules layer, so the rules layer must keep delivering it."""
        earth = api.character.ring_rank('earth')
        api.character.set_health_multiplier(2)
        table = api.rules.get_wounds_table()
        self.assertEqual(earth * 5, table[0][0])
        for idx in range(1, 8):
            self.assertEqual(earth * 2, table[idx][0])

        api.character.set_health_multiplier(4)
        table = api.rules.get_wounds_table()
        self.assertEqual(earth * 5, table[0][0])
        for idx in range(1, 8):
            self.assertEqual(earth * 4, table[idx][0])

    def test_lowering_multiplier_does_not_clamp_existing_wounds(self):
        """Multiplier change does *not* re-clamp pc.wounds, by design --
        the value lives independently in the model, and the wound-table
        rendering handles the overflow via min(stacked, tot_wounds).
        If you ever decide to clamp on multiplier change, this test
        should flip to `assertEqual(new_max, pc.wounds)`; pinning the
        current behaviour here makes the choice explicit."""
        api.character.set_health_multiplier(4)
        max_at_4 = api.rules.get_max_wounds()
        api.character.set_wounds_taken(max_at_4 - 2)
        before = api.character.get_wounds_taken()

        api.character.set_health_multiplier(1)
        new_max = api.rules.get_max_wounds()
        self.assertLess(new_max, before)
        self.assertEqual(before, api.character.get_wounds_taken())

    def test_max_wounds_grows_with_multiplier(self):
        """The card-grid 'TOTAL' number and the RankStepper's `to` upper
        bound both consume get_max_wounds; verify monotonicity so the
        stepper can't outrun the model."""
        earth = api.character.ring_rank('earth')
        previous = 0
        for mult in (1, 2, 3, 4, 5):
            api.character.set_health_multiplier(mult)
            current = api.rules.get_max_wounds()
            self.assertGreater(current, previous,
                               "max wounds must grow with multiplier")
            self.assertEqual(earth * 5 + 7 * earth * mult, current)
            previous = current


class TestBaseHealthMultiplier(unittest.TestCase):
    """Cover the Healthy-level (idx 0) base multiplier, editable via
    api.character.set_base_health_multiplier. RAW is Earth*5; sagas with
    modified starting health (#389) change the base, the rest of the wound
    table is untouched."""

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
        # Fresh PC: Earth 2, base 5, per-rank mult 2.

    def test_default_base_is_five(self):
        self.assertEqual(5, api.character.model().health_base_multiplier)
        self.assertEqual(5, api.character.get_base_health_multiplier())

    def test_healthy_level_uses_base_multiplier(self):
        earth = api.character.ring_rank('earth')
        for base in (1, 3, 5, 8):
            api.character.set_base_health_multiplier(base)
            self.assertEqual(earth * base, api.rules.get_health_rank(0))

    def test_base_does_not_affect_penalty_levels(self):
        """Changing the Healthy base must leave levels 1..7 (Earth*mult)
        untouched."""
        earth = api.character.ring_rank('earth')
        api.character.set_base_health_multiplier(8)
        for idx in range(1, 8):
            self.assertEqual(earth * 2, api.rules.get_health_rank(idx))

    def test_setter_updates_model_and_marks_dirty(self):
        pc = api.character.model()
        pc.unsaved = False
        api.character.set_base_health_multiplier(7)
        self.assertEqual(7, pc.health_base_multiplier)
        self.assertTrue(pc.unsaved)

    def test_setter_no_op_does_not_dirty(self):
        pc = api.character.model()
        pc.unsaved = False
        api.character.set_base_health_multiplier(pc.health_base_multiplier)
        self.assertFalse(pc.unsaved)

    def test_setter_rejects_below_one(self):
        with self.assertRaises(ValueError):
            api.character.set_base_health_multiplier(0)

    def test_setter_coerces_int(self):
        api.character.set_base_health_multiplier("6")
        self.assertEqual(6, api.character.model().health_base_multiplier)

    def test_setter_emits_wounds_changed_on_change(self):
        events = _record_signal(self, api.signals.bus().wounds_changed)
        api.character.set_base_health_multiplier(3)
        self.assertEqual(1, len(events))

    def test_setter_no_op_does_not_emit(self):
        pc = api.character.model()
        events = _record_signal(self, api.signals.bus().wounds_changed)
        api.character.set_base_health_multiplier(pc.health_base_multiplier)
        self.assertEqual(0, len(events))

    def test_max_wounds_uses_base(self):
        """Earth=2: base 5 -> 38; base 3 -> 2*3 + 7*(2*2) = 6 + 28 = 34."""
        earth = api.character.ring_rank('earth')
        api.character.set_base_health_multiplier(3)
        self.assertEqual(earth * 3 + 7 * earth * 2, api.rules.get_max_wounds())

    def test_missing_attr_defaults_to_five(self):
        """Characters saved before #389 have no health_base_multiplier;
        the rules layer and getter must fall back to RAW (5)."""
        pc = api.character.model()
        del pc.health_base_multiplier
        earth = api.character.ring_rank('earth')
        self.assertEqual(5, api.character.get_base_health_multiplier())
        self.assertEqual(earth * 5, api.rules.get_health_rank(0))


# ---------------------------------------------------------------------------
# Wound-table edge cases the QML proxy depends on. These document quiet
# invariants that bit us when porting the wounds panel to QML.
# ---------------------------------------------------------------------------

class TestWoundPenaltiesRange(unittest.TestCase):
    """get_wound_penalties only knows about levels 0..6 (Healthy..Down).
    Out (idx 7) is unconscious / fatal, not a TN penalty — looking it up
    must raise so accidental callers fail loudly. The QML wounds() proxy
    guards on idx < 7 because of this constraint; if you ever extend the
    table, update both."""

    def setUp(self):
        self._stack = contextlib.ExitStack()
        self.addCleanup(self._stack.close)
        self._stack.enter_context(use(L5RCMContext()))
        api.data.set_model(dal.Data([], []))
        api.character.new()

    def test_penalty_for_known_levels(self):
        # Spot-check the canonical 4e values so any reshuffle of the
        # WOUND_PENALTIES_VALUES table is caught here.
        self.assertEqual(0,  api.rules.get_wound_penalties(0))   # Healthy
        self.assertEqual(3,  api.rules.get_wound_penalties(1))   # Nicked
        self.assertEqual(5,  api.rules.get_wound_penalties(2))
        self.assertEqual(10, api.rules.get_wound_penalties(3))
        self.assertEqual(15, api.rules.get_wound_penalties(4))
        self.assertEqual(20, api.rules.get_wound_penalties(5))
        self.assertEqual(40, api.rules.get_wound_penalties(6))   # Down

    def test_penalty_for_out_raises(self):
        with self.assertRaises(IndexError):
            api.rules.get_wound_penalties(7)


# ---------------------------------------------------------------------------
# Wounds setters: get_wounds_taken / set_wounds_taken / damage_health.
# These live next to set_health_multiplier in api.character and follow
# the same shape (clamp + dirty flag + character_refreshed emit).
# ---------------------------------------------------------------------------

class TestWoundsSetters(unittest.TestCase):

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
        # Fresh PC: Earth 2, mult 2 -> max wounds = 38, current wounds = 0.
        self.max_wounds = api.rules.get_max_wounds()
        self.assertEqual(38, self.max_wounds)

    # --- get_wounds_taken --------------------------------------------------

    def test_get_wounds_default_zero(self):
        self.assertEqual(0, api.character.get_wounds_taken())

    def test_get_wounds_reads_model_value(self):
        api.character.model().wounds = 12
        self.assertEqual(12, api.character.get_wounds_taken())

    # --- set_wounds_taken --------------------------------------------------

    def test_set_updates_model(self):
        api.character.set_wounds_taken(7)
        self.assertEqual(7, api.character.model().wounds)
        self.assertEqual(7, api.character.get_wounds_taken())

    def test_set_marks_dirty(self):
        pc = api.character.model()
        pc.unsaved = False
        api.character.set_wounds_taken(5)
        self.assertTrue(pc.unsaved)

    def test_set_no_op_does_not_dirty(self):
        """Idempotent setter: assigning the same value must not flip the
        unsaved flag, otherwise re-opening a clean character and not
        touching the wounds counter would still prompt to save."""
        pc = api.character.model()
        pc.wounds = 5
        pc.unsaved = False
        api.character.set_wounds_taken(5)
        self.assertFalse(pc.unsaved)

    def test_set_clamps_below_zero(self):
        api.character.set_wounds_taken(-10)
        self.assertEqual(0, api.character.get_wounds_taken())

    def test_set_clamps_above_max(self):
        api.character.set_wounds_taken(self.max_wounds + 50)
        self.assertEqual(self.max_wounds, api.character.get_wounds_taken())

    def test_set_coerces_int(self):
        api.character.set_wounds_taken("9")
        self.assertEqual(9, api.character.get_wounds_taken())

    def test_set_emits_wounds_changed_on_change(self):
        events = _record_signal(self, api.signals.bus().wounds_changed)
        api.character.set_wounds_taken(4)
        self.assertEqual(1, len(events))

    def test_set_no_op_does_not_emit(self):
        events = _record_signal(self, api.signals.bus().wounds_changed)
        api.character.set_wounds_taken(0)   # already 0
        self.assertEqual(0, len(events))

    # --- damage_health -----------------------------------------------------

    def test_damage_adds_positive_delta(self):
        api.character.set_wounds_taken(5)
        api.character.damage_health(3)
        self.assertEqual(8, api.character.get_wounds_taken())

    def test_damage_negative_delta_heals(self):
        api.character.set_wounds_taken(10)
        api.character.damage_health(-4)
        self.assertEqual(6, api.character.get_wounds_taken())

    def test_damage_clamps_at_zero(self):
        api.character.set_wounds_taken(3)
        api.character.damage_health(-50)
        self.assertEqual(0, api.character.get_wounds_taken())

    def test_damage_clamps_at_max(self):
        api.character.set_wounds_taken(self.max_wounds - 2)
        api.character.damage_health(99)
        self.assertEqual(self.max_wounds, api.character.get_wounds_taken())

    def test_damage_zero_delta_is_a_no_op(self):
        pc = api.character.model()
        pc.wounds = 5
        pc.unsaved = False
        events = _record_signal(self, api.signals.bus().wounds_changed)
        api.character.damage_health(0)
        self.assertEqual(5, pc.wounds)
        self.assertFalse(pc.unsaved)
        self.assertEqual(0, len(events))


def _record_signal(test_case, signal):
    """Subscribe a counter handler to ``signal`` and auto-disconnect on
    test teardown. ``api.signals.bus()`` is a process-wide singleton, so
    leaking subscribers across tests would make assertions flaky."""
    events = []

    def _handler(*args, **kwargs):
        events.append(args)

    signal.connect(_handler)
    test_case.addCleanup(signal.disconnect, _handler)
    return events
