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
from asq.selectors import a_

import l5rdal as dal
import l5rdal.query

import l5r.api as api

from l5r.api import __api
from l5r.util import log


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
    """returns alternate path schools list"""
    return query(__api.ds.schools) \
        .where(lambda x: 'alternate' in x.tags) \
        .to_list()

def get_paths_with_rank(rank):
    """returns alternate schools list with rank equal to `rank`"""

    return query(__api.ds.schools) \
        .where(lambda x: 'alternate' in x.tags) \
        .where(lambda x: query(x.techs).select(a_('rank')).first_or_default(0) == rank) \
        .to_list()

def is_path(sid):
    """returns true if the given school is an alternate path"""

    school = get(sid)
    if not school:
        return False
    return 'alternate' in school.tags


def is_bushi(sid):
    """returns true if the given school is a bushi school"""
    school = get(sid)
    if not school:
        return False
    return 'bushi' in school.tags


def is_shugenja(sid):
    """returns true if the given school is a shugenja school"""
    school = get(sid)
    if not school:
        return False
    return 'shugenja' in school.tags


def is_courtier(sid):
    """returns true if the given school is a courtier school"""
    school = get(sid)
    if not school:
        return False
    return 'courtier' in school.tags


def is_monk(sid):
    """returns true if the given school is a monk school"""
    school = get(sid)
    if not school:
        return False
    return 'monk' in school.tags


def is_samurai_monk(sid):
    """returns true if the given school is a samurai monk school"""
    school = get(sid)
    if not school:
        return False
    return 'monk' in school.tags and 'brotherhood' not in school.tags


def is_brotherhood_monk(sid):
    """returns true if the given school is a brotherhood monk school"""
    school = get(sid)
    if not school:
        return False
    return 'monk' in school.tags and 'brotherhood' in school.tags


def is_ninja(sid):
    """returns true if the given school is a monk school"""
    school = get(sid)
    if not school:
        return False
    return 'ninja' in school.tags


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


def get_requirements(sid):
    """returns the requirements to join the given school"""
    school_ = get(sid)
    if not school_:
        log.api.error(u"school not found: %s", sid)
        return []

    requirements_by_data_ = school_.require

    # fixme. since i can't rewrite all alternate path
    # I decided to patch these requirement by code

    import l5r.api.character.schools
    from l5rdal.requirements import Requirement
    coded_requirements_ = []

    if is_path(sid):
        # An alternate path can only be joined
        # on the same school rank that its technique replaces

        path_rank_ = query(school_.techs).select(a_('rank')).first_or_default(0)

        if path_rank_ > 0:

            r = Requirement()
            r.field = api.character.schools.get_current()
            r.type = 'school'
            r.min = path_rank_ - 1
            r.max = path_rank_ - 1
            r.trg = None
            r.text = __api.tr("Replaces School Rank: {0}").format(path_rank_)

            coded_requirements_.append(r)

    return requirements_by_data_ + coded_requirements_


def get_school_trait(sid):
    """return school trait"""
    school_ = get(sid)
    if not school_:
        return None
    return school_.trait


def get_starting_perks(sid):
    """return a school's starting perks"""
    school_ = get(sid)
    if not school_:
        return []
    return school_.perks
