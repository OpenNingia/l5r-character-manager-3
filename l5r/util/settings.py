# -*- coding: utf-8 -*-
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

from qtpy.QtGui import QBrush, QColor
from qtpy.QtCore import QSettings, QDir


def _is_true(val):
    return val in [1, 'true', 'True', True]


class L5RCMSettings(object):
    """A QSettings wrapper for easy access to application settings"""

    def __init__(self):
        self._qsettings = QSettings()

        # Application settings
        self._app = L5RCMSettings_App(self._qsettings)
        # UI settings
        self._ui = L5RCMSettings_UI(self._qsettings)
        # PC export PDF generation settings
        self._pc_export = L5RCMSettings_PcExport(self._qsettings)
        # NPC export PDF generation settings
        self._npc_export = L5RCMSettings_NpcExport(self._qsettings)

    @property
    def app(self):
        return self._app

    @property
    def ui(self):
        return self._ui

    @property
    def pc_export(self):
        return self._pc_export

    @property
    def npc_export(self):
        return self._npc_export

    def sync(self):
        self._qsettings.sync()

    def load_defaults(self):
        self._app.load_defaults()
        self._ui.load_defaults()
        self._pc_export.load_defaults()
        self._npc_export.load_defaults()



class L5RCMSettings_UI(object):
    """Contains UI settings"""

    def __init__(self, qsettings):
        self._qsettings = qsettings

    def load_defaults(self):
        self.table_row_color_bg = self.table_row_color_bg
        self.table_row_color_fg = self.table_row_color_fg
        self.table_row_color_alt_bg = self.table_row_color_alt_bg
        self.table_row_color_alt_fg = self.table_row_color_alt_fg
        self.table_row_size = self.table_row_size
        self.use_system_font = self.use_system_font
        self.user_font = self.user_font
        self.banner_enabled = self.banner_enabled
        self.use_qml_ui = self.use_qml_ui

    # getter
    @property
    def table_row_color_bg(self):
        return self._qsettings.value('ui/table_row_color_bg')

    @property
    def table_row_color_fg(self):
        return self._qsettings.value('ui/table_row_color_fg')

    @property
    def table_row_color_alt_bg(self):
        return self._qsettings.value('ui/table_row_color_alt_bg', QBrush(QColor("#eeeeee")))

    @property
    def table_row_color_alt_fg(self):
        return self._qsettings.value('ui/table_row_color_alt_fg')

    @property
    def table_row_size(self):
        return self._qsettings.value('ui/table_row_size')

    @property
    def use_system_font(self):
        return _is_true(self._qsettings.value('ui/use_system_font', True))        

    @property
    def user_font(self):
        return self._qsettings.value('ui/user_font')

    @property
    def banner_enabled(self):
        return _is_true(self._qsettings.value('ui/isbannerenabled', True))

    @property
    def use_qml_ui(self):
        # The new parchment QML front-end is the default; the legacy
        # QWidget UI is the opt-out. The L5RCM_UI env var still overrides
        # this at startup (dev escape hatch) -- see l5r.main.main().
        return _is_true(self._qsettings.value('ui/use_qml_ui', True))

    # setter
    @table_row_color_bg.setter
    def table_row_color_bg(self, value):
        self._qsettings.setValue('ui/table_row_color_bg', value)

    @table_row_color_fg.setter
    def table_row_color_fg(self, value):
        self._qsettings.setValue('ui/table_row_color_fg', value)

    @table_row_color_alt_bg.setter
    def table_row_color_alt_bg(self, value):
        self._qsettings.setValue('ui/table_row_color_alt_bg', value)

    @table_row_color_alt_fg.setter
    def table_row_color_alt_fg(self, value):
        self._qsettings.setValue('ui/table_row_color_alt_fg', value)

    @table_row_size.setter
    def table_row_size(self, value):
        self._qsettings.setValue('ui/table_row_size', value)

    @use_system_font.setter
    def use_system_font(self, value):
        self._qsettings.setValue('ui/use_system_font', value)

    @user_font.setter
    def user_font(self, value):
        self._qsettings.setValue('ui/user_font', value)

    @banner_enabled.setter
    def banner_enabled(self, value):
        self._qsettings.setValue('ui/isbannerenabled', value)

    @use_qml_ui.setter
    def use_qml_ui(self, value):
        self._qsettings.setValue('ui/use_qml_ui', value)


