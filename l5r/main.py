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


#import sip
#sip.setapi('QDate', 2)
#sip.setapi('QDateTime', 2)
#sip.setapi('QString', 2)
#sip.setapi('QTextStream', 2)
#sip.setapi('QTime', 2)
#sip.setapi('QUrl', 2)
#sip.setapi('QVariant', 2)

import mimetypes
import os
import sys

from qtpy import QtCore, QtGui, QtWidgets

import l5r.sinks
import l5r.api.character
import l5r.api.character.spells
import l5r.api.data.clans
import l5r.api.data.families
import l5r.api.data.schools
import l5r.api.character
import l5r.api.character.spells
import l5r.api.character.skills
import l5r.api.rules

import l5r.widgets as widgets
import l5r.dialogs as dialogs

from l5r.l5rcmcore import *
from l5r.ui.advance import AdvanceMixin
from l5r.ui.advise import AdviseMixin
from l5r.ui.health import HealthDisplayMixin
from l5r.ui.helpers import (
    new_horiz_line,
    new_item_groupbox,
    new_small_le,
    new_small_plus_bt,
    new_vert_line,
)
from l5r.ui.menu import MenuMixin
from l5r.ui.nicebar import NicebarMixin
from l5r.ui.persistence import PersistenceMixin
from l5r.ui.tabs.about import AboutTabMixin
from l5r.ui.tabs.advancements import AdvancementsTabMixin
from l5r.ui.tabs.pc_info import PcInfoTabMixin
from l5r.ui.tabs.settings_tab import SettingsTabMixin
from l5r.util import log
from l5r.util.settings import L5RCMSettings


