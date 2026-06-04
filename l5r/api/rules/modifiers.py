# -*- coding: utf-8 -*-
# Copyright (C) 2014-2026 Daniele Simonetti
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.

"""Sandboxed evaluator for the declarative stat-modifier DSL.

This is the runtime counterpart of the datapack schema documented in
``docs/MODIFIERS_SCHEMA.md`` (datapacks repo) and validated by
``scripts/packlib.py`` there. It evaluates a *value* expression (arithmetic over
a read-only character facade) or a *requires* predicate (booleans over an
equipment/state facade), refusing anything outside a strict AST whitelist.

The facade is injectable so the evaluator can be unit-tested without building a
full character; the default :class:`LiveFacade` reads the active character via
``l5r.api.character`` accessors.
"""

import ast
import math

import l5r.api as api
import l5r.api.character
import l5r.api.character.skills
import l5r.api.character.powers
from l5r.util import log


class ModifierEvalError(Exception):
    """Raised when an expression is malformed or steps outside the whitelist."""


# Attribute roots: rings.<x>, traits.<x>, skills.<x>
_ATTR_ROOTS = ("rings", "traits", "skills")

# Bare facade names usable in a value expression.
_VALUE_BARE = ("insight_rank", "honor", "glory", "status", "taint")
# Extra bare names usable only inside a requires predicate.
_PRED_BARE = ("unarmored", "in_light_armor", "in_heavy_armor",
              "has_kiho", "has_tattoo")

_VALUE_FUNCS = ("min", "max", "floor", "ceil", "abs", "round",
                "skill", "merit_rank", "flaw_rank")
_PRED_FUNCS = ("wielding", "has_kiho", "has_tattoo") + _VALUE_FUNCS


class LiveFacade(object):
    """Read-only view of the active character backing the DSL names.

    Every accessor is resolved lazily against ``l5r.api.character`` so the
    facade always reflects the current context's PC.
    """

    # -- numeric facade -----------------------------------------------------
    def ring(self, ring_id):
        return api.character.ring_rank(ring_id)

    def trait(self, trait_id):
        return api.character.modified_trait_rank(trait_id)

    def skill(self, skill_id):
        return api.character.skills.get_skill_rank(skill_id)

    @property
    def insight_rank(self):
        return api.character.insight_rank()

    @property
    def honor(self):
        return int(api.character.honor())

    @property
    def glory(self):
        return int(api.character.glory())

    @property
    def status(self):
        return int(api.character.status())

    @property
    def taint(self):
        return int(api.character.taint())

    def merit_rank(self, merit_id):
        return _perk_rank(api.character.merits.get_all(), merit_id)

    def flaw_rank(self, flaw_id):
        return _perk_rank(api.character.flaws.get_all(), flaw_id)

    # -- predicate facade ---------------------------------------------------
    @property
    def unarmored(self):
        return api.character.get_armor() is None

    @property
    def in_light_armor(self):
        return _armor_has_tag("light")

    @property
    def in_heavy_armor(self):
        return _armor_has_tag("heavy")

    @property
    def has_tattoo(self):
        return bool(api.character.powers.get_all_tattoo())

    def has_kiho(self, kiho_id=None):
        kihos = api.character.powers.get_all_kiho()
        if kiho_id is None:
            return bool(kihos)
        return any(getattr(k, "id", k) == kiho_id for k in kihos)

    def wielding(self, what):
        # The model has no "equipped" flag, so this resolves to "owns a weapon
        # matching <what>" (by name or tag). 'daisho' = owns katana + wakizashi.
        names, tags = _owned_weapon_names_tags()
        if what == "daisho":
            return ("katana" in names) and ("wakizashi" in names)
        return (what in names) or (what in tags)


def _perk_rank(perks, perk_id):
    """Best-effort rank of an owned merit/flaw: its declared rank if present,
    otherwise the number of times it was taken; 0 if not owned."""
    matches = [p for p in perks if getattr(p, "perk", getattr(p, "id", None)) == perk_id]
    if not matches:
        return 0
    ranks = [getattr(p, "rank", None) for p in matches]
    ranks = [r for r in ranks if isinstance(r, int)]
    return max(ranks) if ranks else len(matches)


def _armor_has_tag(tag):
    armor = api.character.get_armor()
    if armor is None:
        return False
    tags = getattr(armor, "tags", None) or []
    return tag in tags


def _owned_weapon_names_tags():
    names, tags = set(), set()
    try:
        for w in api.character.weapons.get_all():
            nm = getattr(w, "name", None)
            if nm:
                names.add(nm)
            for t in (getattr(w, "tags", None) or []):
                tags.add(t)
    except Exception:
        pass
    return names, tags


_BINOPS = {
    ast.Add: lambda a, b: a + b,
    ast.Sub: lambda a, b: a - b,
    ast.Mult: lambda a, b: a * b,
    ast.Div: lambda a, b: a / b,
    ast.FloorDiv: lambda a, b: a // b,
}

_FUNCS = {
    "min": min, "max": max, "abs": abs, "round": round,
    "floor": lambda x: int(math.floor(x)),
    "ceil": lambda x: int(math.ceil(x)),
}


