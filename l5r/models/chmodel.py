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

from . import advances as adv
from . import outfit as outfit
from . import modifiers as modifiers
from .advancements.rank import Rank

import l5r.api.rules
import l5rdal.school

import json
import os


from copy import deepcopy

# RINGS


class RINGS:
    EARTH = 0
    AIR = 1
    WATER = 2
    FIRE = 3
    VOID = 4

    _names = dict(earth=0, air=1, water=2, fire=3, void=4)
    _ids = ['earth', 'air', 'water', 'fire', 'void']


def ring_from_name(name):
    if name in RINGS._names:
        return RINGS._names[name]
    return -1


def ring_name_from_id(ring_id):
    if 0 <= ring_id < len(RINGS._ids):
        return RINGS._ids[ring_id]


class ATTRIBS:
    # earth ring
    STAMINA = 0
    WILLPOWER = 1

    # air ring
    REFLEXES = 2
    AWARENESS = 3

    # water ring
    STRENGTH = 4
    PERCEPTION = 5

    # fire ring
    AGILITY = 6
    INTELLIGENCE = 7

    _names = dict(stamina=0, willpower=1, reflexes=2, awareness=3,
                  strength=4, perception=5, agility=6, intelligence=7)
    _ids = ['stamina', 'willpower', 'reflexes', 'awareness', 'strength',
            'perception', 'agility', 'intelligence']


def attrib_from_name(name):
    if name in ATTRIBS._names:
        return ATTRIBS._names[name]
    return -1


def attrib_name_from_id(attrib_id):
    if 0 <= attrib_id < len(ATTRIBS._ids):
        return ATTRIBS._ids[attrib_id]
    else:
        return None


class MyJsonEncoder(json.JSONEncoder):

    def default(self, obj):
        if hasattr(obj, '__dict__'):
            return obj.__dict__
        return json.JSONEncoder.default(self, obj)

    def encode_pc_model(self, obj):
        if isinstance(obj, AdvancedPcModel):
            return obj.__dict__
        return json.JSONEncoder.default(self, obj)


# DESERIALIZATION HELPERS ###
#
# json.dump flattens every object to its __dict__, so on the way back in a
# flat `out.__dict__[k] = in[k]` copy cannot rebuild objects *nested inside*
# another object. Only Rank advancements nest typed sub-objects, and the
# redeem flows read them by attribute -- so a reloaded character with pending
# choices would otherwise raise AttributeError (e.g. dict has no 'wildcards').
# These helpers rehydrate those nested objects to their original types.


def _rehydrate_wildcard_set(data):
    """Rebuild an l5rdal SchoolSkillWildcardSet (with its nested
    SchoolSkillWildcards) from the plain dict left by the JSON round-trip.
    A saved Rank stores these under `skills_to_choose`; the redeem flow
    (api.character.rankadv + the skill choosers, legacy and QML) reads
    `.wildcards` / `.rank` and each wildcard's `.value` / `.modifier` by
    attribute, which a bare dict cannot serve."""
    if not isinstance(data, dict):
        return data  # fresh, never-saved object: already the right type
    wc_set = l5rdal.school.SchoolSkillWildcardSet()
    wc_set.__dict__.update(data)
    rebuilt = []
    for w in (wc_set.wildcards or []):
        if isinstance(w, dict):
            wc = l5rdal.school.SchoolSkillWildcard()
            wc.__dict__.update(w)
            rebuilt.append(wc)
        else:
            rebuilt.append(w)
    wc_set.wildcards = rebuilt
    return wc_set


def _rehydrate_perk(data):
    """Rebuild a PerkAdv stored inside a Rank's `merits` / `flaws` list
    (school-granted merits/flaws). Consumers read `.perk` / `.rank` /
    `.cost` / `.tag` by attribute."""
    if not isinstance(data, dict):
        return data
    perk = adv.PerkAdv(None, None, 0)
    perk.__dict__.update(data)
    return perk


def _load_advancement(data):
    """Reconstruct a single advancement from its serialized dict.

    Rank advancements are the only ones nesting typed sub-objects
    (`skills_to_choose` wildcard sets, `merits` / `flaws` PerkAdvs); a flat
    __dict__ copy leaves those as plain dicts and every path that reads them
    by attribute then raises on a reloaded character. So a rank is rebuilt as
    a real Rank() -- which also back-fills defaults for fields a pre-feature
    save predates -- and its nested objects rehydrated. All other
    advancements carry only flat attributes, so the duck-typed generic
    Advancement the consumers already rely on is enough."""
    if data.get('type') == 'rank':
        a = Rank()
        a.__dict__.update(data)
        a.skills_to_choose = [_rehydrate_wildcard_set(x)
                              for x in (a.skills_to_choose or [])]
        a.merits = [_rehydrate_perk(x) for x in (a.merits or [])]
        a.flaws = [_rehydrate_perk(x) for x in (a.flaws or [])]
        # spells_to_choose entries are (element, count, tag) tuples; JSON
        # round-trips them to lists. Restore the tuple shape so the reloaded
        # rank is identical to the freshly-built one.
        a.spells_to_choose = [tuple(x) if isinstance(x, list) else x
                              for x in (a.spells_to_choose or [])]
        return a
    a = adv.Advancement(None, None)
    a.__dict__.update(data)
    return a


