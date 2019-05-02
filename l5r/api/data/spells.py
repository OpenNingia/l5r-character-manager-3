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
import l5r.api.character.schools

from l5r.api import __api


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

    school_id_list = []
    if school is not None:
        school_id_list = [school]
    else:
        school_id_list = api.character.schools.get_all()

    return query(s.tags).where(
        lambda x: x.school is None or x.school in school_id_list).select(lambda x: x.name).to_list()


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


def get_maho_spells(ring, mastery):
    """returns all the maho spells for the given ring and mastery"""
    return query(get_spells(ring, mastery)).where(lambda x: 'maho' in tags(x.id)).to_list()


def get_spells(ring, mastery, maho=True):
    """returns all the maho spells for the given ring and mastery, if maho include maho spells"""
    including_maho = query(all()).where(lambda x: x.element == ring and x.mastery == mastery)
    if not maho:
        return query(including_maho).where(lambda x: 'maho' not in tags(x.id)).to_list()
    return including_maho.to_list()
