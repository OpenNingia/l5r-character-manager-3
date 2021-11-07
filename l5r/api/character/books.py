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
__author__ = 'Daniele'

import l5r.api as api
import l5r.api.data

from l5r.api import __api

from collections import namedtuple
from l5r.util import log

from asq.initiators import query
from asq.selectors import a_


def get_references():
    """return a list of data-packs that are referenced by the character"""

    refs_ = []
    # get references from families
    family_ = api.data.families.get(api.character.get_family())
    if family_:
        refs_.append(family_.pack)

    # get references from schools
    for s in [api.data.schools.get(x) for x in api.character.schools.get_all() if api.data.schools.get(x) is not None]:
        refs_.append(s.pack)

    # get references from skills
    for s in [api.data.skills.get(x) for x in api.character.skills.get_all() if api.data.skills.get(x) is not None]:
        refs_.append(s.pack)

    # get references from spells
    for s in [api.data.spells.get(x) for x in api.character.spells.get_all() if api.data.spells.get(x) is not None]:
        refs_.append(s.pack)

    return query(refs_).where(lambda y: y is not None).distinct(a_('id')).to_list()


def set_dependencies():
    """set the datapack dependencies"""

    deps = get_references()

    book_list = []

    log.api.debug(u"set book dependencies")

    for p in deps:
        # for each package we store the 'id' and the 'version'
        book_list.append(dict(id=p.id, name=p.display_name, version=p.version))
        log.api.debug(u"pack: %s %s", p.id, p.version)

    __api.pc.pack_refs = book_list


def get_dependencies():
    """returns the list of datapack dependencies"""
    return __api.pc.pack_refs


def get_missing_dependencies():
    """returns the dependencies that are referenced in the character file but are not loaded"""

    BookReferenceType = namedtuple('BookReference', ['id', 'name', 'version'])

    for d in get_dependencies():

        br = BookReferenceType(id=d['id'], name=d['name'], version=d['version'])

        loaded_pack = api.data.pack_by_id(br.id)
        
        if not loaded_pack:
            log.api.warning(u"referenced pack %s is not loaded", br.id)
            yield br
        elif not loaded_pack.active:
            log.api.warning(u"referenced pack %s is not active", br.id)
            yield br
        elif api.ver_cmp(loaded_pack.version, br.version) < 0:
            log.api.warning(u"referenced pack %s is outdated. referenced %s, loaded %s", br.id, br.version, loaded_pack.version)
            yield br


def fulfills_dependencies():
    """returns True if all the dependencies are loaded"""
    return sum(1 for x in get_missing_dependencies()) == 0
