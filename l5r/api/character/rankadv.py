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
from models.advancements.rank import Rank
from asq.initiators import query
from asq.selectors import a_

import api.character.schools
import api.data.merits

from util import log


def all():
    if not __api.pc:
        return []
    return query(__api.pc.advans).where(lambda x: x.type == 'rank').to_list()


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

    from models.advancements.rank import Rank
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

    api.character.append_advancement(adv)


def leave_path():
    """the character resume its former path"""

    # this function assumes that the character is
    # currently following an alternate path

    former_school_ = query(all()).where(
        lambda x: not api.data.schools.is_path(x)).order_by(a_('rank')).first_or_default()

    if not former_school_:
        log.api.error(u"former school not found. could not resume old path")
        return False


    from models.advancements.rank import Rank
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

    api.character.append_advancement(adv)


def join_new(school_id):
    """the character joins a new school"""

    from models.advancements.rank import Rank
    adv = Rank()
    # the insight rank
    adv.rank = api.character.insight_rank()
    # this is the current school for this rank
    adv.school = school_id
    # no cost advancing in the same rank
    adv.cost = 0
    # description
    adv.desc = api.tr("Insight Rank {0}. School: {1} rank {2} ").format(
        adv.rank,
        api.data.schools.get(adv.school).name,
        api.character.schools.get_school_rank(adv.school) + 1
    )

    api.character.append_advancement(adv)
