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


def all():
    """returns the list of spells"""
    if not __api:
        return []
    return __api.ds.spells


def get(sid):
    """return the spell that matches the given id"""
    if not sid:
        return None
    return query(all()).where(lambda x: x.id == sid).first_or_default(None)


def has_tag(sid, tag, school=None):
    """return True if the given spell has the given tag, with support for school-only tags"""
    return tag in tags(sid, school)


def tags(sid, school=None):
    """return all the tags of the given spell, with support for school-only tags"""
    s = get(sid)
    if not s:
        return []
    return query(s.tags).where(lambda x: x.school is None or x.school == school).select(lambda x: x.name)


def is_multi_element(sid):
    """returns true if the spell is multi element"""
    s = get(sid)
    if not s:
        return False
    return s.element == 'multi'


def is_dragon(sid):
    """returns true if the spell is a dragon spell"""
    s = get(sid)
    if not s:
        return False
    return s.element == 'dragon'



