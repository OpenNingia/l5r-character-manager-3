# -*- coding: utf-8 -*-
"""Tests for the dynamic-modifier builder (l5r.api.rules.modifiers).

Ownership, the school-rank binding and the facade are stubbed so these focus on
the materialization logic (affects->type, value shape, when/active, wpen sign).
"""

import contextlib
import unittest

import l5rdal as dal
from l5r.api.context import L5RCMContext, use
from l5r.api.rules import modifiers as M
from l5r.api.tests.test_modifier_eval import FakeFacade


MODS_XML = """<L5RCM>
  <ModifierDef target="kitsuki" kind="tech">
    <Mod affects="armor_tn" value="traits.perception"/>
  </ModifierDef>
  <ModifierDef target="mountain" kind="tech">
    <Mod affects="reduction" value="rings.earth"/>
  </ModifierDef>
  <ModifierDef target="bamboo" kind="tattoo">
    <Mod affects="armor_tn" value="2 * school_rank + 5"/>
  </ModifierDef>
  <ModifierDef target="crane" kind="tech">
    <Mod affects="attack_roll" roll="1" keep="1" bonus="school_rank" when="center_stance"/>
  </ModifierDef>
  <ModifierDef target="indomitable" kind="kata">
    <Mod affects="wound_penalty" value="-rings.earth"/>
  </ModifierDef>
  <ModifierDef target="ranged" kind="path">
    <Mod affects="attack_roll" detail="tag:ranged" bonus="1"/>
  </ModifierDef>
  <ModifierDef target="lame" kind="flaw">
    <Mod affects="ring_rank" detail="ring:water" op="set" value="1"/>
  </ModifierDef>
</L5RCM>"""


class TestBuildDynamicModifiers(unittest.TestCase):

    def setUp(self):
        self._stack = contextlib.ExitStack()
        self.addCleanup(self._stack.close)

        ctx = L5RCMContext()
        ds = dal.Data([], [])
        ds.from_string(MODS_XML)
        ctx.ds = ds
        ctx.pc = object()          # presence is all the builder checks
        self._stack.enter_context(use(ctx))
        self.ctx = ctx

        # own everything; fixed school rank; fake facade values
        self._patch(M, "_owns", lambda target, kind: True)
        self._patch(M, "_school_rank_for", lambda target, kind: 3)
        self._patch(M, "_make_facade",
                    lambda: FakeFacade(rings={"earth": 3, "air": 2, "fire": 4,
                                              "water": 2, "void": 2},
                                       traits={"perception": 5}))

    def _patch(self, obj, name, value):
        old = getattr(obj, name)
        setattr(obj, name, value)
        self.addCleanup(lambda: setattr(obj, name, old))

    def _by_reason(self, mods, target):
        return [m for m in mods if m.reason == target]

    def test_scalar_and_expression(self):
        mods = M.build_dynamic_modifiers()
        kitsuki = self._by_reason(mods, "kitsuki")[0]
        self.assertEqual("artn", kitsuki.type)
        self.assertEqual((0, 0, 5), kitsuki.value)          # traits.perception
        self.assertTrue(kitsuki.active)                      # auto
        self.assertFalse(kitsuki.toggleable)
        self.assertTrue(kitsuki.readonly)

        mountain = self._by_reason(mods, "mountain")[0]
        self.assertEqual("arrd", mountain.type)
        self.assertEqual((0, 0, 3), mountain.value)          # rings.earth

        bamboo = self._by_reason(mods, "bamboo")[0]
        self.assertEqual((0, 0, 11), bamboo.value)           # 2*3 + 5

    def test_roll_typed_and_when_toggle(self):
        mods = M.build_dynamic_modifiers()
        crane = self._by_reason(mods, "crane")[0]
        self.assertEqual("atkr", crane.type)
        self.assertTrue(crane.toggleable)
        self.assertFalse(crane.active)                       # when -> off by default
        self.assertEqual((1, 1, 3), crane.value)             # roll/keep/bonus(school_rank)

        # flip it on via the session state, rebuild
        M.set_runtime_modifier_active(crane.key, True)
        crane2 = self._by_reason(M.build_dynamic_modifiers(), "crane")[0]
        self.assertTrue(crane2.active)

    def test_wound_penalty_sign_is_negated(self):
        # schema value -rings.earth (= -3) must surface as +3 reduction for the
        # engine (which does result - value[2]).
        indom = self._by_reason(M.build_dynamic_modifiers(), "indomitable")[0]
        self.assertEqual("wpen", indom.type)
        self.assertEqual((0, 0, 3), indom.value)

    def test_filter_by_type(self):
        artn = M.build_dynamic_modifiers(filter_type="artn")
        self.assertTrue(all(m.type == "artn" for m in artn))
        self.assertEqual(2, len(artn))                       # kitsuki + bamboo

    def test_skipped_constructs(self):
        mods = M.build_dynamic_modifiers()
        # tag: detail not representable yet -> ranged tech produces nothing
        self.assertEqual([], self._by_reason(mods, "ranged"))
        # op=set not supported yet -> lame produces nothing
        self.assertEqual([], self._by_reason(mods, "lame"))


if __name__ == "__main__":
    unittest.main()