def _eval(node, facade, bindings, predicate):
    if isinstance(node, ast.Expression):
        return _eval(node.body, facade, bindings, predicate)

    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float, str)):
            return node.value
        raise ModifierEvalError("constant of type {0} not allowed".format(
            type(node.value).__name__))

    if isinstance(node, ast.BinOp):
        op = _BINOPS.get(type(node.op))
        if op is None:
            raise ModifierEvalError("operator {0} not allowed".format(
                type(node.op).__name__))
        return op(_eval(node.left, facade, bindings, predicate),
                  _eval(node.right, facade, bindings, predicate))

    if isinstance(node, ast.UnaryOp):
        if isinstance(node.op, ast.USub):
            return -_eval(node.operand, facade, bindings, predicate)
        if isinstance(node.op, ast.UAdd):
            return +_eval(node.operand, facade, bindings, predicate)
        if isinstance(node.op, ast.Not):
            if not predicate:
                raise ModifierEvalError("'not' is only allowed in predicates")
            return not _eval(node.operand, facade, bindings, predicate)
        raise ModifierEvalError("unary {0} not allowed".format(type(node.op).__name__))

    if predicate and isinstance(node, ast.BoolOp):
        vals = [_eval(v, facade, bindings, predicate) for v in node.values]
        if isinstance(node.op, ast.And):
            return all(vals)
        return any(vals)

    if predicate and isinstance(node, ast.Compare):
        left = _eval(node.left, facade, bindings, predicate)
        for op, comp in zip(node.ops, node.comparators):
            right = _eval(comp, facade, bindings, predicate)
            if not _compare(op, left, right):
                return False
            left = right
        return True

    if isinstance(node, ast.Attribute):
        base = node.value
        if not isinstance(base, ast.Name) or base.id not in _ATTR_ROOTS:
            raise ModifierEvalError("attribute access only on rings/traits/skills")
        if base.id == "rings":
            return facade.ring(node.attr)
        if base.id == "traits":
            return facade.trait(node.attr)
        return facade.skill(node.attr)

    if isinstance(node, ast.Name):
        return _resolve_name(node.id, facade, bindings, predicate)

    if isinstance(node, ast.Call):
        return _eval_call(node, facade, bindings, predicate)

    raise ModifierEvalError("syntax element {0} not allowed".format(type(node).__name__))


def _compare(op, left, right):
    if isinstance(op, ast.Eq):
        return left == right
    if isinstance(op, ast.NotEq):
        return left != right
    if isinstance(op, ast.Lt):
        return left < right
    if isinstance(op, ast.LtE):
        return left <= right
    if isinstance(op, ast.Gt):
        return left > right
    if isinstance(op, ast.GtE):
        return left >= right
    raise ModifierEvalError("comparison operator not allowed")


def _resolve_name(name, facade, bindings, predicate):
    if bindings and name in bindings:
        return bindings[name]
    if name in _VALUE_BARE:
        return getattr(facade, name)
    if predicate and name in _PRED_BARE:
        attr = getattr(facade, name)
        # has_kiho is a method (callable); bare use means "owns any"
        return attr() if callable(attr) else attr
    raise ModifierEvalError("unknown name '{0}'".format(name))


def _eval_call(node, facade, bindings, predicate):
    if not isinstance(node.func, ast.Name):
        raise ModifierEvalError("only simple function calls are allowed")
    fname = node.func.id
    if node.keywords:
        raise ModifierEvalError("keyword arguments are not allowed")
    allowed = _PRED_FUNCS if predicate else _VALUE_FUNCS
    if fname not in allowed:
        raise ModifierEvalError("unknown function '{0}'".format(fname))
    args = [_eval(a, facade, bindings, predicate) for a in node.args]

    if fname in _FUNCS:
        return _FUNCS[fname](*args)
    if fname == "skill":
        return facade.skill(*args)
    if fname == "merit_rank":
        return facade.merit_rank(*args)
    if fname == "flaw_rank":
        return facade.flaw_rank(*args)
    if fname == "wielding":
        return facade.wielding(*args)
    if fname == "has_kiho":
        return facade.has_kiho(*args)
    if fname == "has_tattoo":
        return facade.has_tattoo
    raise ModifierEvalError("unknown function '{0}'".format(fname))


def _parse(expr):
    try:
        return ast.parse(expr, mode="eval")
    except SyntaxError as exc:
        raise ModifierEvalError("not parseable: {0}".format(exc.msg))


def evaluate(expr, bindings=None, facade=None):
    """Evaluate a numeric *value* expression. Returns an int/float.

    `bindings` supplies context-specific names (e.g. ``school_rank`` and any
    ``<Param>`` values). Raises :class:`ModifierEvalError` on bad input.
    """
    if expr is None or str(expr).strip() == "":
        raise ModifierEvalError("empty expression")
    if facade is None:
        facade = LiveFacade()
    return _eval(_parse(expr), facade, bindings or {}, predicate=False)


def evaluate_predicate(expr, bindings=None, facade=None):
    """Evaluate a `requires` boolean predicate. Returns a bool."""
    if expr is None or str(expr).strip() == "":
        return True
    if facade is None:
        facade = LiveFacade()
    return bool(_eval(_parse(expr), facade, bindings or {}, predicate=True))


def safe_evaluate(expr, bindings=None, facade=None, default=0):
    """Evaluate, but never raise: log and return `default` on error. Used by the
    runtime so a single malformed modifier cannot break the whole sheet."""
    try:
        return evaluate(expr, bindings, facade)
    except Exception as exc:
        log.api.warning("modifier value '%s' failed to evaluate: %s", expr, exc)
        return default


def safe_evaluate_predicate(expr, bindings=None, facade=None, default=False):
    try:
        return evaluate_predicate(expr, bindings, facade)
    except Exception as exc:
        log.api.warning("modifier predicate '%s' failed to evaluate: %s", expr, exc)
        return default
