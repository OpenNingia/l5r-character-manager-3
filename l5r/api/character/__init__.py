# -*- coding: utf-8 -*-
# Copyright (C) 2014-2022 Daniele Simonetti
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
__author__ = 'Daniele'

import operator

import l5r.api as api
import l5r.api.data
import l5r.api.rules
import l5r.api.signals
import l5r.models

from l5r.api import get_context

from asq.initiators import query
from asq.selectors import a_

from l5r.util import log


def model():
    """return character model"""
    return get_context().pc


def new():
    """creates new player character model"""
    get_context().pc = l5r.models.AdvancedPcModel()
    get_context().pc.load_default()

    log.api.info("Created new character")
    l5r.api.signals.bus().model_replaced.emit()


def set_model(value):
    """set character model"""
    get_context().pc = value
    l5r.api.signals.bus().model_replaced.emit()


def set_name(value):
    """set the character name (canonical setter; emits on the bus)"""
    get_context().pc.name = value
    set_dirty_flag(True)
    l5r.api.signals.bus().name_changed.emit(value)
    log.api.info(u"set character name: %s", value)


def get_notes():
    """return the character extra notes (rich-text HTML)"""
    pc = get_context().pc
    return pc.extra_notes if pc else ""


def set_notes(value):
    """set the character extra notes (canonical setter; emits on the bus)"""
    pc = get_context().pc
    if pc is None:
        return
    value = value or ""
    if pc.extra_notes == value:
        return
    pc.extra_notes = value
    set_dirty_flag(True)
    l5r.api.signals.bus().notes_changed.emit(value)


_PERSONAL_INFO_KEYS = (
    "sex", "age", "height", "weight", "hair", "eyes",
    "father", "mother", "brothers", "sisters",
    "marsta", "spouse", "childr",
)


def personal_info_keys():
    """return the canonical anagraphic/family property keys"""
    return _PERSONAL_INFO_KEYS


def get_personal_info(key):
    """return a single anagraphic/family property as a string"""
    pc = get_context().pc
    if pc is None:
        return ""
    return pc.get_property(key, "") or ""


def set_personal_info(key, value):
    """set a single anagraphic/family property (canonical setter)"""
    pc = get_context().pc
    if pc is None:
        return
    value = value or ""
    if pc.get_property(key, "") == value:
        return
    pc.set_property(key, value)
    set_dirty_flag(True)
    l5r.api.signals.bus().personal_info_changed.emit()


def get_family_tags():
    """return tags related to the choosen family"""
    if get_family():
        return [get_family(), get_clan()]
    return []


def get_school_tags():
    """return tags related to the character schools"""
    tags_ = []
    for s in api.character.schools.get_all():
        school_ = api.data.schools.get(s)
        if school_:
            tags_ += [school_.id] + school_.tags
    return tags_


def get_tags():
    """return all character tags"""
    return get_family_tags() + get_school_tags()


def get_school_rules():
    """returns school related rules"""

    rules_ = []

    for r in api.character.rankadv.get_all():
        tech_ = api.character.schools.get_tech_by_rank(r.rank)
        if tech_:
            rules_.append(tech_)

    return rules_


def get_perk_rules():
    """return merit/flaw related rules"""
    return [x.rule for x in get_context().pc.advans if getattr(x, 'rule', None) is not None]


def get_rules():
    """return all character tags"""
    return get_school_rules() + get_perk_rules()


def has_tag(tag):
    return tag in get_tags()


def has_rule(tag):
    return tag in get_rules()


def cnt_tag(tag):
    return sum([1 for x in get_tags() if x == tag])


def cnt_rule(tag):
    return sum([1 for x in get_rules() if x == tag])


def has_tag_or_rule(tag):
    return has_tag(tag) or has_rule(tag)


def remove_advancement(adv):
    """remove an advancement, returns True on success"""
    if not get_context().pc or adv not in get_context().pc.advans:
        return False
    get_context().pc.advans.remove(adv)
    log.api.info(u"removed advancement: %s", adv.desc)
    return True


