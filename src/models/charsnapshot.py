# Copyright (C) 2011 Daniele Simonetti
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

from chmodel import ring_name_from_id, attrib_name_from_id
from copy import copy

class CharacterSnapshot(object):

    skills   = {} # id ==> value
    traits   = {} # id ==> value
    rings    = {} # id ==> value

    tags     = [] # tag list
    rules    = [] # rules list

    schools  = {} # id ==> rank

    insight_rank = 0

    model  = None

    honor  = 0.0

    def __init__(self, pc):
        self.model = pc

        for k, v in [ (x, pc.get_skill_rank(x)) for x in pc.get_skills() ]:
            self.skills[k] = v

        for k, v in [ (attrib_name_from_id(i), pc.get_attrib_rank(i)) for i in xrange(0, 8) ]:
            self.traits[k] = v

        for k, v in [ (ring_name_from_id(i), pc.get_ring_rank(i)) for i in xrange(0, 5) ]:
            self.rings[k] = v
            
        for k, v in [ (x.school_id, pc.get_school_rank(x)) for x in pc.schools ]:
            self.schools[k] = v            
            
        self.tags += pc.tags
        self.tags += pc.step_1.tags
        for s in pc.schools:
            self.tags += s.tags
                        
        for s in pc.schools:
            self.rules += s.tech_rules
        self.rules += [ x.rule for x in pc.advans if hasattr(x,'rule') ]

        self.insight_rank = pc.get_insight_rank()
        self.honor        = pc.get_honor()

    def get_skills(self):
        return self.model.get_skills()

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
        return self.model.get_skill_emphases(skid)

    def get_insight_rank(self):
        return self.insight_rank

    def get_honor(self):
        return self.honor
