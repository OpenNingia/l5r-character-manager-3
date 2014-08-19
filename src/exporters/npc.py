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
from fdfexporter import FDFExporter

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

    def export_npc(self, index, pc, fields ):

        def _af( name, value ):
            fields['{}{}'.format(name, index)] = str(value)

        family_name = ""
        if pc.family:
            family_name = dal.query.get_family( self.dstore, pc.family ).name + " "

        _af( "Name", "{}{}".format(family_name, pc.name) )
        _af( "Clan", dal.query.get_clan( self.dstore, pc.clan ).name )
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

        # WOUNDS
        w_labels = ['Healthy', 'Nicked', 'Grazed',
                    'Hurt', 'Injured', 'Crippled',
                    'Down', 'Out']

        hl = [0]*8
        for i in range(0, 8):
            if i == 0: hl[i] = pc.get_health_rank(i)
            else: hl[i] = pc.get_health_rank(i) + hl[i-1]
            _af( w_labels[i], hl[i] )