def refund_last_advancement():
    """Pop the head of the advancement stack (the most recently
    purchased entry), refunding its XP cost. Returns the popped
    Advancement instance, or None when the stack is empty.

    Stack-LIFO is the only safe refund order: L5R 4e advancement
    costs scale with the current rank of the trait/skill, so each
    entry's recorded cost is valid only against the state produced
    by every entry beneath it. Removing a non-head entry would
    leave subsequent entries with stale costs.

    Owns the dirty-flag contract (CLAUDE.md: api-level setters set
    the dirty flag) and emits character_refreshed so QML bindings
    re-evaluate.
    """
    pc = get_context().pc
    if not pc or not pc.advans:
        return None
    adv = pc.advans.pop()
    log.api.info(u"refunded advancement: %s (cost %s)", adv.desc, adv.cost)
    set_dirty_flag(True)
    l5r.api.signals.bus().character_refreshed.emit()
    return adv


def reset_advancements():
    """Clear the whole advancement stack, refunding all spent XP and
    returning the character to its freshly-created (rank 1) state.
    Family and school (set at creation, not advancements) are kept.

    Returns the number of entries removed (0 when there was nothing to
    reset). Owns the dirty-flag contract (CLAUDE.md: api-level setters
    set the dirty flag) and emits character_refreshed so QML bindings
    re-evaluate.
    """
    pc = get_context().pc
    if not pc or not pc.advans:
        return 0
    count = len(pc.advans)
    pc.advans = []
    log.api.info(u"reset advancements: cleared %d entries", count)
    set_dirty_flag(True)
    l5r.api.signals.bus().character_refreshed.emit()
    return count


def get_xp_gained_from_flaws():
    """returns the experience gained from disadvantages"""
    return sum([-x.cost for x in get_context().pc.advans if x.type == 'perk' and x.tag == 'flaw'])

def xp():
    """returns the spent experience"""
    if not get_context().pc:
        return 0
    return sum([x.cost for x in get_context().pc.advans if x.cost > 0])


def xp_limit():
    """returns the experience limit"""
    if not get_context().pc:
        return 0
    return get_context().pc.exp_limit + get_xp_gained_from_flaws()


def xp_left():
    """returns the experience left to spend"""
    return xp_limit() - xp()


def get_starting_honor():
    """return the starting honor"""
    school_ = api.data.schools.get(
        api.character.schools.get_first())
    if not school_:
        return 0
    return school_.honor


def honor():
    """returns the honor value"""
    return get_context().pc.honor + get_starting_honor()


def set_honor(value):
    """store the character honor as difference with the starting value"""
    get_context().pc.honor = value - get_starting_honor()
    set_dirty_flag(True)
    l5r.api.signals.bus().character_refreshed.emit()


def get_starting_glory():
    """returns the startin glory"""
    value = 0.0
    if has_rule('fame'):
        value += 1.0
    if not is_monk()[0]:
        value += 1.0
    return value


def glory():
    """returns the glory value"""
    return get_context().pc.glory + get_starting_glory()


def set_glory(value):
    """store the character glory as difference with the starting value"""
    get_context().pc.glory = value - get_starting_glory()
    set_dirty_flag(True)
    l5r.api.signals.bus().character_refreshed.emit()


def get_starting_status():
    """returns the starting status"""
    if has_rule('social_disadvantage'):
        return 0.0
    return 1.0


def status():
    """returns the status value"""
    return get_context().pc.status + get_starting_status()


def set_status(value):
    """store the character status as difference with the starting value"""
    get_context().pc.status = value - get_starting_status()
    set_dirty_flag(True)
    l5r.api.signals.bus().character_refreshed.emit()


def get_starting_infamy():
    """returns the starting infamy"""
    return 0.0


def infamy():
    """returns the infamy value"""
    return get_context().pc.infamy + get_starting_infamy()


