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

import advances as adv
import outfit
import modifiers
import dal.school
import json
import os
import api.rules

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
        print("unknown trait_id: {0}".format(attrib_id))
        return None


def get_ring_id_from_attrib_id(attrib_id):
    if ATTRIBS.STAMINA <= attrib_id <= ATTRIBS.INTELLIGENCE:
        return attrib_id // 2
    return -1


class MyJsonEncoder(json.JSONEncoder):

    def default(self, obj):
        if hasattr(obj, '__dict__'):
            return obj.__dict__
        return json.JSONEncoder.default(self, obj)

    def encode_pc_model(self, obj):
        if isinstance(obj, BasePcModel) or \
           isinstance(obj, AdvancedPcModel):
            return obj.__dict__
        return json.JSONEncoder.default(self, obj)


class BasePcModel(object):

    def __init__(self):
        self.void = 0
        self.attribs = [0, 0, 0, 0, 0, 0, 0, 0]
        self.skills = {}
        self.emph = {}
        self.pending_wc = []
        self.pending_wc_emph = []
        self.pending_wc_spell = []
        self.tags = []
        self.honor = 0.0
        self.glory = 0.0
        self.infamy = 0.0
        self.status = 0.0
        self.taint = 0.0

        self.start_spell_count = 0
        self.school_tech = None

    def load_default(self):
        self.void = 2
        self.attribs = [2, 2, 2, 2, 2, 2, 2, 2]
        self.rank = 1
        #self.glory = 1.0
        #self.status = 1.0

    def add_tag(self, tag):
        if tag not in self.tags:
            self.tags.append(tag)

    def has_tag(self, tag):
        return tag in self.tags

    def del_tag(self, tag):
        if tag in self.tags:
            self.tags.remove(tag)

    def clear_tags(self):
        self.tags = []


class CharacterSchool(object):

    def __init__(self, school_id=0):
        self.school_id = school_id
        self.school_rank = 1
        self.techs = []
        self.tech_rules = []
        self.skills = {}
        self.emph = {}
        self.spells = []
        self.tags = []
        self.outfit = []
        self.affinity = None
        self.deficiency = None

        # alternate path
        self.is_path = False
        self.path_rank = 0

    def add_tag(self, tag):
        if tag not in self.tags:
            self.tags.append(tag)

    def has_tag(self, tag):
        return tag in self.tags

    def del_tag(self, tag):
        if tag in self.tags:
            self.tags.remove(tag)

    def clear_tags(self):
        self.tags = []


