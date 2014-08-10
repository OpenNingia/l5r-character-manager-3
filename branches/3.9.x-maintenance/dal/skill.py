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

class MasteryAbility(object):
    
    @staticmethod
    def build_from_xml(elem):
        f = MasteryAbility()
        f.rank = int(elem.attrib['rank'])
        f.rule = elem.attrib['rule'] if ('rule' in elem.attrib) else None
        f.desc = elem.text
        return f
        
class SkillCateg(object):        
    @staticmethod
    def build_from_xml(elem):
        f = SkillCateg()
        f.id = elem.attrib['id']
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
        
class Skill(object):

    @staticmethod
    def build_from_xml(elem):
        f = Skill()
        f.name  = elem.attrib['name']
        f.id    = elem.attrib['id']
        f.trait = elem.attrib['trait']
        f.type  = elem.attrib['type']
        f.tags  = [f.type]        
        if elem.find('Tags'):
            for se in elem.find('Tags').iter():
                if se.tag == 'Tag':
                    f.tags.append(se.text)
        f.mastery_abilities = []
        if elem.find('MasteryAbilities'):
            for se in elem.find('MasteryAbilities').iter():
                if se.tag == 'MasteryAbility':
                    f.mastery_abilities.append(MasteryAbility.build_from_xml(se))
        return f        
        
    def __str__(self):
        return self.name or self.id
        
    def __unicode__(self):
        return self.name

    def __eq__(self, obj):
        return obj and obj.id == self.id

    def __ne__(self, obj):
        return not self.__eq__(obj)
        
    def __hash__(self):
        return self.id.__hash__()

