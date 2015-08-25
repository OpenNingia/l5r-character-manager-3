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
from asq.initiators import query
from asq.selectors import a_

import api.data
import api.character
import api.character.merits
import api.data.schools
import api.data.clans
import widgets


def green(text):
    return u'<span style="color: #0A0">{}</span>'.format(text)


def red(text):
    return u'<span style="color: #A00">{}</span>'.format(text)


class FirstSchoolChooserDialog(QtGui.QDialog):

    def __init__(self, parent=None):
        super(FirstSchoolChooserDialog, self).__init__(parent)

        self.widget = SchoolChooserWidget(self)
        self.build_ui()
        self.setup()

    def build_ui(self):
        self.vbox_lo = QtGui.QVBoxLayout(self)
        self.bt_ok = QtGui.QPushButton(self.tr('Ok'), self)
        self.bt_cancel = QtGui.QPushButton(self.tr('Cancel'), self)

        self.header = QtGui.QLabel(self)

        # bottom bar
        bottom_bar = QtGui.QFrame(self)
        hbox = QtGui.QHBoxLayout(bottom_bar)
        hbox.addStretch()
        hbox.addWidget(self.bt_ok)
        hbox.addWidget(self.bt_cancel)

        fr_central = QtGui.QFrame(self)
        vb = QtGui.QVBoxLayout(fr_central)
        vb.setContentsMargins(40, 20, 40, 20)
        vb.addWidget(self.widget)

        self.vbox_lo.addWidget(self.header)
        self.vbox_lo.addWidget(fr_central)
        self.vbox_lo.addWidget(bottom_bar)

        self.bt_ok.clicked.connect(self.accept)
        self.bt_cancel.clicked.connect(self.reject)

        self.setWindowTitle(self.tr("L5R: CM - First School"))

        self.resize(400, 240)

    def setup(self):

        self.widget.allow_advanced_schools = False
        self.widget.allow_alternate_paths = False
        self.widget.allow_basic_schools = True
        self.widget.show_filter_selection = False
        self.widget.show_bonus_trait = True
        self.widget.show_school_requirements = False
        self.widget.show_multiple_schools_option = False

        self.widget.load()
        self.widget.selected_clan = api.character.get_clan()

        self.header.setText(self.get_h1_text())

    def get_h1_text(self):
        return self.tr('''
<center>
<h1>Join your First School</h1>
<p style="color: #666">In this phase you're limited to base schools</p>
</center>
        ''')

    def accept(self):

        self.apply_to_first_school()
        super(FirstSchoolChooserDialog, self).accept()

    def apply_to_first_school(self):
        api.character.schools.set_first(self.widget.selected_school)
        if self.widget.different_school_merit:
            api.character.merits.add('different_school')