class AdvancedPcModel(object):

    def __init__(self):
        super(AdvancedPcModel, self).__init__()

        self.starting_traits = [2, 2, 2, 2, 2, 2, 2, 2]
        self.starting_void = 2

        self.void = 0
        self.attribs = [0, 0, 0, 0, 0, 0, 0, 0]

        self.honor = 0.0
        self.glory = 0.0
        self.infamy = 0.0
        self.status = 0.0
        self.taint = 0.0

        self.unsaved = False
        self.version = '0.0'

        self.name = ''
        self.clan = None
        self.family = None

        self.insight = 0
        self.advans = []

        self.armor = None
        self.weapons = []
        self.outfit = []
        self.money = (0, 0, 0)

        self.attrib_costs = [4, 4, 4, 4, 4, 4, 4, 4]
        self.void_cost = 6
        self.health_multiplier = 2
        self.health_base_multiplier = 5
        self.spells_per_rank = 3
        self.exp_limit = 40
        self.wounds = 0
        self.void_points = 0
        self.extra_notes = ''
        self.insight_calculation = 1

        self.pack_refs = []
        self.modifiers = []
        self.properties = {}

    def load_default(self):
        pass

    def is_dirty(self):
        return self.unsaved

    def get_attrib_cost(self, idx):
        return self.attrib_costs[idx]

    def get_spells_per_rank(self):
        return self.spells_per_rank

    def set_spells_per_rank(self, value):
        self.spells_per_rank = value

    def get_weapons(self):
        return self.weapons

    def get_modifiers(self, filter_type=None):
        if not filter_type:
            return self.modifiers
        return [x for x in self.modifiers if x.type == filter_type]

    def add_weapon(self, item):
        self.weapons.append(item)

    def add_modifier(self, item):
        self.modifiers.append(item)

    def set_family(self, family_id=0, perk=None, perkval=1, tags=()):
        pass

    def set_school(self, school_id=0, perk=None, perkval=1, honor=0.0, tags=()):
        pass

    def set_void_points(self, value):
        self.void_points = value
        self.unsaved = True

    def add_advancement(self, adv):
        self.advans.append(adv)
        self.unsaved = True

    # properties
    def has_property(self, name):
        return name in self.properties

    def get_property(self, name, default=''):
        if name not in self.properties:
            self.properties[name] = default
        return self.properties[name]

    def set_property(self, name, value):
        self.properties[name] = value
        self.unsaved = True

# LOAD AND SAVE METHODS ###

    def save_to(self, file, clear_dirty=True):
        # Autosave to the recovery file passes clear_dirty=False: the
        # work is mirrored to the recovery file but NOT to the
        # character's real .l5r, so the in-memory unsaved flag must
        # survive (the session still counts as having unsaved changes).
        if clear_dirty:
            self.unsaved = False

        fp = open(file, 'wt')
        if fp:
            json.dump(self, fp, cls=MyJsonEncoder, indent=2)
            fp.close()
            return True
        return False

    def load_from(self, file_):
        if len(file_) == 0 or not os.path.exists(file_):
            return False

        def _load_obj(in_dict, out_obj):
            for k in in_dict:
                out_obj.__dict__[k] = in_dict[k]

        fp = open(file_, 'rt')
        if fp:
            obj = json.load(fp)
            fp.close()

            _load_obj(deepcopy(obj), self)

            self.advans = []
            for ad in obj['advans']:
                self.advans.append(_load_advancement(deepcopy(ad)))

            # armor
            self.armor = outfit.ArmorOutfit()
            if obj['armor'] is not None:
                _load_obj(deepcopy(obj['armor']), self.armor)

            self.weapons = []
            if 'weapons' in obj:
                # weapons
                for w in obj['weapons']:
                    item = outfit.WeaponOutfit()
                    _load_obj(deepcopy(w), item)
                    self.add_weapon(item)

            self.modifiers = []
            if 'modifiers' in obj:
                for m in obj['modifiers']:
                    item = modifiers.ModifierModel()
                    _load_obj(deepcopy(m), item)
                    self.add_modifier(item)

            self.unsaved = False
            return True
        return False
