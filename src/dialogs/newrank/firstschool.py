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

class FirstSchoolPage(WizardPage):
    def __init__(self, parent=None):
        super(FirstSchoolPage, self).__init__(parent)

        w = widgets.SchoolChooserWidget(parent.pc, parent.dstore, self)
        w.allow_advanced_schools = False
        w.allow_alternate_paths = False
        w.allow_basic_schools = True
        w.show_filter_selection = False
        w.show_bonus_trait = True
        w.show_school_requirements = False
        w.show_multiple_schools_option = False

        w.statusChanged.connect(self.nextAllowed)

        self._set_ui(w)

    def get_h1_text(self):
        return self.tr('''
<center>
<h1>Join your First School</h1>
<p style="color: #666">In this phase you're limited to base schools,
        however you can replace this rank with an alternate path
        on the next step</p>
</center>
        ''')