class AdvancedPcModel(BasePcModel):

    def __init__(self):
        super(AdvancedPcModel, self).__init__()

        # clan selection
        self.step_0 = BasePcModel()
        # family selection
        self.step_1 = BasePcModel()
        # school selection
        self.step_2 = BasePcModel()

        self.unsaved = False
        self.version = '0.0'

        self.name = ''
        self.clan = None
        self.school = None
        self.family = None

        self.insight = 0
        self.advans = []

        self.armor = None
        self.weapons = []
        self.schools = []
        self.outfit = []
        self.money = (0, 0, 0)

        self.mastery_abilities = []
        self.current_school_id = ''

        self.attrib_costs = [4, 4, 4, 4, 4, 4, 4, 4]
        self.void_cost = 6
        self.health_multiplier = 2
        self.spells_per_rank = 3
        self.pending_spells_count = 0
        self.exp_limit = 40
        self.wounds = 0
        self.mod_init = (0, 0)
        self.void_points = 0
        self.extra_notes = ''
        self.insight_calculation = 1
        self.free_kiho_count = 0
        self.can_get_another_tech = False

        self.pack_refs = []
        self.modifiers = []
        self.properties = {}

    def load_default(self):
        self.step_0.load_default()

    def is_dirty(self):
        return self.unsaved

    def get_free_kiho_count(self):
        return self.free_kiho_count

    def set_free_kiho_count(self, value):
        self.free_kiho_count = value

    def set_current_school_id(self, school_id):
        self.current_school_id = school_id

    def get_current_school_id(self):
        return self.current_school_id

    def get_attrib_cost(self, idx):
        return self.attrib_costs[idx]

    def get_pending_wc_skills(self):
        return self.step_2.pending_wc

    def get_pending_wc_emphs(self):
        return self.step_2.pending_wc_emph

    def get_pending_wc_spells(self):
        return self.step_2.pending_wc_spell

    def can_get_other_techs(self):
        return self.can_get_another_tech

    def set_can_get_other_tech(self, flag):
        self.can_get_another_tech = flag

    def get_school_spells_qty(self):
        return self.step_2.start_spell_count

    def can_get_other_spells(self):
        if not self.has_tag('shugenja'):
            return False
        return self.get_pending_spells_count() > 0 or len(self.get_pending_wc_spells())

    def get_how_many_spell_i_miss(self):
        if not self.has_tag('shugenja'):
            return 0
        return self.get_pending_spells_count()

    def get_spells_per_rank(self):
        return self.spells_per_rank

    def set_spells_per_rank(self, value):
        self.spells_per_rank = value

    def set_pending_spells_count(self, value):
        self.pending_spells_count = value

    def get_pending_spells_count(self):
        return self.pending_spells_count

    def set_pending_kiho_count(self, value):
        self.pending_kiho_count = value

    def get_pending_kiho_count(self):
        return self.pending_kiho_count

    def can_get_other_kiho(self):
        if not self.has_tag('monk'):
            return False
        return self.get_pending_kiho_count() > 0

    def get_how_many_kiho_i_miss(self):
        if not self.has_tag('monk'):
            return 0
        return self.get_pending_kiho_count()

    def get_weapons(self):
        return self.weapons

    def get_modifiers(self, filter_type=None):
        if not filter_type:
            return self.modifiers
        return filter(lambda x: x.type == filter_type, self.modifiers)

    def add_pending_wc_skill(self, wc):
        self.step_2.pending_wc.append(wc)
        self.unsaved = True

    def add_pending_wc_spell(self, wc):
        self.step_2.pending_wc_spell.append(wc)
        self.unsaved = True

    def add_pending_wc_emph(self, wc):
        self.step_2.pending_wc_emph.append(wc)
        self.unsaved = True

    def clear_pending_wc_skills(self):
        self.step_2.pending_wc = []
        self.unsaved = True

    def clear_pending_wc_spells(self):
        self.step_2.pending_wc_spell = []
        self.unsaved = True

    def clear_pending_wc_emphs(self):
        self.step_2.pending_wc_emph = []
        self.unsaved = True

    def add_weapon(self, item):
        self.weapons.append(item)

    def add_modifier(self, item):
        self.modifiers.append(item)

    def set_family(self, family_id=0, perk=None, perkval=1, tags=[]):
        if self.family == family_id:
            return
        self.step_1 = BasePcModel()
        self.unsaved = True
        self.family = family_id
        if family_id == 0:
            return

        for t in tags:
            self.step_1.add_tag(t)

        # void ?
        if perk == 'void':
            self.step_1.void += perkval
            return True
        else:
            a = attrib_from_name(perk)
            if a >= 0:
                self.step_1.attribs[a] += perkval
                return True
        return False

    def set_school(self, school_id=0, perk=None, perkval=1,
                   honor=0.0, tags=[]):
        if self.school == school_id:
            return
        self.step_2 = BasePcModel()
        self.schools = []
        self.unsaved = True
        self.school = school_id
        self.clear_pending_wc_skills()
        self.clear_pending_wc_spells()
        self.clear_pending_wc_emphs()
        if school_id == 0:
            return

        self.schools = [CharacterSchool(school_id)]
        self.step_2.honor = honor
        self.set_current_school_id(school_id)

        for t in tags:
            self.schools[0].add_tag(t)


    def set_school_spells_qty(self, qty):
        self.step_2.start_spell_count = qty

    def set_void_points(self, value):
        self.void_points = value
        self.unsaved = True

    def add_advancement(self, adv):
        self.advans.append(adv)
        self.unsaved = True

    # properties
    def has_property(self, name):
        return name not in self.properties

    def get_property(self, name, default=''):
        if name not in self.properties:
            self.properties[name] = default
        return self.properties[name]

    def set_property(self, name, value):
        self.properties[name] = value
        self.unsaved = True

# LOAD AND SAVE METHODS ###

    def save_to(self, file):
        self.unsaved = False

        print('saving to', file)

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
            for k in in_dict.iterkeys():
                out_obj.__dict__[k] = in_dict[k]

        fp = open(file_, 'rt')
        if fp:
            obj = json.load(fp)
            fp.close()

            _load_obj(deepcopy(obj), self)

            self.step_0 = BasePcModel()
            self.step_1 = BasePcModel()
            self.step_2 = BasePcModel()

            _load_obj(deepcopy(obj['step_0']), self.step_0)
            _load_obj(deepcopy(obj['step_1']), self.step_1)
            _load_obj(deepcopy(obj['step_2']), self.step_2)

            # pending wildcard object in step2
            self.step_2.pending_wc = []
            if 'pending_wc' in obj['step_2']:
                for m in obj['step_2']['pending_wc']:
                    item = dal.school.SchoolSkillWildcardSet()
                    _load_obj(deepcopy(m), item)
                    for i in xrange(0, len(item.wildcards)):
                        s_item = dal.school.SchoolSkillWildcard()
                        _load_obj(deepcopy(item.wildcards[i]), s_item)
                        item.wildcards[i] = s_item

                    self.add_pending_wc_skill(item)

            # schools
            self.schools = []
            if 'schools' in obj:
                for s in obj['schools']:
                    item = CharacterSchool()
                    _load_obj(deepcopy(s), item)
                    self.schools.append(item)

            self.advans = []
            for ad in obj['advans']:
                a = adv.Advancement(None, None)
                _load_obj(deepcopy(ad), a)
                self.advans.append(a)

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

            try:
                if self.get_current_school() is None and len(self.schools) > 0:
                    print('missing current school. old save?')
                    self.current_school_id = self.schools[-1].school_id
            except:
                print('cannot recover current school')

            self.unsaved = False
            return True
        return False
