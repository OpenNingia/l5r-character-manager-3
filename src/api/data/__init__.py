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


import dal.query
from api import __api


def set_locale(loc):
    """set data locale"""
    __api.locale = loc


def set_blacklist(blk):
    """set data blacklist"""
    __api.blacklist = blk


def get_blacklist():
    """return data blacklist"""
    return __api.blacklist


def reload():
    """reloads data from storage"""
    __api.reload()


def get_trait(trait_id):
    """returns the trait from the given id"""
    if not __api.ds:
        return None
    return dal.query.get_trait(__api.ds, trait_id)


def get_ring(ring_id):
    """returns the ring from the given id"""
    if not __api.ds:
        return None
    return dal.query.get_ring(__api.ds, ring_id)


def get_trait_or_ring(traitid):
    """returns the trait or the ring from the given id"""
    if not __api.ds:
        return None
    return (dal.query.get_trait(__api.ds, traitid) or
            dal.query.get_ring(__api.ds, traitid))


def rings():
    """returns all the rings"""
    if not __api.ds:
        return []
    return __api.ds.rings


def traits():
    """returns all the traits"""
    if not __api.ds:
        return []
    return __api.ds.traits


def get_trait_ring(trait_id):
    """
        # earth ring
        STAMINA
        WILLPOWER

        # air ring
        REFLEXES
        AWARENESS

        # water ring
        STRENGTH
        PERCEPTION

        # fire ring
        AGILITY
        INTELLIGENCE
    """
    if trait_id == 'stamina' or trait_id == 'willpower':
        return get_ring('earth')
    if trait_id == 'reflexes' or trait_id == 'awareness':
        return get_ring('air')
    if trait_id == 'strength' or trait_id == 'perception':
        return get_ring('water')
    if trait_id == 'agility' or trait_id == 'intelligence':
        return get_ring('fire')


def model():
    """returns data access model"""
    return __api.ds


def packs():
    """returns loaded data packs"""
    if not __api.ds:
        return []
    return __api.ds.get_packs()


class CMErrors(object):
    NO_ERROR = 'no_error'
    NOT_ENOUGH_XP = 'not_enough_xp'
