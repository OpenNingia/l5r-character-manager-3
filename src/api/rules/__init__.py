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
import api.character
import models.chmodel


def get_trait_cost(trait_nm):
    """return the base multiplier to purchase the given trait"""
    if not __api.pc:
        return 0
    trait_id = models.chmodel.attrib_from_name(trait_nm)
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

    elemental_bless = "elem_bless_{}".format(ring.text)
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

def apply_tech_side_effects(tech_id):
    pass
