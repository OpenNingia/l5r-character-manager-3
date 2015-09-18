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
from asq.selectors import a_
from util import log
import models


def get_all():
    """return all character skills"""
    return get_school_spells() + get_learned_spells()


def base_deficiencies():
    """returns character deficiencies"""
    list_ = []
    if not __api.pc:
        return list_

    for r in api.character.rankadv.get_all():
        list_ += r.deficiencies

    return list_


def deficiencies():
    """returns character deficiencies"""
    return base_deficiencies() + additional_deficiencies()


def base_affinities():
    """returns character base affinities"""
    list_ = []
    if not __api.pc:
        return list_

    for r in api.character.rankadv.get_all():
        list_ += r.affinities

    return list_


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

    return ret


def special_deficiency(spell):
    ret = 0
    school = api.character.schools.get_current()

    # special handling of scorpion_yogo_wardmaster_school
    if school == 'scorpion_yogo_wardmaster_school':
        if (api.data.spells.has_tag(spell.id, 'travel', school) or
                api.data.spells.has_tag(spell.id, 'craft', school)):
            ret += 1

    return ret


def phoenix_embrace_the_elements():
    main_affinity_ = base_affinities()[0] if len(base_affinities()) else None
    if main_affinity_ is None:
        return None, []

    deficiencies_ = [x for x in api.data.rings() if x != main_affinity_]
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


def affinities_by_school(school_id):
    """return affinities got from that school"""
    school_ = api.data.schools.get(school_id)
    if not school_:
        return []

    ret_ = []
    ranks_ = query(api.character.rankadv.get_all()).where(
        lambda x: x.school == school_id and len(x.affinities) > 0).to_list()
    for r in ranks_:
        ret_ += r.affinities

    # special affinities
    if school_id == 'scorpion_yogo_wardmaster_school':
        ret_.append('wards')

    is_phoenix_embrace_the_elements = query(school_.techs).where(
        lambda x: x.id == 'phoenix_embrace_the_elements').count() > 0
    if is_phoenix_embrace_the_elements:
        affinity_, deficiencies_ = phoenix_embrace_the_elements()
        ret_.append(affinity_)

    is_mantis_favor_of_the_sun = query(school_.techs).where(lambda x: x.id == 'mantis_favor_of_the_sun').count() > 0
    if is_mantis_favor_of_the_sun:
        ret_.append('fire')

    return ret_


def deficiencies_by_school(school_id):
    """return deficiencies got from that school"""
    school_ = api.data.schools.get(school_id)
    if not school_:
        return []

    ret_ = []
    ranks_ = query(api.character.rankadv.get_all()).where(
        lambda x: x.school == school_id and len(x.deficiencies) > 0).to_list()
    for r in ranks_:
        ret_ += r.deficiencies

    # special affinities
    if school_id == 'scorpion_yogo_wardmaster_school':
        ret_ += ['travel', 'craft']

    is_phoenix_embrace_the_elements = query(school_.techs).where(
        lambda x: x.id == 'phoenix_embrace_the_elements').count() > 0
    if is_phoenix_embrace_the_elements:
        affinity_, deficiencies_ = phoenix_embrace_the_elements()
        ret_ += deficiencies_

    return ret_


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


def purchase_memo_spell(spell_id):
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
                .format(text, spell_.mastery, adv.cost))

    return api.character.purchase_advancement(adv)


def add_school_spell(spell_id):
    """add a spell to the current rank advancement"""
    rank_ = api.character.rankadv.get_last()
    if not rank_:
        log.api.error(u"add_school_spell. no rank advancement found")
        return False

    spell_ = api.data.spells.get(spell_id)
    if not spell_:
        log.api.error(u"add_school_spell. spell not found: %s", spell_id)
        return False

    if spell_id not in rank_.spells:
        rank_.spells.append(spell_id)

    return True


def add_spell(spell_id):
    """add a spell, not bound to a specific rank advancement"""
    spell_ = api.data.spells.get(spell_id)
    if not spell_:
        log.api.error(u"add_school_spell. spell not found: %s", spell_id)
        return False

    adv = models.SpellAdv(spell_id)
    adv.desc = (api.tr('{0}, Mastery {1}. Element: {2}')
                .format(spell_.name, spell_.mastery, spell_.element))

    api.character.append_advancement(adv)
    return True


def get_school_spells():
    """return the spells bounded to a rank advancement"""
    spells_ = []
    for r in api.character.rankadv.get_all():
        spells_ += r.spells
    return spells_


def get_learned_spells():
    """return the spells not bounded to a rank advancement"""
    return query(__api.pc.advans).where(
        lambda x: x.type == 'spell').select(a_('spell')).distinct().to_list()


def get_memorized_spells():
    """return the memorized spels"""
    return query(__api.pc.advans).where(
        lambda x: x.type == 'memo_spell').select(a_('spell')).distinct().to_list()


