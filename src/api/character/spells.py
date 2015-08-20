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

import api
from api import __api
from asq.initiators import query


def get_all():
    """return all character skills"""
    if not __api.pc:
        return []
    return __api.pc.get_spells()


def deficiencies():
    """returns character deficiencies"""
    if not __api.pc:
        return []
    return __api.pc.get_deficiency()


def affinities():
    """returns character deficiencies"""
    if not __api.pc:
        return []
    return __api.pc.get_affinity()


def is_learnable(spell):
    """returns true if character can learn this spell"""
    max_mastery = api.character.insight_rank()

    max_mastery -= deficiency(spell)
    max_mastery += affinity(spell)

    return max_mastery >= spell.mastery


def special_affinity(spell):

    ret = 0
    school = api.character.schools.get_current()

    # special handling of scorpion_yogo_wardmaster_school
    if school == 'scorpion_yogo_wardmaster_school':
        if api.data.spells.has_tag(spell.id, 'wards', school):
            ret += 1

    if api.character.has_tag_or_rule('phoenix_embrace_the_elements'):
        affinity_, deficiencies_ = phoenix_embrace_the_elements()
        if affinity_ == spell.element:
            ret += 1

    return ret


def special_deficiency(spell):
    ret = 0
    school = api.character.schools.get_current()

    # special handling of scorpion_yogo_wardmaster_school
    if school == 'scorpion_yogo_wardmaster_school':
        if (api.data.spells.has_tag(spell.id, 'travel', school) and
                api.data.spells.has_tag(spell.id, 'craft', school)):
            ret += 1

    if api.character.has_tag_or_rule('phoenix_embrace_the_elements'):
        affinity_, deficiencies_ = phoenix_embrace_the_elements()
        ret += query(deficiencies_).where(lambda x: x == spell.element or x in spell.elements).count()

    return ret


def phoenix_embrace_the_elements():
    main_affinity_ = affinities()[0] if len(affinities()) else None
    if main_affinity_ is None:
        return None, []

    deficiencies_ = [x.id for x in api.data.rings() if x.id != main_affinity_]
    return main_affinity_, deficiencies_


def affinity(spell):
    """calculate affinity with a given spell"""
    return (
        query(affinities()).where(lambda x: x == spell.element or spell.element in x).count() +
        special_affinity(spell))


def deficiency(spell):
    """calculate deficiency with a given spell"""
    return (
        query(deficiencies()).where(lambda x: x == spell.element or spell.element in x or x in spell.elements).count() +
        special_deficiency(spell))


def get_mastery_modifier(spell):
    """get mastery bonus or malus for a given spell"""
    if spell.element != 'multi':
        return (
            api.character.spells.affinity(spell) -
            api.character.spells.deficiency(spell)
        )
    else:
        return -api.character.spells.deficiency(spell)


def character_can_learn():
    """returns spells that the character can learn at its current school rank"""
    return [x for x in get_all() if is_learnable(x)]


