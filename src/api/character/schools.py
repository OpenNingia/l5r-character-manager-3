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


def get_all():
    """return all the character schools"""
    if not __api.pc:
        return []
    return [x.school_id for x in __api.pc.schools]


def get_current():
    """returns the id of the character current school"""
    if not __api.pc:
        return None
    return __api.pc.current_school_id


def get_rank(sid):
    """returns the character rank in the given school"""
    if not __api.pc:
        return 0

    return query(__api.pc.schools) \
        .where(lambda x: x.school_id == sid) \
        .select(a_('school_rank')).first_or_default(0)

    #return query(api.character.rankadv.all()) \
    #    .where(lambda x: x.school == sid) \
    #    .order_by_descending(a_('school_rank')) \
    #    .select(a_('school_rank')).first_or_default(0)


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

    # set schools
    __api.pc.set_school(school_.id, school_.trait, 1, school_.honor, school_.tags + [school_.id])

    # set starting skills
    for sk in school_.skills:
        __api.pc.add_school_skill(sk.id, sk.rank, sk.emph)

    # pending player choose skills
    for sk in school_.skills_pc:
        __api.pc.add_pending_wc_skill(sk)

    # get school tech rank 1
    tech0 = query(school_.techs).where(lambda x: x.rank == 1).first_or_default(None)
    if tech0:
        __api.pc.set_free_school_tech(tech0.id, tech0.id)

    # outfit and money
    __api.pc.set_school_outfit(school_.outfit, tuple(school_.money))

    # starting spells
    count = 0

    for spell in school_.spells:
        __api.pc.add_free_spell(spell.id)
        count += 1

    for spell in school_.spells_pc:
        __api.pc.add_pending_wc_spell(
            (spell.element, spell.count, spell.tag))
        count += spell.count

    __api.pc.set_school_spells_qty(count)

    # affinity / deficiency
    __api.pc.set_affinity(school_.affinity)
    __api.pc.set_deficiency(school_.deficiency)
    __api.pc.get_school().affinity = school_.affinity
    __api.pc.get_school().deficiency = school_.deficiency

    # starting kiho
    if school_.kihos:
        __api.pc.set_free_kiho_count(school_.kihos.count)
