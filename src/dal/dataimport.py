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

import os
import json
import zipfile
import shutil

CM_VERSION = None

class ManifestNotFound(Exception):
    def __init__(self, msg):
        super(ManifestNotFound, self).__init__(msg)

class InvalidDataPack(Exception):
    def __init__(self, msg):
        super(InvalidDataPack, self).__init__(msg)

class VersionMismatch(Exception):
    def __init__(self, msg):
        super(VersionMismatch, self).__init__(msg)

def cmp_versions(v1, v2):
    t1 = v1.split('.')
    t2 = v2.split('.')
    i = 0
    r = 0
    e = max( len(t1), len(t2) )
    while True:
        n1 = int(t1[i]) if len(t1) > i else 0
        n2 = int(t2[i]) if len(t2) > i else 0
        if n1 > n2: return 1
        if n2 > n1: return -1
        i+=1
        if i == e: break
    return 0

class DataPack(object):

    def __init__(self, archive_path):
        self.authors      = []
        self.id           = None
        self.dsp_name     = None
        self.language     = None
        self.version      = None
        self.update_uri   = None
        self.download_uri = None
        self.min_cm_ver   = None

        self.archive_path = archive_path

        # look for "manifest" file in root directory
        # no manifest file == no valid archive
        # read manifest file and extract:
        # 1. data target language ( es. us_US )
        # no language field == culture invariant
        # read id, data will be extracted in a subdirectory named that way
        # other fields:
        # author
        # display_name

        with zipfile.ZipFile(archive_path, 'r') as dz:
            try:
                # search manifest
                manifest_info = dz.getinfo('manifest')
                manifest_fp   = dz.open(manifest_info)
                manifest_js   = json.load(manifest_fp)

                self.id       = manifest_js['id']
                if 'display_name' in manifest_js:
                    self.dsp_name = manifest_js['display_name']
                if 'language' in manifest_js:
                    self.language = manifest_js['language']
                if 'authors' in manifest_js:
                    self.authors = manifest_js['authors']
                if 'version' in manifest_js:
                    self.version = manifest_js['version']
                if 'update-uri' in manifest_js:
                    self.update_uri = manifest_js['update-uri']
                if 'download-uri' in manifest_js:
                    self.download_uri = manifest_js['download-uri']
                if 'min-cm-version' in manifest_js:
                    self.min_cm_ver = manifest_js['min-cm-version']
            except Exception as e:
                print('manifest not found!')
                print(e.message)
                raise ManifestNotFound('Not a valid Data pack file.')

    def export_to(self, data_path):
        if not self.good():
            raise InvalidDataPack('Cannot extract. Not a valid Data pack file.')

        if not self.check_cm_version():
            raise VersionMismatch( 'Cannot install. This datapack require L5R: CM v{0} or newer.'.format(self.min_cm_ver) )

        data_path = os.path.join(data_path, self.id)

        if not os.path.exists(data_path):
            os.makedirs(data_path)

        dest_dir = os.path.join(data_path, self.id)
        if os.path.exists(dest_dir):
            if self.is_older_or_same(data_path):
                try:
                    shutil.rmtree(dest_dir, ignore_errors=True)
                except:
                    print("cannot delete old data pack")
            else:
                raise VersionMismatch("A new version of this Data pack is already installed.")
        try:
            with zipfile.ZipFile(self.archive_path, 'r') as dz:
                dz.extractall(data_path)
        except:
            raise InvalidDataPack('Cannot extract. Not a valid Data pack file.')

    def is_older_or_same(self, src_dir):
        try:
            with open( os.path.join(src_dir, 'manifest'), 'rt' ) as fp:
                js = json.load(fp)
                print('{0} datapack version {1} vs {2}'.format(self.id, self.version, js['version']))                
                return cmp_versions(self.version, js['version']) >= 0
        except Exception as e:
            return True

    def check_cm_version(self):
        if self.min_cm_ver is None: return True
        try:
            return cmp_versions(self.min_cm_ver, CM_VERSION) <= 0
        except:
            return True

    def good(self):
        return self.id is not None

    def __str__(self):
        return self.dsp_name or self.id

    def __unicode__(self):
        return self.dsp_name or self.id

    def __eq__(self, obj):
        return obj and hasattr(obj, 'id') and obj.id == self.id

    def __ne__(self, obj):
        return not self.__eq__(obj)

    def __hash__(self):
        if self.id:
            return self.id.__hash__()
        return 0

def test():
    data = 'test.zip'
    importer = DataPack(data)
    print(importer.good())

    importer.export_to('./test_out')

def test2():
    v1 = '1.9.1.0'
    v2 = '1.9.1'
    print(cmp_versions(v1,v2))

if __name__ == '__main__':
    #test()
    test2()
