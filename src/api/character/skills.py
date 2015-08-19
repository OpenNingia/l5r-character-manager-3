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

from api import __api

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

