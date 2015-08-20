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
from util import log


def get_all():
    """return all character skills"""
    if not __api.pc:
        return []
    return __api.pc.get_spells()


def base_deficiencies():
    """returns character deficiencies"""
    if not __api.pc:
        return []
    return __api.pc.get_deficiency()


def deficiencies():
    """returns character deficiencies"""
    return base_deficiencies() + additional_deficiencies()


def base_affinities():
    """returns character base affinities"""
    if not __api.pc:
        return []
    return __api.pc.get_affinity()


def affinities():
    """returns character affinities"""
    return base_affinities() + additional_affinities()


def is_learnable(spell):
    """returns true if character can learn this spell"""
    max_mastery = api.character.insight_rank()

    max_mastery -= deficiency(spell)
    max_mastery += affinity(spell)

    return max_mastery >= spell.mastery


def additional_affinities():
    """return additional affinities of the character"""
    result_ = []

    if api.character.has_tag_or_rule('phoenix_embrace_the_elements'):
        affinity_, deficiencies_ = phoenix_embrace_the_elements()
        result_.append(affinity_)

    if api.character.has_tag_or_rule('mantis_favor_of_the_sun'):
        result_.append('fire')

    return result_


def additional_deficiencies():
    """return additional deficiencies of the character"""
    result_ = []

    if api.character.has_tag_or_rule('phoenix_embrace_the_elements'):
        affinity_, deficiencies_ = phoenix_embrace_the_elements()
        result_ += deficiencies_

    return result_


def special_affinity(spell):

    ret = 0
    school = api.character.schools.get_current()

    # special handling of scorpion_yogo_wardmaster_school
    if school == 'scorpion_yogo_wardmaster_school':
        if api.data.spells.has_tag(spell.id, 'wards', school):
            ret += 1

    #if api.character.has_tag_or_rule('phoenix_embrace_the_elements'):
    #    affinity_, deficiencies_ = phoenix_embrace_the_elements()
    #    if affinity_ == spell.element:
    #        ret += 1

    return ret


def special_deficiency(spell):
    ret = 0
    school = api.character.schools.get_current()

    # special handling of scorpion_yogo_wardmaster_school
    if school == 'scorpion_yogo_wardmaster_school':
        if (api.data.spells.has_tag(spell.id, 'travel', school) and
                api.data.spells.has_tag(spell.id, 'craft', school)):
            ret += 1

    #if api.character.has_tag_or_rule('phoenix_embrace_the_elements'):
    #    affinity_, deficiencies_ = phoenix_embrace_the_elements()
    #    ret += query(deficiencies_).where(lambda x: x == spell.element or x in spell.elements).count()

    return ret


def phoenix_embrace_the_elements():
    main_affinity_ = base_affinities()[0] if len(base_affinities()) else None
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


def purchase_memo_spell(self, spell_id):
    """purchase a memorized spell"""
    log.api.info(u"purchase memorized spell: %s", spell_id)

    spell_ = api.data.spells.get(spell_id)
    if not spell_:
        log.api.error(u"spell not found")
        return api.data.CMErrors.INTERNAL_ERROR

    # no special rules for memorized spells
    cost = spell_.mastery
    text = spell_.name

    adv = models.MemoSpellAdv(spell_id, cost)
    adv.desc = (api.tr('{0}, Mastery {1}. Cost: {2} xp')
                .format(text, cost, adv.cost))

    return api.character.purchase_advancement(adv)
