# -*- coding: utf-8 -*-
# Copyright (C) 2014-2022 Daniele Simonetti
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
__author__ = 'Daniele'

import os

# global cache
cache_names = {}


def get_random_name(path):
    names = []
    if path in cache_names:
        names = cache_names[path]
    else:
        f = open(path, 'rt')
        for l in f:
            if l.strip().startswith('*'):
                names.append(l.strip('* \n\r'))
        f.close()
        cache_names[path] = names

    i = (ord(os.urandom(1)) + (ord(os.urandom(1)) << 8)) % len(names)
    return names[i]
