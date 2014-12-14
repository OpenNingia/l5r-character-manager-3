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

class ClanAndFamilyPage(WizardPage):
    def __init__(self, parent=None):
        super(ClanAndFamilyPage, self).__init__(parent)
        self._set_ui(widgets.FamilyChooserWidget(self))

    def get_h1_text(self):
        return self.tr('''
<center>
<h1>Select Clan and Family</h1>
<p style="color: #666">a Samurai should serve its clan first and foremost</p>
</center>
        ''')
