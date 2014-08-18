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

def get_clan(storage, id):
    try:
        return filter( lambda x: x.id == id, storage.clans )[0]
    except:
        return None
        
def get_family(storage, id):
    try:
        return filter( lambda x: x.id == id, storage.families )[0]
    except:
        return None
        
def get_school(storage, id):
    try:
        return filter( lambda x: x.id == id, storage.schools )[0]
    except:
        return None
        
def get_base_schools(storage):
    def is_base_school(school):
        return (len(school.require) == 0 and
                'advanced' not in school.tags and
                'alternate' not in school.tags)
    try:
        return [x for x in storage.schools if is_base_school(x)]
    except:
        return None
        
def get_school_tech(school_obj, rank):
    try:
        return filter( lambda x: x.rank == rank, school_obj.techs )[0]
    except:
        return None
        
def get_tech(storage, id):
    for sc in storage.schools:
        tech   = filter( lambda x: x.id == id, sc.techs )
        if len(tech): return sc, tech[0]
    return None, None 

def get_skill(storage, id):
    try:
        return filter( lambda x: x.id == id, storage.skills )[0]
    except:
        return None

def get_skills(storage, categ):
    return filter( lambda x: x.type == categ, storage.skills )
        
def get_spells(storage, ring, mastery):
    return filter( lambda x: x.element == ring and x.mastery == mastery, storage.spells )

def get_maho_spells(storage, ring, mastery):
    return filter( lambda x: x.element == ring and x.mastery == mastery and 'maho' in x.tags, storage.spells )
    
def get_mastery_ability_rule(storage, id, value):
    try:
        skill = get_skill(storage, id)
        return filter( lambda x: x.rank == value, skill.mastery_abilities )[0].rule        
    except:
        return None    
        
def get_kata(storage, id):
    try:
        return [x for x in storage.katas if x.id == id][0]
    except:
        return None
        
def get_kiho(storage, id):
    try:
        return [x for x in storage.kihos if x.id == id][0]
    except:
        print(id)
        return None        
        
def get_spell(storage, id):
    try:
        return filter( lambda x: x.id == id, storage.spells )[0]
    except:
        return None

def get_merit(storage, id):
    try:
        return [x for x in storage.merits if x.id == id][0]
    except:
        return None
        
def get_flaw(storage, id):
    try:
        return [x for x in storage.flaws if x.id == id][0]
    except:
        return None
        
def get_weapon(storage, name):
    try:
        return [x for x in storage.weapons if x.name == name][0]
    except:
        return None
        
def get_armor(storage, name):
    try:
        return [x for x in storage.armors if x.name == name][0]
    except:
        return None
        
def get_weapon_effect(storage, id):
    try:
        return [x for x in storage.weapon_effects if x.id == id][0]
    except:
        return None         
        
def get_ring(storage, id):
    try:
        return [x for x in storage.rings if x.id == id][0]
    except:
        return None
        
def get_trait(storage, id):
    try:
        return [x for x in storage.traits if x.id == id][0]
    except:
        return None        