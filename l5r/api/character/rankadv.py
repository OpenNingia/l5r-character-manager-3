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

import l5r.api as api
import l5r.api.character.schools
import l5r.api.data.merits

from l5r.models.advancements.rank import Rank
from l5r.api import __api

from asq.initiators import query
from asq.selectors import a_

from l5r.util import log


def get_all():
    if not __api.pc:
        return []
    return query(__api.pc.advans).where(lambda x: x.type == 'rank').to_list()


def get(rank):
    """returns the Rank advancement for the given insight rank"""
    return query(get_all()).where(lambda x: x.rank == rank).first_or_default(None)


def get_last():
    """returns the last rank advancement"""
    return query(get_all()).last_or_default(None)


def get_first():
    """returns the last rank advancement"""
    return query(get_all()).first_or_default(None)


def can_advance_rank():
    """returns True if the character is able to advance to the next rank
       using the same path as the previous rank
    """

    # normally a character is able to advance in the same school
    # unless the current school is a path

    return not api.data.schools.is_path(
        api.character.schools.get_current())


def can_abandon_path():
    """returns True if the character can abandon the current path to
       resume the former
    """

    return api.data.schools.is_path(
        api.character.schools.get_current())


def advance_rank():
    """advance the character in the same path as the previous rank
       returns False if this option is not available
    """

    # this function assumes that the character is able to
    # advance in the same path

    from l5r.models.advancements.rank import Rank
    adv = Rank()
    # the insight rank
    adv.rank = api.character.insight_rank()
    # this is the current school for this rank
    adv.school = api.character.schools.get_current()
    # no cost advancing in the same rank
    adv.cost = 0
    # description
    adv.desc = api.tr("Insight Rank {0}. School: {1} rank {2} ").format(
        adv.rank,
        api.data.schools.get(adv.school).name,
        api.character.schools.get_school_rank(adv.school) + 1
    )

    # get 3 spells each rank other than the first
    if api.data.schools.is_shugenja(adv.school) and adv.rank > 1:
        adv.gained_spells_count = __api.pc.get_spells_per_rank()

    # get 2 kiho each rank
    if api.data.schools.is_brotherhood_monk(adv.school) and adv.rank > 1:
        adv.gained_kiho_count = 2

    return api.character.append_advancement(adv)


def leave_path():
    """the character resume its former path"""

    # this function assumes that the character is
    # currently following an alternate path

    former_school_ = query(get_all()).where(
        lambda x: not api.data.schools.is_path(x)).order_by(a_('rank')).first_or_default(None)

    if not former_school_:
        log.api.error(u"former school not found. could not resume old path")
        return False

    from l5r.models.advancements.rank import Rank
    adv = Rank()
    # the insight rank
    adv.rank = api.character.insight_rank()
    # this is the current school for this rank
    adv.school = former_school_.school
    # no cost advancing in the same rank
    adv.cost = 0
    # description
    adv.desc = api.tr("Insight Rank {0}. School: {1} rank {2} ").format(
        adv.rank,
        api.data.schools.get(adv.school).name,
        api.character.schools.get_school_rank(adv.school) + 1
    )

    # get 3 spells each rank other than the first
    if api.data.schools.is_shugenja(adv.school) and adv.rank > 1:
        adv.gained_spells_count = __api.pc.get_spells_per_rank()

    # get 2 kiho each rank
    if api.data.schools.is_brotherhood_monk(adv.school) and adv.rank > 1:
        adv.gained_kiho_count = 2

    return api.character.append_advancement(adv)


