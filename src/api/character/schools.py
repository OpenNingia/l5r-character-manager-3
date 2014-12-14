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
import api.character.rankadv

from asq.initiators import query
from asq.selectors import a_


def get_current():
    """returns the id of the character current school"""
    if not __api.pc: return None
    return __api.pc.current_school_id


def get_rank(sid):
    """returns the character rank in the given school"""

    return query(api.character.rankadv.all()) \
        .where(lambda x: x.school == sid) \
        .order_by_descending(a_('school_rank')) \
        .select(a_('school_rank')).first_or_default(0)

