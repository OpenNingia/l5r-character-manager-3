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
# Expects self.widgets / self.tabs / self.ic_idx / self.menu_sink (and
# the other per-mixin sinks) from the host class plus self.please_donate
# / self.update_from_model from L5RCMCore / other mixins.

import os

from qtpy import QtCore, QtGui, QtWidgets

import l5r.api as api
import l5r.api.character
import l5r.dialogs as dialogs
import l5r.models

from l5r.util import osutil
from l5r.util.fsutil import get_icon_path
from l5r.util.settings import L5RCMSettings


class MenuSink(QtCore.QObject):
    """Qt slots for the gear-button application menu actions (Rules,
    Options, Outfit, Data submenus)."""

    def __init__(self, window):
        super().__init__(window)
        self.window = window

    # --- Rules submenu ---

    def on_set_wnd_mult(self):
        window = self.window
        val, ok = QtWidgets.QInputDialog.getInt(window, 'Set Health Multiplier',
                                                "Multiplier:", window.pc.health_multiplier,
                                                2, 5, 1)
        if ok:
            window.set_health_multiplier(val)

    def on_damage_act(self):
        window = self.window
        val, ok = QtWidgets.QInputDialog.getInt(window, 'Cure/Inflict Damage',
                                                "Wounds:", 1,
                                                -1000, 1000, 1)
        if ok:
            window.damage_health(val)

    # --- Outfit submenu ---

    def show_wear_armor(self):
        window = self.window
        dlg = dialogs.ChooseItemDialog(window.pc, 'armor', window)
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            window.update_from_model()

    def show_wear_cust_armor(self):
        window = self.window
        dlg = dialogs.CustomArmorDialog(window.pc, window)
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            window.update_from_model()

    # --- Options submenu ---

    def on_toggle_buy_for_free(self, flag):
        l5r.models.Advancement.set_buy_for_free(flag)

    def on_toggle_display_banner(self):
        settings = L5RCMSettings()
        settings.ui.banner_enabled = not settings.ui.banner_enabled
        self.set_banner_visibility(settings.ui.banner_enabled)

    def set_banner_visibility(self, value):
        window = self.window
        for i in range(0, window.mvbox.count()):
            logo = window.mvbox.itemAt(i).widget()
            if logo.objectName() == 'BANNER':
                if value:
                    logo.show()
                else:
                    logo.hide()
                    window.widgets.adjustSize()
                    window.widgets.resize(1, 1)
                    window.widgets.setGeometry(QtCore.QRect(0, 0, 727, 573))
                break

    def open_data_dir_act(self):
        path = os.path.normpath(osutil.get_user_data_path())
        if not os.path.exists(path):
            os.makedirs(path)
        osutil.portable_open(path)

    def show_dice_roller(self):
        from l5r.diceroller import drgui
        dlg = drgui.DiceRoller(self.window)
        dlg.show()


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

        new_act .triggered.connect(self.persistence_sink.new_character)
        open_act.triggered.connect(self.persistence_sink.load_character)
        save_act.triggered.connect(self.persistence_sink.save_character)
        exit_act.triggered.connect(self.close)

        export_pdf_act .triggered.connect(self.persistence_sink.export_character_as_pdf)
        export_npc_act .triggered.connect(self.persistence_sink.show_npc_export_dialog)

        # Advancement menu
        # actions buy advancement, view advancements
        resetadv_act = QtWidgets.QAction(self.tr("&Reset advancements"), self)
        refund_act = QtWidgets.QAction(self.tr("Refund last advancement"), self)

        refund_act .setShortcut(QtGui.QKeySequence.Undo)

        resetadv_act.triggered.connect(self.advancements_sink.reset_adv)
        refund_act  .triggered.connect(self.advancements_sink.refund_last_adv)

        # Outfit menu
        # actions, select armor, add weapon, add misc item
        sel_armor_act = QtWidgets.QAction(self.tr("Wear Armor..."), self)
        sel_cust_armor_act = QtWidgets.QAction(
            self.tr("Wear Custom Armor..."), self)
        add_weap_act = QtWidgets.QAction(self.tr("Add Weapon..."), self)
        add_cust_weap_act = QtWidgets.QAction(
            self.tr("Add Custom Weapon..."), self)

        sel_armor_act     .triggered.connect(self.menu_sink.show_wear_armor)
        sel_cust_armor_act.triggered.connect(self.menu_sink.show_wear_cust_armor)
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

        set_wound_mult_act.triggered.connect(self.menu_sink.on_set_wnd_mult)
        damage_act        .triggered.connect(self.menu_sink.on_damage_act)

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
            self.menu_sink.on_toggle_display_banner)
        options_buy_for_free_act.toggled.connect(
            self.menu_sink.on_toggle_buy_for_free)
        options_open_data_dir_act.triggered.connect(
            self.menu_sink.open_data_dir_act)
        options_dice_roll_act.triggered.connect(self.menu_sink.show_dice_roller)

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
