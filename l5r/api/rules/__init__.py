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

import re

import l5r.api as api
import l5r.api.data
import l5r.api.character

from l5r.models import chmodel
from l5r.api import __api
from l5r.util import log


def get_trait_cost(trait_nm):
    """return the base multiplier to purchase the given trait"""
    if not __api.pc:
        return 0
    trait_id = chmodel.attrib_from_name(trait_nm)
    return __api.pc.get_attrib_cost(trait_id)


def get_void_cost():
    """return the base multiplier to increase Void ring"""
    if not __api.pc:
        return 0
    return __api.pc.void_cost


def get_trait_rank_cost(trait_nm, new_value):
    """purchasing a trait cost new_value * trait_cost"""
    cost = new_value * get_trait_cost(trait_nm)
    ring = api.data.get_trait_ring(trait_nm)

    elemental_bless = "elem_bless_{}".format(ring.id)
    if api.character.has_rule(elemental_bless):
        cost -= 1

    return cost


def get_void_rank_cost(new_value):
    """purchasing a void rank cost new_value * void_cost"""
    cost = new_value * get_void_cost()
    if api.character.has_rule('enlightened'):
        cost -= 2
    return cost


def get_skill_rank_cost(skill_id, new_value):
    """purchasing a skill rank will cost new_value"""
    skill_ = api.data.skills.get(skill_id)
    if not skill_:
        return 0

    type_ = skill_.type

    if (api.character.has_rule('obtuse') and
            type_ == 'high' and
            skill_id != 'investigation' and
            skill_id != 'medicine'):

        # double the cost for high skill
        # other than medicine and investigation
        return new_value * 2

    return new_value


def parse_rtk(rtk):
    """parse a string in the format roll/keep"""
    tk = rtk.split('k')
    if len(tk) != 2:
        return 0, 0
    # the sign of the first commands
    sign = -1 if int(tk[0]) < 0 else 1
    return int(tk[0]), int(tk[1]) * sign


def parse_rtk_with_bonus(rtk):
    """parse a string in the format roll/keep plus a numeric bonus"""
    # 3k2+1
    rtk = rtk.replace(' ', '')
    #print('parsing ' + rtk)
    if 'k' not in rtk:
        irtk = int(rtk)
        if irtk != 0:
            sign = '+' if irtk > 0 else '-'
            return parse_rtk_with_bonus('0k0' + sign + str(abs(irtk)))
        return 0, 0, 0
    m = re.match('([+-]?\\d{1,2})k(\\d{1,2})([+-]?\\d*)', rtk)
    if not m:
        return 0, 0, 0
    r, k, b = m.groups(1)
    sign = -1 if int(r) < 0 else 1
    try:
        return int(r), int(k) * sign, int(b)
    except:
        return int(r), int(k) * sign, 0


def format_rtk_t(rtk):
    """format a tuple as roll/keep string"""
    if len(rtk) == 3:
        return format_rtk(rtk[0], rtk[1], rtk[2])
    else:
        return format_rtk(rtk[0], rtk[1])


def format_rtk(r, k, bonus=0):
    """format a tuple as roll/keep string, with an optional numeric bonus"""
    if bonus:
        sign_chr = '-' if bonus < 0 else '+'
        if r == k == 0:
            return '%s%d' % (sign_chr, abs(bonus))
        return '%dk%d %s %d' % (r, abs(k), sign_chr, abs(bonus))
    else:
        return '%dk%d' % (r, abs(k))


def insight_calculation_1():
    """Default insight calculation method = Rings*10+Skills+SpecialPerks"""

    n = 0
    for r in api.data.rings():
        n += api.character.ring_rank(r) * 10

    for s in api.character.skills.get_all():
        n += api.character.skills.get_skill_rank(s)

    n += 3 * api.character.cnt_rule('ma_insight_plus_3')
    n += 7 * api.character.cnt_rule('ma_insight_plus_7')

    return n


def insight_calculation_2():
    """Another insight calculation method. Similar to 1, but ignoring
       rank 1 skills
    """

    n = 0
    for r in api.data.rings():
        n += api.character.ring_rank(r) * 10

    for s in api.character.skills.get_all():
        sk = api.character.skills.get_skill_rank(s)
        if sk > 1:
            n += sk

    n += 3 * api.character.cnt_rule('ma_insight_plus_3')
    n += 7 * api.character.cnt_rule('ma_insight_plus_7')

    return n


def insight_calculation_3():
    """Another insight calculation method. Similar to 2, but
       school skill are counted even if rank 1
    """

    n = 0
    for r in api.data.rings():
        n += api.character.ring_rank(r) * 10

    for s in api.character.skills.get_all():
        sk = api.character.skills.get_skill_rank(s)
        if sk > 1 or api.character.skills.is_starter(s):
            n += sk

    n += 3 * api.character.cnt_rule('ma_insight_plus_3')
    n += 7 * api.character.cnt_rule('ma_insight_plus_7')

    return n