def join_new(school_id):
    """the character joins a new school"""

    school_ = api.data.schools.get(school_id)
    if not school_:
        log.api.error(u"join_new, school not found: %s", school_id)
        return

    from l5r.models.advancements.rank import Rank
    adv = Rank()
    # the insight rank
    adv.rank = api.character.insight_rank()
    # this is the current school for this rank
    adv.school = school_id
    # no cost advancing in the same rank
    adv.cost = 0
    # description

    school_rank = api.character.schools.get_school_rank(adv.school)

    # get 3 spells each rank other than the first
    if api.data.schools.is_shugenja(school_id) and adv.rank > 1:
        adv.gained_spells_count = __api.pc.get_spells_per_rank()

    if api.data.schools.is_path(adv.school):
        # replaces current school
        adv.replaced = api.character.schools.get_current()
    else:
        school_rank += 1

        # get 2 kiho each rank
        # alternate path doesn't get the bonus
        if api.data.schools.is_brotherhood_monk(school_id) and adv.rank > 1:
            adv.gained_kiho_count = 2

    if school_.affinity:
        if 'any' in school_.affinity or 'nonvoid' in school_.affinity:
            adv.affinities_to_choose.append(school_.affinity)
        else:
            adv.affinities.append(school_.affinity)

    if school_.deficiency:
        if 'any' in school_.deficiency or 'nonvoid' in school_.deficiency:
            adv.deficiencies_to_choose.append(school_.deficiency)
        else:
            adv.deficiencies.append(school_.deficiency)

    adv.desc = api.tr("Insight Rank {0}. School: {1} rank {2} ").format(
        adv.rank,
        school_.name,
        school_rank
    )

    return api.character.append_advancement(adv)

def join_rank1_path(school_id):
    """the character replaces its first technique with a rank1 path"""

    school_ = api.data.schools.get(school_id)
    if not school_:
        log.api.error(u"join_rank1_path, school not found: %s", school_id)
        return

    from l5r.models.advancements.rank import Rank
    adv = Rank()
    # the insight rank
    adv.rank = 1
    # this is the current school for this rank
    adv.school = school_id
    # no cost advancing in the same rank
    adv.cost = 0
    # description

    school_rank = 1
    adv.replaced = api.character.schools.get_current()

    replaced_school = api.data.schools.get(adv.replaced)

    adv.desc = api.tr("Replaced {0} with {1} (Rank1)").format(
        replaced_school.name,
        school_.name,
    )

    return api.character.append_advancement(adv)


def clear_skills_to_choose():
    """clear the list of skills and emphases to choose on the current rank advancement"""
    rank_ = get_last()
    if rank_:
        rank_.skills_to_choose = []
        rank_.emphases_to_choose = []


def get_gained_kiho_count():
    """returns available free kiho"""
    rank_ = get_last()
    if not rank_:
        return 0
    return rank_.gained_kiho_count


def set_gained_kiho_count(value):
    """set left free kiho"""
    rank_ = get_last()
    if rank_:
        rank_.gained_kiho_count = value


def get_pending_spells_count():
    """returns the number of pending spells"""
    rank_ = api.character.rankadv.get_last()
    if not rank_:
        return 0
    return rank_.gained_spells_count


def get_starting_spells_to_choose():
    """returns the spells that the user can choose"""
    rank_ = api.character.rankadv.get_last()
    if not rank_:
        return []
    return rank_.spells_to_choose


def get_starting_skills_to_choose():
    """returns the skills that the user can choose"""
    rank_ = api.character.rankadv.get_last()
    if not rank_:
        return []
    return rank_.skills_to_choose


def get_starting_emphases_to_choose():
    """returns the emphases that the user can choose"""
    rank_ = api.character.rankadv.get_last()
    if not rank_:
        return []
    return rank_.emphases_to_choose


def clear_spells_to_choose():
    """clear the list of spells to choose on the current rank advancement"""
    rank_ = get_last()
    if rank_:
        rank_.spells_to_choose = []
        rank_.gained_spells_count = 0


def has_granted_free_spells():
    """returns True if the character is granted with more free spells"""

    # only grant free spells to shugenja characters
    if not api.character.is_shugenja():
        return False

    pending_spells_count_ = get_pending_spells_count()
    spells_to_choose_count_ = len(get_starting_spells_to_choose())

    return (pending_spells_count_ + spells_to_choose_count_) > 0


def has_granted_skills_to_choose():
    """return if the player can choose some skills or emphases"""
    rank_ = get_last()
    if rank_:
        return (len(rank_.skills_to_choose) + len(rank_.emphases_to_choose)) > 0
    return False


def has_granted_affinities_to_choose():
    """return if the player can choose some skills or emphases"""
    rank_ = get_last()
    if rank_:
        return len(rank_.affinities_to_choose) > 0
    return False


def has_granted_deficiencies_to_choose():
    """return if the player can choose some skills or emphases"""
    rank_ = get_last()
    if rank_:
        return len(rank_.deficiencies_to_choose) > 0
    return False
