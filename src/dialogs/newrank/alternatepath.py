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
import sys
import dal
import dal.query
import models
import widgets

from wizardpage import WizardPage
from PySide import QtCore, QtGui

class AlternatePathPage(WizardPage):

    def __init__(self, parent=None):
        super(AlternatePathPage, self).__init__(parent)

        w = widgets.SchoolChooserWidget(parent.pc, parent.dstore, self)
        w.allow_advanced_schools = False
        w.allow_alternate_paths = True
        w.allow_basic_schools = False
        w.show_filter_selection = False
        w.show_bonus_trait = False
        w.show_school_requirements = True
        w.show_multiple_schools_option = False
        w.show_different_school_option = False

        w.statusChanged.connect(self.nextAllowed)

        self._set_ui(w)

    def get_h1_text(self):
        return self.tr('''
<center>
<h1>Follow an Alternate Path</h1>
<p style="color: #666">If you don't like a certain school rank you can
replace it with another one</p>
<p style="color: #066">
If you're happy with your school technique, skip this step
</p>
</center>
        ''')
