# -*- coding: utf-8 -*-
# Copyright (C) 2014-2026 Daniele Simonetti
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

import mimetypes
import sys

from qtpy import QtCore, QtGui, QtWidgets

import l5r.api as api
import l5r.api.rules

from l5r.l5rcmcore import *
from l5r.ui.advance import AdvanceMixin
from l5r.ui.advise import AdviseMixin
from l5r.ui.health import HealthDisplayMixin
from l5r.ui.menu import MenuMixin, MenuSink
from l5r.ui.nicebar import NicebarMixin
from l5r.ui.persistence import PersistenceMixin, PersistenceSink
from l5r.ui.refresh import ModelRefreshMixin
from l5r.ui.tabs.about import AboutTabMixin
from l5r.ui.tabs.advancements import AdvancementsTabMixin, AdvancementsSink
from l5r.ui.tabs.equipment import EquipmentTabMixin, EquipmentSink
from l5r.ui.tabs.modifiers import ModifiersTabMixin, ModifiersSink
from l5r.ui.tabs.notes import NotesTabMixin
from l5r.ui.tabs.pc_info import PcInfoTabMixin, PcInfoSink
from l5r.ui.tabs.perks import PerksTabMixin, PerksSink
from l5r.ui.tabs.powers import PowersTabMixin, PowersSink
from l5r.ui.tabs.settings_tab import SettingsTabMixin
from l5r.ui.tabs.skills import SkillsTabMixin, SkillsSink
from l5r.ui.tabs.techniques import TechniquesTabMixin, TechniquesSink
from l5r.ui.tabs.weapons import WeaponsTabMixin, WeaponsSink
from l5r.util import log
from l5r.util.settings import L5RCMSettings


