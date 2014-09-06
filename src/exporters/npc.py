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

import dal
import dal.query
import models
import rules
from fdfexporter import FDFExporter, zigzag

class FDFExporterTwoNPC(FDFExporter):
    def __init__(self, dstore, pcs):
        super(FDFExporterTwoNPC, self).__init__()

        self.dstore = dstore
        self.pcs    = pcs

    def export_body(self, io):
        f = self.form

        fields = {}

        for i, pc in enumerate( self.pcs ):
            self.export_npc( i + 1, pc, fields )

        # EXPORT FIELDS
        for k in fields.iterkeys():
            self.export_field(k, fields[k], io)

    def get_skills_sorted( self, pc, key ):

        skill_list = []
        for s in pc.get_skills():
            sk_obj = dal.query.get_skill( self.dstore, s )
            if not sk_obj: continue
            o = {
            'id': s,
            'rank': pc.get_skill_rank(s),
            'name': sk_obj.name,
            'emph': ', '.join( pc.get_skill_emphases(s) ) }

            skill_list.append( o )

        return sorted( skill_list, key=key )

    def fmt_skill_line( self, sk ):
        if len( sk['emph'] ) > 0:
            return "{nm} {r} ({e})".format( nm=sk['name'], r=sk['rank'], e=sk['emph'] )
        return "{nm} {r}".format( nm=sk['name'], r=sk['rank'] )

    def export_npc(self, index, pc, fields ):

        def _af( name, value, idx = index ):
            fields['{}{}'.format(name, idx)] = str(value)


        clan_obj = dal.query.get_clan( self.dstore, pc.clan )
        if clan_obj:
            _af( "Clan", clan_obj.name )

        name = ""
        family_obj  = dal.query.get_family( self.dstore, pc.family )
        if family_obj:
            name = "{} {}".format( family_obj.name, pc.name )
        else:
            name = pc.name
        _af( "Name", name )

        sobj = dal.query.get_school( self.dstore, pc.get_school_id() )
        if sobj:
            _af("School", sobj.name)

        _af("Rank", pc.get_insight_rank())
        _af("Insight", pc.get_insight())
        _af("XP", pc.get_px())

        # rings
        _af("Earth", pc.get_ring_rank( models.RINGS.EARTH ) )
        _af("Air"  , pc.get_ring_rank( models.RINGS.AIR ) )
        _af("Water", pc.get_ring_rank( models.RINGS.WATER ) )
        _af("Fire" , pc.get_ring_rank( models.RINGS.FIRE ) )
        _af("Void" , pc.get_ring_rank( models.RINGS.VOID ) )

        # traits
        _af("Stamina"     , pc.get_attrib_rank( models.ATTRIBS.STAMINA ) )
        _af("Willpower"   , pc.get_attrib_rank( models.ATTRIBS.WILLPOWER ) )
        _af("Reflexes"    , pc.get_attrib_rank( models.ATTRIBS.REFLEXES ) )
        _af("Awareness"   , pc.get_attrib_rank( models.ATTRIBS.AWARENESS ) )
        _af("Strength"    , pc.get_attrib_rank( models.ATTRIBS.STRENGTH ) )
        _af("Perception"  , pc.get_attrib_rank( models.ATTRIBS.PERCEPTION ) )
        _af("Agility"     , pc.get_attrib_rank( models.ATTRIBS.AGILITY ) )
        _af("Intelligence", pc.get_attrib_rank( models.ATTRIBS.INTELLIGENCE ) )

        _af("Initiative", rules.format_rtk_t(pc.get_tot_initiative()) )
        _af("Armor"     , pc.get_cur_tn () )
        _af("Reduction" , pc.get_full_rd() )

        # HEALTH
        w_labels = ['Healthy', 'Nicked', 'Grazed',
                    'Hurt', 'Injured', 'Crippled',
                    'Down', 'Out']

        hl = [0]*8
        for i in range(0, 8):
            if i == 0: hl[i] = pc.get_health_rank(i)
            else: hl[i] = pc.get_health_rank(i) + hl[i-1]
            _af( w_labels[i], hl[i] )

        # WEAPONS
        melee_weapons = [ x for x in pc.get_weapons() if 'melee' in x.tags     ]
        range_weapons = [ x for x in pc.get_weapons() if 'ranged' in x.tags and 'melee' not in x.tags ]

        wl  = zigzag(melee_weapons, range_weapons)

        for i, weapon in enumerate( wl ):
            if i >= 2: break
            j = (index-1)*2 + i + 1
            _af( "Type"  , weapon.name, j )
            atk_roll = rules.format_rtk_t(rules.calculate_mod_attack_roll (pc, weapon))
            _af( "Attack", atk_roll, j )
            dmg_roll = rules.format_rtk_t(rules.calculate_mod_damage_roll (pc, weapon))
            _af( "Damage", atk_roll, j )
            _af( "Notes", weapon.desc, j )

        # OTHER TRAITS
        _af("Status" , pc.get_status() )
        _af("Honor"  , pc.get_honor () )
        _af("Glory"  , pc.get_glory () )
        _af("GloryTN", int(50 - pc.get_glory() * 5) )

        # SKILLS
        skills = self.get_skills_sorted( pc, lambda x: x['rank'] )
        # divide in 5 lists
        skill_per_line = max( 5, len(skills) / 5 )

        # offset
        off = 0

        for i in range(0, 5):
            sks = []
            if i == 4:
                sks = skills[ off: ]
            else:
                sks = skills[ off:off+skill_per_line ]

            if len( sks ) == 0: break

            skill_line = ', '.join( [ self.fmt_skill_line(x) for x in sks ] )

            fn = "Skill  Rank Emphases {}".format(i+1)
            if index > 1:
                fn += "_2"

            fields[fn] = skill_line

            off += skill_per_line