def set_infamy(value):
    """store the character infamy as difference with the starting value"""
    get_context().pc.infamy = value - get_starting_infamy()
    set_dirty_flag(True)
    l5r.api.signals.bus().character_refreshed.emit()


def get_starting_taint():
    """returns the starting taint"""
    return 0.0


def taint():
    """returns the taint value"""
    return get_context().pc.taint + get_starting_taint()


def set_taint(value):
    """store the character taint as difference with the starting value"""
    get_context().pc.taint = value - get_starting_taint()
    set_dirty_flag(True)
    l5r.api.signals.bus().character_refreshed.emit()


def trait_rank(trait_id):
    """returns the rank of the given trait"""
    if not get_context().pc:
        return 0

    trait_nm = trait_id
    trait_idx = l5r.models.attrib_from_name(trait_id)

    starting_value_ = get_context().pc.starting_traits[trait_idx]

    family_trait_ = api.data.families.get_family_trait(
        get_family()
    )
    school_trait_ = api.data.schools.get_school_trait(
        get_starting_school()
    )

    total_ = starting_value_ + sum([1 for x in get_context().pc.advans if x.type == 'attrib' and x.attrib == trait_idx])
    if family_trait_ == trait_nm:
        total_ += 1
    if school_trait_ == trait_nm:
        total_ += 1

    return total_


def modified_trait_rank(trait_id):

    trait_nm = trait_id
    if trait_nm == 'void':
        return void_rank()

    base_value_ = trait_rank(trait_id)
    weakness_flaw = 'weak_{0}'.format(trait_nm)

    if has_rule(weakness_flaw):
        return base_value_ - 1
    return base_value_


def ring_rank(ring_id):
    """returns the rank of the given ring"""

    ring_nm = ring_id
    if ring_nm == 'void':
        return void_rank()

    traits = api.data.get_traits_by_ring(ring_id)
    trait_1 = trait_rank(traits[0])
    trait_2 = trait_rank(traits[1])

    return min(trait_1, trait_2)


def void_rank():
    """returns the Void ring rank"""

    trait_nm = 'void'

    starting_value_ = get_context().pc.starting_void
    family_trait_ = api.data.families.get_family_trait(
        get_family()
    )
    school_trait_ = api.data.schools.get_school_trait(
        get_starting_school()
    )

    total_ = starting_value_ + sum([1 for x in get_context().pc.advans if x.type == trait_nm])
    if family_trait_ == trait_nm:
        total_ += 1
    if school_trait_ == trait_nm:
        total_ += 1

    return total_


def get_base_tn():
    """returns the base TN"""
    # reflexes * 5 + 5
    return trait_rank('reflexes') * 5 + 5


def get_armor_tn():
    """returns the armor's TN"""
    return get_context().pc.armor.tn if get_context().pc.armor is not None else 0


def _effective_modifiers(filter_type=None):
    """Static (user) + datapack-derived dynamic modifiers for the active PC.
    Lazy import to avoid an import cycle with the dynamic-modifier builder."""
    from l5r.api.rules.modifiers import effective_modifiers
    return effective_modifiers(filter_type)


def get_armor_tn_mod():
    """return armor TN modifers"""
    return sum(x.value[2] for x in _effective_modifiers('artn') if x.active and len(x.value) > 2)


def _datapack_provides(slug):
    """True if a loaded datapack supplies a <ModifierDef> for this slug. The
    legacy hardcode then yields to the dynamic modifier to avoid double-counting
    (see docs/MODIFIERS_SCHEMA.md section 17)."""
    import l5rdal.query
    ds = get_context().ds
    return bool(ds is not None and l5rdal.query.get_modifiers_for(ds, slug))


def get_base_rd():
    """returns the base RD"""
    # legacy fallback: fires only while no datapack has taken over this effect
    if not _datapack_provides('crab_the_mountain_does_not_move'):
        if has_rule('crab_the_mountain_does_not_move'):
            return ring_rank('earth')
    return 0


