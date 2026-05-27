# -*- coding: utf-8 -*-
# Copyright (C) 2014-2026 Daniele Simonetti
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# Application menu (gear button at top-left of the tab widget) and the
# PayPal donate button in the status bar. Extracted from l5r/main.py
# during the Phase 4 split — no behaviour changes.
# Expects self.widgets / self.tabs / self.ic_idx / self.sink1..sink4
# from the host class plus self.please_donate / self.update_from_model
# from L5RCMCore / other mixins.

from qtpy import QtCore, QtGui, QtWidgets

import l5r.api as api
import l5r.api.character

from l5r.util.fsutil import get_icon_path
from l5r.util.settings import L5RCMSettings


class MenuMixin:
    """Builds the gear-button menu and the donate button."""

    def build_menu(self):

        settings = L5RCMSettings()

        self.app_menu_tb = QtWidgets.QToolButton(self.widgets)
        self.app_menu = QtWidgets.QMenu("AppMenu", self.app_menu_tb)

        # File Menu
        # actions: new, open, save
        new_act = QtWidgets.QAction(self.tr("&New Character"), self)
        open_act = QtWidgets.QAction(self.tr("&Open Character..."), self)
        save_act = QtWidgets.QAction(self.tr("&Save Character..."), self)
        export_pdf_act = QtWidgets.QAction(self.tr("Ex&port as PDF..."), self)
        export_npc_act = QtWidgets.QAction(self.tr("Export NPC sheet..."), self)
        exit_act = QtWidgets.QAction(self.tr("E&xit"), self)

        new_act .setShortcut(QtGui.QKeySequence.New)
        open_act.setShortcut(QtGui.QKeySequence.Open)
        save_act.setShortcut(QtGui.QKeySequence.Save)
        exit_act.setShortcut(QtGui.QKeySequence.Quit)

        new_act .triggered.connect(self.sink1.new_character)
        open_act.triggered.connect(self.sink1.load_character)
        save_act.triggered.connect(self.sink1.save_character)
        exit_act.triggered.connect(self.close)

        export_pdf_act .triggered.connect(self.sink1.export_character_as_pdf)
        export_npc_act .triggered.connect(self.sink1.show_npc_export_dialog)

        # Advancement menu
        # actions buy advancement, view advancements
        resetadv_act = QtWidgets.QAction(self.tr("&Reset advancements"), self)
        refund_act = QtWidgets.QAction(self.tr("Refund last advancement"), self)

        refund_act .setShortcut(QtGui.QKeySequence.Undo)

        resetadv_act.triggered.connect(self.sink1.reset_adv)
        refund_act  .triggered.connect(self.sink1.refund_last_adv)

        # Outfit menu
        # actions, select armor, add weapon, add misc item
        sel_armor_act = QtWidgets.QAction(self.tr("Wear Armor..."), self)
        sel_cust_armor_act = QtWidgets.QAction(
            self.tr("Wear Custom Armor..."), self)
        add_weap_act = QtWidgets.QAction(self.tr("Add Weapon..."), self)
        add_cust_weap_act = QtWidgets.QAction(
            self.tr("Add Custom Weapon..."), self)

        sel_armor_act     .triggered.connect(self.sink1.show_wear_armor)
        sel_cust_armor_act.triggered.connect(self.sink1.show_wear_cust_armor)
        add_weap_act      .triggered.connect(self.sink3.show_add_weapon)
        add_cust_weap_act .triggered.connect(self.sink3.show_add_cust_weapon)

        # Rules menu
        set_wound_mult_act = QtWidgets.QAction(
            self.tr("Set Health Multiplier..."), self)
        damage_act = QtWidgets.QAction(
            self.tr("Cure/Inflict Damage..."), self)

        # insight calculation submenu
        m_insight_calc = self.app_menu.addMenu(
            self.tr("Insight Calculation"))
        self.ic_act_grp = QtWidgets.QActionGroup(self)
        ic_default_act = QtWidgets.QAction(
            self.tr("Default"), self)
        ic_no_rank1_1 = QtWidgets.QAction(
            self.tr("Ignore Rank 1 Skills"), self)
        ic_no_rank1_2 = QtWidgets.QAction(
            self.tr("Account Rank 1 School Skills"), self)
        ic_default_act.setProperty('method', 1)
        ic_no_rank1_1 .setProperty('method', 2)
        ic_no_rank1_2 .setProperty('method', 3)
        ic_list = [ic_default_act, ic_no_rank1_1, ic_no_rank1_2]
        for act in ic_list:
            self.ic_act_grp.addAction(act)
            act.setCheckable(True)
            m_insight_calc.addAction(act)
        ic_list[self.ic_idx].setChecked(True)

        # health calculation submenu
        m_health_calc = self.app_menu.addMenu(self.tr("Health Display"))
        self.hm_act_grp = QtWidgets.QActionGroup(self)
        hm_default_act = QtWidgets.QAction(self.tr("Default"), self)
        hm_cumulative_act = QtWidgets.QAction(self.tr("Health left"), self)
        hm_totwounds_act = QtWidgets.QAction(self.tr("Total wounds"), self)
        hm_default_act   .setProperty('method', 'default')
        hm_cumulative_act.setProperty('method', 'stacked')
        hm_totwounds_act .setProperty('method', 'wounds')
        hm_list = [hm_default_act, hm_cumulative_act, hm_totwounds_act]
        hm_mode = settings.app.health_method
        for act in hm_list:
            self.hm_act_grp.addAction(act)
            act.setCheckable(True)
            m_health_calc.addAction(act)
            if act.property('method') == hm_mode:
                act.setChecked(True)

        set_wound_mult_act.triggered.connect(self.sink1.on_set_wnd_mult)
        damage_act        .triggered.connect(self.sink1.on_damage_act)

        # Data menu
        import_data_act = QtWidgets.QAction(self.tr("Import Data pack..."), self)
        manage_data_act = QtWidgets.QAction(
            self.tr("Manage Data packs..."), self)
        reload_data_act = QtWidgets.QAction(self.tr("Reload data"), self)

        # Options
        m_options = self.app_menu.addMenu(
            self.tr("Options"))
        self.options_act_grp = QtWidgets.QActionGroup(self)
        self.options_act_grp.setExclusive(False)

        options_banner_act = QtWidgets.QAction(
            self.tr("Toggle banner display"), self)
        options_buy_for_free_act = QtWidgets.QAction(
            self.tr("Free Shopping"), self)
        options_open_data_dir_act = QtWidgets.QAction(
            self.tr("Open Data Directory"), self)
        options_dice_roll_act = QtWidgets.QAction(
            self.tr("Dice &Roller..."), self)

        options_list = [
            options_banner_act,
            options_buy_for_free_act, options_open_data_dir_act, options_dice_roll_act]  # , options_reset_geometry_act
        for i, act in enumerate(options_list):
            self.options_act_grp.addAction(act)
            m_options.addAction(act)

            if i % 2 == 0:
                m_options.addSeparator()

        options_buy_for_free_act.setCheckable(True)
        options_buy_for_free_act.setChecked(False)

        settings = L5RCMSettings()
        options_banner_act.setCheckable(True)
        options_banner_act.setChecked(settings.ui.banner_enabled)

        options_banner_act.triggered.connect(
            self.sink1.on_toggle_display_banner)
        options_buy_for_free_act.toggled.connect(
            self.sink1.on_toggle_buy_for_free)
        options_open_data_dir_act.triggered.connect(
            self.sink1.open_data_dir_act)
        options_dice_roll_act.triggered.connect(self.sink1.show_dice_roller)

        # GENERAL MENU
        self.app_menu_tb.setAutoRaise(True)
        self.app_menu_tb.setToolButtonStyle(QtCore.Qt.ToolButtonFollowStyle)
        self.app_menu_tb.setPopupMode(QtWidgets.QToolButton.InstantPopup)
        self.app_menu_tb.setIconSize(QtCore.QSize(32, 32))
        self.app_menu_tb.setIcon(QtGui.QIcon.fromTheme(
            "application-menu", QtGui.QIcon(get_icon_path('gear', (32, 32)))))
        self.app_menu_tb.setArrowType(QtCore.Qt.NoArrow)

        # FILE MENU
        self.app_menu.addAction(new_act)
        self.app_menu.addAction(open_act)
        self.app_menu.addAction(save_act)
        self.app_menu.addAction(export_pdf_act)
        self.app_menu.addAction(export_npc_act)
        self.app_menu.addSeparator()
        # OPTIONS
        self.app_menu.addMenu(m_options)
        self.app_menu.addSeparator()
        # ADV
        self.app_menu.addAction(resetadv_act)
        self.app_menu.addAction(refund_act)
        self.app_menu.addSeparator()
        # OUTFIT
        self.app_menu.addAction(sel_armor_act)
        self.app_menu.addAction(sel_cust_armor_act)
        self.app_menu.addAction(add_weap_act)
        self.app_menu.addAction(add_cust_weap_act)
        self.app_menu.addSeparator()
        # RULES
        self.app_menu.addAction(set_wound_mult_act)
        self.app_menu.addSeparator()
        # INSIGHT
        self.app_menu.addMenu(m_insight_calc)
        # HEALTH
        self.app_menu.addMenu(m_health_calc)
        self.app_menu.addAction(damage_act)
        self.app_menu.addSeparator()
        # DATA
        self.app_menu.addAction(import_data_act)
        self.app_menu.addAction(manage_data_act)
        self.app_menu.addAction(reload_data_act)
        self.app_menu.addSeparator()

        # EXIT
        self.app_menu.addAction(exit_act)

        self.app_menu_tb.setMenu(self.app_menu)
        self.tabs.setCornerWidget(self.app_menu_tb, QtCore.Qt.TopLeftCorner)

        import_data_act  .triggered.connect(self.sink4.import_data_act)
        manage_data_act  .triggered.connect(self.sink4.manage_data_act)
        reload_data_act  .triggered.connect(self.sink4.reload_data_act)

    def setup_donate_button(self):
        self.statusBar().showMessage(
            self.tr("You can donate to the project by clicking on the button")
        )

        self.paypal_bt = QtWidgets.QPushButton(self)
        self.paypal_bt.setIcon(
            QtGui.QIcon(get_icon_path('btn_donate_SM', None)))
        self.paypal_bt.setIconSize(QtCore.QSize(74, 21))
        self.paypal_bt.setFlat(True)
        self.paypal_bt.clicked.connect(self.please_donate)
        self.statusBar().addPermanentWidget(self.paypal_bt)

    def on_change_insight_calculation(self):
        method = self.sender().checkedAction().property('method')
        api.character.set_insight_calculation_method(method)
        self.update_from_model()

    def on_change_health_visualization(self):
        method = self.sender().checkedAction().property('method')
        settings = L5RCMSettings()
        settings.app.health_method = method
        self.update_from_model()
