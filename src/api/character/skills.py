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

from .. import __api

def get_wildcard(index):
    pc = __api.pc
    if not pc:
        return None
    wc = pc.get_pending_wc_skills()
    if len(wc) < index:
        return wc[index]
    return None

def get_wildcards():
    if not __api.pc:
        return []
    return __api.pc.get_pending_wc_skills()
