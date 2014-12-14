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
from asq.initiators import query


def categories():
    """returns a list of skill categories with 'id' and 'name' properties"""
    if not __api.ds:
        return []
    return __api.ds.skcategs


def all():
    """returns a list of skills"""
    if not __api.ds:
        return []
    return __api.ds.skills


def get(sid):
    """return a skill by its id"""
    if not __api.ds:
        return None
    return query(all()).where(lambda x: x.id == sid).first_or_default(None)

