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


def set_model(model):
    """set character model"""
    __api.pc = model


def has_tag(tag):
    return tag in __api.pc.tags


def has_rule(tag):
    return __api.pc.has_rule(tag)


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
    return __api.pc.get_px()


def xp_limit():
    """returns the experience limit"""
    if not __api.pc:
        return 0
    return __api.pc.exp_limit


def xp_left():
    """returns the experience left to spend"""
    return xp_limit() - xp()


def trait_rank(trait_id):
    """returns the rank of the given trait"""
    if not __api.pc:
        return 0

    if isinstance(trait_id, str):
        ring_id = models.attrib_from_name(trait_id)

    return __api.pc.get_attrib_rank(trait_id)


def ring_rank(ring_id):
    """returns the rank of the given ring"""
    if not __api.pc:
        return 0

    if isinstance(ring_id, str):
        ring_id = models.ring_from_name(ring_id)

    return __api.pc.get_attrib_rank(ring_id)


def void_rank():
    """returns the Void ring rank"""
    if not __api.pc:
        return 0
    return __api.pc.get_void_rank()


def append_advancement(adv):
    if __api.pc:
        log.api.info(u"add advancement: %s", adv.desc)
        __api.pc.add_advancement(adv)


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
    cur_value = void_rank()
    new_value = cur_value + 1

    cost = api.rules.get_void_rank_cost(new_value)

    adv = models.VoidAdv(cost)
    adv.desc = (api.tr('Void Ring, Rank {0} to {1}. Cost: {2} xp')
                .format(cur_value, new_value, adv.cost))

    return purchase_advancement(adv)


def insight_rank():
    """returns PC's insight rank"""
    return __api.pc.get_insight_rank()


def set_family(family_id):
    """set PC family"""

    family_ = api.data.families.get(family_id)
    if family_:
        __api.pc.set_family(family_.id, family_.trait, 1, [family_.id, family_.clanid])
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


def is_monk():
    """return if pc is a Monk and if its a monk of the brotherhood of shinsei"""
    # is monk ?
    monk_schools = api.character.schools.get_schools_by_tag('monk')

    is_monk = len(monk_schools) > 0
    # is brotherhood monk?
    brotherhood_schools = [
        x for x in monk_schools if 'brotherhood' in api.data.schools.get(x).tags]
    is_brotherhood = len(brotherhood_schools) > 0

    # a friend of the brotherhood pay the same as the brotherhood members
    # fixme, this should be moved from here
    is_brotherhood = is_brotherhood or has_rule(
        'friend_brotherhood')

    return is_monk, is_brotherhood


def is_ninja():
    """returns True if the character is a ninja"""
    # is ninja?
    return len(api.character.schools.get_schools_by_tag('ninja')) > 0


def is_shugenja():
    """returns True if the character is a shugenja"""
    # is shugenja?
    return len(api.character.schools.get_schools_by_tag('shugenja')) > 0


def is_bushi():
    """returns True if the character is a shugenja"""
    # is shugenja?
    return query(api.character.schools.get_all()).where(lambda x: x.has_tag('bushi')).count() > 0


def is_courtier():
    """returns True if the character is a shugenja"""
    # is shugenja?
    return query(api.character.schools.get_all()).where(lambda x: x.has_tag('courtier')).count() > 0
