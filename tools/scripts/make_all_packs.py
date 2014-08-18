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

import os
import json
from subprocess import call

def main():
	r = './data_packs'
	for p in os.listdir(r):
		m  = os.path.join(r, p, 'manifest')
		print(m)
		if not os.path.exists(m):
			print('manifest not found', m)
			continue
		ms = {}

		try:
			with open(m, 'r') as f:
				ms = json.load(f)
		except:
			print('bad manifest', m)
			continue

		if not 'id' in ms or not 'version' in ms:
			print('bad manifest', ms)
			continue

		if os.name == 'nt':
			c = 'makepack.bat'
		else:
			c = './makepack.sh'
		call([c, os.path.join(r, p), "{0}-{1}".format(ms['id'], ms['version'])])

if __name__ == "__main__":
	main()
