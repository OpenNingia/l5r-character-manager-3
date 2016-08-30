# -*- coding: utf-8 -*-
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

import os
import re

import l5rdal as dal

ORG = 'openningia'
APP = 'l5rcm'

def get_user_data_path(rel_path=None):
    user_data = '.'
    if os.name == 'posix':  # Linux is ok but Macosx ???
        user_data = '%s/.config' % (os.environ['HOME'])
    elif os.name == 'nt':
        user_data = os.environ['APPDATA']
    if rel_path:
        return os.path.join(user_data, ORG, APP, rel_path)
    return os.path.join(user_data, ORG, APP)


def set_translation_context(obj):
    __api.translation_provider = obj


def cmp(a, b):
    return (a > b) - (a < b)


def ver_cmp(version1, version2):
    def normalize(v):
        return [int(x) for x in re.sub(r'(\.0+)*$', '', v).split(".")]
    return cmp(normalize(version1), normalize(version2))


def tr(*args, **kwargs):
    """translate text"""
    return __api.tr(*args, **kwargs)


class L5RCMAPI(object):

    # character model
    pc = None

    # data access
    ds = None

    # culture locale
    locale = None

    # data pack blacklist
    blacklist = []

    # current rank advancement
    current_rank_adv = None

    # translation provider
    translation_provider = None

    def __init__(self, app=None):
        """initialize api"""

        # load data
        # self.reload()

        if app:
            self.translation_provider = app

    def reload(self):

        locations = [get_user_data_path('core.data'),
                     get_user_data_path('data')]
        if self.locale:
            locations += [get_user_data_path('data.' + self.locale)]

        if not self.ds:
            self.ds = dal.Data(locations, self.blacklist)
        else:
            self.ds.rebuild(locations, self.blacklist)

    def tr(self, *args, **kwargs):
        if not self.translation_provider:
            return args[0]
        return self.translation_provider.tr(*args, **kwargs)

__api = L5RCMAPI()