def split_decimal(value):
    """given a floating point number returns a tuple with the integer part and the decimal part"""
    import decimal
    decimal.getcontext().prec = 2
    d = decimal.Decimal(value)
    i = int(d)
    return i, d - i


def calculate_base_attack_roll(pc, weap):
    """calculate the base attack roll for a given weapon"""

    # base attack roll is calculated
    # as xky where x is agility + weapon_skill_rank
    # and y is agility

    attrib = 'agility'
    if weap.skill_nm == 'Kyujutsu':
        attrib = 'reflexes'

    trait = api.character.modified_trait_rank(attrib)
    skill = 0
    if weap.skill_id:
        skill = api.character.skills.get_skill_rank(weap.skill_id)
        log.rules.info(u"calc base atk. trait: {0}, weap: {1}, skill: {2}, rank: {3}"
                       .format(trait, weap.name, weap.skill_nm, skill))

    return trait + skill, trait


def calculate_mod_attack_roll(pc, weap):
    """calculate the final attack roll for a given weapon"""

    atk_r, atk_k = calculate_base_attack_roll(pc, weap)
    r_mod = 0
    k_mod = 0

    # any roll bonuses
    anyr = pc.get_modifiers('anyr')
    for x in anyr:
        if x.active:
            r_mod += x.value[0]
            k_mod += x.value[1]

    # skill roll bonuses
    skir = pc.get_modifiers('skir')
    for x in skir:
        if x.active and x.dtl == weap.skill_nm:
            r_mod += x.value[0]
            k_mod += x.value[1]

    # weapon only modifiers to attack roll
    atkr = pc.get_modifiers('atkr')
    for x in atkr:
        if x.active and x.dtl == weap.name:
            r_mod += x.value[0]
            k_mod += x.value[1]

    return atk_r + r_mod, atk_k + k_mod


def calculate_base_damage_roll(pc, weap):
    """calculate the base damage roll for a given weapon"""

    # base damage roll is calculated
    # as xky where x is strength + weapon_damage
    # and y is strength

    attrib = 'strength'
    trait = api.character.modified_trait_rank(attrib)
    weap_str = 0
    try:
        weap_str = int(weap.strength)
    except:
        weap_str = 0

    if 'ranged' in weap.tags and weap_str > 0:
        # ranged calculation is different
        # a weapon does have its own strength
        trait = min(weap_str, trait)

    drr, drk = parse_rtk(weap.dr)

    return trait + drr, drk


def calculate_mod_damage_roll(pc, weap):
    """calculate the final damage roll for a given weapon"""

    dmg_r, dmg_k = calculate_base_damage_roll(pc, weap)
    r_mod = 0
    k_mod = 0
    flat_bonus = 0

    # any roll bonuses
    anyr = pc.get_modifiers('anyr')
    for x in anyr:
        if x.active:
            r_mod += x.value[0]
            k_mod += x.value[1]

    # damage roll bonuses
    wdmg = pc.get_modifiers('wdmg')
    for x in wdmg:
        if x.active and x.dtl == weap.name:
            r_mod += x.value[0]
            k_mod += x.value[1]
            flat_bonus += x.value[2]

    return dmg_r + r_mod, dmg_k + k_mod, flat_bonus


def calculate_base_skill_roll(pc, skill):
    """calculate the base skill roll for a given skill"""

    # base skill roll is calculated
    # as xky where x is skill value + trait value
    # and y is trait

    trait = skill.trait
    trait_value = api.character.modified_trait_rank(trait)
    skill_value = api.character.skills.get_skill_rank(skill.id)

    return DicePool().from_values(roll=skill_value + trait_value,
                                  keep=trait_value)


def calculate_mod_skill_roll(pc, skill):
    """calculate the final skill roll for a given skill"""

    base_roll = calculate_base_skill_roll(pc, skill)

    smod = pc.get_modifiers('skir')
    for x in smod:
        if x.active and x.dtl == skill.name:
            m = DicePool().from_tuple(x.value)
            base_roll += m
    return base_roll


def calculate_kiho_cost(kiho_id):

    kiho = api.data.powers.get_kiho(kiho_id)

    if not kiho:
        return 0

    from math import ceil

    # tattoos are free as long as you're eligible
    if 'tattoo' in kiho.tags:
        return 0

    cost_mult = 1

    is_monk, is_brotherhood = api.character.is_monk()
    is_ninja = api.character.is_ninja()
    is_shugenja = api.character.is_shugenja()

    if is_brotherhood:
        cost_mult = 1  # 1px / mastery
    elif is_monk:
        cost_mult = 1.5
    elif is_shugenja:
        cost_mult = 2
    elif is_ninja:
        cost_mult = 2

    return int(ceil(kiho.mastery * cost_mult))


