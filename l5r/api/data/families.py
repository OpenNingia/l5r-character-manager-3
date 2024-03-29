# -*- coding: utf-8 -*-
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

from asq.initiators import query
from asq.selectors import a_
from l5r.api import __api


def get_all():
    """returns all families"""
    return __api.ds.families


def get(c):
    """returns a family by its family id"""
    return query(get_all()).where(lambda x: x.id == c).first_or_default(None)


def get_family_trait(fam):
    """return family trait"""
    family_ = get(fam)
    if not family_:
        return None
    return family_.trait
