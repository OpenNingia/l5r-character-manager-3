# -*- coding: utf-8 -*-
# Copyright (C) 2011 Daniele Simonetti
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.    See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.

import dal 
import os

# setup jinja2
from jinja2 import Environment, PackageLoader
env = Environment(loader=PackageLoader('l5rcm', 'templates'))

class ReportBuilder(object):
    '''Build an HTML summary of the dal contents'''
    def __init__(self, in_path, out_path):
        self.out_path = out_path
        self.in_path  = in_path
        self.data     = None

    def build(self):
        # load _all_ the packs
        self.data = dal.Data( [self.in_path] )
        
        data_map = {}
        
        core_pack = [ x for x in self.data.packs if x.id == 'core' ]
        pack_list = sorted([ x for x in self.data.packs if x.id != 'core' ], cmp=lambda x,y: cmp(x.display_name, y.display_name) )
        
        for p in self.data.packs:
            # build content summary for each pack in different files
            data_map[ p.id ] = self.get_pack_data(p)
	
        # finally build the index
        self.build_index(core_pack + pack_list, data_map)

    def build_index(self, packs, pack_data):
        o = os.path.join(self.out_path, "index.html")        
        tmpl = env.get_template('index.thtml')
        
        with open(o, 'wt') as fobj:
            fobj.write( tmpl.render(packs = packs, pack_data = pack_data) )

    def build_pack_report(self, pack):
        o = os.path.join(self.out_path, pack.id + ".html")
        tmpl = env.get_template('pack.thtml')
        
        # load a single package
        dp = dal.Data( [pack.path] )
        print(dp.__dict__)
        
        with open(o, 'wt') as fobj:
            fobj.write( tmpl.render(pack = pack, data = dp) )     
            
    def get_pack_data(self, pack):
        # load a single package
        return dal.Data( [pack.path] )
        
        