class L5RMain(AboutTabMixin, AdvancementsTabMixin, AdvanceMixin, AdviseMixin,
              HealthDisplayMixin, MenuMixin, NicebarMixin, PcInfoTabMixin,
              PersistenceMixin, SettingsTabMixin, L5RCMCore):

    default_size = QtCore.QSize(820, 720)
    default_point_size = 8.25
    num_tabs = 11

    def __init__(self, locale=None, parent=None):
        super(L5RMain, self).__init__(locale, parent)

        log.ui.debug(u"Initialize L5RMain window")

        # character file save path
        self.save_path = ''

        # slot sinks
        self.sink1 = l5r.sinks.Sink1(self)  # Menu Sink
        self.sink2 = l5r.sinks.Sink2(self)  # MeritFlaw Sink
        self.sink3 = l5r.sinks.Sink3(self)  # Weapons Sink
        self.sink4 = l5r.sinks.Sink4(self)  # Weapons Sink

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
        for i in range(0, self.num_tabs):
            self.tabs.setTabIcon(i, QtGui.QIcon(get_tab_icon(tabs_icons[i])))
            self.tabs.setTabText(i, '')

        # about = app_icon
        self.tabs.setTabIcon(self.num_tabs, QtGui.QIcon(get_app_icon_path()))
        self.tabs.setTabText(self.num_tabs, '')

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

    def reset_layout_geometry(self):
        self.mvbox.setGeometry(QtCore.QRect(1, 1, 727, 573))

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

    def _build_spell_frame(self, model, layout):
        grp = QtWidgets.QGroupBox(self.tr("Spells"), self)
        hbox = QtWidgets.QHBoxLayout(grp)

        fr_ = QtWidgets.QFrame(self)
        vbox = QtWidgets.QVBoxLayout(fr_)
        vbox.setContentsMargins(3, 3, 3, 3)

        # advantages/disadvantage vertical toolbar
        def _make_vertical_tb():
            vtb = widgets.VerticalToolBar(self)
            vtb.addStretch()

            cb_buy = self.act_buy_spell
            cb_remove = self.act_del_spell
            cb_memo = self.act_memo_spell

            self.add_spell_bt = vtb.addButton(
                QtGui.QIcon(get_icon_path('buy', (16, 16))),
                self.tr("Add new spell"), cb_buy)

            self.del_spell_bt = vtb.addButton(
                QtGui.QIcon(get_icon_path('minus', (16, 16))),
                self.tr("Remove spell"), cb_remove)

            self.memo_spell_bt = vtb.addButton(
                QtGui.QIcon(get_icon_path('book', (16, 16))),
                self.tr("Memorize/Forget spell"), cb_memo)

            self.del_spell_bt.setEnabled(False)

            vtb.addStretch()
            return vtb

        # View
        view = QtWidgets.QTableView(fr_)
        view.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                           QtWidgets.QSizePolicy.Expanding)
        view.setSortingEnabled(True)
        view.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Interactive)
        view.horizontalHeader().setStretchLastSection(True)
        view.horizontalHeader().setCascadingSectionResizes(True)
        view.setModel(model)
        self.table_views.append(view)
        sm = view.selectionModel()
        sm.currentRowChanged.connect(self.on_spell_selected)
        self.spell_table_view = view

        # Affinity/Deficiency
        self.lb_affin = QtWidgets.QLabel(self.tr("None"), self)
        self.lb_defic = QtWidgets.QLabel(self.tr("None"), self)

        aff_fr = QtWidgets.QFrame(self)
        aff_fr.setSizePolicy(QtWidgets.QSizePolicy.Preferred,
                             QtWidgets.QSizePolicy.Maximum)
        fl = QtWidgets.QFormLayout(aff_fr)
        fl.addRow(self.tr("<b><i>Affinity</i></b>"), self.lb_affin)
        fl.addRow(self.tr("<b><i>Deficiency</i></b>"), self.lb_defic)
        fl.setHorizontalSpacing(60)
        fl.setVerticalSpacing(5)
        fl.setContentsMargins(0, 0, 0, 0)

        vbox.addWidget(aff_fr)
        vbox.addWidget(view)

        hbox.addWidget(_make_vertical_tb())
        hbox.addWidget(fr_)
        layout.addWidget(grp)

        view.doubleClicked.connect(self.sink4.on_spell_item_activate)

        return view

    def _build_tech_frame(self, model, layout):
        grp = QtWidgets.QGroupBox(self.tr("Techs"), self)
        vbox = QtWidgets.QVBoxLayout(grp)

        # View
        view = QtWidgets.QTableView(self)
        view.setSortingEnabled(False)
        view.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.Interactive)
        view.horizontalHeader().setStretchLastSection(True)
        view.horizontalHeader().setCascadingSectionResizes(True)

        view.setModel(model)
        self.table_views.append(view)
        vbox.addWidget(view)
        layout.addWidget(grp)

        view.doubleClicked.connect(self.sink4.on_tech_item_activate)

        return view

    def _build_kata_frame(self, model, layout):
        grp = QtWidgets.QGroupBox(self.tr("Kata"), self)
        hbox = QtWidgets.QHBoxLayout(grp)

        fr_ = QtWidgets.QFrame(self)
        vbox = QtWidgets.QVBoxLayout(fr_)
        vbox.setContentsMargins(3, 3, 3, 3)

        # advantages/disadvantage vertical toolbar
        def _make_vertical_tb():
            vtb = widgets.VerticalToolBar(self)
            vtb.addStretch()

            cb_buy = self.sink2.act_buy_kata
            cb_remove = self.sink2.act_del_kata

            self.add_kata_bt = vtb.addButton(
                QtGui.QIcon(get_icon_path('buy', (16, 16))),
                self.tr("Add new Kata"), cb_buy)

            self.del_kata_bt = vtb.addButton(
                QtGui.QIcon(get_icon_path('minus', (16, 16))),
                self.tr("Remove Kata"), cb_remove)

            self.add_kata_bt.setEnabled(True)
            self.del_kata_bt.setEnabled(True)

            vtb.addStretch()
            return vtb

        # View
        view = QtWidgets.QTableView(self)
        view.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                           QtWidgets.QSizePolicy.Expanding)
        view.setSortingEnabled(True)
        view.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Interactive)
        view.horizontalHeader().setStretchLastSection(True)
        view.horizontalHeader().setCascadingSectionResizes(True)
        view.setModel(model)
        view.doubleClicked.connect(self.sink4.on_kata_item_activate)
        self.ka_table_view = view
        self.table_views.append(view)

        vbox.addWidget(view)

        hbox.addWidget(_make_vertical_tb())
        hbox.addWidget(fr_)

        layout.addWidget(grp)

        return view

    def _build_kiho_frame(self, model, layout):
        grp = QtWidgets.QGroupBox(self.tr("Kiho"), self)
        hbox = QtWidgets.QHBoxLayout(grp)

        fr_ = QtWidgets.QFrame(self)
        vbox = QtWidgets.QVBoxLayout(fr_)
        vbox.setContentsMargins(3, 3, 3, 3)

        # advantages/disadvantage vertical toolbar
        def _make_vertical_tb():
            vtb = widgets.VerticalToolBar(self)
            vtb.addStretch()

            cb_buy = self.sink2.act_buy_kiho
            cb_remove = self.sink2.act_del_kiho
            cb_buy_tattoo = self.sink2.act_buy_tattoo

            self.add_kiho_bt = vtb.addButton(
                QtGui.QIcon(get_icon_path('buy', (16, 16))),
                self.tr("Add new Kiho"), cb_buy)

            self.add_tattoo_bt = vtb.addButton(
                QtGui.QIcon(get_icon_path('buy', (16, 16))),
                self.tr("Add new Tattoo"), cb_buy_tattoo)

            self.del_kiho_bt = vtb.addButton(
                QtGui.QIcon(get_icon_path('minus', (16, 16))),
                self.tr("Remove Kiho"), cb_remove)

            self.add_kiho_bt.setEnabled(True)
            self.del_kiho_bt.setEnabled(True)

            vtb.addStretch()
            return vtb

        # View
        view = QtWidgets.QTableView(self)
        view.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                           QtWidgets.QSizePolicy.Expanding)
        view.setSortingEnabled(True)
        view.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Interactive)
        view.horizontalHeader().setStretchLastSection(True)
        view.horizontalHeader().setCascadingSectionResizes(True)
        view.setModel(model)
        view.doubleClicked.connect(self.sink4.on_kiho_item_activate)
        self.ki_table_view = view
        self.table_views.append(view)

        vbox.addWidget(view)

        hbox.addWidget(_make_vertical_tb())
        hbox.addWidget(fr_)

        layout.addWidget(grp)

        return view

    def build_ui_page_2(self):
        self.sk_view_model = models.SkillTableViewModel(self)
        self.ma_view_model = models.MaViewModel(self)

        # enable sorting through a proxy model
        self.sk_sort_model = models.ColorFriendlySortProxyModel(self)
        self.sk_sort_model.setDynamicSortFilter(True)
        self.sk_sort_model.setSourceModel(self.sk_view_model)

        # enable sorting through a proxy model
        self.ma_sort_model = models.ColorFriendlySortProxyModel(self)
        self.ma_sort_model.setDynamicSortFilter(True)
        self.ma_sort_model.setSourceModel(self.ma_view_model)

        # skills vertical toolbar
        vtb = widgets.VerticalToolBar(self)
        vtb.addStretch()
        vtb.addButton(QtGui.QIcon(get_icon_path('add', (16, 16))),
                      self.tr("Add skill rank"), self.on_buy_skill_rank)
        vtb.addButton(QtGui.QIcon(get_icon_path('buy', (16, 16))),
                      self.tr("Buy skill emphasys"), self.show_buy_emph_dlg)
        vtb.addButton(QtGui.QIcon(get_icon_path('buy', (16, 16))),
                      self.tr("Buy another skill"), self.show_buy_skill_dlg)
        vtb.addStretch()

        models_ = [
            (
                "Skills",
                'table',
                self.sk_sort_model,
                None,
                vtb,
                self.sink4.on_skill_item_activate
            ),
            (
                self.tr("Mastery Abilities"),
                'table',
                self.ma_sort_model,
                None,
                None,
                None
            )
        ]
        frame_, views_ = self._build_generic_page(models_)

        if len(views_) > 0:
            self.skill_table_view = views_[0]

        self.tabs.addTab(frame_, self.tr("Skills"))

    def build_ui_page_3(self):
        self.sp_view_model = models.SpellTableViewModel(self)
        self.th_view_model = models.TechViewModel(self)

        # enable sorting through a proxy model
        self.sp_sort_model = models.ColorFriendlySortProxyModel(self)
        self.sp_sort_model.setDynamicSortFilter(True)
        self.sp_sort_model.setSourceModel(self.sp_view_model)

        frame_ = QtWidgets.QFrame(self)
        vbox = QtWidgets.QVBoxLayout(frame_)

        self._build_spell_frame(self.sp_sort_model, vbox)
        self._build_tech_frame(self.th_view_model, vbox)

        self.tabs.addTab(frame_, self.tr("Techniques"))

    def build_ui_page_4(self):
        self.ka_view_model = models.KataTableViewModel(self)
        self.ki_view_model = models.KihoTableViewModel(self)

        # enable sorting through a proxy model
        self.ka_sort_model = models.ColorFriendlySortProxyModel(self)
        self.ka_sort_model.setDynamicSortFilter(True)
        self.ka_sort_model.setSourceModel(self.ka_view_model)

        self.ki_sort_model = models.ColorFriendlySortProxyModel(self)
        self.ki_sort_model.setDynamicSortFilter(True)
        self.ki_sort_model.setSourceModel(self.ki_view_model)

        frame_ = QtWidgets.QFrame(self)
        vbox = QtWidgets.QVBoxLayout(frame_)

        self.kata_view = self._build_kata_frame(self.ka_sort_model, vbox)
        self.kiho_view = self._build_kiho_frame(self.ki_sort_model, vbox)

        self.tabs.addTab(frame_, self.tr("Powers"))

    def build_ui_page_5(self):
        mfr = QtWidgets.QFrame(self)
        vbox = QtWidgets.QVBoxLayout(mfr)

        # advantages/disadvantage vertical toolbar
        def _make_vertical_tb(tag, has_edit, has_remove):
            vtb = widgets.VerticalToolBar(self)
            vtb.addStretch()

            cb_buy = (self.sink2.act_buy_merit if tag == 'merit'
                      else self.sink2.act_buy_flaw)
            cb_edit = (self.sink2.act_edit_merit if tag == 'merit'
                       else self.sink2.act_edit_flaw)
            cb_remove = (self.sink2.act_del_merit if tag == 'merit'
                         else self.sink2.act_del_flaw)

            vtb.addButton(QtGui.QIcon(get_icon_path('buy', (16, 16))),
                          self.tr("Add Perk"), cb_buy)

            if has_edit:
                vtb.addButton(QtGui.QIcon(get_icon_path('edit', (16, 16))),
                              self.tr("Edit Perk"), cb_edit)

            if has_remove:
                vtb.addButton(QtGui.QIcon(get_icon_path('minus', (16, 16))),
                              self.tr("Remove Perk"), cb_remove)

            vtb.addStretch()
            return vtb

        self.merits_view_model = models.PerkViewModel('merit')
        self.flaws_view_model = models.PerkViewModel('flaws')

        self.merits_sort_model = models.ColorFriendlySortProxyModel(self)
        self.merits_sort_model.setDynamicSortFilter(True)
        self.merits_sort_model.setSourceModel(self.merits_view_model)

        self.flaws_sort_model = models.ColorFriendlySortProxyModel(self)
        self.flaws_sort_model.setDynamicSortFilter(True)
        self.flaws_sort_model.setSourceModel(self.flaws_view_model)

        merit_view = QtWidgets.QTableView(self)
        merit_view.setSortingEnabled(True)
        merit_view.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.Interactive)
        merit_view.horizontalHeader().setStretchLastSection(True)
        merit_view.horizontalHeader().setCascadingSectionResizes(True)
        merit_view.doubleClicked.connect(self.sink2.act_view_merit)
        merit_view.setModel(self.merits_sort_model)
        merit_vtb = _make_vertical_tb('merit', True, True)
        fr_ = QtWidgets.QFrame(self)
        hb_ = QtWidgets.QHBoxLayout(fr_)
        hb_.setContentsMargins(3, 3, 3, 3)
        hb_.addWidget(merit_vtb)
        hb_.addWidget(merit_view)
        vbox.addWidget(new_item_groupbox(self.tr("Advantages"), fr_))

        flaw_view = QtWidgets.QTableView(self)
        flaw_view.setSortingEnabled(True)
        flaw_view.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.Interactive)
        flaw_view.horizontalHeader().setStretchLastSection(True)
        flaw_view.horizontalHeader().setCascadingSectionResizes(True)
        flaw_view.doubleClicked.connect(self.sink2.act_view_flaw)
        flaw_view.setModel(self.flaws_sort_model)
        flaw_vtb = _make_vertical_tb('flaw', True, True)
        fr_ = QtWidgets.QFrame(self)
        hb_ = QtWidgets.QHBoxLayout(fr_)
        hb_.setContentsMargins(3, 3, 3, 3)
        hb_.addWidget(flaw_vtb)
        hb_.addWidget(flaw_view)
        vbox.addWidget(new_item_groupbox(self.tr("Disadvantages"), fr_))

        self.merit_view = merit_view
        self.flaw_view = flaw_view
        self.table_views.append(self.merit_view)
        self.table_views.append(self.flaw_view)

        self.tabs.addTab(mfr, self.tr("Perks"))

    def build_ui_page_7(self):
        self.melee_view_model = models.WeaponTableViewModel('melee', self)
        self.ranged_view_model = models.WeaponTableViewModel('ranged', self)
        self.arrow_view_model = models.WeaponTableViewModel('arrow', self)

        def _make_sortable(model):
            # enable sorting through a proxy model
            sort_model_ = models.ColorFriendlySortProxyModel(self)
            sort_model_.setDynamicSortFilter(True)
            sort_model_.setSourceModel(model)
            return sort_model_

        # weapon vertical toolbar
        def _make_vertical_tb(has_custom, has_edit, has_qty, filt):
            vtb = widgets.VerticalToolBar(self)
            vtb.setProperty('filter', filt)
            vtb.addStretch()
            vtb.addButton(QtGui.QIcon(get_icon_path('buy', (16, 16))),
                          self.tr("Add weapon"), self.sink3.show_add_weapon)
            if has_custom:
                vtb.addButton(QtGui.QIcon(get_icon_path('custom', (16, 16))),
                              self.tr("Add custom weapon"), self.sink3.show_add_cust_weapon)
            if has_edit:
                vtb.addButton(QtGui.QIcon(get_icon_path('edit', (16, 16))),
                              self.tr("Edit weapon"), self.sink3.edit_selected_weapon)
            vtb.addButton(QtGui.QIcon(get_icon_path('minus', (16, 16))),
                          self.tr("Remove weapon"), self.sink3.remove_selected_weapon)
            if has_qty:
                vtb.addButton(QtGui.QIcon(get_icon_path('add', (16, 16))),
                              self.tr("Increase Quantity"), self.sink3.on_increase_item_qty)
                vtb.addButton(QtGui.QIcon(get_icon_path('minus', (16, 16))),
                              self.tr("Decrease Quantity"), self.sink3.on_decrease_item_qty)

            vtb.addStretch()
            return vtb

        melee_vtb = _make_vertical_tb(True, True, False, 'melee')
        ranged_vtb = _make_vertical_tb(True, True, False, 'ranged')
        arrow_vtb = _make_vertical_tb(False, False, True, 'arrow')

        models_ = [
            (self.tr("Melee Weapons"), 'table', _make_sortable(self.melee_view_model), None, melee_vtb, None),
            (self.tr("Ranged Weapons"), 'table', _make_sortable(self.ranged_view_model), None, ranged_vtb, None),
            (self.tr("Arrows"), 'table', _make_sortable(self.arrow_view_model), None, arrow_vtb, None)
        ]

        frame_, views_ = self._build_generic_page(models_)

        melee_vtb .setProperty('source', views_[0])
        ranged_vtb.setProperty('source', views_[1])
        arrow_vtb .setProperty('source', views_[2])

        self.tabs.addTab(frame_, self.tr("Weapons"))

    def build_ui_page_8(self):
        # modifiers
        self.mods_view_model = models.ModifiersTableViewModel(self)
        self.mods_view_model.user_change.connect(self.update_from_model)

        def _make_sortable(model):
            # enable sorting through a proxy model
            sort_model_ = models.ColorFriendlySortProxyModel(self)
            sort_model_.setDynamicSortFilter(True)
            sort_model_.setSourceModel(model)
            return sort_model_

        # weapon vertical toolbar
        def _make_vertical_tb():
            vtb = widgets.VerticalToolBar(self)
            vtb.addStretch()
            vtb.addButton(QtGui.QIcon(get_icon_path('buy', (16, 16))),
                          self.tr("Add modifier"), self.sink4.add_new_modifier)
            vtb.addButton(QtGui.QIcon(get_icon_path('edit', (16, 16))),
                          self.tr("Edit modifier"), self.sink4.edit_selected_modifier)
            vtb.addButton(QtGui.QIcon(get_icon_path('minus', (16, 16))),
                          self.tr("Remove modifier"), self.sink4.remove_selected_modifier)

            vtb.addStretch()
            return vtb

        vtb = _make_vertical_tb()

        models_ = [
            (self.tr("Modifiers"), 'table', _make_sortable(self.mods_view_model), None, vtb, None)
        ]

        frame_, views_ = self._build_generic_page(models_)
        self.mod_view = views_[0]

        vtb .setProperty('source', self.mod_view)
        self.tabs.addTab(frame_, self.tr("Modifiers"))

    def build_ui_page_9(self):
        mfr = QtWidgets.QFrame(self)
        vbox = QtWidgets.QVBoxLayout(mfr)

        self.tx_pc_notes = widgets.SimpleRichEditor(self)
        vbox.addWidget(self.tx_pc_notes)

        def build_pers_info():
            grp = QtWidgets.QGroupBox(self.tr("Personal Informations"), self)
            grp.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                              QtWidgets.QSizePolicy.Preferred)

            hgrp = QtWidgets.QHBoxLayout(grp)

            # anagraphic

            afr = QtWidgets.QFrame(self)
            afl = QtWidgets.QFormLayout(afr)

            self.tx_pc_sex = QtWidgets.QLineEdit(self)
            self.tx_pc_age = QtWidgets.QLineEdit(self)
            self.tx_pc_height = QtWidgets.QLineEdit(self)
            self.tx_pc_weight = QtWidgets.QLineEdit(self)
            self.tx_pc_hair = QtWidgets.QLineEdit(self)
            self.tx_pc_eyes = QtWidgets.QLineEdit(self)

            afl.addRow(self.tr("Sex"), self.tx_pc_sex)
            afl.addRow(self.tr("Age"), self.tx_pc_age)
            afl.addRow(self.tr("Height"), self.tx_pc_height)
            afl.addRow(self.tr("Weight"), self.tx_pc_weight)
            afl.addRow(self.tr("Hair"), self.tx_pc_hair)
            afl.addRow(self.tr("Eyes"), self.tx_pc_eyes)
            hgrp.addWidget(afr)

            # separator
            hgrp.addWidget(new_vert_line())

            # parents
            bfr = QtWidgets.QFrame(self)
            bfl = QtWidgets.QFormLayout(bfr)

            self.tx_pc_father = QtWidgets.QLineEdit(self)
            self.tx_pc_mother = QtWidgets.QLineEdit(self)
            self.tx_pc_bro = QtWidgets.QLineEdit(self)
            self.tx_pc_sis = QtWidgets.QLineEdit(self)
            self.tx_pc_marsta = QtWidgets.QLineEdit(self)
            self.tx_pc_spouse = QtWidgets.QLineEdit(self)
            self.tx_pc_childr = QtWidgets.QLineEdit(self)

            bfl.addRow(self.tr("Father"), self.tx_pc_father)
            bfl.addRow(self.tr("Mother"), self.tx_pc_mother)
            bfl.addRow(self.tr("Brothers"), self.tx_pc_bro)
            bfl.addRow(self.tr("Sisters"), self.tx_pc_sis)
            bfl.addRow(self.tr("Marital Status"), self.tx_pc_marsta)
            bfl.addRow(self.tr("Spouse"), self.tx_pc_spouse)
            bfl.addRow(self.tr("Children"), self.tx_pc_childr)
            hgrp.addWidget(bfr)

            self.pers_info_widgets = [
                self.tx_pc_sex, self.tx_pc_age,
                self.tx_pc_height, self.tx_pc_weight,
                self.tx_pc_hair, self.tx_pc_eyes,
                self.tx_pc_father, self.tx_pc_mother,
                self.tx_pc_bro, self.tx_pc_marsta,
                self.tx_pc_sis, self.tx_pc_spouse, self.tx_pc_childr]

            # link personal information widgets
            self.tx_pc_sex.link = 'sex'
            self.tx_pc_age.link = 'age'
            self.tx_pc_height.link = 'height'
            self.tx_pc_weight.link = 'weight'
            self.tx_pc_hair.link = 'hair'
            self.tx_pc_eyes.link = 'eyes'
            self.tx_pc_father.link = 'father'
            self.tx_pc_mother.link = 'mother'
            self.tx_pc_bro.link = 'brothers'
            self.tx_pc_sis.link = 'sisters'
            self.tx_pc_marsta.link = 'marsta'
            self.tx_pc_spouse.link = 'spouse'
            self.tx_pc_childr.link = 'childr'

            return grp

        vbox.addWidget(build_pers_info())

        self.tabs.addTab(mfr, self.tr("Notes"))

    def build_ui_page_10(self):
        self.equip_view_model = models.EquipmentListModel(self)
        # self.equip_view_model.user_change.connect(self.update_from_model)

        def _make_sortable(model):
            # enable sorting through a proxy model
            sort_model_ = models.ColorFriendlySortProxyModel(self)
            sort_model_.setDynamicSortFilter(True)
            sort_model_.setSourceModel(model)
            return sort_model_

        # weapon vertical toolbar
        def _make_vertical_tb():
            vtb = widgets.VerticalToolBar(self)
            vtb.addStretch()
            vtb.addButton(QtGui.QIcon(get_icon_path('buy', (16, 16))),
                          self.tr("Add equipment"), self.sink4.add_equipment)
            vtb.addButton(QtGui.QIcon(get_icon_path('minus', (16, 16))),
                          self.tr("Remove equipment"), self.sink4.remove_selected_equipment)

            vtb.addStretch()
            return vtb

        vtb = _make_vertical_tb()

        models_ = [
            (self.tr("Equipment"), 'list', _make_sortable(self.equip_view_model), None, vtb, None)
        ]

        frame_, views_ = self._build_generic_page(models_)
        self.equip_view = views_[0]

        font = self.equip_view.font()
        font.setPointSize(11)
        self.equip_view.setFont(font)

        self.money_widget = widgets.MoneyWidget(self)
        frame_.layout().setSpacing(12)
        frame_.layout().addWidget(new_horiz_line(self))
        frame_.layout().addWidget(self.money_widget)
        self.money_widget.valueChanged.connect(
            self.sink4.on_money_value_changed)

        vtb .setProperty('source', self.equip_view)
        self.tabs.addTab(frame_, self.tr("Equipment"))

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

        self.bt_edit_family.clicked.connect(self.sink4.on_edit_family)
        self.bt_edit_school.clicked.connect(self.sink4.on_edit_first_school)

        self.bt_set_exp_points.clicked.connect(self.sink1.on_set_exp_limit)

    def do_buy_kata(self, kata):
        """attempt to buy a new kata"""
        if self.buy_kata(kata) == CMErrors.NOT_ENOUGH_XP:
            self.not_enough_xp_advise(self)

    def do_buy_kiho(self, kiho):
        """attempt to buy a new kiho"""
        if self.buy_kiho(kiho) == CMErrors.NOT_ENOUGH_XP:
            self.not_enough_xp_advise(self)

    def on_buy_skill_rank(self):
        # get selected skill
        sm_ = self.skill_table_view.selectionModel()
        if sm_.hasSelection():
            model_ = self.skill_table_view.model()
            skill_id = model_.data(sm_.currentIndex(), QtCore.Qt.UserRole)

            err_ = self.buy_next_skill_rank(skill_id)
            if err_ != CMErrors.NO_ERROR:
                if err_ == CMErrors.NOT_ENOUGH_XP:
                    self.not_enough_xp_advise(self)
                return

            idx = None
            for i in range(0, self.skill_table_view.model().rowCount()):
                idx = self.skill_table_view.model().index(i, 0)
                if model_.data(idx, QtCore.Qt.UserRole) == skill_id:
                    break
            if idx.isValid():
                sm_.setCurrentIndex(idx, (QtCore.QItemSelectionModel.Select |
                                          QtCore.QItemSelectionModel.Rows))

    def act_memo_spell(self):
        # get selected spell
        sm_ = self.spell_table_view.selectionModel()
        if sm_.hasSelection():
            model_ = self.spell_table_view.model()
            spell_itm = model_.data(sm_.currentIndex(), QtCore.Qt.UserRole)

            err_ = CMErrors.NO_ERROR
            if spell_itm.memo:
                self.remove_advancement_item(spell_itm.adv)
            else:
                err_ = self.memo_spell(spell_itm.spell_id)

            if err_ != CMErrors.NO_ERROR:
                if err_ == CMErrors.NOT_ENOUGH_XP:
                    self.not_enough_xp_advise(self)
                return

            idx = None
            for i in range(0, self.spell_table_view.model().rowCount()):
                idx = self.spell_table_view.model().index(i, 0)
                if model_.data(idx, QtCore.Qt.UserRole).spell_id == spell_itm.spell_id:
                    break
            if idx.isValid():
                sm_.setCurrentIndex(idx, (QtCore.QItemSelectionModel.Select |
                                          QtCore.QItemSelectionModel.Rows))

    def act_buy_spell(self):
        dlg = dialogs.SpellAdvDialog(self.pc, 'freeform', self)
        dlg.setWindowTitle(self.tr('Add New Spell'))
        dlg.set_header_text(
            self.tr("<center><h2>Select the spell to learn</h2></center>"))
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            self.update_from_model()

    def act_del_spell(self):
        # get selected spell
        sm_ = self.spell_table_view.selectionModel()
        if sm_.hasSelection():
            model_ = self.spell_table_view.model()
            spell_itm = model_.data(sm_.currentIndex(), QtCore.Qt.UserRole)

            if spell_itm.memo:
                return
            self.remove_spell(spell_itm.spell_id)

    def on_spell_selected(self, current, previous):
        # get selected spell
        model_ = self.spell_table_view.model()
        spell_itm = model_.data(current, QtCore.Qt.UserRole)

        # toggle remove
        self.del_spell_bt.setEnabled(not spell_itm.memo)

    def update_from_model(self):

        with QtSignalLock(self.pers_info_widgets+[self.tx_pc_name]):

            self.tx_pc_name.setText(self.pc.name)
            self.set_clan(self.pc.clan)
            self.set_family(api.character.get_family())
            self.set_school(api.character.schools.get_current())

            for w in self.pers_info_widgets:
                if hasattr(w, 'link'):
                    w.setText(self.pc.get_property(w.link))

        pc_xp = api.character.xp()
        self.tx_pc_exp.setText('{0} / {1}'.format(pc_xp, api.character.xp_limit()))

        # rings
        for i, r in enumerate(api.data.rings()):
            self.rings[i][1].setText(str(api.character.ring_rank(r)))

        # traits
        for i, t in enumerate(api.data.traits()):
            self.attribs[i][1].setText(str(api.character.trait_rank(t)))

        # pc rank
        self.tx_pc_rank.setText(str(api.character.insight_rank()))
        self.tx_pc_ins .setText(str(api.character.insight()))

        # pc flags
        with QtSignalLock(self.pc_flags_points+self.pc_flags_rank+[self.void_points]):

            self.set_honor(api.character.honor())
            self.set_glory(api.character.glory())
            self.set_infamy(api.character.infamy())
            self.set_status(api.character.status())
            self.set_taint(api.character.taint())

            self.set_void_points(self.pc.void_points)

        # armor
        self.tx_armor_nm .setText(str(api.character.get_armor_name()))
        self.tx_base_tn  .setText(str(api.character.get_base_tn()))
        self.tx_armor_tn .setText(str(api.character.get_armor_tn()))
        self.tx_armor_rd .setText(str(api.character.get_full_rd()))
        self.tx_cur_tn   .setText(str(api.character.get_full_tn()))
        # armor description
        self.tx_armor_nm.setToolTip(str(api.character.get_armor_desc()))

        self.display_health()
        self.update_wound_penalties()
        self.wnd_lb.setTitle(
            self.tr("Health / Wounds (x%d)") % self.pc.health_multiplier)

        # initiative
        self.tx_base_init.setText(
            api.rules.format_rtk_t(api.rules.get_base_initiative()))
        self.tx_mod_init.setText(
            api.rules.format_rtk_t(api.rules.get_init_modifiers()))
        self.tx_cur_init.setText(
            api.rules.format_rtk_t(api.rules.get_tot_initiative()))

        # affinity / deficiency
        affinities_ = []
        for a in api.character.spells.affinities():
            ring_ = api.data.get_ring(a)
            if not ring_:
                affinities_.append(a)
            else:
                affinities_.append(ring_.text)

        deficiencies_ = []
        for a in api.character.spells.deficiencies():
            ring_ = api.data.get_ring(a)
            if not ring_:
                deficiencies_.append(a)
            else:
                deficiencies_.append(ring_.text)

        self.lb_affin.setText(u', '.join(affinities_))
        self.lb_defic.setText(u', '.join(deficiencies_))

        # money
        with QtSignalLock([self.money_widget]):
            self.money_widget.set_value(api.character.get_money())

        self.hide_nicebar()

        self.check_new_skills()
        self.check_affinity_wc()
        self.check_rank_advancement()
        self.check_school_new_spells()
        self.check_free_kihos()

        # disable step 0-1-2 if any xp are spent
        has_adv = len(self.pc.advans) > 0
        self.bt_edit_family.setEnabled(not has_adv)
        self.bt_edit_school.setEnabled(not has_adv)

        # Update view-models
        self.sk_view_model    .update_from_model(self.pc)
        self.ma_view_model    .update_from_model(self.pc)
        self.adv_view_model   .update_from_model(self.pc)
        self.th_view_model    .update_from_model(self.pc)
        self.merits_view_model.update_from_model(self.pc)
        self.flaws_view_model .update_from_model(self.pc)
        self.sp_view_model    .update_from_model(self.pc)
        self.melee_view_model .update_from_model(self.pc)
        self.ranged_view_model.update_from_model(self.pc)
        self.arrow_view_model .update_from_model(self.pc)
        self.mods_view_model  .update_from_model(self.pc)
        self.ka_view_model    .update_from_model(self.pc)
        self.ki_view_model    .update_from_model(self.pc)
        self.equip_view_model .update_from_model(self.pc)

        # update table views to fit new contents
        for v in self.table_views:
            v.setVisible(False)
            v.resizeColumnsToContents()
            v.setVisible(True)

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
                self.sink1.save_character()
            elif resp == QtWidgets.QMessageBox.Cancel:
                ev.ignore()
            else:
                super(L5RMain, self).closeEvent(ev)
        else:
            super(L5RMain, self).closeEvent(ev)

