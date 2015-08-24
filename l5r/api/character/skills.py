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

import models
from api import __api
from util import log

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
    # get first rank advancement
    rank_ = api.character.rankadv.get(1)
    if not rank_:
        log.api.error(u"first rank advancement not found")
        return []

    return query(rank_.skills).distinct().to_list()

    #first_id = api.character.schools.get_first()
    #ch_school = query(__api.pc.schools).where(lambda x: x.school_id == first_id).first_or_default(None)
    #if not ch_school:
    #    return []
    #return ch_school.skills.keys()


def is_starter(skill_id):
    """returns True if the skill is from the starting ones"""
    return skill_id in get_starting()


def get_skill_rank(skill_id):
    """return the character skill rank"""
    if not __api.pc:
        return 0

    sk_rank_ = 0
    for r in api.character.rankadv.all():
        sk_rank_ += query(r.skills).where(lambda x: x == skill_id).count()

    sk_rank_ += query(__api.pc.advans).where(
        lambda x: x.type == 'skill' and x.skill == skill_id).count()

    return sk_rank_


def get_skill_emphases(skill_id):
    """return the emphases for a skill"""
    sk_emph_list = []
    for r in api.character.rankadv.all():
        if skill_id not in r.emphases:
            continue
        sk_emph_list += r.emphases[skill_id]

    sk_emph_list += query(__api.pc.advans).where(
        lambda x: x.type == 'emph' and x.skill == skill_id).to_list()

    return sk_emph_list


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


def add_starting_skill(skill_id, rank=0, emph=None):
    """add a starting skill"""

    skill_ = api.data.skills.get(skill_id)
    if not skill_:
        log.api.error(u"skill not found: %s", skill_id)
        return False

    # get first rank advancement
    rank_ = api.character.rankadv.get(1)

    if not rank_:
        log.api.error(u"add_starting_skill. first rank advancement not found")
        return False

    for i in range(0, rank):
        rank_.skills.append(skill_id)

    if emph:
        skill_emphases = rank_.emphases[skill_id] if skill_id in rank_.emphases else []
        skill_emphases.append(emph)
        rank_.emphases[skill_id] = skill_emphases

    return True