class L5RMain(AboutTabMixin, AdvancementsTabMixin, AdvanceMixin, AdviseMixin,
              EquipmentTabMixin, HealthDisplayMixin, MenuMixin,
              ModelRefreshMixin, ModifiersTabMixin, NicebarMixin,
              NotesTabMixin, PcInfoTabMixin, PerksTabMixin, PersistenceMixin,
              PowersTabMixin, SettingsTabMixin, SkillsTabMixin,
              TechniquesTabMixin, WeaponsTabMixin, L5RCMCore):

    default_size = QtCore.QSize(820, 720)
    default_point_size = 8.25
    num_tabs = 11

    def __init__(self, locale=None, parent=None):
        super(L5RMain, self).__init__(locale, parent)

        log.ui.debug(u"Initialize L5RMain window")

        # character file save path
        self.save_path = ''

        # Per-mixin Qt slot containers (sinks). Each mixin contributes its
        # own QObject child rather than sharing a global grab-bag -- gives
        # proper Qt parent-ownership and keeps the per-class slot surface
        # bounded.
        self.persistence_sink = PersistenceSink(self)
        self.advancements_sink = AdvancementsSink(self)
        self.pc_info_sink = PcInfoSink(self)
        self.menu_sink = MenuSink(self)
        self.perks_sink = PerksSink(self)
        self.powers_sink = PowersSink(self)
        self.weapons_sink = WeaponsSink(self)
        self.skills_sink = SkillsSink(self)
        self.techniques_sink = TechniquesSink(self)
        self.modifiers_sink = ModifiersSink(self)
        self.equipment_sink = EquipmentSink(self)

        self.table_views = []

        # Build interface and menus
        self.build_ui()
        self.build_menu()

        # Build page 1
        self.build_ui_page_1()
        self.build_ui_page_2()
        self.build_ui_page_3()
        self.build_ui_page_4()
        self.build_ui_page_5()
        self.build_ui_page_6()
        self.build_ui_page_7()
        self.build_ui_page_8()
        self.build_ui_page_9()
        self.build_ui_page_10()
        self.build_ui_page_settings()
        self.build_ui_page_about()

        self.tabs.setIconSize(QtCore.QSize(24, 24))
        tabs_icons = ['samurai', 'music', 'burn', 'powers', 'userinfo', 'book',
                      'katana', 'disk', 'text', 'bag', 'dragonball']

        tabs_names = [self.tr('Character'),
                      self.tr('Skills'),
                      self.tr('Spells/Techniques'),
                      self.tr('Kata/Kiho'),
                      self.tr('Merits/Flaws'),
                      self.tr('Advancements'),
                      self.tr('Weapons'),
                      self.tr('Modifiers'),
                      self.tr('Notes/Personal Info'),
                      self.tr('Equipment'),
                      self.tr('Settings')]

        for i in range(0, self.num_tabs):
            self.tabs.setTabIcon(i, QtGui.QIcon(get_tab_icon(tabs_icons[i])))
            self.tabs.setTabText(i, '')
            self.tabs.setTabToolTip(i,tabs_names[i])


        # about = app_icon
        self.tabs.setTabIcon(self.num_tabs, QtGui.QIcon(get_app_icon_path()))
        self.tabs.setTabText(self.num_tabs, '')
        self.tabs.setTabToolTip(self.num_tabs,self.tr('About'))

        # donate button
        self.setup_donate_button()

        self.connect_signals()

    def build_ui(self):

        log.ui.debug(u"Build L5RMain UI")

        # Main interface widgets
        # self.view = ZoomableView(self)
        settings = L5RCMSettings()

        self.widgets = QtWidgets.QFrame(self)
        self.widgets.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.widgets.setLineWidth(1)
        self.tabs = QtWidgets.QTabWidget(self)

        self.nicebar = None
        mvbox = QtWidgets.QVBoxLayout(self.widgets)
        logo = QtWidgets.QLabel(self)

        # Set Banner
        logo.setScaledContents(True)
        logo.setPixmap(QtGui.QPixmap(get_app_file('banner_s.png')))
        logo.setObjectName('BANNER')

        if not settings.ui.banner_enabled:
            logo.hide()

        mvbox.addWidget(logo)
        mvbox.addWidget(self.tabs)

        log.ui.debug(u"show banner: %s", u"yes" if settings.ui.banner_enabled else u"no" )

        self.mvbox = mvbox
        self.setCentralWidget(self.widgets)

        # LOAD SETTINGS
        geo = settings.app.geometry

        if geo is not None:
            self.restoreGeometry(geo)
            log.ui.info(u"restore geometry from settings")
        else:
            log.ui.info(u"using default geometry")
            self.reset_geometry()

        self.ic_idx = int(settings.app.insight_calculation) - 1
        ic_calcs = [api.rules.insight_calculation_1,
                    api.rules.insight_calculation_2,
                    api.rules.insight_calculation_3]
        if self.ic_idx not in range(0, len(ic_calcs)):
            self.ic_idx = 0

        log.rules.info(u"insight calculator settings: %d/%d", self.ic_idx+1, len(ic_calcs))

        self.ic_calc_method = ic_calcs[self.ic_idx]

    def reset_geometry(self):
        self.setGeometry(QtCore.QRect(100, 100, 820, 720))

    def _build_generic_page(self, models_):
        mfr = QtWidgets.QFrame(self)
        vbox = QtWidgets.QVBoxLayout(mfr)
        views_ = []

        for k, t, m, d, tb, on_double_click in models_:
            grp = QtWidgets.QGroupBox(k, self)
            hbox = QtWidgets.QHBoxLayout(grp)
            view = None
            if t == 'table':
                view = QtWidgets.QTableView(self)
                view.setSortingEnabled(True)
                view.horizontalHeader().setSectionResizeMode(
                    QtWidgets.QHeaderView.Interactive)
                view.horizontalHeader().setStretchLastSection(True)
                view.horizontalHeader().setCascadingSectionResizes(True)
                if d is not None and len(d) == 2:
                    col_ = d[0]
                    obj_ = d[1]
                self.table_views.append(view)
            elif t == 'list':
                view = QtWidgets.QListView(self)
            if on_double_click:
                view.doubleClicked.connect(on_double_click)
            view.setModel(m)

            if tb is not None:
                hbox.addWidget(tb)
            hbox.addWidget(view)
            vbox.addWidget(grp)
            views_.append(view)
        return mfr, views_

    def init(self):
        """ second step initialization """
        pass

    def connect_signals(self):

        # notify only user edit
        self.tx_mod_init.editingFinished.connect(self.update_from_model)

        # update model name
        self.tx_pc_name.editingFinished.connect(self.on_pc_name_change)

        # personal information
        for widget in self.pers_info_widgets:
            widget.editingFinished.connect(self.on_pers_info_change)
        for widget in self.pc_flags_points:
            widget.valueChanged.connect(self.on_flag_points_change)
        for tx in self.pc_flags_rank:
            tx.editingFinished.connect(self.on_flag_rank_change)

        self.void_points.valueChanged.connect(self.on_void_points_change)

        self.trait_sig_mapper.mappedString.connect(self.on_trait_increase)

        self.ic_act_grp.triggered.connect(self.on_change_insight_calculation)
        self.hm_act_grp.triggered.connect(self.on_change_health_visualization)

        self.bt_edit_family.clicked.connect(self.pc_info_sink.on_edit_family)
        self.bt_edit_school.clicked.connect(self.pc_info_sink.on_edit_first_school)

        self.bt_set_exp_points.clicked.connect(self.pc_info_sink.on_set_exp_limit)
        self.bt_add_exp_points.clicked.connect(self.pc_info_sink.on_add_exp_points)

    def closeEvent(self, ev):
        # update interface last time, to set unsaved states
        self.update_from_model()

        # SAVE GEOMETRY
        settings = L5RCMSettings()
        settings.app.geometry = self.saveGeometry()

        if self.pc.insight_calculation == api.rules.insight_calculation_2:
            settings.app.insight_calculation = 2
        elif self.pc.insight_calculation == api.rules.insight_calculation_3:
            settings.app.insight_calculation = 3
        else:
            settings.app.insight_calculation = 1

        if self.pc.is_dirty():
            resp = self.ask_to_save()
            if resp == QtWidgets.QMessageBox.Save:
                self.persistence_sink.save_character()
            elif resp == QtWidgets.QMessageBox.Cancel:
                ev.ignore()
            else:
                super(L5RMain, self).closeEvent(ev)
        else:
            super(L5RMain, self).closeEvent(ev)

