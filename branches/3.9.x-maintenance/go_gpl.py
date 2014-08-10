#!/usr/bin/python
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

HEADER_CHECK_STRING = """# -*- coding: iso-8859-1 -*-"""
HEADER_TO_REMOVE    = """#!/usr/bin/python"""

GPL_HEADER = """# -*- coding: iso-8859-1 -*-
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
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA."""

EXCEPTS = ['go_gpl.py', 'l5rcm.py', 'l5rdb.py']

import os, sys

def place_header(header, file, remove_old_header = True):
    f = None
    try:
        f = open(file, 'r+')
    except:
        f = None

    if f is None:
        return False

    contents = [ x for x in f ]
    #print 'read %d lines' % len(contents)

    if contents[0].startswith(HEADER_TO_REMOVE):
        del contents[0]

    if not contents[0].startswith(HEADER_CHECK_STRING):
        f.seek(0)
        if remove_old_header == False:
            f.write(HEADER_TO_REMOVE + '\n')
        f.write(header + '\n')
        f.write(''.join(contents))
    f.close()
    return True

def visit_tree(path, func):
    for path, dirs, files in os.walk(path):
        dirn = os.path.basename(path)
        print dirn
        if dirn != '.' and dirn.startswith('.'):
            continue
        for file_ in files:
            if file_.startswith('.') or file_.endswith('~'):
                continue
            if '.py' not in file_:
                continue

            file_path = os.path.join(path, file_)
            remove_old = not (file_ in EXCEPTS)
            if not func(GPL_HEADER, file_path, remove_old):
                sys.stderr.write('Failed to apply header to %s\n' % file_path)
            else:
                print 'processed %s' % file_path
def main():
    #if not place_header(GPL_HEADER, "test.py"):
    #    print "Failure"
    visit_tree('.', place_header)

if __name__ == "__main__":
    main()
