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

from l5r.api import get_context

import l5rdal as dal
import l5rdal.query

from asq.initiators import query


def get_weapons():
    """returns all the weapons"""
    if not get_context().ds:
        return []
    return get_context().ds.weapons


def get_armors():
    """returns all the armors"""
    if not get_context().ds:
        return []
    return get_context().ds.armors


def get_weapon(weap_nm):
    """returns a weapon by name"""
    if not get_context().ds:
        return None
    return dal.query.get_weapon(get_context().ds, weap_nm)


def get_armor(armor_nm):
    """returns an armor by name"""
    if not get_context().ds:
        return None
    return dal.query.get_armor(get_context().ds, armor_nm)


def get_effect(effectid):
    """returns an item effect by id"""
    if not get_context().ds:
        return None
    return dal.query.get_weapon_effect(get_context().ds, effectid)

