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

from l5r.models.chmodel import ring_name_from_id, attrib_name_from_id
from copy import copy
import l5r.api as api
import l5r.api.character
import l5r.api.character.schools


class CharacterSnapshot(object):

    def __init__(self, pc):
        self.model = pc

        self.skills = {}  # id ==> value
        self.traits = {}  # id ==> value
        self.rings = {}  # id ==> value
        self.emphases = {}  # skill_id => [emphases]

        self.tags = []  # tag list
        self.rules = []  # rules list

        self.schools = {}  # id ==> rank

        self.insight_rank = 0

        self.model = None

        self.honor = 0.0
        self.glory = 0.0

        for k in api.character.skills.get_all():
            self.skills[k] = api.character.skills.get_skill_rank(k)
            self.emphases[k] = api.character.skills.get_skill_emphases(k)

        for t in api.data.traits():
            self.traits[t] = api.character.trait_rank(t)

        for r in api.data.rings():
            self.rings[r] = api.character.ring_rank(r)

        for s in api.character.schools.get_all():
            self.schools[s] = api.character.schools.get_school_rank(s)

        self.tags += api.character.get_tags()
        self.rules += api.character.get_rules()

        self.insight_rank = api.character.insight_rank()
        self.honor = api.character.honor()
        self.glory = api.character.glory()

    def get_skills(self):
        return self.skills.keys()

    def get_skill_rank(self, id_):
        if id_ in self.skills:
            return self.skills[id_]
        return 0

    def set_skill_rank(self, id_, val):
        self.skills[id_] = val

    def get_ring_rank(self, id_):
        if id_ in self.rings:
            return self.rings[id_]
        return 0

    def set_ring_rank(self, id_, val):
        self.rings[id_] = val

    def get_trait_rank(self, id_):
        if id_ in self.traits:
            return self.traits[id_]
        return 0

    def set_trait_rank(self, id_, val):
        self.traits[id_] = val

    def has_tag(self, tag):
        return tag in self.tags

    def has_rule(self, rule):
        return rule in self.rules

    def get_schools(self):
        return self.schools.keys()

    def get_school_rank(self, id_):
        if id_ in self.schools:
            return self.schools[id_]
        return 0

    def set_school_rank(self, id_, val):
        self.schools[id_] = val

    def get_skill_emphases(self, skid):
        if skid not in self.emphases:
            return []
        return self.emphases[skid]

    def get_insight_rank(self):
        return self.insight_rank

    def get_honor(self):
        return self.honor

    def get_glory(self):
        return self.glory