class L5RCMSettings_PcExport(object):
    """Contains PC export settings"""

    def __init__(self, qsettings):
        self._qsettings = qsettings

    def load_defaults(self):
        self.first_page_skills = self.first_page_skills
        self.print_current_armor_tn = self.print_current_armor_tn

    @property
    def first_page_skills(self):
        return _is_true(self._qsettings.value('pcexport/first_page_skills', True))

    @first_page_skills.setter
    def first_page_skills(self, value):
        self._qsettings.setValue('pcexport/first_page_skills', value)

    @property
    def print_current_armor_tn(self):
        # The current Armor TN changes constantly during play, so by default
        # it is left blank on the exported sheet to be filled in by hand.
        return _is_true(self._qsettings.value('pcexport/print_current_armor_tn', False))

    @print_current_armor_tn.setter
    def print_current_armor_tn(self, value):
        self._qsettings.setValue('pcexport/print_current_armor_tn', value)


class L5RCMSettings_NpcExport(object):
    """Contains NPC export settings"""

    def __init__(self, qsettings):
        self._qsettings = qsettings

    def load_defaults(self):
        pass


class L5RCMSettings_App(object):
    """Contains application settings"""
    def __init__(self, qsettings):
        self._qsettings = qsettings

    def load_defaults(self):
        self.health_method = self.health_method
        self.data_pack_blacklist = self.data_pack_blacklist
        self.warn_about_refund = self.warn_about_refund
        self.last_open_image_dir = self.last_open_image_dir
        self.last_open_data_dir = self.last_open_data_dir
        self.last_open_dir = self.last_open_dir
        self.insight_calculation = self.insight_calculation
        self.advise_successful_import = self.advise_successful_import
        #self.ui_exp_display = self.ui_exp_display
        # skip geometry
        self.user_locale = self.user_locale
        self.use_system_locale = self.use_system_locale

    # getter
    @property
    def health_method(self):
        return self._qsettings.value('health_method', 'wounds')

    @property
    def data_pack_blacklist(self):
        return self._qsettings.value('data_pack_blacklist', [])

    @property
    def warn_about_refund(self):
        return _is_true(self._qsettings.value('warn_about_refund', True))

    @property
    def last_open_image_dir(self):
        return self._qsettings.value('last_open_image_dir', QDir.homePath())

    @property
    def last_open_data_dir(self):
        return self._qsettings.value('last_open_data_dir', QDir.homePath())

    @property
    def last_open_dir(self):
        return self._qsettings.value('last_open_dir', QDir.homePath())

    @property
    def insight_calculation(self):
        return self._qsettings.value('insight_calculation', 1)

    @property
    def advise_successful_import(self):
        return _is_true(self._qsettings.value('advise_successful_import', True))

    @property
    def geometry(self):
        return self._qsettings.value('geometry')

    @property
    def user_locale(self):
        return self._qsettings.value('user_locale', 'en_US')

    @property
    def use_system_locale(self):
        return _is_true(self._qsettings.value('use_machine_locale', True))

    @property
    def ui_font_size(self):
        return self._qsettings.value('ui_font_size', 'standard')

    @property
    def ui_exp_display(self):
        return self._qsettings.value('ui_exp_display', 1)

    # setter
    @health_method.setter
    def health_method(self, value):
        self._qsettings.setValue('health_method', value)

    @data_pack_blacklist.setter
    def data_pack_blacklist(self, value):
        self._qsettings.setValue('data_pack_blacklist', value)

    @warn_about_refund.setter
    def warn_about_refund(self, value):
        self._qsettings.setValue('warn_about_refund', value)

    @last_open_image_dir.setter
    def last_open_image_dir(self, value):
        self._qsettings.setValue('last_open_image_dir', value)

    @last_open_data_dir.setter
    def last_open_data_dir(self, value):
        self._qsettings.setValue('last_open_data_dir', value)

    @last_open_dir.setter
    def last_open_dir(self, value):
        self._qsettings.setValue('last_open_dir', value)

    @insight_calculation.setter
    def insight_calculation(self, value):
        self._qsettings.setValue('insight_calculation', value)

    @advise_successful_import.setter
    def advise_successful_import(self, value):
        self._qsettings.setValue('advise_successful_import', value)

    @geometry.setter
    def geometry(self, value):
        self._qsettings.setValue('geometry', value)

    @use_system_locale.setter
    def use_system_locale(self, value):
        self._qsettings.setValue('use_machine_locale', value)

    @user_locale.setter
    def user_locale(self, value):
        self._qsettings.setValue('user_locale', value)

    @ui_font_size.setter
    def ui_font_size(self, value):
        self._qsettings.setValue('ui_font_size', value)

    @ui_exp_display.setter
    def ui_exp_display(self, value):
        self._qsettings.setValue('ui_exp_display', value)

