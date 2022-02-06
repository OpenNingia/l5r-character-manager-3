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

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QObject, pyqtProperty
from l5r.util.settings import L5RCMSettings
import api

class QExampleListModel(QtCore.QAbstractListModel):
    def __init__(self, parent=None):
        super(QExampleListModel, self).__init__(parent)
        self.items = [
            self.tr("An odd row"),
            self.tr("An even row"),
            self.tr("Another odd row"),
        ]

        self._alt_bg = QtGui.QBrush()
        self._alt_fg = QtGui.QBrush()
        self._bg = QtGui.QBrush()
        self._fg = QtGui.QBrush()

    @pyqtProperty(QtGui.QBrush)
    def odd_bg(self):
        print('get odd bg')
        return self._bg

    @odd_bg.setter
    def odd_bg(self, value):
        print('set odd bg')
        self._bg = value

    @pyqtProperty(QtGui.QBrush)
    def odd_fg(self):
        return self._fg

    @odd_fg.setter
    def odd_fg(self, value):
        self._fg = value

    @pyqtProperty(QtGui.QBrush)
    def evn_bg(self):
        return self._alt_bg

    @evn_bg.setter
    def evn_bg(self, value):
        self._alt_bg = value

    @pyqtProperty(QtGui.QBrush)
    def evn_fg(self):
        return self._alt_fg

    @evn_fg.setter
    def evn_fg(self, value):
        self._alt_fg = value

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self.items)

    def data(self, index, role=QtCore.Qt.UserRole):
        if not index.isValid() or index.row() >= len(self.items):
            return None
        item = self.items[index.row()]
        if role == QtCore.Qt.DisplayRole:
            return item
        elif role == QtCore.Qt.ForegroundRole:
            if index.row() % 2:
                return self._alt_fg
            return self._fg
        elif role == QtCore.Qt.BackgroundRole:
            if index.row() % 2:
                return self._alt_bg
            return self._bg
        #elif role == QtCore.Qt.SizeHintRole:
        #    return self.settings.ui.table_row_size
        return None

class QDataConverter(QtCore.QObject):
    def __init__(self, parent=None):
        super(QDataConverter, self).__init__(parent)

    def convert_from(self, value):
        pass

    def convert_to(self, value):
        pass


class QFontSelectorDataConverter(QDataConverter):
    """Convert a QFont to font-family string and back"""

    def __init__(self, parent=None):
        super(QFontSelectorDataConverter, self).__init__(parent)

    def convert_from(self, value):
        font, ok = QtWidgets.QFontDialog.getFont(QtGui.QFont(), self.parent())
        if ok:
            return "{}, {}".format(font.family(), font.pointSize())
        return value

    def convert_to(self, value):
        print('convert_to', value)
        return value


class QColorPaletteDataConverter(QDataConverter):
    """Select a color, convert to QBrush for settings"""

    def __init__(self, role=None, parent=None):
        super(QColorPaletteDataConverter, self).__init__(parent)
        self.color_role = role

    def convert_from(self, value):
        color = QtWidgets.QColorDialog.getColor(QtGui.QColor(), self.parent())
        return QtGui.QBrush(color)

    def convert_to(self, value):
        print('convert_to', value)
        palette = self.parent().palette()
        if value:
            palette.setBrush(self.color_role, value)
        return palette

class QBrushSelectorDataConverter(QDataConverter):
    """Select a color, convert to QBrush for settings"""

    def __init__(self, parent=None):
        super(QBrushSelectorDataConverter, self).__init__(parent)

    def convert_from(self, value):
        color = QtWidgets.QColorDialog.getColor(QtGui.QColor(), self.parent())
        return QtGui.QBrush(color)

    def convert_to(self, value):
        print('convert_to', value)
        return value

class QPropertySettingsBinder(QtCore.QObject):
    """Bind Qt Properties to QSettings' values"""
    def __init__(self, parent, signal, prop, setting, data_converter=None, callback=None):
        super(QPropertySettingsBinder, self).__init__(parent)

        self.signal = signal
        self.prop = prop
        self.setting = setting
        self.converter = data_converter
        self.callback = callback

        signal.connect(self.on_notify)

        self.update_property()

    def on_notify(self, *args, **kwargs):
        if self.converter:
            nv = self.converter.convert_from(self.parent().property(self.prop))
        else:
            nv = self.parent().property(self.prop)

        print("update settings {} = {}".format(self.setting, nv))
        settings = QtCore.QSettings()
        settings.setValue(self.setting, nv)
        self.update_property()

    def update_property(self):
        settings = QtCore.QSettings()

        if self.converter:
            nv = self.converter.convert_to(settings.value(self.setting))
        else:
            nv = settings.value(self.setting)

        #if self.parent().property(self.prop) == nv:
        #    return

        print("set property {} from {} to {}".format(self.prop, self.parent().property(self.prop), nv))
        self.parent().blockSignals(True)
        self.parent().setProperty(self.prop, nv)
        self.parent().blockSignals(False)
        
        if self.callback:
            self.callback(nv)

