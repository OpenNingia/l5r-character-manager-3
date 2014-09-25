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


class SchoolChooserWidget(QtGui.QWidget):
    def __init__(self, dstore, parent=None):
        super(SchoolChooserWidget, self).__init__(parent)

        self.dstore = dstore

        self.cb_clan = QtGui.QComboBox(self)
        self.cb_school = QtGui.QComboBox(self)
        self.lb_trait = QtGui.QLabel(self)

        self.current_clan_id = None
        self.current_school_id = None

        self._show_filter_selection = True
        self._show_bonus_trait = True
        self._show_school_requirements = True
        self._allow_basic_schools = True
        self._allow_advanced_schools = True
        self._allow_alternate_paths = True

        self.build_ui()
        self.load_clans()

    def build_ui(self):

        #
        # [ clan  : ____ ]
        # [ school: ____ ]
        #
        # Bonus: ______
        #
        form = QtGui.QFormLayout(self)
        form.addRow(self.tr("Clan:"), self.cb_clan)
        form.addRow(self.tr("School:"), self.cb_school)

        form.addRow("<hr/>", QtGui.QWidget(self))  # empty row
        form.addRow(self.tr("Bonus:"), self.lb_trait)

        self.pl_filter = self.build_filter_panel()

        form.addRow("<hr/>", QtGui.QWidget(self))  # empty row
        form.addRow(self.tr("Filters"), self.pl_filter)

        self.pl_requirements = QtGui.QFrame(self)
        form.addRow("<hr/>", QtGui.QWidget(self))  # empty row
        form.addRow(self.tr("Requirements"), self.pl_requirements)

        self.cb_clan.currentIndexChanged.connect(self.on_clan_changed)
        self.cb_school.currentIndexChanged.connect(self.on_school_changed)

        self.form_layout = form

    def build_filter_panel(self):
        fr = QtGui.QFrame(self)
        vb = QtGui.QVBoxLayout(fr)
        self.cx_base_schools = QtGui.QCheckBox(self.tr("Base schools"), self)
        self.cx_advc_schools = QtGui.QCheckBox(self.tr("Advanced schools"), self)
        self.cx_path_schools = QtGui.QCheckBox(self.tr("Alternate paths"), self)
        vb.addWidget(self.cx_base_schools)
        vb.addWidget(self.cx_advc_schools)
        vb.addWidget(self.cx_path_schools)

        self.cx_base_schools.stateChanged.connect(self.on_base_filter_change)
        self.cx_advc_schools.stateChanged.connect(self.on_advc_filter_change)
        self.cx_path_schools.stateChanged.connect(self.on_path_filter_change)

        self.cx_base_schools.setChecked(self.allow_basic_schools)
        self.cx_advc_schools.setChecked(self.allow_advanced_schools)
        self.cx_path_schools.setChecked(self.allow_alternate_paths)

        return fr

    @property
    def selected_school(self):
        return self.current_school_id

    @selected_school.setter
    def selected_school(self, value):
        '''setting this property will also update the ui'''
        self.update_ui_with_school(value)

    @property
    def selected_clan(self):
        return self.current_clan_id

    @selected_clan.setter
    def selected_clan(self, value):
        '''setting this property will also update the ui'''
        self.update_ui_with_clan(value)

    @property
    def show_filter_selection(self):
        return self._show_filter_selection

    @show_filter_selection.setter
    def show_filter_selection(self, value):
        '''setting this property will also update the ui'''
        self._show_filter_selection = value
        if value:
            self.show_row(self.pl_filter)
        else:
            self.hide_row(self.pl_filter)

    @property
    def show_bonus_trait(self):
        return self._show_filter_selection

    @show_bonus_trait.setter
    def show_bonus_trait(self, value):
        '''setting this property will also update the ui'''
        self._show_filter_selection = value
        if value:
            self.show_row(self.lb_trait)
        else:
            self.hide_row(self.lb_trait)

    @property
    def show_school_requirements(self):
        return self._show_school_requirements

    @show_school_requirements.setter
    def show_school_requirements(self, value):
        '''setting this property will also update the ui'''
        self._show_school_requirements = value
        if value:
            self.show_row(self.pl_requirements)
        else:
            self.hide_row(self.pl_requirements)

    @property
    def allow_basic_schools(self):
        return self._allow_basic_schools

    @allow_basic_schools.setter
    def allow_basic_schools(self, value):
        '''setting this property will also update the ui'''
        self._allow_basic_schools = value
        self.cx_base_schools.setChecked(value)
        self.load_schools(self.current_clan_id)

    @property
    def allow_advanced_schools(self):
        return self._allow_advanced_schools

    @allow_advanced_schools.setter
    def allow_advanced_schools(self, value):
        '''setting this property will also update the ui'''
        self._allow_advanced_schools = value
        self.cx_advc_schools.setChecked(value)
        self.load_schools(self.current_clan_id)

    @property
    def allow_alternate_paths(self):
        return self._allow_alternate_paths

    @allow_alternate_paths.setter
    def allow_alternate_paths(self, value):
        '''setting this property will also update the ui'''
        self._allow_alternate_paths = value
        self.cx_path_schools.setChecked(value)
        self.load_schools(self.current_clan_id)

    def load_clans(self):
        self.cb_clan.clear()
        self.cb_clan.addItem(self.tr("No Clan"), None)
        for c in sorted(self.dstore.clans, key=lambda x: x.name):
            self.cb_clan.addItem(c.name, c.id)

    def load_schools(self, clanid=None):
        self.cb_school.clear()

        school_list = []

        if self.allow_basic_schools:
            school_list += dal.query.get_base_schools(self.dstore)
        if self.allow_advanced_schools:
            school_list += [x for x in self.dstore.schools if 'advanced' in x.tags]
        if self.allow_alternate_paths:
            school_list += [x for x in self.dstore.schools if 'alternate' in x.tags]

        if clanid:
            school_list = [x for x in school_list if x.clanid == clanid]

        for f in sorted(school_list, key=lambda x: x.name):
            self.cb_school.addItem(f.name, f.id)

    def hide_row(self, fld):
        print('hide row', fld)
        fld.hide()
        self.form_layout.labelForField(fld).hide()

    def show_row(self, fld):
        fld.show()
        self.form_layout.labelForField(fld).show()

    def update_ui_with_school(self, school_id):

        self.cb_clan.blockSignals(True)
        self.cb_school.blockSignals(True)

        # get school_dal
        school_dal = dal.query.get_school(self.dstore, school_id)
        if school_dal:

            self.current_school_id = school_id
            self.current_clan_id = school_dal.clanid

            self.load_schools(school_dal.clanid)

            clan_index = self.cb_clan.findData(school_dal.clanid)
            self.cb_clan.setCurrentIndex(clan_index)

            school_index = self.cb_school.findData(school_dal.id)
            self.cb_school.setCurrentIndex(school_index)

            self.update_bonus_trait()

        self.cb_clan.blockSignals(False)
        self.cb_school.blockSignals(False)

    def update_ui_with_clan(self, clan_id):

        self.cb_clan.blockSignals(True)
        self.cb_school.blockSignals(True)

        # get clan_dal
        clan_dal = dal.query.get_clan(self.dstore, clan_id)
        if clan_dal:

            self.current_school_id = None
            self.current_clan_id = clan_id

            self.load_schools(clan_id)

            clan_index = self.cb_clan.findData(clan_id)
            self.cb_clan.setCurrentIndex(clan_index)

            self.update_bonus_trait()

        self.cb_clan.blockSignals(False)
        self.cb_school.blockSignals(False)

    def on_clan_changed(self, index_or_text):
        self.current_clan_id = self.cb_clan.itemData(self.cb_clan.currentIndex())
        self.load_schools(self.current_clan_id)

    def on_school_changed(self, index_or_text):
        self.current_school_id = self.cb_school.itemData(self.cb_school.currentIndex())
        self.update_bonus_trait()

    def on_base_filter_change(self, state):
        self.allow_basic_schools = self.sender().isChecked()
    def on_advc_filter_change(self, state):
        self.allow_advanced_schools = self.sender().isChecked()
    def on_path_filter_change(self, state):
        self.allow_alternate_paths = self.sender().isChecked()

    def green(self, text):
        return '<span style="color: #0A0">' + text + '</span>'

    def red(self, text):
        return '<span style="color: #A00">' + text + '</span>'

    def get_trait_or_ring(self, traitid):
        return (dal.query.get_trait(self.dstore, traitid) or
                dal.query.get_ring(self.dstore, traitid))

    def update_bonus_trait(self):
        bonus_trait = None
        try:
            bonus_trait = dal.query.get_school(self.dstore, self.current_school_id).trait
        except:
            print('cannot find bonus trait of {}'.format(self.current_school_id))

        if not bonus_trait:
            self.lb_trait.setText(self.red(self.tr("None")))
        else:
            self.lb_trait.setText(self.green("+1 {}").format(self.get_trait_or_ring(bonus_trait)))


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
    fam = SchoolChooserWidget(dstore, dlg)

    #fam.selected_school = 'hida_bushi_school'
    fam.selected_clan = 'mantis'
    vbox = QtGui.QVBoxLayout(dlg)
    vbox.addWidget(fam)
    dlg.exec_()

    print('selected school', fam.selected_school)

if __name__ == '__main__':
    main()
