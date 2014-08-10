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

# check if the dal has corrected data

import models
import dal

class DataCheck(object):
    d = None
    
    def __init__(self):
        self.d = dal.Data( ['./data_packs'] )
        
        self.tags =  [ x.id for x in self.d.clans    ]
        self.tags += [ x.id for x in self.d.families ]
        for s in self.d.schools:
            self.tags += s.tags        
    
    def check(self):
        self.check_many( self.d.skills, self.check_skill, 'skill'     )
        self.check_many( self.d.merits, self.check_perk , 'merit'     )
        self.check_many( self.d.flaws , self.check_perk , 'flaw'      )
        self.check_many( self.d.families, self.check_family, 'family' )
        self.check_many( self.d.schools,  self.check_school, 'school' )
        #self.check_schools ()
        
    def check_many(self, items, func, name):
        for i in items:
            if not func(i):
                print("{0} {1} fails.".format(name, i.id))
                
    def check_skill(self, i):
        ret = True
        # check skill category
        if len( [x for x in self.d.skcategs if x.id == i.type] ) == 0:
            print("skill category {0} not found".format(i.type))
            ret = False
        # check skill trait
        #if len( [x for x in self.d.traits if x.id == i.trait] + [x for x in self.d.rings if x.id == i.trait] ) == 0:
        #    print("skill trait {0} not found".format(i.trait))
        #    ret = False            
        return ret
        
    def check_perk(self, i):
        ret = True
        # check perk category
        if len( [x for x in self.d.perktypes if x.id == i.type] ) == 0:
            print("perk category {0} not found".format(i.type))
            ret = False     

        # check exception tags
        for r in i.ranks:
            for e in r.exceptions:
                if e.tag not in self.tags:
                    print("perk exception tag {0} not found".format(e.tag))
                    ret = False        
        return ret
        
    def check_family(self, i):
        ret = True
        #check clanid
        if len( [x for x in self.d.clans if x.id == i.clanid] ) == 0:
            print("clan {0} not found".format(i.clanid))
            ret = False            
        return ret
        
    def check_school(self, i):
        ret = True
        #check clanid
        if len( [x for x in self.d.clans if x.id == i.clanid] ) == 0:
            print("clan {0} not found".format(i.clanid))
            ret = False
        # check  trait
        if len( [x for x in self.d.traits if x.id == i.trait] + ['void'] ) == 0:
            print("school trait {0} not found".format(i.trait))
            ret = False

        # check affinity and deficiency
        if len( [x for x in self.d.rings if x.id == i.affinity] + ['void'] ) == 0:
            print("element {0} not found (affinity)".format(i.trait))
            ret = False        
        if len( [x for x in self.d.rings if x.id == i.deficiency] + ['void'] ) == 0:
            print("element {0} not found (deficiency)".format(i.trait))
            ret = False
          
        is_path_or_advanced = 'advanced' in i.tags or 'alternate' in i.tags
          
        # check honor value
        if i.honor == 0.0 and not is_path_or_advanced:
            print("warning. honor 0.0 can be a parsing error. school {0}".format(i.id))
            
        # check skills
        for s in i.skills:
            if len( [x for x in self.d.skills if x.id == s.id] ) == 0:
                print("skill {0} not found".format(s.id))
                ret = False   
        return ret
        
            
if __name__ == "__main__":
    dc = DataCheck()
    dc.check()
        
        
    