def get_armor_rd():
    """returns the armor's RD"""
    return get_context().pc.armor.rd if get_context().pc.armor is not None else 0


def get_full_tn():
    """return the full TN value"""
    return get_base_tn() + get_armor_tn() + get_armor_tn_mod()


def get_armor_rd_mod():
    """return armor RD modifers"""
    return sum(x.value[2] for x in _effective_modifiers('arrd') if x.active and len(x.value) > 2)


def get_full_rd():
    """return the full RD value"""
    return get_armor_rd() + get_base_rd() + get_armor_rd_mod()


def get_armor_name():
    """return the armor name if any"""
    return get_context().pc.armor.name if get_context().pc.armor is not None else api.tr("No Armor")


def get_armor_desc():
    """returns the armor description"""
    return get_context().pc.armor.desc if get_context().pc.armor is not None else u""


def get_armor():
    """return the worn armor (an ArmorOutfit) or None."""
    return get_context().pc.armor


def set_armor(item):
    """wear an armor -- a character wears at most one (owns the dirty
    flag). Replaces the legacy dialogs' direct ``pc.armor = item``."""
    get_context().pc.armor = item
    set_dirty_flag(True)


def clear_armor():
    """take off the worn armor (owns the dirty flag)."""
    get_context().pc.armor = None
    set_dirty_flag(True)


def append_advancement(adv):
    """append an advancement to the advancement list"""
    if get_context().pc:
        log.api.info(u"add advancement: %s", adv.desc)
        get_context().pc.add_advancement(adv)
        return adv
    return None


def purchase_advancement(adv):
    """returns True if there are enought xp to purchase the advancement"""
    if (adv.cost + xp()) > xp_limit():
        log.api.warning(u"not enough xp to purchase advancement: %s. xp left: %d",
                        adv.desc, xp_left())
        return api.data.CMErrors.NOT_ENOUGH_XP

    api.character.append_advancement(adv)

    return api.data.CMErrors.NO_ERROR


def purchase_trait_rank(trait_id):
    """purchase the next rank in a trait"""

    trait_nm = l5r.models.chmodel.attrib_name_from_id(trait_id)

    cur_value = trait_rank(trait_nm)
    new_value = cur_value + 1

    cost = api.rules.get_trait_rank_cost(trait_nm, new_value)

    # build advancement model
    adv = l5r.models.advances.AttribAdv(trait_id, cost)

    adv.desc = (api.tr('{0}, Rank {1} to {2}. Cost: {3} xp')
                .format(trait_nm, cur_value, new_value, adv.cost))

    return purchase_advancement(adv)


def purchase_void_rank():
    """purchase a void rank"""

    cur_value = void_rank()
    new_value = cur_value + 1

    cost = api.rules.get_void_rank_cost(new_value)

    adv = l5r.models.VoidAdv(cost)
    adv.desc = (api.tr('Void Ring, Rank {0} to {1}. Cost: {2} xp')
                .format(cur_value, new_value, adv.cost))

    return purchase_advancement(adv)


def insight():
    """return the calculated insight value"""
    return api.rules.calculate_insight()


def insight_rank(strict=False):
    """returns PC potential insight rank, if strict then return the last finalized rank advancement"""

    if strict:
        last_rank_ = api.character.rankadv.get_last()
        if not last_rank_:
            # todo, when the program will handle zero-ranked characters just return 0
            return 1
        return last_rank_.rank

    value = insight()

    if value > 349:
        return int((value - 349) / 25 + 10)
    if value > 324:
        return 9
    if value > 299:
        return 8
    if value > 274:
        return 7
    if value > 249:
        return 6
    if value > 224:
        return 5
    if value > 199:
        return 4
    if value > 174:
        return 3
    if value > 149:
        return 2
    return 1


def insight_calculation_method():
    """returns PC's insight calculation method"""
    return get_context().pc.insight_calculation


def set_insight_calculation_method(value):
    """set PC's insight calculation method"""
    get_context().pc.insight_calculation = value