# MAIN ###

OPEN_CMD_SWITCH = '--open'
IMPORT_CMD_SWITCH = '--import'

MIME_L5R_CHAR = "applications/x-l5r-character"
MIME_L5R_PACK = "applications/x-l5r-pack"

UI_MODE_ENV = "L5RCM_UI"


def _resolve_startup_action(argv):
    """Parse argv and return (action, path).

    Action is one of "open", "import", "new". For "new" the path is
    None. Shared by the widget and QML entry points so CLI flags behave
    identically across UI modes.
    """
    if len(argv) <= 1:
        return ("new", None)

    if OPEN_CMD_SWITCH in argv:
        idx = argv.index(OPEN_CMD_SWITCH)
        if idx + 1 < len(argv):
            return ("open", argv[idx + 1])
        return ("new", None)

    if IMPORT_CMD_SWITCH in argv:
        idx = argv.index(IMPORT_CMD_SWITCH)
        if idx + 1 < len(argv):
            return ("import", argv[idx + 1])
        return ("new", None)

    # mime sniff on the first positional
    file_path = argv[1]
    mime = mimetypes.guess_type(file_path)
    if mime[0] == MIME_L5R_CHAR:
        return ("open", file_path)
    if mime[0] == MIME_L5R_PACK:
        return ("import", file_path)
    return ("new", None)