class SchoolChooserDialog(QtGui.QDialog):

    def __init__(self, parent=None):
        super(SchoolChooserDialog, self).__init__(parent)

        self.widget = SchoolChooserWidget(self)
        self.build_ui()
        self.setup()

    def build_ui(self):
        self.vbox_lo = QtGui.QVBoxLayout(self)
        self.bt_ok = QtGui.QPushButton(self.tr('Ok'), self)
        self.bt_cancel = QtGui.QPushButton(self.tr('Cancel'), self)

        self.header = QtGui.QLabel(self)

        # bottom bar
        bottom_bar = QtGui.QFrame(self)
        hbox = QtGui.QHBoxLayout(bottom_bar)
        hbox.addStretch()
        hbox.addWidget(self.bt_ok)
        hbox.addWidget(self.bt_cancel)

        fr_central = QtGui.QFrame(self)
        vb = QtGui.QVBoxLayout(fr_central)
        vb.setContentsMargins(40, 20, 40, 20)
        vb.addWidget(self.widget)

        self.vbox_lo.addWidget(self.header)
        self.vbox_lo.addWidget(fr_central)
        self.vbox_lo.addWidget(bottom_bar)

        self.bt_ok.clicked.connect(self.accept)
        self.bt_cancel.clicked.connect(self.reject)

        self.setWindowTitle(self.tr("L5R: CM - Select School"))

        self.resize(400, 240)

    def setup(self):

        self.widget.allow_advanced_schools = True
        self.widget.allow_alternate_paths = True
        self.widget.allow_basic_schools = True
        self.widget.show_filter_selection = True
        self.widget.show_bonus_trait = False
        self.widget.show_school_requirements = True
        self.widget.show_multiple_schools_option = True
        self.widget.show_different_school_option = False

        self.widget.statusChanged.connect(self.bt_ok.setEnabled)

        self.widget.load()
        self.widget.enable()
        self.widget.selected_clan = api.character.get_clan()

        self.header.setText(self.get_h1_text())

    def get_h1_text(self):
        return self.tr('''
<center>
<h1>Choose the school to join</h1>
<p style="color: #666">You can choose between normal schools, advanced schools and alternative paths<br/>
If you choose an advanced school or alternative path be sure to check the requirements
</p>
</center>
        ''')

    def accept(self):

        self.apply_to_character_advancement()
        super(SchoolChooserDialog, self).accept()

    def apply_to_character_advancement(self):
        api.character.schools.join_new(self.widget.selected_school)
        if self.widget.multiple_schools_merit:
            api.character.merits.add('multiple_schools')


