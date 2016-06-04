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
    

class QWidgetSettingsBinder(QtCore.QObject):
    """Bind qwidgets to qsettings"""
    def __init__(self, parent, signal, prop, setting, value_type):
        super(QWidgetSettingsBinder, self).__init__(parent)
        
        self.signal = signal
        self.prop = prop
        self.setting = setting
        self.value_type = value_type

        self.settings = QtCore.QSettings()
    
        print("set property {} to {}".format(self.prop, self.settings.value(setting)))
        parent.setProperty(self.prop, self.settings.value(setting))
        signal.connect(self.on_notify)


    def on_notify(self, *args, **kwargs):
        print("property {} = {}".format(self.prop, self.parent().property(self.prop)))
        self.settings.setValue(self.setting, self.parent().property(self.prop)) 
        
class QComboBoxSettingsBinder(QWidgetSettingsBinder):
    def __init__(self, parent, setting):
        super(QComboBoxSettingsBinder, self).__init__(parent, parent.activated, 'currentData', setting, None)
        
        # workaround for combobox
        idx = parent.findData(self.settings.value(setting))
        parent.setCurrentIndex(idx) 

class QFontComboBoxSettingsBinder(QWidgetSettingsBinder):
    def __init__(self, parent, setting):
        super(QComboBoxSettingsBinder, self).__init__(parent, parent.activated, 'currentFont', setting, None)
        
        # workaround for combobox
        tmp = QFont(self.settings.value(setting))
        parent.setCurrentFont(tmp) 


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

        # Generic
        vb.addWidget(QtWidgets.QLabel(self.tr("<h2>Generic</h2>")))
        self.ck_use_system_lang = QtWidgets.QCheckBox(
            self.tr("Use system language"), self)
        self.cb_select_lang = QtWidgets.QComboBox(self)
        self.ck_use_system_font = QtWidgets.QCheckBox(
            self.tr("Use system font"), self)

        hb1 = QtWidgets.QHBoxLayout()
        self.cb_select_font = QtWidgets.QFontComboBox(self)
        self.sz_font_size = QtWidgets.QDoubleSpinBox(self)
        for w in [self.cb_select_font, self.sz_font_size]:
            hb1.addWidget(w)

        self.ck_show_banner = QtWidgets.QCheckBox(
            self.tr("Show application banner"), self)

        vb.addWidget(self.ck_use_system_lang)
        vb.addWidget(self.cb_select_lang)
        vb.addWidget(self.ck_use_system_font)
        vb.addLayout(hb1)
        vb.addWidget(self.ck_show_banner)

        #
        vb.addWidget(QtWidgets.QLabel(self.tr("<h2>Health display</h2>")))
        fr.setLayout(vb)

        self.area.setWidget(fr)
        self.area.viewport().setBackgroundRole(QtGui.QPalette.Light);
        self.area.viewport().setAutoFillBackground(True);

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

        # system language
        QWidgetSettingsBinder(
            self.ck_use_system_lang, 
            self.ck_use_system_lang.stateChanged, 
            "checked", "use_machine_language", type(bool))
    
        QComboBoxSettingsBinder(
            self.cb_select_lang, 
            "use_locale")

        QComboBoxSettingsBinder(
            self.cb_select_font, 
            "font-family")
def test():
    a = QtWidgets.QApplication([])
    d = SettingsDialog()
    d.setup()
    d.show()
    a.exec_()

if __name__ == "__main__":
    test()