def main():
    try:
        app = QtWidgets.QApplication(sys.argv)

        log.app.info(u"START. Qt Version: %s", QtCore.__version__)

        # setup mimetypes
        mimetypes.add_type(MIME_L5R_CHAR, ".l5r")
        mimetypes.add_type(MIME_L5R_PACK, ".l5rcmpack")

        QtCore.QCoreApplication.setApplicationName(APP_NAME)
        QtCore.QCoreApplication.setApplicationVersion(APP_VERSION)
        QtCore.QCoreApplication.setOrganizationName(APP_ORG)

        log.app.info(u"%s %s %s by %s", APP_NAME, APP_VERSION, APP_DESC, APP_ORG)

        app.setWindowIcon(QtGui.QIcon(get_app_icon_path()))

        # Setup translation
        settings = L5RCMSettings()
        settings.load_defaults()
        settings.sync()

        app_translator = QtCore.QTranslator(app)
        qt_translator = QtCore.QTranslator(app)

        log.app.debug(u"use machine locale: %s, machine locale: %s",
                      "yes" if settings.app.use_system_locale else "no", QtCore.QLocale.system().name())

        if settings.app.use_system_locale:
            app_locale = QtCore.QLocale.system().name()
        else:
            app_locale = settings.app.user_locale

        if '_' in app_locale:
            qt_loc = 'qt_{0}'.format(app_locale[:2])
        else:
            qt_loc = 'qt_{0}'.format(app_locale)

        app_loc_file = get_app_file('i18n/{0}'.format(app_locale))

        log.app.debug(u"current locale: %s, qt locale: %s, app locale file: %s", app_locale, qt_loc, app_loc_file)
        log.app.debug(u"qt translation path: %s", QtCore.QLibraryInfo.location(QtCore.QLibraryInfo.TranslationsPath))

        qt_translator .load(
            qt_loc, QtCore.QLibraryInfo.location(QtCore.QLibraryInfo.TranslationsPath))
        app.installTranslator(qt_translator)
        app_translator.load(app_loc_file)
        app.installTranslator(app_translator)

        # application font
        log.app.debug(f"settings.ui.use_system_font: {settings.ui.use_system_font}")
        
        if not settings.ui.use_system_font:
            try:                                
                font_family, font_size = settings.ui.user_font.split(",")
                log.app.debug(f"applying user font: {font_family} {font_size}")
                app_font = QtGui.QFont(font_family, float(font_size))
                QtWidgets.QApplication.setFont(app_font)
                log.app.info(f"applyed user font: {font_family} {font_size}")
            except:
                log.app.error(f"Could not apply user font: {settings.ui.user_font}", exc_info=1)

        startup_action = _resolve_startup_action(sys.argv)
        log.app.debug(u"startup action: %s", startup_action)

        # Choose the front-end. The L5RCM_UI env var is a dev override:
        # when set it wins (and unknown values fall back to widgets with a
        # warning). When it is unset, the persisted `ui/use_qml_ui`
        # preference decides -- the new QML UI is the default, the legacy
        # QWidget UI is the opt-out (toggled from either Settings panel).
        env_mode = os.environ.get(UI_MODE_ENV)
        if env_mode is not None:
            ui_mode = env_mode.strip().lower()
            if ui_mode not in ("widgets", "qml"):
                log.app.warning(u"Unknown %s=%r, falling back to widgets",
                                UI_MODE_ENV, ui_mode)
                ui_mode = "widgets"
        else:
            ui_mode = "qml" if settings.ui.use_qml_ui else "widgets"

        if ui_mode == "qml":
            from l5r.qmlui import run_qml_app
            return run_qml_app(app, app_locale, startup_action)

        # start main form
        l5rcm = L5RMain(app_locale)
        l5rcm.setWindowTitle(APP_DESC + ' v' + APP_VERSION)
        l5rcm.init()

        # initialize new character
        l5rcm.create_new_character()

        action, path = startup_action
        if action == "open" and path:
            log.app.debug(u"open character from command line")
            l5rcm.load_character_from(path)
        elif action == "import" and path:
            log.app.debug(u"import datapack from command line: %s", path)
            app.quit()
            return l5rcm.import_data_pack(path)

        l5rcm.show()

        # alert if not datapacks are installed
        l5rcm.check_datapacks()

        return app.exec_()
    except Exception as e:
        log.app.exception(e)
    finally:
        log.app.info("KTHXBYE")

if __name__ == '__main__':
    sys.exit(main())
