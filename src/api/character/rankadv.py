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
from models.advancements.rank import Rank
from asq.initiators import query

import api.character.schools
import api.data.merits


def all():
    if __api.pc: return []
    return query(__api.pc.advans).where(lambda x: x.type == 'rank').to_list()


def get_current():
    """returns the current rank advancement"""
    if not __api.current_rank_adv:
        __api.current_rank_adv = Rank()
    return __api.current_rank_adv


def start(rank):
    """start a new rank advancement for the given rank
    :type rank: int
    """
    get_current().rank = rank


def set_clan(cid):
    """set rank advancement clan
    :type cid: str
    """
    get_current().clan = cid


def set_family(fid):
    """set rank advancement family
    :type fid: str
    """
    get_current().family = fid


def set_school(sid):
    """set rank advancement family
    :type sid: str
    """

    # get school rank
    school_rank = api.character.schools.get_rank(sid)

    # check if alternate path
    get_current().is_alternate_path = api.data.schools.is_path(sid)

    # check if character has left a path
    get_current().original_school = api.character.schools.get_current()
    get_current().left_alternate_path = (get_current().original_school != sid and
                                         api.data.schools.is_path(get_current().original_school))
    get_current().school = sid

    # set school rank
    # if school rank was 0 the character has joined a school on rank 1
    # if the school_rank was != 0 the character advanced in the previous school
    get_current().school_rank = school_rank + 1


def add_merit(mid, rank=1, free=False):
    """adds a merit rank, increasing the advancement cost if free==False
    :type mid: str
    :type rank: int
    """

    merit = api.data.merits.get_rank(mid, rank)
    pair = (mid, rank)
    if merit and pair not in get_current().merits:
        get_current().merits.append(pair)
        if not free:
            get_current().cost += api.data.merits.get_rank_cost(mid, rank)

