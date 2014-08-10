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

import os
import re
import models

# global cache
_cache_names = {}

def parse_rtk(rtk):
    tk = rtk.split('k')
    if len(tk) != 2:
        return 0, 0
    # the sign of the first commands
    sign = -1 if int(tk[0]) < 0 else 1
    return int(tk[0]), int(tk[1])*sign
    
def parse_rtk_with_bonus(rtk):
    # 3k2+1
    rtk = rtk.replace(' ', '')
    print('parsing ' + rtk);
    if 'k' not in rtk:
        irtk = int(rtk)
        if irtk != 0:
            sign = '+' if irtk > 0 else '-'
            return parse_rtk_with_bonus('0k0'+sign+str(abs(irtk)))
        return 0, 0, 0
    m = re.match('([+-]?\\d{1,2})k(\\d{1,2})([+-]?\\d*)', rtk)
    if not m:
        return 0, 0, 0
    r, k, b = m.groups(1)
    sign = -1 if int(r) < 0 else 1
    try:
        return int(r), int(k)*sign, int(b)
    except:
        return int(r), int(k)*sign, 0

def format_rtk_t(rtk):    
    if len(rtk) == 3:
        return format_rtk(rtk[0], rtk[1], rtk[2])
    else:
        return format_rtk(rtk[0], rtk[1])     
    
def format_rtk(r, k, bonus = 0):
    #if r > 10:
    #    k += (r-10)
    #    r = 10
    #if k > 10:
    #    bonus = (k-10)*2
    #    k = 10
    #sign = -1 if r < 0 else 1
    #sign_chr = '-' if sign < 0 else '+'
    if bonus:        
        sign_chr = '-' if bonus < 0 else '+'  
        if r == k == 0:
            return '%s%d' % (sign_chr, abs(bonus))
        return '%dk%d %s %d' % (r, abs(k), sign_chr, abs(bonus))
    else:
        return '%dk%d' % (r, abs(k))
    
def get_random_name(path):
    global _cache_names
    
    names = []
    if path in _cache_names:
        names = _cache_names[path]
    else:
        f = open(path, 'rt')
        for l in f:
            if l.strip().startswith('*'):
                names.append( l.strip('* \n\r') )
        f.close()
        _cache_names[path] = names
    
    i = ( ord(os.urandom(1)) + ( ord(os.urandom(1)) << 8) ) % len(names)
    return names[i]
       
def insight_calculation_1(model):
    '''Default insight calculation method = Rings*10+Skills+SpecialPerks'''
    n = 0
    for i in xrange(0, 5):
        n += model.get_ring_rank(i)*10
    for s in model.get_skills():
        n += model.get_skill_rank(s)
    
    n += 3*model.cnt_rule('ma_insight_plus_3')
    n += 7*model.cnt_rule('ma_insight_plus_7')
    
    return n
    
def insight_calculation_2(model):
    '''Another insight calculation method. Similar to 1, but ignoring
       rank 1 skills
    '''
    n = 0
    for i in xrange(0, 5):
        n += model.get_ring_rank(i)*10
    for s in model.get_skills():
        sk = model.get_skill_rank(s)
        if sk > 1:
            n += sk
    
    n += 3*model.cnt_rule('ma_insight_plus_3')
    n += 7*model.cnt_rule('ma_insight_plus_7')
    
    return n
    
def insight_calculation_3(model):
    '''Another insight calculation method. Similar to 2, but
       school skill are counted even if rank 1
    '''
    school_skills = model.get_school_skills()
    
    n = 0
    for i in xrange(0, 5):
        n += model.get_ring_rank(i)*10
    for s in model.get_skills():
        sk = model.get_skill_rank(s)
        if sk > 1 or s in school_skills:
            n += sk
    
    n += 3*model.cnt_rule('ma_insight_plus_3')
    n += 7*model.cnt_rule('ma_insight_plus_7')
    
    return n
    
def split_decimal(value):
    import decimal
    decimal.getcontext().prec = 2
    d = decimal.Decimal(value)
    i = int(d)
    return (i, d-i)
    
def calculate_base_attack_roll(pc, weap):
    # base attack roll is calculated 
    # as xky where x is agility + weapon_skill_rank
    # and y is agility
    
    attrib = models.ATTRIBS.AGILITY
    if weap.skill_nm == 'Kyujutsu':
        attrib = models.ATTRIBS.REFLEXES
    
    trait   = pc.get_mod_attrib_rank(attrib)
    skill   = 0
    if weap.skill_id:
        skill = pc.get_skill_rank(weap.skill_id)
        print('calc base atk. trait: {0}, weap: {1}, skill: {2}, rank: {3}'
             .format(trait, weap.name, weap.skill_nm, skill))
            
    return trait+skill, trait
    
def calculate_mod_attack_roll(pc, weap):
    atk_r, atk_k = calculate_base_attack_roll(pc, weap)
    r_mod = 0
    k_mod = 0        

    # any roll bonuses
    anyr = pc.get_modifiers('anyr')
    for x in anyr:
        if x.active:
            r_mod += x.value[0]
            k_mod += x.value[1]
    
    # skill roll bonuses
    skir = pc.get_modifiers('skir')    
    for x in skir:
        if x.active and x.dtl == weap.skill_nm:            
            r_mod += x.value[0]
            k_mod += x.value[1]
            
    # weapon only modifiers to attack roll
    atkr = pc.get_modifiers('atkr')
    for x in atkr:
        if x.active and x.dtl == weap.name:            
            r_mod += x.value[0]
            k_mod += x.value[1]
            
    return atk_r+r_mod, atk_k+k_mod
    
def calculate_base_damage_roll(pc, weap):
    # base damage roll is calculated 
    # as xky where x is strength + weapon_damage
    # and y is strength
    
    attrib   = models.ATTRIBS.STRENGTH   
    trait    = pc.get_mod_attrib_rank(attrib)
    weap_str = 0
    try:
        weap_str = int(weap.strength)
    except:
        weap_str = 0
    
    if 'ranged' in weap.tags and weap_str > 0: 
        # ranged calculation is different
        # a weapon does have its own strength
        trait = min(weap_str, trait)
    
    drr, drk = parse_rtk(weap.dr)
                   
    return trait+drr, drk
    
def calculate_mod_damage_roll(pc, weap):
    dmg_r, dmg_k = calculate_base_damage_roll(pc, weap)
    r_mod = 0
    k_mod = 0        

    # any roll bonuses
    anyr = pc.get_modifiers('anyr')
    for x in anyr:
        if x.active:
            r_mod += x.value[0]
            k_mod += x.value[1]            
        
    # damage roll bonuses
    wdmg = pc.get_modifiers('wdmg')
    for x in wdmg:
        if x.active and x.dtl == weap.name:
            r_mod += x.value[0]
            k_mod += x.value[1]
            
    return dmg_r+r_mod, dmg_k+k_mod    
 