def set_family(family_id):
    """set PC family"""

    family_ = api.data.families.get(family_id)
    if family_:
        #get_context().pc.set_family(family_.id, family_.trait, 1, [family_.id, family_.clanid])
        get_context().pc.family = family_.id
        get_context().pc.clan = family_.clanid

        log.api.info(u"set family: %s, clan: %s", family_.id, family_.clanid)
        l5r.api.signals.bus().family_changed.emit(family_.id)
        l5r.api.signals.bus().clan_changed.emit(family_.clanid)
    else:
        log.api.warning(u"family not found: %s", family_id)


def get_clan():
    """get PC clan"""
    family_ = api.data.families.get(get_family())
    if not family_:
        return None
    return family_.clanid


def get_family():
    """get PC family"""
    return get_context().pc.family


def get_starting_school():
    """returns character starting school"""
    return api.character.schools.get_first()


def is_monk():
    """return if pc is a Monk and if its a monk of the brotherhood of shinsei"""
    # is monk ?
    monk_schools = query(api.character.schools.get_all()).where(
        lambda y: api.data.schools.is_monk(y)).to_list()

    is_monk_ = len(monk_schools) > 0
    # is brotherhood monk?
    brotherhood_schools = [
        x for x in monk_schools if 'brotherhood' in api.data.schools.get(x).tags]
    is_brotherhood = len(brotherhood_schools) > 0

    # a friend of the brotherhood pay the same as the brotherhood members
    # fixme, this should be moved from here
    is_brotherhood = is_brotherhood or has_rule(
        'friend_brotherhood')

    return is_monk_, is_brotherhood


def is_ninja():
    """returns True if the character is a ninja"""
    # is ninja?
    return query(api.character.schools.get_all()).where(
        lambda x: api.data.schools.is_ninja(x)).count() > 0


def is_shugenja():
    """returns True if the character is a shugenja"""
    # is shugenja?
    return query(api.character.schools.get_all()).where(
        lambda x: api.data.schools.is_shugenja(x)).count() > 0


def is_bushi():
    """returns True if the character is a shugenja"""
    # is bushi?
    return query(api.character.schools.get_all()).where(
        lambda x: api.data.schools.is_bushi(x)).count() > 0


def is_courtier():
    """returns True if the character is a shugenja"""
    # is courtier?
    return query(api.character.schools.get_all()).where(
        lambda x: api.data.schools.is_courtier(x)).count() > 0


def set_dirty_flag(value):
    """set the character dirty flag"""
    get_context().pc.unsaved = value
    l5r.api.signals.bus().dirty_changed.emit(bool(value))


def notify_character_refreshed():
    """Coarse 'character recomputed' notification. Use after mutations
    that change derived state lacking a dedicated bus signal -- trait
    purchases, void purchases, school changes -- so the QML proxy
    re-emits its bundle signals. A no-op for the QWidget UI, which uses
    a pull (update_from_model) refresh instead."""
    l5r.api.signals.bus().character_refreshed.emit()


def set_exp_limit(value):
    """set the character's experience-point limit (canonical setter)"""
    pc = get_context().pc
    if pc is None:
        return
    value = int(value)
    if pc.exp_limit == value:
        return
    pc.exp_limit = value
    set_dirty_flag(True)
    l5r.api.signals.bus().character_refreshed.emit()
    log.api.info(u"set exp limit: %d", value)


def set_void_points(value):
    """set the character's current Void-points pool (canonical setter)"""
    pc = get_context().pc
    if pc is None:
        return
    value = int(value)
    if pc.void_points == value:
        return
    pc.set_void_points(value)
    set_dirty_flag(True)
    l5r.api.signals.bus().character_refreshed.emit()


def get_health_multiplier():
    """return the wound-level multiplier (default 2, per L5R 4e)"""
    return get_context().pc.health_multiplier