class QComboBoxSettingsBinder(QPropertySettingsBinder):
    def __init__(self, parent, setting, data_converter=None, callback=None):
        super(QComboBoxSettingsBinder, self).__init__(parent, parent.activated, 'currentData', setting, data_converter, callback)

        settings = QtCore.QSettings()

        # workaround for combobox
        idx = parent.findData(settings.value(setting))
        parent.setCurrentIndex(idx)


class SettingsWidget(QtWidgets.QWidget):
    """Application settings widget"""

    def __init__(self, parent=None):
        super(SettingsWidget, self).__init__(parent)

        # build interface
        self.area = QtWidgets.QScrollArea(self)
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.area)
        layout.setContentsMargins(0, 0, 0, 0)

        fr = QtWidgets.QFrame()
        vb = QtWidgets.QVBoxLayout(fr)
        vb.setContentsMargins(32, 32, 32, 32)
        vb.addStrut(300)

        # Generic
        vb.addWidget(QtWidgets.QLabel(self.tr("<h2>Settings</h2>")))
        self.ck_use_system_lang = QtWidgets.QCheckBox(
            self.tr("Use system language"), self)
        self.cb_select_lang = QtWidgets.QComboBox(self)
        self.ck_use_system_font = QtWidgets.QCheckBox(
            self.tr("Use system font"), self)

        self.bt_select_font = QtWidgets.QPushButton(self)
        self.ck_show_banner = QtWidgets.QCheckBox(
            self.tr("Show application banner"), self)

        vb.addWidget(self.ck_use_system_lang)
        vb.addWidget(self.cb_select_lang)
        vb.addWidget(self.ck_use_system_font)
        vb.addWidget(self.bt_select_font)
        vb.addWidget(self.ck_show_banner)

        vb.addSpacing(12)
        vb.addWidget(QtWidgets.QLabel(self.tr("<h3>Health display</h3>")))
        self.cb_health_method = QtWidgets.QComboBox(self)
        vb.addWidget(self.cb_health_method)

        vb.addSpacing(12)
        vb.addWidget(QtWidgets.QLabel(self.tr("<h3>Insight calculation</h3>")))
        self.cb_insight_method = QtWidgets.QComboBox(self)
        vb.addWidget(self.cb_insight_method)

        vb.addSpacing(12)
        vb.addWidget(QtWidgets.QLabel(self.tr("<h3>Table Colors</h3>")))
        self.lv_example = QtWidgets.QListView(self)
        #self.lv_example.setAlternatingRowColors(True)
        self.lv_example_model = QExampleListModel(self)
        self.lv_example.setModel(self.lv_example_model)

        self.bt_odd_bg = QtWidgets.QPushButton(self.tr("Odd row background"), self)
        self.bt_odd_fg = QtWidgets.QPushButton(self.tr("Odd row foreground"), self)
        self.bt_evn_bg = QtWidgets.QPushButton(self.tr("Even row background"), self)
        self.bt_evn_fg = QtWidgets.QPushButton(self.tr("Even row foreground"), self)

        hb_odd = QtWidgets.QHBoxLayout()
        hb_evn = QtWidgets.QHBoxLayout()
        hb_odd.addWidget(self.bt_odd_bg)
        hb_odd.addWidget(self.bt_odd_fg)
        hb_evn.addWidget(self.bt_evn_bg)
        hb_evn.addWidget(self.bt_evn_fg)

        vb.addWidget(self.lv_example)
        vb.addLayout(hb_odd)
        vb.addLayout(hb_evn)

        # PC EXPORT
        vb.addSpacing(20)
        vb.addWidget(QtWidgets.QLabel(self.tr("<h2>Character sheet</h2>")))
        self.ck_skills_on_first_page = QtWidgets.QCheckBox(
            self.tr("Print skills on first page"), self)
        vb.addWidget(self.ck_skills_on_first_page)        

        fr.setLayout(vb)

        self.area.setWidget(fr)
        self.area.viewport().setBackgroundRole(QtGui.QPalette.Light)
        self.area.viewport().setAutoFillBackground(True)

        self.setLayout(layout)

    def setup(self, app):

        # fill data
        languages = [
            ('en_US', self.tr("US English")),
            ('en_GB', self.tr("UK English")),
            ('it_IT', self.tr("Italian")),
            ('es_ES', self.tr("Spanish")),
            ('fr_FR', self.tr("French")),
            ('pt_BR', self.tr("Portoguese (Brasil)")),
            ('ru_RU', self.tr("Russian"))
        ]

        for t in languages:
            self.cb_select_lang.addItem(t[1], t[0])

        # language
        QPropertySettingsBinder(
            self.ck_use_system_lang,
            self.ck_use_system_lang.stateChanged,
            "checked", "use_machine_locale")

        QComboBoxSettingsBinder(
            self.cb_select_lang,
            "user_locale")

        self.ck_use_system_lang.toggled.connect(
            lambda x: self.cb_select_lang.setEnabled(not x)
        )
        self.cb_select_lang.setEnabled(
            not self.ck_use_system_lang.isChecked()
        )


        # font
        QPropertySettingsBinder(
            self.ck_use_system_font,
            self.ck_use_system_font.stateChanged,
            "checked", "ui/use_system_font")

        QPropertySettingsBinder(
            self.bt_select_font,
            self.bt_select_font.clicked,
            "text",
            "ui/user_font",
            QFontSelectorDataConverter(self))

        self.ck_use_system_font.toggled.connect(
            lambda x: self.bt_select_font.setEnabled(not x)
        )

        self.bt_select_font.setEnabled(
            not self.ck_use_system_font.isChecked()
        )

        # banner
        QPropertySettingsBinder(
            self.ck_show_banner,
            self.ck_show_banner.stateChanged,
            "checked", "ui/isbannerenabled",
            callback=lambda x: app.sink1.set_banner_visibility(x))

        # health display
        hmethods = [
            ('default', self.tr("Default")),
            ('stacked', self.tr("Health left")),
            ('wounds', self.tr("Total wounds"))
        ]

        for t in hmethods:
            self.cb_health_method.addItem(t[1], t[0])

        QComboBoxSettingsBinder(
            self.cb_health_method,
            "health_method", callback=lambda x: app.display_health())

        # insight calculation
        imethods = [
            (1, self.tr("Default")),
            (2, self.tr("Ignore Rank 1 Skills")),
            (3, self.tr("Account Rank 1 School Skills"))
        ]

        for t in imethods:
            self.cb_insight_method.addItem(t[1], t[0])

        QComboBoxSettingsBinder(
            self.cb_insight_method,
            "insight_calculation")

        QPropertySettingsBinder(
            self.lv_example_model,
            self.bt_odd_bg.clicked,
            "odd_bg",
            "ui/table_row_color_bg",
            QBrushSelectorDataConverter(self))

        QPropertySettingsBinder(
            self.lv_example_model,
            self.bt_evn_bg.clicked,
            "evn_bg",
            "ui/table_row_color_alt_bg",
            QBrushSelectorDataConverter(self))

        QPropertySettingsBinder(
            self.lv_example_model,
            self.bt_odd_fg.clicked,
            "odd_fg",
            "ui/table_row_color_fg",
            QBrushSelectorDataConverter(self))

        QPropertySettingsBinder(
            self.lv_example_model,
            self.bt_evn_fg.clicked,
            "evn_fg",
            "ui/table_row_color_alt_fg",
            QBrushSelectorDataConverter(self))

        # pdf sheet
        QPropertySettingsBinder(
            self.ck_skills_on_first_page,
            self.ck_skills_on_first_page.stateChanged,
            "checked", "pcexport/first_page_skills")


def test():
    a = QtWidgets.QApplication([])

    APP_NAME = 'l5rcm'
    APP_VERSION = '3.11.0'
    APP_ORG = 'openningia'

    QtCore.QCoreApplication.setApplicationName(APP_NAME)
    QtCore.QCoreApplication.setApplicationVersion(APP_VERSION)
    QtCore.QCoreApplication.setOrganizationName(APP_ORG)

    d = QtWidgets.QDialog()
    s = SettingsWidget(d)
    vb = QtWidgets.QVBoxLayout(d)
    vb.addWidget(s)
    d.resize(366, 640)
    s.setup(None)
    d.show()
    a.exec_()

if __name__ == "__main__":
    test()
