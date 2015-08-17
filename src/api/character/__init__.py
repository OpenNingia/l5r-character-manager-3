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

from api import __api
import api.data
import models


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
    return tag in __api.pc.rules


def has_tag_or_rule(tag):
    return has_tag(tag) or has_rule(tag)


def remove_advancement(adv):
    """remove an advancement, returns True on success"""
    if not __api.pc or not adv in __api.pc.advans:
        return False
    __api.pc.advans.remove(adv)
    return True


def xp():
    if not __api.pc:
        return 0
    return __api.pc.get_px()


def xp_limit():
    if not __api.pc:
        return 0
    return __api.pc.get_xp_limit()


def trait_rank(trait_id):
    if not __api.pc:
        return 0
    return __api.pc.get_attrib_rank(trait_id)


def append_advancement(adv):
    if __api.pc:
        __api.pc.add_advancement(adv)


def increase_trait(trait_id):

    cur_value = trait_rank(trait_id)
    new_value = cur_value + 1

    cost = api.rules.get_trait_increase_cost(trait_id, cur_value, new_value)

    # cur_value = self.pc.get_attrib_rank(attrib)
    # new_value = cur_value + 1
    # ring_id = models.get_ring_id_from_attrib_id(attrib)
    # ring_nm = models.ring_name_from_id(ring_id)
    # cost = self.pc.get_attrib_cost(attrib) * new_value
    # if self.pc.has_rule('elem_bless_%s' % ring_nm):
    #    cost -= 1
    # text = models.attrib_name_from_id(attrib).capitalize()

    # build advancement model
    adv = models.advances.AttribAdv(trait_id, cost)

    #adv.desc = (self.tr('{0}, Rank {1} to {2}. Cost: {3} xp')
    #            .format(trait.name, cur_value, new_value, adv.cost))

    if (adv.cost + xp()) > xp_limit():
        return api.data.CMErrors.NOT_ENOUGH_XP

    append_advancement(adv)

    return api.data.CMErrors.NO_ERROR


def insight_rank():
    """returns PC's insight rank"""
    return __api.pc.get_insight_rank()


def set_clan(clan_id):
    """set PC clan"""
    __api.pc.clan = clan_id


def set_family(family_id):
    """set PC family"""

    family_ = api.data.families.get(family_id)
    if family_:
        __api.pc.set_family(family_.id, family_.trait, 1, [family_.id, family_.clanid])


def get_family():
    """get PC family"""
    return __api.pc.family