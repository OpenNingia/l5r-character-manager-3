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

import models
from api import __api
from l5rcmcore import log

import api.data.schools
import api.data.skills

from asq.initiators import query


def get_all():
    """return all character skills"""
    if not __api.pc:
        return []

    return get_starting() + get_learned()


def get_learned():
    """return all the learned ( not starting ) skills"""
    if not __api.pc:
        return []
    return query(__api.pc.advans).where(
        lambda x: x.type == 'skill' and x.skill not in get_starting()).select(
        lambda x: x.skill).distinct().to_list()


def get_starting():
    """get character starting skills"""
    if not __api.pc:
        return []
    first_id = api.character.schools.get_first()
    ch_school = query(__api.pc.schools).where(lambda x: x.school_id == first_id).first_or_default(None)
    if not ch_school:
        return []
    return ch_school.skills.keys()


def get_skill_rank(skill_id):
    """return the character skill rank"""
    if not __api.pc:
        return 0
    return __api.pc.get_skill_rank(skill_id)


def purchase_skill_rank(skill_id):
    log.api.info(u"purchase skill rank: %s", skill_id)

    skill_ = api.data.skills.get(skill_id)
    if not skill_:
        log.api.error(u"skill not found")
        return api.data.CMErrors.INTERNAL_ERROR

    cur_value = get_skill_rank(skill_id)
    new_value = cur_value + 1

    cost = api.rules.get_skill_rank_cost(skill_id, new_value)

    mastery_ability_rank = api.data.skills.get_mastery_ability(skill_id, new_value)

    adv = models.SkillAdv(skill_id, cost)
    if mastery_ability_rank:
        adv.rule = mastery_ability_rank.rule
    adv.desc = (api.tr('{0}, Rank {1} to {2}. Cost: {3} xp')
                .format(skill_.name, cur_value, new_value, adv.cost))

    return api.character.purchase_advancement(adv)


def purchase_memo_spell(self, spell_id):
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
