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
    """return the cost to increase the given trait"""
    if not __api.pc:
        return 0
    trait_id = models.chmodel.attrib_from_name(trait_nm)
    return __api.pc.get_attrib_cost(trait_id)


def get_trait_increase_cost(trait_nm, cur_value, new_value):
    """increasing a trait cost new_value * trait_cost"""
    # cur_value is ignored
    cost = new_value * get_trait_cost(trait_nm)
    ring = api.data.get_trait_ring(trait_nm)

    elemental_bless = "elem_bless_{}".format(ring.text)
    if api.character.has_rule(elemental_bless):
        cost -= 1

    return cost


def apply_tech_side_effects(tech_id):
    pass
