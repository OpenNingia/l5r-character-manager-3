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


# --------------------------------------------------------------------------- #
# Runtime (dynamic) modifiers: materialize ModifierModel-shaped objects from the
# datapack <ModifierDef> records the character currently owns.
# --------------------------------------------------------------------------- #

from l5r.api import get_context  # noqa: E402
import l5r.api.character.merits   # noqa: E402
import l5r.api.character.flaws    # noqa: E402
import l5r.api.character.schools  # noqa: E402
import l5r.api.character.rankadv  # noqa: E402
import l5rdal.query               # noqa: E402

# schema `affects` -> internal ModifierModel.type code. The first block reuses
# the existing engine codes; the second adds new scalar targets (consumed in
# api.rules / api.character).
AFFECTS_TO_TYPE = {
    "any_roll": "anyr", "skill_roll": "skir", "attack_roll": "atkr",
    "damage_roll": "wdmg", "trait_roll": "trat", "ring_roll": "ring",
    "armor_tn": "artn", "reduction": "arrd", "initiative": "init",
    "wound_penalty": "wpen", "health_rank": "hrnk",
    "insight": "insight", "honor": "honor", "glory": "glory",
    "status": "status", "void_max": "void_max",
    "trait_rank": "trait_rank", "ring_rank": "ring_rank",
    "spell_tn_self": "spell_tn_self",
}
_ROLL_AFFECTS = {"any_roll", "skill_roll", "attack_roll", "damage_roll",
                 "trait_roll", "ring_roll", "initiative"}
_DETAIL_PREFIXES = ("skill:", "weapon:", "trait:", "ring:")


class DynamicModifier(object):
    """A ModifierModel-shaped, datapack-derived modifier.

    Duck-typed to what the rules engine reads (`type`, `dtl`, `value`,
    `active`, `reason`). `value` is a live property recomputed from the source
    expressions on each access, so it tracks the current character. These are
    never serialized; `readonly` marks them for the UI, and `toggleable`
    flags the `when`-gated ones whose `active` the user may flip.
    """

    def __init__(self, type, dtl, reason, roll_typed, exprs, bindings,
                 when, active, key, source=None, kind=None):
        self.type = type
        self.dtl = dtl
        self.reason = reason
        self.source = source     # originating record slug
        self.kind = kind
        self.label = None        # resolved display name of the source record
        self.when = when
        self.active = active
        self.key = key
        self.readonly = True
        self.toggleable = (when != "auto")
        self._roll = roll_typed
        self._exprs = exprs
        self._bindings = bindings

    @property
    def value(self):
        f = _make_facade()
        if self._roll:
            return (int(safe_evaluate(self._exprs.get("roll") or "0", self._bindings, f)),
                    int(safe_evaluate(self._exprs.get("keep") or "0", self._bindings, f)),
                    int(safe_evaluate(self._exprs.get("bonus") or "0", self._bindings, f)))
        v = int(safe_evaluate(self._exprs.get("value") or "0", self._bindings, f))
        # The engine stores wound-penalty modifiers as a *reduction* amount
        # (it does `result - value[2]`), whereas the schema value is in the
        # natural direction (negative = reduction). Negate at the boundary.
        if self.type == "wpen":
            v = -v
        return (0, 0, v)


def _make_facade():
    """Facade factory (indirection so tests can inject a fake)."""
    return LiveFacade()


def _record_name(ms):
    """Resolve the human display name of the record a ModifierDef targets, so
    the UI shows e.g. 'Kitsuki's Method' rather than the raw slug. None when it
    cannot be resolved."""
    ds = get_context().ds
    if ds is None:
        return None
    try:
        if ms.kind in ("tech", "path"):
            _school, tech = l5rdal.query.get_tech(ds, ms.target)
            return tech.name if tech else None
        if ms.kind == "kata":
            r = l5rdal.query.get_kata(ds, ms.target)
        elif ms.kind in ("kiho", "tattoo"):
            r = l5rdal.query.get_kiho(ds, ms.target)
        elif ms.kind in ("merit", "ancestor"):
            r = l5rdal.query.get_merit(ds, ms.target)
        elif ms.kind == "flaw":
            r = l5rdal.query.get_flaw(ds, ms.target)
        else:
            return None
        return getattr(r, "name", None) if r else None
    except Exception:
        return None


def _mod_key(target, kind, affects, detail, when):
    return "{0}|{1}|{2}|{3}|{4}".format(target, kind, affects, detail or "", when)


