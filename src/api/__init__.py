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
import dal

ORG = 'openningia'
APP = 'l5rcm'


def get_user_data_path(rel_path = ''):
    user_data = '.'
    if os.name == 'posix': # Linux is ok but Macosx ???
        user_data = '%s/.config' % (os.environ['HOME'])
    elif os.name == 'nt':
        user_data = os.environ['APPDATA'].decode('latin-1')
    return os.path.join(user_data, ORG, APP)


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

    def __init__(self):
        '''initialize api'''

        # load data
        self.reload()

    def reload(self):

        locations =  [get_user_data_path('core.data'),
                     get_user_data_path('data')]
        if self.locale:
            locations += [get_user_data_path('data.' + self.locale)]

        if not self.ds:
            self.ds = dal.Data(locations, self.blacklist)
        else:
            self.ds.rebuild(locations, self.blacklist)

__api = L5RCMAPI()
