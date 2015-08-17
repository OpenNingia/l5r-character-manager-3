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

from widgets.spells.choosemore import ChooseMoreSpells
from wizardpage import WizardPage

class SpellsPage(WizardPage):
    def __init__(self, parent=None):
        super(SpellsPage, self).__init__(parent)

        w = ChooseMoreSpells(self)
        w.statusChanged.connect(self.nextAllowed)

        self._set_ui(w)

    def get_h1_text(self):
        return self.tr('''
<center>
<h1>Choose school's spells</h1>
<p style="color: #666">Your school has granted you knowledge of several spells.</p>
</center>
        ''')