# MAIN ###


#def dump_slots(obj, out_file):
#    with open(out_file, 'wt') as fobj:
#        mobj = obj.metaObject()
#        for i in range(mobj.methodOffset(), mobj.methodCount()):
#            if mobj.method(i).methodType() == QtCore.QMetaMethod.Slot:
#                fobj.write(
#                    mobj.method(i).signature() + ' ' + mobj.method(i).tag() + '\n')

OPEN_CMD_SWITCH = '--open'
IMPORT_CMD_SWITCH = '--import'

MIME_L5R_CHAR = "applications/x-l5r-character"
MIME_L5R_PACK = "applications/x-l5r-pack"

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

        # start main form
        l5rcm = L5RMain(app_locale)
        l5rcm.setWindowTitle(APP_DESC + ' v' + APP_VERSION)
        l5rcm.init()

        # initialize new character
        l5rcm.create_new_character()

        if len(sys.argv) > 1:
            if OPEN_CMD_SWITCH in sys.argv:
                log.app.debug(u"open character from command line")
                of = sys.argv.index(OPEN_CMD_SWITCH)
                l5rcm.load_character_from(sys.argv[of + 1])
            elif IMPORT_CMD_SWITCH in sys.argv:
                imf = sys.argv.index(IMPORT_CMD_SWITCH)
                pack_path = sys.argv[imf + 1]
                log.app.debug(u"import datapack from command line: %s", pack_path)
                app.quit()
                return l5rcm.import_data_pack(pack_path)
            else:
                # check mimetype
                log.app.debug(u"import file from command line ( should guess mimetype )")
                file_path = sys.argv[1]
                mime = mimetypes.guess_type(file_path)
                log.app.info(u"open file: %s, mime type: %s", file_path, mime)
                if mime[0] == MIME_L5R_CHAR:
                    l5rcm.load_character_from(file_path)
                elif mime[0] == MIME_L5R_PACK:
                    app.quit()
                    return l5rcm.import_data_pack(file_path)

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
