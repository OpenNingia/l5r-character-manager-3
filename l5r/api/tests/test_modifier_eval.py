# -*- coding: utf-8 -*-
"""Unit tests for the stat-modifier DSL evaluator (l5r.api.rules.modifiers).

The facade is faked so these exercise the evaluator in isolation, with no need
to build a character or a context.
"""

import unittest

from l5r.api.rules import modifiers as M
from l5r.api.rules.modifiers import ModifierEvalError


class FakeFacade(object):
    """A scripted facade with fixed values."""

    def __init__(self, **kw):
        self._rings = kw.get("rings", {"air": 2, "earth": 3, "fire": 4, "water": 2, "void": 2})
        self._traits = kw.get("traits", {"perception": 5, "reflexes": 3, "strength": 2})
        self._skills = kw.get("skills", {"iaijutsu": 4, "kenjutsu": 3})
        self.insight_rank = kw.get("insight_rank", 2)
        self.honor = kw.get("honor", 6)
        self.glory = kw.get("glory", 1)
        self.status = kw.get("status", 1)
        self.taint = kw.get("taint", 0)
        self.unarmored = kw.get("unarmored", True)
        self.in_light_armor = kw.get("in_light_armor", False)
        self.in_heavy_armor = kw.get("in_heavy_armor", False)
        self.has_tattoo = kw.get("has_tattoo", False)
        self._kihos = kw.get("kihos", [])
        self._weapons = kw.get("weapons", set())

    def ring(self, x):
        return self._rings[x]

    def trait(self, x):
        return self._traits[x]

    def skill(self, x):
        return self._skills.get(x, 0)

    def merit_rank(self, x):
        return 0

    def flaw_rank(self, x):
        return 0

    def has_kiho(self, kid=None):
        return bool(self._kihos) if kid is None else (kid in self._kihos)

    def wielding(self, what):
        if what == "daisho":
            return {"katana", "wakizashi"} <= self._weapons
        return what in self._weapons


class TestEvaluateValue(unittest.TestCase):

    def setUp(self):
        self.f = FakeFacade()

    def ev(self, expr, **kw):
        return M.evaluate(expr, bindings=kw.pop("bindings", None), facade=self.f)

    def test_arithmetic(self):
        self.assertEqual(11, self.ev("2 * 3 + 5"))
        self.assertEqual(3, self.ev("ceil(5 / 2)"))
        self.assertEqual(2, self.ev("floor(5 / 2)"))
        self.assertEqual(7, self.ev("abs(-7)"))
        self.assertEqual(2, self.ev("10 // 4"))

    def test_facade_attrs(self):
        self.assertEqual(3, self.ev("rings.earth"))
        self.assertEqual(5, self.ev("traits.perception"))
        self.assertEqual(4, self.ev("skills.iaijutsu"))
        self.assertEqual(3, self.ev("skill('kenjutsu')"))
        self.assertEqual(0, self.ev("skill('unknown')"))
        self.assertEqual(2, self.ev("insight_rank"))
        self.assertEqual(6, self.ev("honor"))

    def test_catalog_expressions(self):
        # Kitsuki's Method, Mountain Does Not Move, Soul of the Four Winds,
        # Honor Is My Shield, Strength of the Crane, tattoo_bamboo
        self.assertEqual(5, self.ev("traits.perception"))
        self.assertEqual(3, self.ev("rings.earth"))
        self.assertEqual(4, self.ev("insight_rank + rings.air"))
        self.assertEqual(3, self.ev("ceil(honor / 2)"))
        self.assertEqual(3, self.ev("max(honor - 3, 1)"))
        self.assertEqual(11, self.ev("2 * school_rank + 5", bindings={"school_rank": 3}))

    def test_bindings_param_and_school_rank(self):
        self.assertEqual(3, self.ev("school_rank", bindings={"school_rank": 3}))
        self.assertEqual(-2, self.ev("-x", bindings={"x": 2}))

    def test_rejects_dangerous_and_unknown(self):
        for bad in ("__import__('os')", "().__class__", "open('f')",
                    "2 ** 3", "undeclared + 1", "frobnicate(1)", "not honor"):
            with self.assertRaises(ModifierEvalError):
                M.evaluate(bad, facade=self.f)

    def test_empty_raises(self):
        with self.assertRaises(ModifierEvalError):
            M.evaluate("   ", facade=self.f)

    def test_safe_evaluate_returns_default(self):
        self.assertEqual(0, M.safe_evaluate("__import__('os')", facade=self.f))
        self.assertEqual(7, M.safe_evaluate("bogus(", facade=self.f, default=7))
        self.assertEqual(3, M.safe_evaluate("rings.earth", facade=self.f))


class TestEvaluatePredicate(unittest.TestCase):

    def ev(self, expr, **kw):
        return M.evaluate_predicate(expr, facade=kw.pop("facade"))

    def test_boolean_and_comparison(self):
        f = FakeFacade(taint=2, unarmored=True, kihos=["air_fist"])
        self.assertTrue(M.evaluate_predicate("unarmored and not has_kiho('earth_palm')", facade=f))
        self.assertTrue(M.evaluate_predicate("taint > 0", facade=f))
        self.assertFalse(M.evaluate_predicate("taint > 5", facade=f))
        self.assertTrue(M.evaluate_predicate("has_kiho", facade=f))            # bare = owns any
        self.assertTrue(M.evaluate_predicate("has_kiho('air_fist')", facade=f))
        self.assertFalse(M.evaluate_predicate("has_kiho('nope')", facade=f))

    def test_wielding(self):
        f = FakeFacade(weapons={"katana", "wakizashi"})
        self.assertTrue(M.evaluate_predicate("wielding('daisho')", facade=f))
        self.assertTrue(M.evaluate_predicate("wielding('katana')", facade=f))
        f2 = FakeFacade(weapons={"katana"})
        self.assertFalse(M.evaluate_predicate("wielding('daisho')", facade=f2))

    def test_empty_predicate_is_true(self):
        self.assertTrue(M.evaluate_predicate(None, facade=FakeFacade()))
        self.assertTrue(M.evaluate_predicate("", facade=FakeFacade()))


if __name__ == "__main__":
    unittest.main()
