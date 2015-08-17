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
from asq.initiators import query

import api.character


def all():
    """returns all the merits"""
    if not __api.pc: return []
    return __api.ds.merits


def get(mid):
    """returns a merit by its id, None if not found"""
    if not __api.pc:
        return None
    return query(all()).where(lambda x: x.id == mid).first_or_default(None)


def get_rank(mid, rank):
    """returns a merit rank"""
    merit = get(mid)
    if not merit:
        return None
    return query(merit.ranks).where(lambda x: x.id == rank).first_or_default(None)


def get_rank_cost(mid, rank):
    """returns the cost of a merit rank"""
    merit_rank = get_rank(mid, rank)
    if not merit_rank:
        return 0

    # calculate the cost with exceptions
    cost = merit_rank.value

    for e in merit_rank.exceptions:
        if api.character.has_tag_or_rule(e.tag):
            cost = e.value
    return cost