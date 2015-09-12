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
from asq.selectors import a_

import api.data.merits


def get_all():
    """returns character flaws"""
    return get_starting() + get_bought()


def get_bought():
    """return all flaws that comes from advancements"""
    if not __api.pc:
        return []
    return query(__api.pc.advans).where(
        lambda x: x.type == 'perk' and (x.cost < 0 or x.tag == 'flaw')).to_list()


def get_starting():
    """return flaws that comes from the starting school"""
    first_rank_ = api.character.rankadv.get_first()
    if not first_rank_:
        return []
    return first_rank_.flaws


def add(flaw_id, rank=None):
    """add a flaw advancement"""

    flaw_ = api.data.flaws.get(flaw_id)
    if not flaw_:
        return False

    if not rank:
        rank = 1

    flaw_rank_ = api.data.flaws.get_rank(flaw_id, rank)
    if not flaw_rank_:
        return False

    gain_ = api.data.flaws.get_rank_gain(flaw_id, rank)

    adv_ = models.PerkAdv(flaw_id, flaw_rank_.id, -gain_, "flaw")
    adv_.rule = flaw_id
    adv_.desc = unicode.format(__api.tr("{0} Rank {1}, XP Gain: {2}"),
                               flaw_.name, flaw_rank_.id, gain_)

    api.character.append_advancement(adv_)
    return True


def add_starting(flaw_id, rank=None):
    """add a flaw advancement to starting school rank"""

    first_rank_ = api.character.rankadv.get_first()
    if not first_rank_:
        return False

    flaw_ = api.data.flaws.get(flaw_id)
    if not flaw_:
        return False

    if not rank:
        rank = 1

    flaw_rank_ = api.data.flaws.get_rank(flaw_id, rank)
    if not flaw_rank_:
        return False

    gain_ = 0

    adv_ = models.PerkAdv(flaw_id, flaw_rank_.id, -gain_, "flaw")
    adv_.rule = flaw_id
    adv_.desc = unicode.format(__api.tr("{0} Rank {1}, XP Gain: {2}"),
                               flaw_.name, flaw_rank_.id, gain_)

    first_rank_.flaws.append(adv_)
    return True
