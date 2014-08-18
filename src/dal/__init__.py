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

from clan        import *
from family      import *
from school      import *
from skill       import *
from spell       import *
from perk        import *
from powers      import *
from weapon      import *
from generic     import *
from requirements import *

import os
import json
import xml.etree.ElementTree
import xml.etree.cElementTree as ET

class DataManifest(object):
    def __init__(self, d):
        self.id           = d['id']
        self.display_name = None
        self.language     = None
        self.version      = None
        self.update_uri   = None
        self.download_uri = None
        self.authors      = []
        self.active       = True
        self.path         = None

        if 'display_name' in d:
            self.display_name = d['display_name']
        if 'language' in d:
            self.language = d['language']
        if 'authors' in d:
            self.authors = d['authors']
        if 'version' in d:
            self.version = d['version']
        if 'update-uri' in d:
            self.update_uri = d['update-uri']
        if 'download-uri' in d:
            self.download_uri = d['download-uri']

class Data(object):
    def __init__(self, data_dirs = [], blacklist = []):
        self.rebuild(data_dirs, blacklist)

    def rebuild(self, data_dirs = [], blacklist = []):
        self.data_dirs = data_dirs

        self.blacklist = blacklist or []
        self.packs     = []

        self.clans     = []
        self.families  = []
        self.schools   = []

        self.spells    = []
        self.skills    = []
        self.merits    = []
        self.flaws     = []
        self.katas     = []
        self.kihos     = []

        self.weapons   = []
        self.armors    = []

        self.skcategs       = []
        self.perktypes      = []
        self.weapon_effects = []

        self.rings  = []
        self.traits = []

        for d in data_dirs:
            if d and os.path.exists(d):
                self.load_data(d)

    def append_to(self, collection, item):
        if item in collection:
            i = collection.index(item)
            collection[i] = item
        else:
            collection.append(item)

    def get_packs(self):
        return self.packs

    def load_data(self, data_path):
        # iter through all the data tree and import all xml files
        for path, dirs, files in os.walk(data_path):
            dirn = os.path.basename(path)

            if dirn.startswith('.'):
                continue

            try:
                manifest_path = os.path.join(path, 'manifest')
                if os.path.exists(manifest_path):
                    with open(manifest_path, 'r') as manifest_fp:
                        dm = DataManifest(json.load(manifest_fp))
                        if dm.id in self.blacklist:
                            dm.active = False
                        dm.path = path
                        self.packs.append(dm)
                        print('DATA PACK', dm.id, dm.display_name)
            except Exception as ex:
                print(ex)

            if dirn in self.blacklist:
                print('{0} is blacklisted'.format(dirn))
                continue

            for file_ in files:
                if file_.startswith('.') or file_.endswith('~'):
                    continue
                if not file_.endswith('.xml'):
                    continue
                try:
                    self.__load_xml(os.path.join(path, file_))
                except Exception as e:
                    print("cannot parse file {0}".format(file_))
                    import traceback
                    traceback.print_exc()
        self.__log_imported_data(data_path)

    def __load_xml(self, xml_file):
        #print('load data from {0}'.format(xml_file))
        tree = ET.parse(xml_file)
        root = tree.getroot()
        if root is None or root.tag != 'L5RCM':
            raise Exception("Not an L5RCM data file")
        for elem in list(root):
            if elem.tag == 'Clan':
                self.append_to(self.clans, Clan.build_from_xml(elem))
            elif elem.tag == 'Family':
                self.append_to(self.families, Family.build_from_xml(elem))
            elif elem.tag == 'School':
                self.append_to(self.schools, School.build_from_xml(elem))
            elif elem.tag == 'SkillDef':
                self.append_to(self.skills, Skill.build_from_xml(elem))
            elif elem.tag == 'SpellDef':
                self.append_to(self.spells, Spell.build_from_xml(elem))
            elif elem.tag == 'Merit':
                self.append_to(self.merits, Perk.build_from_xml(elem))
            elif elem.tag == 'Flaw':
                self.append_to(self.flaws, Perk.build_from_xml(elem))
            elif elem.tag == 'SkillCateg':
                self.append_to(self.skcategs, SkillCateg.build_from_xml(elem))
            elif elem.tag == 'KataDef':
                self.append_to(self.katas, Kata.build_from_xml(elem))
            elif elem.tag == 'KihoDef':
                self.append_to(self.kihos, Kiho.build_from_xml(elem))
            elif elem.tag == 'PerkCateg':
                self.append_to(self.perktypes, PerkCateg.build_from_xml(elem))
            elif elem.tag == 'EffectDef':
                self.append_to(self.weapon_effects, WeaponEffect.build_from_xml(elem))
            elif elem.tag == 'Weapon':
                self.append_to(self.weapons, Weapon.build_from_xml(elem))
            elif elem.tag == 'Armor':
                self.append_to(self.armors, Armor.build_from_xml(elem))
            elif elem.tag == 'RingDef':
                self.append_to(self.rings, GenericId.build_from_xml(elem))
            elif elem.tag == 'TraitDef':
                self.append_to(self.traits, GenericId.build_from_xml(elem))

    def __log_imported_data(self, source):
        map = {}
        map['clans'] = self.clans
        map['families'] = self.families
        map['schools'] = self.schools
        map['spells'] = self.spells
        map['skills'] = self.skills
        map['merits'] = self.merits
        map['flaws'] = self.flaws
        map['katas'] = self.katas
        map['kihos'] = self.kihos
        map['weapons'] = self.weapons
        map['armors'] = self.armors
        map['skcategs'] = self.skcategs
        map['perktypes'] = self.perktypes
        map['weapon_effects'] = self.weapon_effects

        print('IMPORTED DATA', source)
        for k in map:
            print("imported {0} {1}".format( len(map[k]), k))
