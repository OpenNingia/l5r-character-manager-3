# -*- coding: utf-8 -*-
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

from PyQt5.QtGui import QBrush, QColor
from PyQt5.QtCore import QSettings, QDir


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

    def __exit__(self):
        # probably not needed
        self._qsettings.sync()


class L5RCMSettings_UI(object):
    """Contains UI settings"""

    def __init__(self, qsettings):
        self._qsettings = qsettings

    # getter
    @property
    def table_row_color_bg(self):
        return self._qsettings.value('ui/table-row-color-bg')

    @property
    def table_row_color_fg(self):
        return self._qsettings.value('ui/table-row-color-fg')

    @property
    def table_row_color_alt_bg(self):
        return self._qsettings.value('ui/table-row-color-alt-bg', QBrush(QColor("#eeeeee")))

    @property
    def table_row_color_alt_fg(self):
        return self._qsettings.value('ui/table-row-color-alt-fg')

    @property
    def table_row_size(self):
        return self._qsettings.value('ui/table-row-size')

    @property
    def use_system_font(self):
        return self._qsettings.value('ui/use-system-font')

    @property
    def user_font(self):
        return self._qsettings.value('ui/user-font')

    @property
    def banner_enabled(self):
        return _is_true(self._qsettings.value('ui/isbannerenabled', True))

    # setter
    @table_row_color_bg.setter
    def table_row_color_bg(self, value):
        self._qsettings.setValue('ui/table-row-color-bg', value)

    @table_row_color_fg.setter
    def table_row_color_fg(self, value):
        self._qsettings.setValue('ui/table-row-color-fg', value)

    @table_row_color_alt_bg.setter
    def table_row_color_alt_bg(self, value):
        self._qsettings.setValue('ui/table-row-color-alt-bg', value)

    @table_row_color_alt_fg.setter
    def table_row_color_alt_fg(self, value):
        self._qsettings.setValue('ui/table-row-color-alt-fg', value)

    @table_row_size.setter
    def table_row_size(self, value):
        self._qsettings.setValue('ui/table-row-size', value)

    @use_system_font.setter
    def use_system_font(self, value):
        self._qsettings.setValue('ui/use-system-font', value)

    @user_font.setter
    def font_size(self, value):
        self._qsettings.setValue('ui/user-font', value)

    @banner_enabled.setter
    def banner_enabled(self, value):
        self._qsettings.setValue('ui/isbannerenabled', str(value))


class L5RCMSettings_PcExport(object):
    """Contains PC export settings"""

    def __init__(self, qsettings):
        self._qsettings = qsettings

    @property
    def first_page_skills(self):
        return _is_true(self._qsettings.value('pcexport/first-page-skills', True))


class L5RCMSettings_NpcExport(object):
    """Contains NPC export settings"""

    def __init__(self, qsettings):
        self._qsettings = qsettings


class L5RCMSettings_App(object):
    """Contains application settings"""
    def __init__(self, qsettings):
        self._qsettings = qsettings

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
        return _is_true(self._qsettings.value('advise_successfull_import', True))

    @property
    def geometry(self):
        return self._qsettings.value('geometry')

    @property
    def user_locale(self):
        return self._qsettings.value('use_locale', 'en_US')

    @property
    def use_system_locale(self):
        return _is_true(self._qsettings.value('use_machine_locale', True))

    # setter
    @health_method.setter
    def health_method(self, value):
        self._qsettings.setValue('health_method', value)

    @data_pack_blacklist.setter
    def data_pack_blacklist(self, value):
        self._qsettings.setValue('data_pack_blacklist', value)

    @warn_about_refund.setter
    def warn_about_refund(self, value):
        self._qsettings.setValue('warn_about_refund', str(value))

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
        self._qsettings.setValue('advise_successfull_import', str(value))

    @geometry.setter
    def geometry(self, value):
        self._qsettings.setValue('geometry', value)

    @use_system_locale.setter
    def use_system_locale(self, value):
        self._qsettings.setValue('use_machine_locale', str(value))

    @user_locale.setter
    def user_locale(self, value):
        self._qsettings.setValue('user_locale', value)