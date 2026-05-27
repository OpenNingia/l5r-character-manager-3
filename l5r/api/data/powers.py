# -*- coding: utf-8 -*-
# Copyright (C) 2014-2022 Daniele Simonetti
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

from l5r.api import get_context
from asq.initiators import query


def kiho():
    if not get_context().ds:
        return []
    return get_context().ds.kihos


def get_kiho(kid):
    return query(kiho()).where(lambda x: x.id == kid).first_or_default(None)


def kata():
    if not get_context().ds:
        return []
    return get_context().ds.katas


def get_kata(kid):
    return query(kata()).where(lambda x: x.id == kid).first_or_default(None)