def _owns(target, kind):
    import l5r.api.character as character
    import l5r.api.character.powers as powers
    if kind in ("tech", "path"):
        return character.has_rule(target)
    if kind == "kata":
        return powers.has_kata(target)
    if kind == "kiho":
        return powers.has_kiho(target)
    if kind == "tattoo":
        return target in set(powers.get_all_tattoo())
    if kind in ("merit", "ancestor"):
        return target in {getattr(p, "perk", None) for p in character.merits.get_all()}
    if kind == "flaw":
        return target in {getattr(p, "perk", None) for p in character.flaws.get_all()}
    # mastery / weapon_effect / armor: not yet tracked -> never owned (MVP)
    return False


def _school_rank_for(target, kind):
    """Best-effort 'School Rank' binding for the source's expressions."""
    ds = get_context().ds
    if kind in ("tech", "path") and ds is not None:
        try:
            school, _tech = l5rdal.query.get_tech(ds, target)
            if school is not None:
                return api.character.schools.get_school_rank(school.id)
        except Exception:
            pass
    return _primary_school_rank()


def _primary_school_rank():
    try:
        schools = {r.school for r in api.character.rankadv.get_all() if getattr(r, "school", None)}
        ranks = [api.character.schools.get_school_rank(s) for s in schools]
        if ranks:
            return max(ranks)
    except Exception:
        pass
    try:
        return api.character.insight_rank()
    except Exception:
        return 0


def _resolve_detail(detail):
    """Return (dtl, ok). ok=False means the detail cannot be honored by the MVP
    engine (e.g. a tag: selector) and the modifier should be skipped."""
    if detail is None:
        return None, True
    for pfx in _DETAIL_PREFIXES:
        if detail.startswith(pfx):
            return detail[len(pfx):], True
    if detail.startswith("tag:"):
        return None, False   # tag-scoped roll mods not representable yet
    return detail, True       # bare/legacy detail -> use as-is


def _make_dynamic(ms, mod, bindings):
    if (mod.op or "add") != "add":
        log.api.debug("skip modifier on %s: op=%s not supported yet", ms.target, mod.op)
        return None
    affects = mod.affects
    type_ = AFFECTS_TO_TYPE.get(affects)
    if type_ is None:
        log.api.debug("skip modifier on %s: unknown affects %s", ms.target, affects)
        return None
    if mod.requires and not safe_evaluate_predicate(mod.requires, bindings):
        return None
    dtl, ok = _resolve_detail(mod.detail)
    if not ok:
        log.api.debug("skip modifier on %s: detail %s not supported yet", ms.target, mod.detail)
        return None

    when = mod.when or "auto"
    key = _mod_key(ms.target, ms.kind, affects, mod.detail, when)
    if when == "auto":
        active = True
    else:
        active = bool(get_context().runtime_modifier_state.get(key, False))

    roll_typed = affects in _ROLL_AFFECTS and (mod.value is None)
    if roll_typed:
        exprs = {"roll": mod.roll, "keep": mod.keep, "bonus": mod.bonus}
    else:
        exprs = {"value": mod.value if mod.value is not None else (mod.bonus or "0")}

    return DynamicModifier(type_, dtl, mod.reason, roll_typed, exprs, bindings,
                           when, active, key, source=ms.target, kind=ms.kind)


def build_dynamic_modifiers(filter_type=None):
    """Materialize every dynamic modifier the active character currently owns.

    Pull-based: called from the modifier-consumption sites, recomputed on demand
    (the architecture has no central recompute pass). Never serialized.
    """
    ctx = get_context()
    pc, ds = ctx.pc, ctx.ds
    if pc is None or ds is None:
        return []
    out = []
    for ms in getattr(ds, "modifier_sets", []):
        if not _owns(ms.target, ms.kind):
            continue
        bindings = {"school_rank": _school_rank_for(ms.target, ms.kind)}
        for p in getattr(ms, "params", []):
            bindings[p.name] = 0   # player-chosen magnitude: no input UI yet (MVP)
        label = _record_name(ms)
        for mod in getattr(ms, "mods", []):
            dm = _make_dynamic(ms, mod, bindings)
            if dm is not None:
                dm.label = label
                out.append(dm)
        # <OneOf> and <Substitute> are deferred (need choice UI / formula
        # substitution support in the engine).
    if filter_type:
        out = [x for x in out if x.type == filter_type]
    return out


def effective_modifiers(filter_type=None, pc=None):
    """Return user-defined (static) modifiers plus the datapack-derived dynamic
    ones, optionally filtered by type. This is what the rules engine should
    consume; the editable Modifiers UI keeps using ``pc.get_modifiers`` (static)
    and shows the dynamic ones read-only via ``build_dynamic_modifiers``."""
    if pc is None:
        pc = get_context().pc
    static = pc.get_modifiers(filter_type) if pc is not None else []
    return list(static) + build_dynamic_modifiers(filter_type)


def set_runtime_modifier_active(key, active):
    """Flip the session on/off state of a `when`-gated dynamic modifier."""
    get_context().runtime_modifier_state[key] = bool(active)