class DicePool(object):
    """represents a dice pool"""
    def __init__(self):
        self.roll = 0
        self.keep = 0
        self.flat = 0

    def from_string(self, string):
        r, k, f = parse_rtk_with_bonus(string)
        self.from_values(r, k, f)
        return self

    def from_values(self, roll=0, keep=0, flat=0):
        self.roll = roll
        self.keep = abs(keep)
        self.flat = flat
        return self

    def from_tuple(self, rkf):
        if len(rkf) > 2:
            return self.from_values(rkf[0], rkf[1], rkf[2])
        return self.from_values(rkf[0], rkf[1])

    def normalize(self):
        pass

    def __str__(self):
        return format_rtk(self.roll, self.keep, self.flat)

    def __sub__(self, b):
        # a - b

        c = DicePool().from_values(self.roll, self.keep, self.flat)
        if isinstance(b, DicePool):
            c.roll -= b.roll
            c.keep -= b.keep
            c.flat -= b.flat
        else:
            c.flat -= b
        c.normalize()
        return c

    def __add__(self, b):
        # self + b

        c = DicePool().from_values(self.roll, self.keep, self.flat)
        if isinstance(b, DicePool):
            c.roll += b.roll
            c.keep += b.keep
            c.flat += b.flat
        else:
            c.flat += b

        c.normalize()
        return c


def calculate_insight():
    """calculate the insight value using the given method"""

    method = api.character.insight_calculation_method()

    if method == 3:
        return insight_calculation_3()
    if method == 2:
        return insight_calculation_2()
    return insight_calculation_1()


def get_base_initiative():
    """returns the base initiative"""
    return (api.character.insight_rank() +
            api.character.trait_rank('reflexes'),
            api.character.trait_rank('reflexes'))


def get_init_modifiers():
    """returns initiative modifiers"""
    r, k, b = 0, 0, 0
    mods = [x for x in
            __api.pc.get_modifiers('anyr') + __api.pc.get_modifiers('init')
            if x.active]
    for m in mods:
        r += m.value[0]
        k += m.value[1]
        if len(m.value) > 2:
            b += m.value[2]
    return r, k, b


def get_tot_initiative():
    """returns total initiative"""
    r, k = get_base_initiative()
    b = 0
    r1, k1, b1 = get_init_modifiers()
    return r + r1, k + k1, b + b1


def get_wound_penalties(index):
    WOUND_PENALTIES_VALUES = [0, 3, 5, 10, 15, 20, 40]
    result = WOUND_PENALTIES_VALUES[index]

    if api.character.has_rule('strength_of_earth'):
        # Advantage: Strength of Earh (Core, pg154)
        result = max(0, result-3)

    if api.character.has_rule('monkey_tokus_lesson'):
        # Technique: Toku's Lesson (Core, pg222)
        reduction = (api.character.insight_rank() * 2) + api.character.trait_rank('willpower')
        result = max(0, result-reduction)

    for x in __api.pc.get_modifiers('wpen'):
        if x.active:
            result = max(0, result - x.value[2])

    return result


def get_health_rank(idx):
    """return the value for the given health rank"""
    earth_rank = api.character.ring_rank('earth')
    if idx == 0:
        return earth_rank * 5 + get_health_rank_mod()
    return earth_rank * __api.pc.health_multiplier + get_health_rank_mod()


def get_health_rank_mod():
    """return health rank modifiers"""
    mod = 0
    if api.character.has_rule('crane_the_force_of_honor'):
        mod = max(1, int(api.character.honor() - 4))

    for x in __api.pc.get_modifiers('hrnk'):
        if x.active and len(x.value) > 2:
            mod += x.value[2]
    return mod


def get_max_wounds():
    """return total health"""
    max_ = 0
    for i in range(0, 8):
        max_ += get_health_rank(i)
    return max_


def get_wound_heal_rate():
    """return the wound heal rate"""
    return api.character.modified_trait_rank('stamina') * 2 + api.character.insight_rank()


def get_wounds_table():
    """
    Returns the wounds table with three possible variants:
        * increment
        * total
        * stacked

    :return list(tuple(int, int, int)):
        Return a list with 8 elements, each element containing thrree values for wounds: the increments, the total
        and the stacked value.
    """

    if not __api.pc:
        return

    tot_wounds = __api.pc.wounds
    cur_wounds = tot_wounds
    increments = [get_health_rank(i) for i in range(0, 8)]
    total = sum(increments)

    result = []
    stacked = 0
    empty = cur_wounds == 0
    for i in increments:
        stacked += i

        # inc_wounds
        inc_wounds = min(cur_wounds, i)

        # total_wounds
        total_wounds = max(0, i - cur_wounds)

        # stacked_wounds
        if empty:
            stacked_wounds = 0
        else:
            stacked_wounds = min(stacked, tot_wounds)
        empty = empty or tot_wounds <= stacked

        cur_wounds -= inc_wounds

        result.append(
            (
                i,
                total,
                stacked,
                inc_wounds,
                total_wounds,
                stacked_wounds,
            )
        )
        total -= i
    return result
