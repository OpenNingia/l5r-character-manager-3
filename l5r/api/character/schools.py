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

from util import log


def get_all():
    """return all the character schools"""
    if not __api.pc:
        return []
    return [x.school_id for x in __api.pc.schools]


def get_current():
    """returns the id of the character current school"""
    rank_ = api.character.rankadv.get_last()
    if not rank_:
        return None
    return rank_.school


def get_rank(sid):
    """returns the character rank in the given school"""
    if not __api.pc:
        return 0

    return query(__api.pc.schools) \
        .where(lambda x: x.school_id == sid) \
        .select(a_('school_rank')).first_or_default(0)


def get_first():
    """returns character starting school"""
    if not __api.pc:
        return None
    return __api.pc.school


def set_first(sid):
    """set first school to PC"""
    school_ = api.data.schools.get(sid)
    if not school_:
        return

    # rank advancement
    rank_ = api.character.rankadv.join_new(school_.id)

    # reset character honor, glory and status
    __api.pc.honor = __api.pc.glory = __api.pc.status = 0

    # set schools
    __api.pc.set_school(school_.id, school_.trait, 1, school_.honor, school_.tags + [school_.id])

    # set starting skills
    for sk in school_.skills:
        api.character.skills.add_starting_skill(sk.id, sk.rank, sk.emph)

    # pending player choose skills
    for sk in school_.skills_pc:
        rank_.skills_to_choose.append(sk)

    # outfit and money
    rank_.outfit = school_.outfit
    rank_.money = tuple(school_.money)

    # starting spells
    for spell in school_.spells:
        api.character.spells.add_school_spell(spell.id)

    for spell in school_.spells_pc:
        rank_.spells_to_choose.append(
            (spell.element, spell.count, spell.tag))

    # starting kiho
    if school_.kihos:
        rank_.gained_kiho_count = school_.kihos.count


def join_new(sid):
    """join a new school"""

    school_ = api.data.schools.get(sid)
    if not school_:
        return

    # add advancement
    rank_ = api.character.rankadv.join_new(school_.id)

    #import models

    #school_nm = school_.name

    #school_obj = models.CharacterSchool(school_.id)
    #school_obj.tags = school_.tags
    #school_obj.school_rank = 0

    #school_obj.affinity = school_.affinity
    #school_obj.deficiency = school_.deficiency

    #__api.pc.schools.append(school_obj)

    # check free kihos
    #if school_.kihos:
    #    __api.pc.set_free_kiho_count(school_.kihos.count)

    # check for alternate path
    #if school_obj.has_tag('alternate'):
    #    school_obj.is_path = True
    #    school_obj.path_rank = api.character.insight_rank()


def get_schools_by_tag(tag):
    """returns character schools by tag"""
    return query(get_all()).where(
        lambda x: tag in api.data.schools.get(x).tags if api.data.schools.get(x) is not None else False).to_list()


def get_school_by_rank(rank):
    """returns the school joined at the given insight rank, considering alternate paths"""
    rank_ = query(api.character.rankadv.get_all()).where(lambda x: x.rank == rank).first_or_default(None)
    if not rank_:
        log.api.error(u"get_school_by_rank. rank advancement not found: %d", rank)
        return None
    return rank_.school


def get_tech_by_rank(rank):
    """returns the technique learned at the given insight rank, or None"""

    # get the school rank at that insight rank
    rank_ = query(api.character.rankadv.get_all()).where(
        lambda x: x.rank == rank).first_or_default(None)

    if not rank_:
        log.api.error(u"get_tech_by_rank. rank advancement not found: %d", rank)
        return None

    school_id = rank_.school
    school_rank = query(api.character.rankadv.get_all()).where(
        lambda x: (x.school == school_id or
                   x.replaced == school_id) and x.rank <= rank).count()

    school_ = api.data.schools.get(school_id)

    if not school_:
        return None

    # for path use the school rank as a tech index
    if api.data.schools.is_path(school_.id):
        try:
            return school_.techs[school_rank-1].id
        except:
            return None

    return query(school_.techs).where(
        lambda x: x.rank == school_rank).select(a_('id')).first_or_default(None)


def get_school_rank(sid):
    """return the school rank"""

    if api.data.schools.is_path(sid):
        return query(api.data.schools.get(sid).techs).select(a_('rank')).first_or_default(1)
    return query(api.character.rankadv.get_all()).where(
            lambda x: x.school == sid or x.replaced == sid).count()


def get_techs_by_school(sid):
    """returns all the techniques learned in the given school"""

    school_ = api.data.schools.get(sid)
    if not school_:
        return []

    return query(school_.techs).where(lambda x: api.character.has_rule(x.id)).to_list()
