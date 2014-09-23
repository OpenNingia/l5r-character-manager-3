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

from PySide import QtGui, QtCore
try:
    import dal
    import dal.query
except:
    from ..dal import query

import os
import sys


class FamilyChooserWidget(QtGui.QWidget):
    def __init__(self, dstore, parent=None):
        super(FamilyChooserWidget, self).__init__(parent)

        self.dstore = dstore

        self.cb_clan = QtGui.QComboBox(self)
        self.cb_family = QtGui.QComboBox(self)
        self.lb_trait = QtGui.QLabel(self)

        self.current_clan_id = None
        self.current_family_id = None

        self.build_ui()
        self.load_clans()

    def build_ui(self):

        #
        # [ clan  : ____ ]
        # [ family: ____ ]
        #
        # Bonus: ______
        #
        form = QtGui.QFormLayout(self)
        form.addRow(self.tr("Clan:"), self.cb_clan)
        form.addRow(self.tr("Family:"), self.cb_family)
        form.addRow("<hr/>", QtGui.QWidget(self))  # empty row
        form.addRow(self.tr("Bonus:"), self.lb_trait)

        self.cb_clan.currentIndexChanged.connect(self.on_clan_changed)
        self.cb_family.currentIndexChanged.connect(self.on_family_changed)

    @property
    def selected_family(self):
        return self.current_family_id

    @selected_family.setter
    def selected_family(self, value):
        '''setting this property will also update the ui'''
        self.update_ui_with_family(value)

    def load_clans(self):
        self.cb_clan.clear()
        self.cb_clan.addItem(self.tr("No Clan"), None)
        for c in sorted(self.dstore.clans, key=lambda x: x.name):
            self.cb_clan.addItem(c.name, c.id)

    def load_families(self, clanid=None):
        self.cb_family.clear()

        family_list = []
        if clanid:
            family_list = [x for x in self.dstore.families if x.clanid == clanid]
        else:
            family_list = self.dstore.families

        for f in sorted(family_list, key=lambda x: x.name):
            self.cb_family.addItem(f.name, f.id)

    def update_ui_with_family(self, family_id):

        self.cb_clan.blockSignals(True)
        self.cb_family.blockSignals(True)

        # get family_dal
        family_dal = dal.query.get_family(self.dstore, family_id)
        if family_dal:

            self.current_family_id = family_id
            self.current_clan_id = family_dal.clanid

            self.load_families(family_dal.clanid)

            clan_index = self.cb_clan.findData(family_dal.clanid)
            self.cb_clan.setCurrentIndex(clan_index)

            family_index = self.cb_family.findData(family_dal.id)
            self.cb_family.setCurrentIndex(family_index)

            self.update_bonus_trait()

        self.cb_clan.blockSignals(False)
        self.cb_family.blockSignals(False)

    def on_clan_changed(self, index_or_text):
        self.current_clan_id = self.cb_clan.itemData(self.cb_clan.currentIndex())
        self.load_families(self.current_clan_id)

    def on_family_changed(self, index_or_text):
        self.current_family_id = self.cb_family.itemData(self.cb_family.currentIndex())
        self.update_bonus_trait()

    def green(self, text):
        return '<span style="color: #0A0">' + text + '</span>'

    def get_trait_or_ring(self, traitid):
        return (dal.query.get_trait(self.dstore, traitid) or
                dal.query.get_ring(self.dstore, traitid))

    def update_bonus_trait(self):
        bonus_trait = None
        try:
            bonus_trait = dal.query.get_family(self.dstore, self.current_family_id).trait

            if not bonus_trait:
                self.lb_trait.setText("")
            else:
                self.lb_trait.setText(self.green("+1 {}").format(self.get_trait_or_ring(bonus_trait)))
        except:
            print('cannot find bonus trait of {}'.format(self.current_family_id))

# ## MAIN ## #


def main():
    app = QtGui.QApplication(sys.argv)

    user_data_dir = os.environ['APPDATA'].decode('latin-1')
    pack_data_dir = os.path.join(user_data_dir, 'openningia', 'l5rcm')

    dstore = dal.Data(
        [os.path.join(pack_data_dir, 'core.data'),
         os.path.join(pack_data_dir, 'data')],
        [])

    dlg = QtGui.QDialog()
    fam = FamilyChooserWidget(dstore, dlg)
    fam.selected_family = 'scorpion_bayushi'
    vbox = QtGui.QVBoxLayout(dlg)
    vbox.addWidget(fam)
    dlg.exec_()

    print('selected family', fam.selected_family)

if __name__ == '__main__':
    main()
