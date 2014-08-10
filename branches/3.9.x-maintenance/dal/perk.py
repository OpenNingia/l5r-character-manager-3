# -*- coding: iso-8859-1 -*-
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

from xmlutils import *

class PerkCateg(object):        
    @staticmethod
    def build_from_xml(elem):
        f = PerkCateg()
        f.id   = elem.attrib['id']
        f.name = elem.text
        return f
    
    def __str__(self):
        return self.name
        
    def __unicode__(self):
        return self.name        
        
    def __eq__(self, obj):
        return obj and obj.id == self.id
        
    def __ne__(self, obj):
        return not self.__eq__(obj)
        
    def __hash__(self):
        return self.id.__hash__()        
        
class PerkException(object):
    
    @staticmethod
    def build_from_xml(elem):
        f = PerkException()
        f.tag   = elem.attrib['tag']
        f.value = int(elem.attrib['value'])       
        return f
        
class PerkRank(object):
    
    @staticmethod
    def build_from_xml(elem):
        f = PerkRank()
        f.id    = int(elem.attrib['id'])
        f.value = int(elem.attrib['value'])
        f.exceptions = []        
        for se in elem.iter():
            if se.tag == 'Exception':
                f.exceptions.append(PerkException.build_from_xml(se))       
        
        return f

class Perk(object):

    @staticmethod
    def build_from_xml(elem):
        f = Perk()
        f.name  = elem.attrib['name']
        f.id    = elem.attrib['id']
        f.type  = elem.attrib['type']
        f.rule  = elem.attrib['rule'] if ('rule' in elem.attrib) else f.id
        f.desc  = read_sub_element_text(elem, 'Description', "")
        f.ranks = []
        for se in elem.iter():
            if se.tag == 'Rank':
                f.ranks.append(PerkRank.build_from_xml(se))
        return f        
        
    def get_rank_value(self, rank):
        for r in self.ranks:
            if r.id == rank: return r.value
        return None
        
    def __str__(self):
        return self.name or self.id

    def __unicode__(self):
        return self.name or self.id
        
    def __eq__(self, obj):
        return obj and obj.id == self.id

    def __ne__(self, obj):
        return not self.__eq__(obj)
        
    def __hash__(self):
        return self.id.__hash__()