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

from l5r.models.advances import Advancement


class Rank(Advancement):
    def __init__(self):
        super(Rank, self).__init__('rank', 0)

        # the insight rank
        self.rank = 0
        # this is the current school for this rank
        self.school = None
        # the school rank
        self.school_rank = 0
        # the school optionally replaced by this one
        self.replaced = None
        # skills obtained with the rank advancement
        self.skills = []
        self.skills_to_choose = []
        # emphases to skills ( skill_id => [list] )
        self.emphases = {}
        self.emphases_to_choose = []
        # spells
        self.spells = []
        self.spells_to_choose = []
        self.gained_spells_count = 0
        # outfit
        self.outfit = []
        # money
        self.money = (0, 0, 0)
        # affinities
        self.affinities = []
        self.affinities_to_choose = []
        # deficiencies
        self.deficiencies = []
        self.deficiencies_to_choose = []
        # kiho gained with rank advancement
        self.kiho = []
        self.gained_kiho_count = 0
        # merits gained along starting school
        self.merits = []
        # flaws gained along starting school
        self.flaws = []


class StartingSkill(object):
    def __init__(self, skill_id, rank=1, emphasis=None):
        self.skill_id = skill_id
        self.rank = rank
        self.emphasis = emphasis

    def to_dict(self):
        out = {'skill_id': self.skill_id, 'rank': self.rank, 'emphasis': self.emphasis}

        return out


class CustomStartingSkill(object):
    def __init__(self, options, rank=1):
        self.rank = rank
        self.options = options  # ( value, modifier )

    def to_dict(self):
        out = {'rank': self.rank, 'options': self.options}

        return out


class CustomStartingSpells(object):
    def __init__(self, element, tag, count=1):
        self.element = element
        self.tag = tag
        self.count = count

    def to_dict(self):
        return {'element': self.element, 'tag': self.tag, 'count': self.count}
