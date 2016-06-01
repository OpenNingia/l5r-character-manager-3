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

from asq.initiators import query

import l5r.api as api
import l5r.api.character
from l5r.api import __api


def all():
    """returns all the flaws"""
    if not __api.pc:
        return []
    return __api.ds.flaws


def get(fid):
    """returns a flaw by its id, None if not found"""
    if not __api.pc:
        return None
    return query(all()).where(lambda x: x.id == fid).first_or_default(None)


def get_rank(fid, rank):
    """returns a flaw rank"""
    flaw_ = get(fid)
    if not flaw_:
        return None
    return query(flaw_.ranks).where(lambda x: x.id == rank).first_or_default(None)


def get_rank_gain(fid, rank):
    """returns the gain of a flaw rank"""
    flaw_rank = get_rank(fid, rank)
    if not flaw_rank:
        return 0

    # calculate the cost with exceptions
    gain_ = flaw_rank.value

    for e in flaw_rank.exceptions:
        if api.character.has_tag_or_rule(e.tag):
            gain_ = e.value
    return gain_