def set_health_multiplier(value):
    """set the wound-level multiplier and mark the character dirty.

    The multiplier scales the seven non-Healthy wound levels (the first
    level is always Earth*5). Values < 1 are rejected because they would
    produce a non-monotonic wound table.
    """
    value = int(value)
    if value < 1:
        raise ValueError("health_multiplier must be >= 1, got %r" % value)

    pc = get_context().pc
    if pc.health_multiplier == value:
        return
    pc.health_multiplier = value
    set_dirty_flag(True)
    l5r.api.signals.bus().character_refreshed.emit()
    log.api.info("set health multiplier to: %d", value)


def get_wounds_taken():
    """return the total wounds (HP damage) currently on the character."""
    pc = get_context().pc
    return int(pc.wounds) if pc else 0


def set_wounds_taken(value):
    """set the total wounds on the character, clamped to [0, max].

    Canonical wounds setter -- mutations here own the dirty flag and the
    character_refreshed signal so the QML proxy and QWidget UI both pick
    up the change. The max is api.rules.get_max_wounds() (the "Out"
    threshold), which depends on Earth ring and health multiplier."""
    pc = get_context().pc
    if pc is None:
        return
    value = max(0, min(int(value), int(api.rules.get_max_wounds())))
    if int(pc.wounds) == value:
        return
    pc.wounds = value
    set_dirty_flag(True)
    l5r.api.signals.bus().character_refreshed.emit()


def damage_health(delta):
    """add ``delta`` to the wounds total (negative heals), clamped."""
    set_wounds_taken(get_wounds_taken() + int(delta))


def get_starting_money():
    """return PC starting money"""
    first_rank_ = api.character.rankadv.get_first()
    if not first_rank_:
        return 0, 0, 0
    return first_rank_.money


def get_money():
    """return PC total money"""
    stored_money_ = get_context().pc.get_property('money', (0, 0, 0))
    starting_money_ = get_starting_money()

    return tuple(map(operator.add, stored_money_, starting_money_))


def set_money(value):
    """store PC money as difference with starting money"""
    starting_money_ = get_starting_money()
    stored_money_ = tuple(map(operator.sub, value, starting_money_))

    get_context().pc.set_property('money', stored_money_)
    set_dirty_flag(True)

    log.api.info(u"set character money to: %s", str(value))

def get_starting_outfit():
    """return the starting outfit for the character"""
    first_rank_ = api.character.rankadv.get_first()
    if first_rank_:
        return first_rank_.outfit
    return []

def set_starting_outfit(outfit):
    """sets the starting outfit for the character"""
    first_rank_ = api.character.rankadv.get_first()
    if first_rank_:
        first_rank_.outfit = outfit
        set_dirty_flag(True)


def get_equipment():
    """return the character's free-form (non-school) equipment list."""
    return get_context().pc.get_property('equip', [])


def set_equipment(items):
    """replace the free-form equipment list (owns the dirty flag)."""
    get_context().pc.set_property('equip', list(items))
    set_dirty_flag(True)


def add_equipment(text):
    """append one free-form equipment entry (owns the dirty flag)."""
    items = get_context().pc.get_property('equip', [])
    items.append(text)
    set_dirty_flag(True)


def get_modifiers():
    """return the character's custom roll/stat modifiers."""
    return get_context().pc.get_modifiers()


def add_modifier(item):
    """add a custom modifier (owns the dirty flag)."""
    get_context().pc.add_modifier(item)
    set_dirty_flag(True)


def remove_modifier(item):
    """remove a custom modifier (owns the dirty flag)."""
    mods = get_context().pc.get_modifiers()
    if item in mods:
        mods.remove(item)
        set_dirty_flag(True)


def touch_modifiers():
    """flag the character dirty after an in-place modifier edit/toggle.

    Modifier rows are mutated in place by the caller (the Qt-side edit
    dialog / active toggle resolves the live ModifierModel and writes its
    fields); this is the setter that owns the dirty flag for that path,
    mirroring api.character.weapons.touch()."""
    set_dirty_flag(True)
