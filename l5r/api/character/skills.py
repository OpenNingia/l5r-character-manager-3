# Copyright (C) 2014-2022 Daniele Simonetti
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

import l5r.api as api
import l5r.models
from l5r.models import SkillAdv

import l5r.api.data.schools
import l5r.api.data.skills

from l5r.api import __api
from l5r.util import log

from asq.initiators import query
from asq.selectors import a_


def get_all():
    """return all character skills"""
    if not __api.pc:
        return []

    return query(get_starting() + get_learned() + get_acquired()).distinct().to_list()


def get_learned():
    """return all the learned ( not starting ) skills"""
    if not __api.pc:
        return []
    return query(__api.pc.advans).where(
        lambda x: x.type == 'skill').select(
        lambda x: x.skill).distinct().to_list()


def get_acquired():
    """returns skills acquired in other ways"""

    acquired_ = []

    # add a rank in Craft (Explosives), for free
    if api.character.has_rule('fk_gaijin_pepper'):
        acquired_.append("craft_explosives")

    # add a rank in Lore (Gozoku), for free
    if api.character.has_rule('fk_gozoku'):
        acquired_.append("lore_gozoku")

    # add a rank in Lore (Kolat), for free
    if api.character.has_rule('fk_kolat'):
        acquired_.append("lore_kolat")

    # add a rank in Lore (Lying Darkness), for free
    if api.character.has_rule('fk_lying_darkness'):
        acquired_.append("lore_lying_darkness")

    # add a rank in Lore (Maho), for free
    if api.character.has_rule('fk_maho'):
        acquired_.append("lore_maho")

    return acquired_


def get_starting():
    """get character starting skills"""
    # get first rank advancement
    rank_ = api.character.rankadv.get(1)
    if not rank_:
        return []

    return query(rank_.skills).distinct().to_list()


def is_starter(skill_id):
    """returns True if the skill is from the starting ones"""
    return skill_id in get_starting()


def get_skill_rank(skill_id):
    """return the character skill rank"""
    if not __api.pc:
        return 0

    sk_rank_ = 0
    for r in api.character.rankadv.get_all():
        sk_rank_ += query(r.skills).where(lambda x: x == skill_id).count()

    sk_rank_ += query(__api.pc.advans).where(
        lambda x: x.type == 'skill' and x.skill == skill_id).count()

    if skill_id in get_acquired():
        sk_rank_ += 1

    return sk_rank_


def get_skill_emphases(skill_id):
    """return the emphases for a skill"""
    sk_emph_list = []
    for r in api.character.rankadv.get_all():
        if skill_id not in r.emphases:
            continue
        sk_emph_list += r.emphases[skill_id]

    sk_emph_list += query(__api.pc.advans).where(
        lambda x: x.type == 'emph' and x.skill == skill_id).select(a_('text')).to_list()

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

    adv = SkillAdv(skill_id, cost)
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
