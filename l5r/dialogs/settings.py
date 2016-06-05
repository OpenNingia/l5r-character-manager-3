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

from PyQt5 import QtCore, QtGui, QtWidgets


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


class QPropertySettingsBinder(QtCore.QObject):
    """Bind Qt Properties to QSettings' values"""
    def __init__(self, parent, signal, prop, setting, data_converter=None):
        super(QPropertySettingsBinder, self).__init__(parent)

        self.signal = signal
        self.prop = prop
        self.setting = setting
        self.converter = data_converter

        self.settings = QtCore.QSettings()

        self.update_property()
        signal.connect(self.on_notify)

    def on_notify(self, *args, **kwargs):
        if self.converter:
            nv = self.converter.convert_from(self.parent().property(self.prop))
        else:
            nv = self.parent().property(self.prop)

        print("update settings {} = {}".format(self.setting, nv))
        self.settings.setValue(self.setting, nv)
        self.update_property()

    def update_property(self):
        if self.converter:
            nv = self.converter.convert_to(self.settings.value(self.setting))
        else:
            nv = self.settings.value(self.setting)
        print("set property {} to {}".format(self.prop, nv))
        self.parent().blockSignals(True)
        self.parent().setProperty(self.prop, nv)
        self.parent().blockSignals(False)


class QComboBoxSettingsBinder(QPropertySettingsBinder):
    def __init__(self, parent, setting, data_converter=None):
        super(QComboBoxSettingsBinder, self).__init__(parent, parent.activated, 'currentData', setting, data_converter)

        # workaround for combobox
        idx = parent.findData(self.settings.value(setting))
        parent.setCurrentIndex(idx)


class SettingsDialog(QtWidgets.QDialog):
    """Application settings dialog"""

    def __init__(self, parent=None):
        super(SettingsDialog, self).__init__(parent)

        # build interface
        self.area = QtWidgets.QScrollArea(self)
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.area)
        layout.setContentsMargins(0, 0, 0, 0)

        fr = QtWidgets.QFrame()
        vb = QtWidgets.QVBoxLayout(fr)
        vb.setContentsMargins(32, 32, 32, 32)
        vb.addStrut(232)

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

        fr.setLayout(vb)

        self.area.setWidget(fr)
        self.area.viewport().setBackgroundRole(QtGui.QPalette.Light)
        self.area.viewport().setAutoFillBackground(True)

        self.setLayout(layout)

    def setup(self):

        # fill data
        languages = [
            ('en_US', self.tr("US English")),
            ('en_GB', self.tr("UK English")),
            ('it_IT', self.tr("Italian")),
            ('es_ES', self.tr("Spanish")),
            ('fr_FR', self.tr("French")),
            ('pr_BR', self.tr("Portoguese (Brasil)")),
            ('ru_RU', self.tr("Russian"))
        ]

        for t in languages:
            self.cb_select_lang.addItem(t[1], t[0])

        # language
        QPropertySettingsBinder(
            self.ck_use_system_lang,
            self.ck_use_system_lang.stateChanged,
            "checked", "use_machine_language")

        QComboBoxSettingsBinder(
            self.cb_select_lang,
            "use_locale")

        self.ck_use_system_lang.toggled.connect(
            self.cb_select_lang.setEnabled
        )
        self.cb_select_lang.setEnabled(
            self.ck_use_system_lang.isChecked()
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
            "ui/user-font",
            QFontSelectorDataConverter(self))

        self.ck_use_system_font.toggled.connect(
            self.bt_select_font.setEnabled
        )

        self.bt_select_font.setEnabled(
            self.ck_use_system_font.isChecked()
        )

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
            "health_method")

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


def test():
    a = QtWidgets.QApplication([])

    APP_NAME = 'l5rcm'
    APP_VERSION = '3.11.0'
    APP_ORG = 'openningia'

    QtCore.QCoreApplication.setApplicationName(APP_NAME)
    QtCore.QCoreApplication.setApplicationVersion(APP_VERSION)
    QtCore.QCoreApplication.setOrganizationName(APP_ORG)

    d = SettingsDialog()
    d.resize(300, 640)
    d.setup()
    d.show()
    a.exec_()

if __name__ == "__main__":
    test()
