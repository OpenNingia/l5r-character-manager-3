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

from pydoc import pager
from PyQt5 import QtCore, QtGui, QtWidgets

# ASQ ( data query )
from asq.initiators import query
from asq.selectors import a_

# L5RCM DATA
import l5r.api as api
import l5r.api.data
import l5r.api.data.families
import l5r.api.data.clans

from l5r.util import log

def green(text):
    return u'<span style="color: #0A0">{}</span>'.format(text)

def red(text):
    return u'<span style="color: #A00">{}</span>'.format(text)

def em(text):
    return u'<em>{}</em>'.format(text)

class FamilyChooserDialog(QtWidgets.QDialog):

    def __init__(self, parent=None):
        super(FamilyChooserDialog, self).__init__(parent)

        self.widget = FamilyChooserWidget(self)
        self.build_ui()
        self.setup()

    def build_ui(self):
        self.vbox_lo = QtWidgets.QVBoxLayout(self)
        self.bt_ok = QtWidgets.QPushButton(self.tr('Ok'), self)
        self.bt_cancel = QtWidgets.QPushButton(self.tr('Cancel'), self)

        self.header = QtWidgets.QLabel(self)

        # bottom bar
        bottom_bar = QtWidgets.QFrame(self)
        hbox = QtWidgets.QHBoxLayout(bottom_bar)
        hbox.addStretch()
        hbox.addWidget(self.bt_ok)
        hbox.addWidget(self.bt_cancel)

        fr_central = QtWidgets.QFrame(self)
        vb = QtWidgets.QVBoxLayout(fr_central)
        vb.setContentsMargins(40, 20, 40, 20)
        vb.addWidget(self.widget)

        self.vbox_lo.addWidget(self.header)
        self.vbox_lo.addWidget(fr_central)
        self.vbox_lo.addWidget(bottom_bar)

        self.bt_ok.clicked.connect(self.accept)
        self.bt_cancel.clicked.connect(self.reject)

        self.setWindowTitle(self.tr("Clan and Family"))

        self.setMinimumSize(400, 0)

    def setup(self):

        self.widget.load()
        self.widget.selected_family = api.character.get_family()

        self.header.setText(self.get_h1_text())

    def get_h1_text(self):
        return self.tr("""
<center>
<h1>Select Clan and Family</h1>
<p style="color: #666">a Samurai should serve its clan first and foremost</p>
</center>
        """)

    def accept(self):

        self.widget.apply_to_model()
        super(FamilyChooserDialog, self).accept()


class FamilyChooserWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(FamilyChooserWidget, self).__init__(parent)

        self.cb_clan = QtWidgets.QComboBox(self)
        self.cb_family = QtWidgets.QComboBox(self)
        self.lb_trait = QtWidgets.QLabel(self)
        self.lb_book = QtWidgets.QLabel(self)

        self.current_clan_id = None
        self.current_family_id = None

        self.build_ui()

    def build_ui(self):

        #
        # [ clan  : ____ ]
        # [ family: ____ ]
        # Core Book, page 183
        #
        # Bonus: ______
        #
        form = QtWidgets.QFormLayout(self)
        form.addRow(self.tr("Clan:"), self.cb_clan)
        form.addRow(self.tr("Family:"), self.cb_family)
        form.addRow(self.tr("Source:"), self.lb_book)
        form.addRow("<hr/>", QtWidgets.QWidget(self))  # empty row
        form.addRow(self.tr("Bonus:"), self.lb_trait)

        self.cb_clan.currentIndexChanged.connect(self.on_clan_changed)
        self.cb_family.currentIndexChanged.connect(self.on_family_changed)

    @property
    def selected_family(self):
        return self.current_family_id

    @selected_family.setter
    def selected_family(self, value):
        """setting this property will also update the ui"""
        self.update_ui_with_family(value)

    def clear(self):
        self.current_clan_id = None
        self.current_family_id = None

    def load(self):
        if not self.current_clan_id:
            self.load_clans()

#    def apply_to_creation(self):
#        api.character.creation.set_clan(self.current_clan_id)
#        api.character.creation.set_family(self.current_family_id)

    def apply_to_model(self):
        # api.character.set_clan(self.current_clan_id)
        api.character.set_family(self.current_family_id)

    def load_clans(self):
        self.cb_clan.blockSignals(True)
        self.cb_clan.clear()
        self.cb_clan.addItem(self.tr("No Clan"), None)

        for c in query(api.data.clans.all()).order_by(a_('name')):
            self.cb_clan.addItem(c.name, c.id)
        self.cb_clan.blockSignals(False)

        # select first clan
        self.on_clan_changed(0)

    def load_families(self, clanid=None):
        self.cb_family.blockSignals(True)
        self.cb_family.clear()

        if clanid:
            family_list = query(api.data.families.get_all()).where(lambda x: x.clanid == clanid).order_by(a_('name'))
        else:
            family_list = query(api.data.families.get_all()).order_by(a_('name'))

        for f in family_list:
            self.cb_family.addItem(f.name, f.id)
        self.cb_family.blockSignals(False)

        # select first family
        self.on_family_changed(0)

    def update_ui_with_family(self, family_id):

        self.cb_clan.blockSignals(True)
        self.cb_family.blockSignals(True)

        # get family_dal
        family_dal = api.data.families.get(family_id)
        if family_dal:

            self.current_family_id = family_id
            self.current_clan_id = family_dal.clanid

            self.load_families(family_dal.clanid)

            clan_index = self.cb_clan.findData(family_dal.clanid)
            self.cb_clan.setCurrentIndex(clan_index)

            family_index = self.cb_family.findData(family_dal.id)
            self.cb_family.setCurrentIndex(family_index)

            self.update_bonus_trait()
            self.update_book()

        self.cb_clan.blockSignals(False)
        self.cb_family.blockSignals(False)

    def on_clan_changed(self, index_or_text):
        self.current_clan_id = self.cb_clan.itemData(self.cb_clan.currentIndex())
        self.load_families(self.current_clan_id)

    def on_family_changed(self, index_or_text):
        self.current_family_id = self.cb_family.itemData(self.cb_family.currentIndex())
        self.update_bonus_trait()
        self.update_book()

    def update_book(self):
        try:
            family_data = api.data.families.get(self.current_family_id)
            source_book = family_data.pack
            page_number = family_data.page

            if not source_book:
                self.lb_book.setText("")
            elif not page_number:                
                self.lb_book.setText(em(source_book.display_name))
            else:
                self.lb_book.setText(em(self.tr(f"{source_book.display_name}, page {page_number}")))
        except:
            log.ui.error(f'cannot load source book for family: {self.current_family_id}', exc_info=1)

    def update_bonus_trait(self):
        try:
            bonus_trait = api.data.families.get(self.current_family_id).trait

            if not bonus_trait:
                self.lb_trait.setText("")
            else:
                self.lb_trait.setText(green("+1 {}").format(api.data.get_trait_or_ring(bonus_trait)))
        except:
            log.ui.error(f'cannot load bonus trait for family: {self.current_family_id}', exc_info=1)

# ## MAIN ## #


def main():
    import sys
    app = QtWidgets.QApplication(sys.argv)

    dlg = QtWidgets.QDialog()
    fam = FamilyChooserWidget(dlg)
    fam.selected_family = 'scorpion_bayushi'
    vbox = QtWidgets.QVBoxLayout(dlg)
    vbox.addWidget(fam)
    dlg.exec_()

    print('selected family', fam.selected_family)

if __name__ == '__main__':
    main()
