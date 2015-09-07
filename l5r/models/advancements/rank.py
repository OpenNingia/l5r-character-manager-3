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
__author__ = 'Daniele'

from models.advances import Advancement


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
        # emphases to skills ( skill_id => [list] )
        self.emphases = {}
        # spells
        self.spells = []
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
        # self.value    = value
        #self.modifier = modifier

    def to_dict(self):
        out = {'rank': self.rank, 'options': self.options}

        return out


class CustomStartingSpells(object):
    def __init__(self, element, tag, count=1):
        self.element = element
        self.tag = tag
        self.count = count

    def to_dict(self):
        out = {}
        out['element'] = self.element
        out['tag'] = self.tag
        out['count'] = self.count

        return out