class SchoolChooserWidget(QtGui.QWidget):
    statusChanged = QtCore.Signal(bool)

    def __init__(self, parent=None):
        super(SchoolChooserWidget, self).__init__(parent)

        self.cb_clan = QtGui.QComboBox(self)
        self.cb_school = QtGui.QComboBox(self)
        self.lb_trait = QtGui.QLabel(self)
        self.lb_book = QtGui.QLabel(self)
        self.lb_desc = QtGui.QLabel(self)

        self.lb_different_school_err = QtGui.QLabel(red(self.tr("Not enough XP")), self)
        self.lb_multiple_schools_err = QtGui.QLabel(red(self.tr("Not enough XP")), self)

        self.lb_different_school_err.setVisible(False)
        self.lb_multiple_schools_err.setVisible(False)

        self.req_list = None
        self.current_clan_id = None
        self.current_school_id = None
        self.character_clan_id = None

        self._show_filter_selection = True
        self._show_bonus_trait = True
        self._show_school_requirements = True
        self._show_different_school_check = True
        self._show_multiple_school_check = True
        self._show_options_panel = True

        self._allow_basic_schools = True
        self._allow_advanced_schools = True
        self._allow_alternate_paths = True

        self._old_status = None

        self.build_ui()

    def enable(self):
        self._old_status = None
        self.connect_signals()
        self.update_status()

    def sizeHint(self):
        return QtCore.QSize(480, 480)

    def clear(self):
        self.current_clan_id = None
        self.current_school_id = None

    def load(self):
        if not self.current_clan_id:
            self.load_clans()

            try:
                char_clan_id = api.character.rankadv.get_current().clan
                self.update_ui_with_clan(char_clan_id)
            except:
                pass

        self.update_status()

    def connect_signals(self):
        self.cb_clan.currentIndexChanged.connect(self.on_clan_changed)
        self.cb_school.currentIndexChanged.connect(self.on_school_changed)

        self.cx_base_schools.stateChanged.connect(self.on_base_filter_change)
        self.cx_advc_schools.stateChanged.connect(self.on_advc_filter_change)
        self.cx_path_schools.stateChanged.connect(self.on_path_filter_change)

        self.ck_multiple_schools.stateChanged.connect(self.update_status)
        self.ck_different_school.stateChanged.connect(self.update_status)

    def build_ui(self):
        # self.setStyleSheet('''QWidget { border: 1px solid red; }''')
        #
        # [ clan:   ____ ]
        # [ school: ____ ]
        # Core Book, page 183
        #
        # Bonus: ______
        #
        # Filters:
        # [x] Base Schools
        #        [x] Advanced Schools
        #        [ ] Alternate Paths
        #
        # Requirements:
        #        [x] Hida bushi school
        #        [x] Being very cool
        #        [ ] Lots of money
        #
        # Options:
        #        [ ] Buy 'Different School' advantage
        #        [ ] Buy 'Multiple Schools' advantage
        form = QtGui.QFormLayout(self)
        form.addRow(self.tr("Clan:"), self.cb_clan)
        form.addRow(self.tr("School:"), self.cb_school)
        form.addRow(self.lb_book, self.lb_desc)

        form.addRow(" ", QtGui.QWidget(self))  # empty row
        form.addRow(self.tr("Bonus:"), self.lb_trait)

        self.pl_filter = self.build_filter_panel()
        form.addRow(self.tr("Filters:"), self.pl_filter)

        self.pl_requirements = self.build_requirements_panel()
        form.addRow(self.tr("Requirements:"), self.pl_requirements)

        self.pl_options = self.build_options_panel()
        form.addRow(self.tr("Options:"), self.pl_options)

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
        vb.setContentsMargins(0, 18, 0, 0)

        self.cx_base_schools.setChecked(self.allow_basic_schools)
        self.cx_advc_schools.setChecked(self.allow_advanced_schools)
        self.cx_path_schools.setChecked(self.allow_alternate_paths)

        return fr

    def build_requirements_panel(self):
        self.req_list = widgets.RequirementsWidget(self)
        return self.req_list

    def build_options_panel(self):
        fr = QtGui.QFrame(self)
        fl = QtGui.QFormLayout(fr)

        self.ck_different_school = QtGui.QCheckBox(self.tr("Buy 'Different School' advantage"), self)
        self.ck_multiple_schools = QtGui.QCheckBox(self.tr("Buy 'Multiple Schools' advantage"), self)

        fl.addRow(self.ck_different_school, self.lb_different_school_err)
        fl.addRow(self.ck_multiple_schools, self.lb_multiple_schools_err)

        fl.setContentsMargins(0, 18, 0, 0)

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
    def character_clan(self):
        return self.character_clan_id

    @character_clan.setter
    def character_clan(self, value):
        '''setting this property will also update the ui'''
        self.character_clan_id = value

    @property
    def show_filter_selection(self):
        return self._show_filter_selection

    @show_filter_selection.setter
    def show_filter_selection(self, value):
        '''setting this property will also update the ui'''
        self._show_filter_selection = value
        self.set_row_visible(self.pl_filter, value)

    @property
    def show_bonus_trait(self):
        return self._show_filter_selection

    @show_bonus_trait.setter
    def show_bonus_trait(self, value):
        '''setting this property will also update the ui'''
        self._show_filter_selection = value
        self.set_row_visible(self.lb_trait, value)

    @property
    def show_school_requirements(self):
        return self._show_school_requirements

    @show_school_requirements.setter
    def show_school_requirements(self, value):
        '''setting this property will also update the ui'''
        self._show_school_requirements = value
        if not value:
            self.set_row_visible(self.pl_requirements, value)

    @property
    def show_different_school_option(self):
        return self._show_different_school_check

    @show_different_school_option.setter
    def show_different_school_option(self, value):
        '''setting this property will also update the ui'''
        self._show_different_school_check = value
        self.show_or_hide_option_panel()

    @property
    def show_multiple_schools_option(self):
        return self._show_multiple_school_check

    @show_multiple_schools_option.setter
    def show_multiple_schools_option(self, value):
        '''setting this property will also update the ui'''
        self._show_multiple_school_check = value
        self.show_or_hide_option_panel()

    @property
    def allow_basic_schools(self):
        return self._allow_basic_schools

    @allow_basic_schools.setter
    def allow_basic_schools(self, value):
        '''setting this property will also update the ui'''
        self._allow_basic_schools = value
        self.cx_base_schools.setChecked(value)
        self.load_clans()

    @property
    def allow_advanced_schools(self):
        return self._allow_advanced_schools

    @allow_advanced_schools.setter
    def allow_advanced_schools(self, value):
        '''setting this property will also update the ui'''
        self._allow_advanced_schools = value
        self.cx_advc_schools.setChecked(value)
        self.load_clans()

    @property
    def allow_alternate_paths(self):
        return self._allow_alternate_paths

    @allow_alternate_paths.setter
    def allow_alternate_paths(self, value):
        '''setting this property will also update the ui'''
        self._allow_alternate_paths = value
        self.cx_path_schools.setChecked(value)
        self.load_clans()

    @property
    def different_school_merit(self):
        """return True if different school merit should be purchased"""
        return self.ck_different_school.isChecked()

    @different_school_merit.setter
    def different_school_merit(self, value):
        """setting this property will also update the ui"""
        self.ck_different_school.setChecked(value)

    @property
    def multiple_schools_merit(self):
        """return True if multiple schools merit should be purchased"""
        return self.ck_multiple_schools.isChecked()

    @multiple_schools_merit.setter
    def multiple_schools_merit(self, value):
        """setting this property will also update the ui"""
        self.ck_multiple_schools.setChecked(value)

    def get_filtered_school_list(self):
        school_list = []
        if self.allow_basic_schools:
            school_list += api.data.schools.get_base()
        if self.allow_advanced_schools:
            school_list += api.data.schools.get_advanced()
        if self.allow_alternate_paths:
            school_list += api.data.schools.get_paths()

        return school_list

    def get_filtered_clan_list(self):
        schools = self.get_filtered_school_list()
        clanids = query(schools) \
            .distinct(a_('clanid')) \
            .select(a_('clanid')) \
            .to_list()

        return [api.data.clans.get(x) for x in clanids]

    def load_clans(self):
        self.cb_clan.blockSignals(True)
        self.cb_clan.clear()
        self.cb_clan.addItem(self.tr("No Clan"), None)

        clan_list = self.get_filtered_clan_list()

        for c in sorted(clan_list, key=lambda x: x.name):
            self.cb_clan.addItem(c.name, c.id)
        self.cb_clan.blockSignals(False)

        self.on_clan_changed(0)

    def load_schools(self, clanid=None):

        self.cb_school.blockSignals(True)
        self.cb_school.clear()

        school_list = self.get_filtered_school_list()

        if clanid:
            school_list = [x for x in school_list if x.clanid == clanid]

        for f in sorted(school_list, key=lambda x: x.name):
            self.cb_school.addItem(f.name, f.id)
        self.cb_school.blockSignals(False)

        # load first school
        self.on_school_changed(0)

    def hide_row(self, fld):
        fld.hide()
        self.form_layout.labelForField(fld).hide()

    def show_row(self, fld):
        fld.show()
        self.form_layout.labelForField(fld).show()

    def set_row_visible(self, fld, flag):
        if flag:
            self.show_row(fld)
        else:
            self.hide_row(fld)

    def update_ui_with_school(self, school_id):

        self.cb_clan.blockSignals(True)
        self.cb_school.blockSignals(True)

        # get school_dal
        school_dal = api.data.schools.get(school_id)
        if school_dal:
            self.current_school_id = school_id
            self.current_clan_id = school_dal.clanid

            self.load_schools(school_dal.clanid)

            clan_index = self.cb_clan.findData(school_dal.clanid)
            self.cb_clan.setCurrentIndex(clan_index)

            school_index = self.cb_school.findData(school_dal.id)
            self.cb_school.setCurrentIndex(school_index)

            self.update_school_properties(school_dal)

        self.cb_clan.blockSignals(False)
        self.cb_school.blockSignals(False)

    def update_ui_with_clan(self, clan_id):

        self.cb_clan.blockSignals(True)
        self.cb_school.blockSignals(True)

        # get clan_dal
        clan_dal = api.data.clans.get(clan_id)
        if clan_dal:
            self.current_school_id = None
            self.current_clan_id = clan_id

            self.load_schools(clan_id)

            clan_index = self.cb_clan.findData(clan_id)
            self.cb_clan.setCurrentIndex(clan_index)

            self.update_school_properties()

        self.cb_clan.blockSignals(False)
        self.cb_school.blockSignals(False)

    def on_clan_changed(self, index_or_text):
        self.current_clan_id = self.cb_clan.itemData(self.cb_clan.currentIndex())
        self.load_schools(self.current_clan_id)

    def on_school_changed(self, index_or_text):
        self.current_school_id = self.cb_school.itemData(self.cb_school.currentIndex())
        self.update_school_properties()

    def on_base_filter_change(self, state):
        self.allow_basic_schools = self.sender().isChecked()

    def on_advc_filter_change(self, state):
        self.allow_advanced_schools = self.sender().isChecked()

    def on_path_filter_change(self, state):
        self.allow_alternate_paths = self.sender().isChecked()

    def update_school_properties(self, school_dal=None):
        if not school_dal:
            school_dal = api.data.schools.get(self.current_school_id)
        if school_dal:
            self.update_bonus_trait(school_dal)
            self.update_school_requirements(school_dal)
            self.update_book(school_dal)

            self.update_status()

    def update_school_requirements(self, school_dal):
        self.req_list.set_requirements(api.character.model(),
                                       api.data.model(),
                                       api.data.schools.get_requirements(school_dal.id))
        if self._show_school_requirements:
            self.set_row_visible(self.pl_requirements,
                                 len(school_dal.require) > 0)
        self.update()

    def update_bonus_trait(self, school_dal):
        bonus_trait = None
        try:
            bonus_trait = school_dal.trait
        except:
            print('cannot find bonus trait of {}'.format(self.current_school_id))

        if not bonus_trait:
            self.lb_trait.setText(red(self.tr("None")))
        else:
            self.lb_trait.setText(green(u"+1 {}").format(api.data.get_trait_or_ring(bonus_trait)))

    def update_book(self, school_dal):
        source_book = None
        try:
            source_book = school_dal.pack
        except:
            print('cannot find source book of {}'.format(self.current_school_id))

        if not source_book:
            self.lb_book.setText("")
        else:
            self.lb_book.setText(source_book.display_name)

    def update_status(self):
        requirements_ok = self.req_list.match() if self.req_list is not None else True
        experience_ok = self.check_needed_experience()
        school_selected = self.current_clan_id is not None and self.current_school_id is not None

        new_status = requirements_ok and school_selected and experience_ok
        if new_status != self._old_status:
            self._old_status = new_status
            self.statusChanged.emit(new_status)

    def check_needed_experience(self):
        xp_needed = 0
        if self.different_school_merit:
            xp_needed += api.data.merits.get_rank_cost('different_school', 1)
        if self.multiple_schools_merit:
            xp_needed += api.data.merits.get_rank_cost('multiple_schools', 1)

        has_enough_xp = api.character.xp_left() >= xp_needed

        self.lb_different_school_err.setVisible(self.different_school_merit and not has_enough_xp)
        self.lb_multiple_schools_err.setVisible(self.multiple_schools_merit and not has_enough_xp)

        return has_enough_xp

    def show_or_hide_option_panel(self):
        self._show_options_panel = (self._show_multiple_school_check or
                                    self._show_different_school_check)
        self.set_row_visible(self.pl_options, self._show_options_panel)
        self.ck_different_school.setVisible(self._show_different_school_check)
        self.ck_multiple_schools.setVisible(self._show_multiple_school_check)


# ## MAIN ## #


def main():
    import sys
    app = QtGui.QApplication(sys.argv)

    dlg = QtGui.QDialog()
    fam = SchoolChooserWidget(dlg)

    # fam.selected_school = 'hida_bushi_school'
    fam.selected_clan = 'mantis'
    vbox = QtGui.QVBoxLayout(dlg)
    vbox.addWidget(fam)
    dlg.exec_()

    print('selected school', fam.selected_school)


if __name__ == '__main__':
    main()
