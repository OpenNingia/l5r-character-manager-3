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

import dal.query
from asq.initiators import query
from api import __api


def get(c):
    """return a school by its id"""
    return query(__api.ds.schools).where(lambda x: x.id == c).first_or_default(None)


def get_base():
    """returns basic schools list"""
    return query(__api.ds.schools) \
        .where(lambda x: 'advanced' not in x.tags) \
        .where(lambda x: 'alternate' not in x.tags) \
        .to_list()


def get_advanced():
    """returns advanced schools list"""
    return query(__api.ds.schools) \
        .where(lambda x: 'advanced' in x.tags) \
        .to_list()


def get_paths():
    """returns advanced schools list"""
    return query(__api.ds.schools) \
        .where(lambda x: 'alternate' in x.tags) \
        .to_list()


def is_path(sid):
    """returns true if the given school is an alternate path"""

    school = get(sid)
    if not school:
        return False
    return 'alternate' in school.tags


def get_skills(sid):
    """return fixed school skills"""
    school = get(sid)
    if not school:
        return []
    return school.skills


def get_skills_to_choose(sid):
    """return variable school skills"""
    school = get(sid)
    if not school:
        return []
    return school.skills_pc


def get_spells_to_choose(sid):
    """return variable school skills"""
    school = get(sid)
    if not school:
        return []
    return school.spells_pc


def get_emphasis_to_choose(sid):
    """returns player choose emphasis"""
    school = get(sid)
    if not school:
        return []
    return query(school.skills) \
        .where(lambda x: x.emph and x.emph.startswith('*')) \
        .to_list()


def get_technique(tech_id):
    """returns the school and the technique by tech_id"""
    return dal.query.get_tech(__api.ds, tech_id)
