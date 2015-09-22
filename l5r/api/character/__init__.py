# -*- coding: utf-8 -*-
# Copyright (C) 2014 Daniele Simonetti
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

from api import __api
import api.data
import api.rules
import models
import operator

from asq.initiators import query
from asq.selectors import a_

from util import log


def model():
    """return character model"""
    return __api.pc


def new():
    """creates new player character model"""
    __api.pc = models.AdvancedPcModel()
    __api.pc.load_default()

    log.api.info("Created new character")


def set_model(value):
    """set character model"""
    __api.pc = value


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
    for s in api.character.schools.get_all():
        school_ = api.data.schools.get(s)
        if school_:
            rules_ += [x.id for x in school_.techs]
    return rules_


def get_perk_rules():
    """return merit/flaw related rules"""
    return [x.rule for x in __api.pc.advans if hasattr(x, 'rule')]


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
    if not __api.pc or adv not in __api.pc.advans:
        return False
    __api.pc.advans.remove(adv)
    log.api.info(u"removed advancement: %s", adv.desc)
    return True


def xp():
    """returns the spent experience"""
    if not __api.pc:
        return 0
    return sum([x.cost for x in __api.pc.advans])


def xp_limit():
    """returns the experience limit"""
    if not __api.pc:
        return 0
    return __api.pc.exp_limit


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
    return __api.pc.honor + get_starting_honor()


def set_honor(value):
    """store the character honor as difference with the starting value"""
    __api.pc.honor = value - get_starting_honor()


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
    return __api.pc.glory + get_starting_glory()


def set_glory(value):
    """store the character glory as difference with the starting value"""
    __api.pc.glory = value - get_starting_glory()


def get_starting_status():
    """returns the starting status"""
    if has_rule('social_disadvantage'):
        return 0.0
    return 1.0


def status():
    """returns the status value"""
    return __api.pc.status + get_starting_status()


def set_status(value):
    """store the character status as difference with the starting value"""
    __api.pc.status = value - get_starting_status()


def get_starting_infamy():
    """returns the starting infamy"""
    return 0.0


def infamy():
    """returns the infamy value"""
    return __api.pc.infamy + get_starting_infamy()


def set_infamy(value):
    """store the character infamy as difference with the starting value"""
    __api.pc.infamy = value - get_starting_infamy()


def get_starting_taint():
    """returns the starting taint"""
    return 0.0


def taint():
    """returns the taint value"""
    return __api.pc.taint + get_starting_taint()


def set_taint(value):
    """store the character taint as difference with the starting value"""
    __api.pc.taint = value - get_starting_taint()


def trait_rank(trait_id):
    """returns the rank of the given trait"""
    if not __api.pc:
        return 0

    trait_nm = trait_id
    trait_idx = models.attrib_from_name(trait_id)

    starting_value_ = __api.pc.starting_traits[trait_idx]

    family_trait_ = api.data.families.get_family_trait(
        get_family()
    )
    school_trait_ = api.data.schools.get_school_trait(
        get_starting_school()
    )

    total_ = starting_value_ + sum([1 for x in __api.pc.advans if x.type == 'attrib' and x.attrib == trait_idx])
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

    starting_value_ = __api.pc.starting_void
    family_trait_ = api.data.families.get_family_trait(
        get_family()
    )
    school_trait_ = api.data.schools.get_school_trait(
        get_starting_school()
    )

    total_ = starting_value_ + sum([1 for x in __api.pc.advans if x.type == trait_nm])
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
    return __api.pc.armor.tn if __api.pc.armor is not None else 0


def get_armor_tn_mod():
    """return armor TN modifers"""
    return sum(x.value[2] for x in __api.pc.get_modifiers('artn') if x.active and len(x.value) > 2)


def get_base_rd():
    """returns the base RD"""
    if has_rule('crab_the_mountain_does_not_move'):
        return ring_rank('earth')
    return 0


def get_armor_rd():
    """returns the armor's RD"""
    return __api.pc.armor.rd if __api.pc.armor is not None else 0


def get_full_tn():
    """return the full TN value"""
    return get_base_tn() + get_armor_tn() + get_armor_tn_mod()


def get_armor_rd_mod():
    """return armor RD modifers"""
    return sum(x.value[2] for x in __api.pc.get_modifiers('arrd') if x.active and len(x.value) > 2)


def get_full_rd():
    """return the full RD value"""
    return get_armor_rd() + get_base_rd() + get_armor_rd_mod()


def get_armor_name():
    """return the armor name if any"""
    return __api.pc.armor.name if __api.pc.armor is not None else api.tr("No Armor")


def get_armor_desc():
    """returns the armor description"""
    return __api.pc.armor.desc if __api.pc.armor is not None else u""


def append_advancement(adv):
    """append an advancement to the advancement list"""
    if __api.pc:
        log.api.info(u"add advancement: %s", adv.desc)
        __api.pc.add_advancement(adv)
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
    cur_value = trait_rank(trait_id)
    new_value = cur_value + 1

    trait_nm = models.chmodel.attrib_name_from_id(trait_id)
    cost = api.rules.get_trait_rank_cost(trait_nm, new_value)

    # build advancement model
    adv = models.advances.AttribAdv(trait_id, cost)

    adv.desc = (api.tr('{0}, Rank {1} to {2}. Cost: {3} xp')
                .format(trait_nm, cur_value, new_value, adv.cost))

    return purchase_advancement(adv)


def purchase_void_rank():
    """purchase a void rank"""

    cur_value = void_rank()
    new_value = cur_value + 1

    cost = api.rules.get_void_rank_cost(new_value)

    adv = models.VoidAdv(cost)
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
    return __api.pc.insight_calculation


def set_insight_calculation_method(value):
    """set PC's insight calculation method"""
    __api.pc.insight_calculation = value


def set_family(family_id):
    """set PC family"""

    family_ = api.data.families.get(family_id)
    if family_:
        #__api.pc.set_family(family_.id, family_.trait, 1, [family_.id, family_.clanid])
        __api.pc.family = family_.id
        __api.pc.clan = family_.clanid

        log.api.info(u"set family: %s, clan: %s", family_.id, family_.clanid)
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
    return __api.pc.family


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
    __api.pc.unsaved = value


def get_starting_money():
    """return PC starting money"""
    first_rank_ = api.character.rankadv.get_first()
    if not first_rank_:
        return 0, 0, 0
    return first_rank_.money


def get_money():
    """return PC total money"""
    stored_money_ = __api.pc.get_property('money', (0, 0, 0))
    starting_money_ = get_starting_money()

    return tuple(map(operator.add, stored_money_, starting_money_))


def set_money(value):
    """store PC money as difference with starting money"""
    starting_money_ = get_starting_money()
    stored_money_ = tuple(map(operator.sub, value, starting_money_))

    __api.pc.set_property('money', stored_money_)
    set_dirty_flag(True)

    log.api.info(u"set character money to: %s", str(value))
