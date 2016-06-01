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
from PyQt5.QtCore import QSettings

class L5RCMSettings(object):
    """A QSettings wrapper for easy access to application settings"""

    def __init__(self):
        qsettings = QSettings()

        # Application settings
        self._app = L5RCMSettings_App(qsettings)
        # UI settings
        self._ui = L5RCMSettings_UI(qsettings)
        # PC export PDF generation settings
        self._pc_export = L5RCMSettings_PcExport(qsettings)
        # NPC export PDF generation settings
        self._npc_export = L5RCMSettings_NpcExport(qsettings)

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

class L5RCMSettings_UI(object):
    """Contains UI settings"""

    def __init__(self, qsettings):
        qsettings.beginGroup("ui")
        self._table_row_color_bg = qsettings.value('table-row-color-bg')        
        self._table_row_color_fg = qsettings.value('table-row-color-fg')
        self._table_row_color_alt_bg = qsettings.value('table-row-color-alt-bg',
            QBrush(QColor("#eeeeee")))
        self._table_row_color_alt_fg = qsettings.value('table-row-color-alt-fg')        
        self._table_row_size = qsettings.value('table-row-size')
        self._font_family = qsettings.value('font-family')
        self._font_size = qsettings.value('font-size')
        qsettings.endGroup()

    @property
    def table_row_color_bg(self):
        return self._table_row_color_bg
    @property
    def table_row_color_fg(self):
        return self._table_row_color_fg
    @property
    def table_row_color_alt_bg(self):
        return self._table_row_color_alt_bg
    @property
    def table_row_color_alt_fg(self):
        return self._table_row_color_alt_fg        
    @property
    def table_row_size(self):
        return self._table_row_size
    @property
    def font_family(self):
        return self._font_family
    @property
    def font_size(self):
        return self._font_size


class L5RCMSettings_PcExport(object):
    """Contains PC export settings"""

    def __init__(self, qsettings):
        qsettings.beginGroup("pcexport")
        self._first_page_skills = qsettings.value('first-page-skill')
        qsettings.endGroup()

    @property
    def first_page_skills(self):
        return self._first_page_skills

class L5RCMSettings_NpcExport(object):
    """Contains NPC export settings"""

    def __init__(self, qsettings):
        qsettings.beginGroup("npcexport")
        # TODO
        qsettings.endGroup()

class L5RCMSettings_App(object):
    """Contains application settings"""
    def __init__(self, qsettings):
        self._health_method = qsettings.value('health_method', 'wounds')
        self._data_pack_blacklist = qsettings.value('data_pack_blacklist', [])
        self._warn_about_refund = qsettings.value('warn_about_refund', 'true') == 'true'
        self._banner_enabled = qsettings.value('isbannerenabled', 1) == 1
        self._last_open_image_dir = qsettings.value('last_open_image_dir')
        self._insight_calculation = qsettings.value('insight_calculation', 1)
        self._advise_successfull_import = qsettings.value('advise_successfull_import', 'true') == 'true'

    @property
    def health_method(self):
        return self._health_method
    @property
    def data_pack_blacklist(self):
        return self._data_pack_blacklist
    @property
    def warn_about_refund(self):
        return self._warn_about_refund
    @property
    def banner_enabled(self):
        return self._banner_enabled
    @property
    def last_open_image_dir(self):
        return self._last_open_image_dir
    @property
    def insight_calculation(self):
        return self._insight_calculation
    @property
    def advise_successfull_import(self):
        return self._advise_successfull_import