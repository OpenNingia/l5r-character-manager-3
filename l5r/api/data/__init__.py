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

__TRAITS = [
    'stamina',
    'willpower',
    'reflexes',
    'awareness',
    'strength',
    'perception',
    'agility',
    'intelligence']

__RINGS = [
    'earth',
    'air',
    'water',
    'fire',
    'void'
]


def set_locale(loc):
    """set data locale"""
    get_context().locale = loc


def set_blacklist(blk):
    """set data blacklist"""
    get_context().blacklist = blk


def get_blacklist():
    """return data blacklist"""
    return get_context().blacklist


def reload():
    """reloads data from storage"""
    get_context().reload()


def rings():
    """return all rings"""
    return __RINGS


def traits():
    """return all traits"""
    return __TRAITS


def get_trait(trait_id):
    """returns the trait from the given id"""
    if not get_context().ds:
        return None
    return dal.query.get_trait(get_context().ds, trait_id)


def get_ring(ring_id):
    """returns the ring from the given id"""
    if not get_context().ds:
        return None
    return dal.query.get_ring(get_context().ds, ring_id)


def get_trait_or_ring(traitid):
    """returns the trait or the ring from the given id"""
    if not get_context().ds:
        return None
    return (dal.query.get_trait(get_context().ds, traitid) or
            dal.query.get_ring(get_context().ds, traitid))


#def rings():
#    """returns all the rings"""
#    if not get_context().ds:
#        return []
#    return get_context().ds.rings


#def traits():
#    """returns all the traits"""
#    if not get_context().ds:
#        return []
#    return get_context().ds.traits


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


def get_traits_by_ring(ring_id):
    """return the traits of the ring"""
    if ring_id == 'void':
        return 'void',

    if ring_id == 'earth':
        return 'stamina', 'willpower'
    if ring_id == 'air':
        return 'reflexes', 'awareness'
    if ring_id == 'water':
        return 'strength', 'perception'
    if ring_id == 'fire':
        return 'agility', 'intelligence'

    return None, None


def get_trait_by_index(trait_n):
    """return trait name from index"""
    if 0 <= trait_n <= len(__TRAITS):
        return get_trait(__TRAITS[trait_n])
    return None


def model():
    """returns data access model"""
    return get_context().ds


def set_model(value):
    """inject the data access model"""
    get_context().ds = value


def packs():
    """returns loaded data packs"""
    if not get_context().ds:
        return []
    return get_context().ds.get_packs()


def pack_by_id(pack_id):
    """return a pack by its id"""
    return query(packs()).where(lambda x: x.id == pack_id).first_or_default(None)


class CMErrors(object):
    NO_ERROR = 'no_error'
    NOT_ENOUGH_XP = 'not_enough_xp'
    INTERNAL_ERROR = 'internal_error'
    # the character's origin (family + school) is not yet set, so XP may not
    # be spent: the family/school starting trait bonuses must be locked in
    # first or they could be stacked on an already-bought rank (issue #448)
    MISSING_ORIGIN = 'missing_origin'


# Public submodules reached via attribute access (e.g. ``api.data.families``).
# They are resolved lazily on first access so they are always available
# regardless of import order — running a single test module in isolation no
# longer fails with ``module 'l5r.api.data' has no attribute 'families'``.
# Lazy (PEP 562) rather than eager imports here to avoid the circular import
# between these submodules and ``l5r.models.chmodel`` during package init.
_SUBMODULES = frozenset((
    'clans',
    'datapacks',
    'families',
    'flaws',
    'merits',
    'outfit',
    'powers',
    'schools',
    'skills',
    'spells',
))


def __getattr__(name):
    if name in _SUBMODULES:
        import importlib
        mod = importlib.import_module(f'{__name__}.{name}')
        globals()[name] = mod
        return mod
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
