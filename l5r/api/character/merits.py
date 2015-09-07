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

# for rank advancement models
import models

from api import __api
from asq.initiators import query

import api.data.merits


def all():
    """returns character merits"""
    if not __api.pc:
        return []
    return query(__api.pc.advans).where(
        lambda x: x.type == 'perk' and (x.cost > 0 or x.tag == 'merit')).to_list()


def add(merit_id, rank=None):
    """add a merit advancement"""

    merit_ = api.data.merits.get(merit_id)
    if not merit_:
        return

    if not rank:
        rank = 1

    merit_rank_ = api.data.merits.get_rank(merit_id, rank)
    if not merit_rank_:
        return

    cost_ = api.data.merits.get_rank_cost(merit_id, rank)

    adv_ = models.PerkAdv(merit_id, merit_rank_.id, cost_, "merit")
    adv_.rule = merit_id
    adv_.desc = unicode.format(__api.tr("{0} Rank {1}, XP Cost: {2}"),
                               merit_.name, merit_rank_.id, cost_)

    return api.character.purchase_advancement(adv_)
