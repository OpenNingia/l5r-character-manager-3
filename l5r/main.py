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

import sys
import os

here = ''

try:
    here = os.path.abspath(os.path.dirname(__file__))
except NameError:  # We are the main py2exe script, not a module
    here = os.path.dirname(os.path.abspath(sys.argv[0]))

parent = os.path.abspath(os.path.dirname(here))
sys.path.append(here)

import mimetypes
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
from l5r.util import log
from l5r.util.settings import L5RCMSettings


def new_small_le(parent=None, ro=True):
    le = QtWidgets.QLineEdit(parent)
    le.setSizePolicy(QtWidgets.QSizePolicy.Maximum,
                     QtWidgets.QSizePolicy.Maximum)
    le.setMaximumSize(QtCore.QSize(32, 24))
    le.setReadOnly(ro)
    return le


def new_horiz_line(parent=None):
    line = QtWidgets.QFrame(parent)
    line.setObjectName("hline")
    line.setGeometry(QtCore.QRect(3, 3, 3, 3))
    line.setFrameShape(QtWidgets.QFrame.HLine)
    line.setFrameShadow(QtWidgets.QFrame.Sunken)
    line.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
    return line


def new_vert_line(parent=None):
    line = QtWidgets.QFrame(parent)
    line.setObjectName("vline")
    line.setGeometry(QtCore.QRect(320, 150, 118, 3))
    line.setFrameShape(QtWidgets.QFrame.VLine)
    line.setFrameShadow(QtWidgets.QFrame.Sunken)
    return line


def new_item_groupbox(name, widget):
    grp = QtWidgets.QGroupBox(name, widget.parent())
    vbox = QtWidgets.QVBoxLayout(grp)
    vbox.addWidget(widget)
    return grp


def new_small_plus_bt(parent=None):
    bt = QtWidgets.QToolButton(parent)
    bt.setAutoRaise(True)
    bt.setText('+')
    bt.setIcon(
        QtGui.QIcon.fromTheme('gtk-add', QtGui.QIcon(
            get_icon_path('add', (16, 16)))))
    bt.setMaximumSize(16, 16)
    bt.setMinimumSize(16, 16)
    bt.setToolButtonStyle(QtCore.Qt.ToolButtonFollowStyle)
    return bt

class L5RMain(L5RCMCore):

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

    def build_ui_page_1(self):

        mfr = QtWidgets.QFrame(self)
        self.tabs.addTab(mfr, self.tr("Character"))

        mvbox = QtWidgets.QVBoxLayout(mfr)
        mvbox.setContentsMargins(0, 0, 0, 0)

        def add_pc_info(row, col):
            fr_pc_info = QtWidgets.QFrame(self)
            fr_pc_info.setSizePolicy(QtWidgets.QSizePolicy.Preferred,
                                     QtWidgets.QSizePolicy.Maximum)

            grid = QtWidgets.QGridLayout(fr_pc_info)
            self.tx_pc_name = QtWidgets.QLineEdit(self)
            self.tx_pc_rank = QtWidgets.QLineEdit(self)
            self.lb_pc_clan = QtWidgets.QLabel(self)
            self.lb_pc_family = QtWidgets.QLabel(self)
            self.lb_pc_school = QtWidgets.QLabel(self)
            self.tx_pc_exp = QtWidgets.QLineEdit(self)
            self.tx_pc_ins = QtWidgets.QLineEdit(self)

            # School
            fr_school = QtWidgets.QFrame(self)
            hb_school = QtWidgets.QHBoxLayout(fr_school)
            hb_school.setContentsMargins(0, 0, 0, 0)

            bt_edit_school = QtWidgets.QToolButton(self)
            bt_edit_school.setToolTip(self.tr("Edit character first school"))
            bt_edit_school.setAutoRaise(True)
            bt_edit_school.setIcon(QtGui.QIcon(get_icon_path('edit', (16, 16))))

            hb_school.addWidget(QtWidgets.QLabel(self.tr("School"), self))
            hb_school.addWidget(bt_edit_school)

            # Family
            bt_edit_family = QtWidgets.QToolButton(self)
            bt_edit_family.setToolTip(self.tr("Edit character family and clan"))
            bt_edit_family.setAutoRaise(True)
            bt_edit_family.setIcon(QtGui.QIcon(get_icon_path('edit', (16, 16))))

            fr_family = QtWidgets.QFrame(self)
            hb_family = QtWidgets.QHBoxLayout(fr_family)
            hb_family.setContentsMargins(0, 0, 0, 0)
            hb_family.addWidget(QtWidgets.QLabel(self.tr("Family")))
            hb_family.addWidget(bt_edit_family)

            # Place "generate random name" near the Name label
            lb_name = QtWidgets.QLabel(self.tr("Name"), self)
            bt_generate_male = QtWidgets.QToolButton(self)
            bt_generate_male.setIcon(
                QtGui.QIcon(get_icon_path('male', (16, 16))))
            bt_generate_female = QtWidgets.QToolButton(self)
            bt_generate_female.setIcon(
                QtGui.QIcon(get_icon_path('female', (16, 16))))
            bt_generate_male  .setAutoRaise(True)
            bt_generate_male  .setToolTip(self.tr("Random male name"))
            bt_generate_female.setAutoRaise(True)
            bt_generate_female.setToolTip(self.tr("Random female name"))
            hb_name = QtWidgets.QHBoxLayout()
            hb_name.addWidget(lb_name)
            hb_name.addWidget(bt_generate_male)
            hb_name.addWidget(bt_generate_female)

            # gender tag, connect signals
            bt_generate_male  .setProperty('gender', 'male')
            bt_generate_female.setProperty('gender', 'female')
            bt_generate_male  .clicked.connect(self.sink1.generate_name)
            bt_generate_female.clicked.connect(self.sink1.generate_name)

            grid.addLayout(hb_name, 0, 0)
            grid.addWidget(QtWidgets.QLabel(self.tr("Clan"), self), 1, 0)
            grid.addWidget(fr_family, 2, 0)
            grid.addWidget(fr_school, 3, 0)

            self.bt_edit_family = bt_edit_family
            self.bt_edit_school = bt_edit_school

            # 3rd column
            fr_exp = QtWidgets.QFrame(self)
            hb_exp = QtWidgets.QHBoxLayout(fr_exp)
            hb_exp.setContentsMargins(0, 0, 0, 0)
            lb_exp = QtWidgets.QLabel(self.tr("Exp. Points"), self)
            bt_exp = QtWidgets.QToolButton(self)
            bt_exp.setToolTip(self.tr("Edit experience points"))
            bt_exp.setAutoRaise(True)
            bt_exp.setIcon(QtGui.QIcon(get_icon_path('edit', (16, 16))))
            hb_exp.addWidget(lb_exp)
            hb_exp.addWidget(bt_exp)

            grid.addWidget(QtWidgets.QLabel(self.tr("Rank"), self), 0, 3)
            grid.addWidget(fr_exp, 1, 3)
            grid.addWidget(QtWidgets.QLabel(self.tr("Insight"), self), 2, 3)

            self.bt_set_exp_points = bt_exp

            # 2nd column
            grid.addWidget(self.tx_pc_name, 0, 1, 1, 2)
            grid.addWidget(self.lb_pc_clan, 1, 1, 1, 2)
            grid.addWidget(self.lb_pc_family, 2, 1, 1, 2)
            grid.addWidget(self.lb_pc_school, 3, 1, 1, 2)

            # 4th column
            grid.addWidget(self.tx_pc_rank, 0, 4, 1, 2)
            grid.addWidget(self.tx_pc_exp, 1, 4, 1, 2)
            grid.addWidget(self.tx_pc_ins, 2, 4, 1, 2)

            self.tx_pc_rank.setReadOnly(True)
            self.tx_pc_exp.setReadOnly(True)
            self.tx_pc_ins.setReadOnly(True)

            fr_pc_info.setLayout(grid)
            mvbox.addWidget(fr_pc_info)

        def build_trait_frame():
            fr = QtWidgets.QFrame(self)
            fr.setSizePolicy(QtWidgets.QSizePolicy.Preferred,
                             QtWidgets.QSizePolicy.Maximum)
            hbox = QtWidgets.QHBoxLayout(fr)
            grp = QtWidgets.QGroupBox(self.tr("Rings and Attributes"), self)
            grid = QtWidgets.QGridLayout(grp)
            grid.setSpacing(1)

            # rings
            rings = [(self.tr("Earth"), new_small_le(self)), (self.tr("Air"), new_small_le(self)),
                     (self.tr("Water"), new_small_le(self)), (self.tr("Fire"), new_small_le(self)),
                     (self.tr("Void"), new_small_le(self))]

            # keep reference to the rings
            self.rings = rings

            for i in range(0, 4):
                grid.addWidget(QtWidgets.QLabel(rings[i][0]), i, 0)
                grid.addWidget(rings[i][1], i, 1)

            # void ring with plus button
            void_fr = QtWidgets.QFrame(self)
            void_hbox = QtWidgets.QHBoxLayout(void_fr)
            void_hbox.setContentsMargins(0, 0, 0, 0)
            void_bt = new_small_plus_bt(self)
            void_hbox.addWidget(rings[4][1])
            void_hbox.addWidget(void_bt)
            void_bt.clicked.connect(self.on_void_increase)
            grid.addWidget(QtWidgets.QLabel(rings[4][0]), 4, 0)
            grid.addWidget(void_fr, 4, 1)

            attribs = []
            # Earth ring
            attribs.append((self.tr("Stamina"), new_small_le(self)))
            attribs.append((self.tr("Willpower"), new_small_le(self)))
            attribs[0][1].setProperty('attrib_id', models.ATTRIBS.STAMINA)
            attribs[1][1].setProperty('attrib_id', models.ATTRIBS.WILLPOWER)
            # Air ring
            attribs.append((self.tr("Reflexes"), new_small_le(self)))
            attribs.append((self.tr("Awareness"), new_small_le(self)))
            attribs[2][1].setProperty('attrib_id', models.ATTRIBS.REFLEXES)
            attribs[3][1].setProperty('attrib_id', models.ATTRIBS.AWARENESS)
            # Water ring
            attribs.append((self.tr("Strength"), new_small_le(self)))
            attribs.append((self.tr("Perception"), new_small_le(self)))
            attribs[4][1].setProperty('attrib_id', models.ATTRIBS.STRENGTH)
            attribs[5][1].setProperty('attrib_id', models.ATTRIBS.PERCEPTION)
            # Fire ring
            attribs.append((self.tr("Agility"), new_small_le(self)))
            attribs.append((self.tr("Intelligence"), new_small_le(self)))
            attribs[6][1].setProperty('attrib_id', models.ATTRIBS.AGILITY)
            attribs[7][1].setProperty('attrib_id', models.ATTRIBS.INTELLIGENCE)

            self.attribs = attribs

            # map increase trait signals
            self.trait_sig_mapper = QtCore.QSignalMapper(self)

            def _attrib_frame(i):
                fr = QtWidgets.QFrame(self)
                hbox = QtWidgets.QHBoxLayout(fr)
                hbox.setContentsMargins(3, 0, 9, 0)
                # small plus button
                tag = str(attribs[i][1].property('attrib_id'))
                bt = new_small_plus_bt(self)
                hbox.addWidget(attribs[i][1])
                hbox.addWidget(bt)
                self.trait_sig_mapper.setMapping(bt, tag)
                bt.clicked.connect( self.trait_sig_mapper.map )
                return fr

            for i in range(0, 8, 2):
                grid.addWidget(QtWidgets.QLabel(attribs[i][0]),
                               (i // 2), 2, 1, 1, QtCore.Qt.AlignLeft)
                grid.addWidget(_attrib_frame(i), (i // 2), 3, 1, 1,
                               QtCore.Qt.AlignLeft)

                grid.addWidget(QtWidgets.QLabel(attribs[i + 1][0]),
                               (i // 2), 4, 1, 1, QtCore.Qt.AlignLeft)
                grid.addWidget(_attrib_frame(i + 1), (i // 2), 5, 1, 1,
                               QtCore.Qt.AlignLeft)
            grid.addWidget(QtWidgets.QLabel(self.tr("<b>Void Points</b>")),
                           4, 2, 1, 3,
                           QtCore.Qt.AlignHCenter)

            self.void_points = widgets.CkNumWidget(count=10, parent=self)
            grid.addWidget(self.void_points, 5, 2, 1, 3,
                           QtCore.Qt.AlignHCenter)

            hbox.addWidget(grp)

            return fr

        def build_flags_frame():
            tx_flags = [self.tr("Honor"), self.tr("Glory"),
                        self.tr("Status"), self.tr("Shadowland Taint"),
                        self.tr("Infamy")]

            ob_flags_p = []
            ob_flags_r = []
            fr = QtWidgets.QFrame(self)
            # fr.setFrameShape(QtWidgets.QFrame.StyledPanel)
            vbox = QtWidgets.QVBoxLayout(fr)
            vbox.setContentsMargins(0, 0, 0, 0)
            vbox.setSpacing(0)
            row = 1
            for f in tx_flags:
                fr_ = QtWidgets.QFrame(self)
                lay = QtWidgets.QGridLayout(fr_)
                lay.setContentsMargins(0, 0, 0, 0)
                lay.setSpacing(0)
                lay.addWidget(QtWidgets.QLabel('<b>%s</b>' % f), row, 0)
                l = new_small_le(self, False)
                lay.addWidget(l, row, 1)
                w = widgets.CkNumWidget(count=9, parent=self)
                lay.addWidget(w, row + 1, 0, 1, 2, QtCore.Qt.AlignHCenter)
                ob_flags_p.append(w)
                ob_flags_r.append(l)
                vbox.addWidget(fr_)
            self.pc_flags_points = ob_flags_p
            self.pc_flags_rank = ob_flags_r

            return fr

        def add_traits_and_flags():
            trait_frame = build_trait_frame()
            flags_frame = build_flags_frame()

            fr = QtWidgets.QFrame(self)
            hbox = QtWidgets.QHBoxLayout(fr)

            fr.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                             QtWidgets.QSizePolicy.Maximum)

            hbox.addWidget(trait_frame)
            hbox.addWidget(flags_frame)

            mvbox.addWidget(fr)

        def add_pc_quantities(row, col):
            fr = QtWidgets.QFrame(self)
            fr.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                             QtWidgets.QSizePolicy.Maximum)
            hbox = QtWidgets.QHBoxLayout(fr)

            monos_ = QtGui.QFont('Monospace')
            monos_.setStyleHint(QtGui.QFont.Courier)

            # fr.setFont(monos_)

            # initiative
            grp = QtWidgets.QGroupBox(self.tr("Initiative"), self)

            grd = QtWidgets.QFormLayout(grp)

            self.tx_base_init = QtWidgets.QLineEdit(self)
            self.tx_mod_init = QtWidgets.QLineEdit(self)
            self.tx_cur_init = QtWidgets.QLineEdit(self)

            self.tx_base_init.setReadOnly(True)
            self.tx_mod_init .setReadOnly(True)
            self.tx_cur_init .setReadOnly(True)

            grd.addRow(self.tr("Base"), self.tx_base_init)
            grd.addRow(self.tr("Modifier"), self.tx_mod_init)
            grd.addRow(self.tr("Current"), self.tx_cur_init)

            hbox.addWidget(grp, 1)

            # Armor TN
            grp = QtWidgets.QGroupBox(self.tr("Armor TN"), self)

            grd = QtWidgets.QFormLayout(grp)

            self.tx_armor_nm = QtWidgets.QLineEdit(self)
            self.tx_base_tn = QtWidgets.QLineEdit(self)
            self.tx_armor_tn = QtWidgets.QLineEdit(self)
            self.tx_armor_rd = QtWidgets.QLineEdit(self)
            self.tx_cur_tn = QtWidgets.QLineEdit(self)

            self.tx_armor_nm.setReadOnly(True)
            self.tx_base_tn .setReadOnly(True)
            self.tx_armor_tn.setReadOnly(True)
            self.tx_armor_rd.setReadOnly(True)
            self.tx_cur_tn  .setReadOnly(True)

            grd.addRow(self.tr("Name"), self.tx_armor_nm)
            grd.addRow(self.tr("Base"), self.tx_base_tn)
            grd.addRow(self.tr("Armor"), self.tx_armor_tn)
            grd.addRow(self.tr("Reduction"), self.tx_armor_rd)
            grd.addRow(self.tr("Current"), self.tx_cur_tn)

            hbox.addWidget(grp, 1)

            # Wounds
            grp = QtWidgets.QGroupBox(self.tr("Wounds"), self)

            grd = QtWidgets.QGridLayout(grp)

            wnd = [(QtWidgets.QLabel(self), new_small_le(self), new_small_le(self)),
                   (QtWidgets.QLabel(self), new_small_le(self), new_small_le(self)),
                   (QtWidgets.QLabel(self), new_small_le(self), new_small_le(self)),
                   (QtWidgets.QLabel(self), new_small_le(self), new_small_le(self)),
                   (QtWidgets.QLabel(self), new_small_le(self), new_small_le(self)),
                   (QtWidgets.QLabel(self), new_small_le(self), new_small_le(self)),
                   (QtWidgets.QLabel(self), new_small_le(self), new_small_le(self)),

                   (QtWidgets.QLabel(self.tr("Out"), self),
                                                                                  new_small_le(self),
                                                                                  new_small_le(self))]

            self.wounds = wnd
            self.wnd_lb = grp

            row_ = 0
            col_ = 0
            for i in range(0, len(wnd)):
                if i == 4:
                    col_ = 3
                    row_ = 0

                grd.addWidget(wnd[i][0], row_, col_)
                grd.addWidget(wnd[i][0], row_, col_)
                grd.addWidget(wnd[i][1], row_, col_ + 1)
                grd.addWidget(wnd[i][2], row_, col_ + 2)
                row_ += 1

            hbox.addWidget(grp, 2)

            mvbox.addWidget(fr)

        add_pc_info(0, 0)
        mvbox.addWidget(new_horiz_line(self))
        add_traits_and_flags()
        mvbox.addWidget(new_horiz_line(self))
        add_pc_quantities(4, 0)

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

    def build_ui_page_6(self):
        mfr = QtWidgets.QFrame(self)
        vbox = QtWidgets.QVBoxLayout(mfr)

        fr_ = QtWidgets.QFrame(self)
        fr_h = QtWidgets.QHBoxLayout(fr_)
        fr_h.setContentsMargins(0, 0, 0, 0)
        fr_h.addWidget(
            QtWidgets.QLabel(self.tr("""<p><i>Select the advancement to refund and hit the button</i></p>"""), self))
        bt_refund_adv = QtWidgets.QPushButton(self.tr("Refund"), self)
        bt_refund_adv.setSizePolicy(QtWidgets.QSizePolicy.Maximum,
                                    QtWidgets.QSizePolicy.Preferred)
        bt_refund_adv.clicked.connect(self.sink1.refund_advancement)
        fr_h.addWidget(bt_refund_adv)
        vbox.addWidget(fr_)

        self.adv_view_model = l5r.models.AdvancementViewModel(self)
        view = QtWidgets.QTableView(self)
        view.setSortingEnabled(False)
        view.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.Interactive)
        view.horizontalHeader().setStretchLastSection(True)
        view.horizontalHeader().setCascadingSectionResizes(True)

        self.table_views.append(view)
        view.setModel(self.adv_view_model)
        vbox.addWidget(view)

        self.adv_view = view

        self.tabs.addTab(mfr, self.tr("Advancements"))

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

    def build_ui_page_settings(self):
        self.settings_widgets = widgets.SettingsWidget(self)
        self.tabs.addTab(self.settings_widgets, self.tr("Settings"))
        self.settings_widgets.setup(self)

    def build_ui_page_about(self):
        mfr = QtWidgets.QFrame(self)
        hbox = QtWidgets.QHBoxLayout()
        hbox.setAlignment(QtCore.Qt.AlignCenter)
        hbox.setSpacing(30)

        logo = QtWidgets.QLabel(self)
        logo.setPixmap(QtGui.QPixmap(get_app_icon_path((64, 64))))
        hbox.addWidget(logo, 0, QtCore.Qt.AlignTop)

        vbox = QtWidgets.QVBoxLayout(mfr)
        vbox.setAlignment(QtCore.Qt.AlignCenter)
        vbox.setSpacing(30)

        info = """<html><style>a { color: palette(text); }</style><body><h1>%s</h1>
                  <p>Version %s</p>
                  <p><a href="%s">%s</a></p>
                  <p>Report bugs and send in your ideas <a href="%s">here</a></p>
                  <p>To know about Legend of the Five rings please visit
                  <a href="%s">L5R RPG Home Page</a>
                  </p>
                  <p>
                  All right on Legend of The Five Rings RPG are possession of
                  <p>
                  <a href="%s">Alderac Entertainment Group (AEG)</a>
                  </p>
                  </p>
                  <p style='color:palette(mid)'>&copy; 2015 %s</p>
                  <p>Special Thanks:</p>
                  <p style="margin-left: 10;">
                  Paul Tar, Jr aka Geiko (Lots of cool stuff)</p>
                  <p style="margin-left: 10;">Derrick D. Cochran (OS X Distro)
                  </p>
                  </body></html>""" % (APP_DESC,
                                       QtWidgets.QApplication.applicationVersion(
                                       ),
                                       PROJECT_PAGE_LINK, PROJECT_PAGE_NAME,
                                       BUGTRAQ_LINK, L5R_RPG_HOME_PAGE,
                                       ALDERAC_HOME_PAGE, AUTHOR_NAME)
        lb_info = QtWidgets.QLabel(info, self)
        lb_info.setOpenExternalLinks(True)
        lb_info.setWordWrap(True)
        hbox.addWidget(lb_info)

        vbox.addLayout(hbox)

        self.tabs.addTab(mfr, self.tr("About"))

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
        # options_reset_geometry_act.triggered.connect(self.sink1.on_reset_geometry)

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

    def init(self):
        """ second step initialization """
        pass

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

        self.trait_sig_mapper.mapped[str].connect(self.on_trait_increase)
        #QtCore.connect(self.trait_sig_mapper,
        #                       QtCore.SIGNAL('mapped(const QString &)'),
        #                       self.on_trait_increase)
        #self.trait_sig_mapper.connect(QtCore.SIGNAL("mapped(const QString &)"),
        #                              self,
        #                              QtCore.SLOT("on_trait_increase(const QString &)"))

        self.ic_act_grp.triggered.connect(self.on_change_insight_calculation)
        self.hm_act_grp.triggered.connect(self.on_change_health_visualization)

        self.bt_edit_family.clicked.connect(self.sink4.on_edit_family)
        self.bt_edit_school.clicked.connect(self.sink4.on_edit_first_school)

        self.bt_set_exp_points.clicked.connect(self.sink1.on_set_exp_limit)

    def show_nicebar(self, wdgs):
        self.nicebar = QtWidgets.QFrame(self)
        self.nicebar.setStyleSheet("""
        QWidget { background: beige;}
        QPushButton {
            color: #333;
            border: 2px solid rgb(200,200,200);
            border-radius: 7px;
            padding: 5px;
            background: qradialgradient(cx: 0.3, cy: -0.4,
            fx: 0.3, fy: -0.4, radius: 1.35, stop: 0 #fff,
            stop: 1 rgb(255,170,0));
            min-width: 80px;
            }

        QPushButton:hover {
            background: qradialgradient(cx: 0.3, cy: -0.4,
            fx: 0.3, fy: -0.4, radius: 1.35, stop: 0 #fff,
            stop: 1 rgb(255,100,30));
        }

        QPushButton:pressed {
            background: qradialgradient(cx: 0.4, cy: -0.1,
            fx: 0.4, fy: -0.1, radius: 1.35, stop: 0 #fff,
            stop: 1 rgb(255,200,50));
        }
        """)
        self.nicebar.setMinimumSize(0, 32)

        # nicebar layout
        hbox = QtWidgets.QHBoxLayout(self.nicebar)
        hbox.setContentsMargins(9, 1, 9, 1)

        for w in wdgs:
            hbox.addWidget(w)

        self.mvbox.insertWidget(1, self.nicebar)
        self.nicebar.setVisible(True)

    def hide_nicebar(self):
        if not self.nicebar:
            return
        self.nicebar.setVisible(False)
        del self.nicebar
        self.nicebar = None

    def on_trait_increase(self, tag):
        """raised when user click on the small '+' button near traits"""

        trait_ = api.data.get_trait_by_index(int(tag))
        if not trait_:
            log.ui.error(u"trait not found by index: %s", tag)
            return

        if self.increase_trait(int(tag)) == CMErrors.NOT_ENOUGH_XP:
            self.not_enough_xp_advise(self)

    def on_void_increase(self):
        """raised when user click on the small '+' button near void ring"""
        if self.increase_void() == CMErrors.NOT_ENOUGH_XP:
            self.not_enough_xp_advise(self)

    def do_buy_kata(self, kata):
        """attempt to buy a new kata"""
        if self.buy_kata(kata) == CMErrors.NOT_ENOUGH_XP:
            self.not_enough_xp_advise(self)

    def do_buy_kiho(self, kiho):
        """attempt to buy a new kiho"""
        if self.buy_kiho(kiho) == CMErrors.NOT_ENOUGH_XP:
            self.not_enough_xp_advise(self)

    def on_pc_name_change(self):
        self.pc.name = self.tx_pc_name.text()

    def on_pers_info_change(self):
        w = self.sender()
        if hasattr(w, 'link'):
            self.pc.set_property(w.link, w.text())

    def on_flag_points_change(self):
        fl = self.sender()
        pt = fl.value

        if fl == self.pc_flags_points[0]:
            val = int(self.pc_flags_rank[0].text())
            api.character.set_honor(float(val + float(pt) / 10))
        elif fl == self.pc_flags_points[1]:
            val = int(self.pc_flags_rank[1].text())
            api.character.set_glory(float(val + float(pt) / 10))
        elif fl == self.pc_flags_points[2]:
            val = int(self.pc_flags_rank[2].text())
            api.character.set_status(float(val + float(pt) / 10))
        elif fl == self.pc_flags_points[3]:
            val = int(self.pc_flags_rank[3].text())
            api.character.set_taint(float(val + float(pt) / 10))
        else:
            val = int(self.pc_flags_rank[4].text())
            api.character.set_infamy(float(val + float(pt) / 10))

    def on_flag_rank_change(self):
        fl = self.sender()
        val = int(fl.text())
        if fl == self.pc_flags_rank[0]:
            pt = self.pc_flags_points[0].value
            api.character.set_honor(float(val + float(pt) / 10))
        elif fl == self.pc_flags_rank[1]:
            pt = self.pc_flags_points[1].value
            api.character.set_glory(float(val + float(pt) / 10))
        elif fl == self.pc_flags_rank[2]:
            pt = self.pc_flags_points[2].value
            api.character.set_status(float(val + float(pt) / 10))
        elif fl == self.pc_flags_rank[3]:
            pt = self.pc_flags_points[3].value
            api.character.set_taint(float(val + float(pt) / 10))
        else:
            pt = self.pc_flags_points[4].value
            api.character.set_infamy(float(val + float(pt) / 10))

    def on_void_points_change(self):
        val = self.void_points.value
        self.pc.set_void_points(val)

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

    def act_choose_skills(self):
        dlg = dialogs.SelWcSkills(self.pc, self)
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            api.character.rankadv.clear_skills_to_choose()
            self.update_from_model()

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

    def check_rank_advancement(self):
        if self.nicebar:
            return

        potential_insight_rank_ = api.character.insight_rank()
        actual_insight_rank_ = api.character.insight_rank(strict=True)

        log.rules.debug(u"check rank advancement. potential rank: %d, actual rank: %d",
                        potential_insight_rank_, actual_insight_rank_)

        if potential_insight_rank_ > actual_insight_rank_:
            # HEY, NEW RANK DUDE!
            lb = QtWidgets.QLabel(self.tr("You reached the next rank, you have an opportunity"
                                      " to decide your destiny."), self)
            bt = QtWidgets.QPushButton(self.tr("Advance rank"), self)
            bt.setSizePolicy(QtWidgets.QSizePolicy.Maximum,
                             QtWidgets.QSizePolicy.Preferred)
            bt.clicked.connect(self.show_advance_rank_dlg)
            self.show_nicebar([lb, bt])

    def check_school_new_spells(self):
        if self.nicebar:
            return

        # Show nicebar if can get other spells
        if api.character.rankadv.has_granted_free_spells():
            lb = QtWidgets.QLabel(
                self.tr("You now fit the requirements to learn other Spells"), self)
            bt = QtWidgets.QPushButton(self.tr("Learn Spells"), self)
            bt.setSizePolicy(QtWidgets.QSizePolicy.Maximum,
                             QtWidgets.QSizePolicy.Preferred)
            bt.clicked.connect(self.learn_next_school_spells)
            self.show_nicebar([lb, bt])

    def check_free_kihos(self):
        if self.nicebar:
            return

        # Show nicebar if can get free kihos
        if api.character.rankadv.get_gained_kiho_count() > 0:
            lb = QtWidgets.QLabel(
                self.tr("You can learn {0} kihos for free").format(api.character.rankadv.get_gained_kiho_count()), self)
            bt = QtWidgets.QPushButton(self.tr("Learn Kihos"), self)
            bt.setSizePolicy(QtWidgets.QSizePolicy.Maximum,
                             QtWidgets.QSizePolicy.Preferred)
            bt.clicked.connect(self.learn_next_free_kiho)
            self.show_nicebar([lb, bt])

    def check_new_skills(self):
        if self.nicebar:
            return

        # Show nicebar if pending wildcard skills
        if api.character.rankadv.has_granted_skills_to_choose():
            lb = QtWidgets.QLabel(
                self.tr("Your school gives you the choice of certain skills"), self)
            bt = QtWidgets.QPushButton(self.tr("Choose Skills"), self)
            bt.setSizePolicy(QtWidgets.QSizePolicy.Maximum,
                             QtWidgets.QSizePolicy.Preferred)
            bt.clicked.connect(self.act_choose_skills)
            self.show_nicebar([lb, bt])

    def check_affinity_wc(self):
        if self.nicebar:
            return

        rank_ = api.character.rankadv.get_last()
        if not rank_:
            return

        log.app.info(u"check if the player can choose his affinity/deficiency: [%s] / [%s] ",
                     u", ".join(rank_.affinities_to_choose),
                     u", ".join(rank_.deficiencies_to_choose))

        if api.character.rankadv.has_granted_affinities_to_choose():
            lb = QtWidgets.QLabel(
                self.tr("You school grant you to choose an elemental affinity."), self)
            bt = QtWidgets.QPushButton(self.tr("Choose Affinity"), self)
            bt.setSizePolicy(QtWidgets.QSizePolicy.Maximum,
                             QtWidgets.QSizePolicy.Preferred)
            bt.clicked.connect(self.show_select_affinity)
            self.show_nicebar([lb, bt])
        elif api.character.rankadv.has_granted_deficiencies_to_choose():
            lb = QtWidgets.QLabel(
                self.tr("You school grant you to choose an elemental deficiency."), self)
            bt = QtWidgets.QPushButton(self.tr("Choose Deficiency"), self)
            bt.setSizePolicy(QtWidgets.QSizePolicy.Maximum,
                             QtWidgets.QSizePolicy.Preferred)
            bt.clicked.connect(self.show_select_deficiency)
            self.show_nicebar([lb, bt])

    def learn_next_school_spells(self):

        dlg = dialogs.SpellAdvDialog(self.pc, 'bounded', self)
        dlg.setWindowTitle(self.tr('Choose School Spells'))
        dlg.set_header_text(self.tr("<center><h2>Your school has granted you \
                                     the right to choose some spells.</h2> \
                                     <h3><i>Choose with care.</i></h3></center>"))
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            api.character.rankadv.clear_spells_to_choose()
            self.update_from_model()

    def learn_next_free_kiho(self):
        dlg = dialogs.KihoDialog(self.pc, self)
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            self.update_from_model()

    def show_advance_rank_dlg(self):
        dlg = dialogs.NextRankDlg(self.pc, self)
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            self.update_from_model()

    def show_buy_skill_dlg(self):
        dlg = dialogs.BuyAdvDialog(self.pc, 'skill', self)
        dlg.exec_()
        self.update_from_model()

    def show_buy_emph_dlg(self):
        # get selected skill
        sm_ = self.skill_table_view.selectionModel()
        if sm_.hasSelection():
            model_ = self.skill_table_view.model()
            skill_id = model_.data(sm_.currentIndex(), QtCore.Qt.UserRole)

            dlg = dialogs.BuyAdvDialog(self.pc, 'emph', self)
            dlg.fix_skill_id(skill_id)
            dlg.exec_()
            self.update_from_model()

    def show_select_affinity(self):

        rank_ = api.character.rankadv.get_last()
        if not rank_:
            return

        to_choose = rank_.affinities_to_choose.pop()

        chooses = None
        if 'nonvoid' in to_choose:
            chooses = [api.data.get_ring(x).text for x in api.data.rings() if x != 'void']
        else:
            chooses = [api.data.get_ring(x).text for x in api.data.rings()]

        affinity, is_ok = QtWidgets.QInputDialog.getItem(self,
                                                     "L5R: CM",
                                                     self.tr(
                                                         "Select your elemental affinity"),
                                                     chooses, 0, False)
        if is_ok:
            ring_ = [x for x in api.data.rings() if api.data.get_ring(x).text == affinity]
            if len(ring_):
                rank_.affinities.append(ring_[0])
        else:
            rank_.affinities_to_choose.append(to_choose)

        self.update_from_model()

    def show_select_deficiency(self):

        rank_ = api.character.rankadv.get_last()
        if not rank_:
            return

        to_choose = rank_.deficiencies_to_choose.pop()

        chooses = None
        if 'nonvoid' in to_choose:
            chooses = [api.data.get_ring(x).text for x in api.data.rings() if x != 'void']
        else:
            chooses = [api.data.get_ring(x).text for x in api.data.rings()]

        deficiency, is_ok = QtWidgets.QInputDialog.getItem(self,
                                                       "L5R: CM",
                                                       self.tr(
                                                           "Select your elemental deficiency"),
                                                       chooses, 0, False)

        if is_ok:
            ring_ = [x for x in api.data.rings() if api.data.get_ring(x).text == deficiency]
            if len(ring_):
                rank_.deficiencies.append(ring_[0])
        else:
            rank_.deficiencies.append(to_choose)

        self.update_from_model()

    def load_character_from(self, path):

        with QtSignalLock(self.pers_info_widgets + [self.tx_pc_name]):

            if not self.pc:
                self.create_new_character()

            if self.pc.load_from(path):
                self.save_path = path

                if not api.character.books.fulfills_dependencies():
                    # warn about missing dependencies
                    self.warn_about_missing_books()

                    # immediately create a new character
                    self.create_new_character()
                    return False

                log.app.info('successfully loaded character from {0}'.format(self.save_path))

                self.tx_pc_notes.set_content(self.pc.extra_notes)
                self.update_from_model()
            else:
                log.app.error('character load failure')

    def set_clan(self, clan_id):
        """Set UI clan"""

        clan_ = api.data.clans.get(clan_id)
        if clan_:
            self.lb_pc_clan.setText(clan_.name)
        else:
            self.lb_pc_clan.setText(self.tr("No Clan"))

    def set_family(self, family_id):
        """Set UI family"""
        family_ = api.data.families.get(family_id)
        if family_:
            self.lb_pc_family.setText(family_.name)
        else:
            self.lb_pc_family.setText(self.tr("No Family"))

    def set_school(self, school_id):
        """Set UI school"""
        school_ = api.data.schools.get(school_id)
        if school_:
            self.lb_pc_school.setText(school_.name)
        else:
            self.lb_pc_school.setText(self.tr("No School"))

    def set_void_points(self, value):
        if self.void_points.value == value:
            return
        self.void_points.set_value(value)

    def set_flag(self, flag, value):
        rank, points = api.rules.split_decimal(value)
        # set rank
        self.pc_flags_rank[flag].setText(str(rank))
        # set points
        self.pc_flags_points[flag].set_value(int(points * 10))

    def set_honor(self, value):
        self.set_flag(0, value)

    def set_glory(self, value):
        self.set_flag(1, value)

    def set_status(self, value):
        self.set_flag(2, value)

    def set_taint(self, value):
        self.set_flag(3, value)

    def set_infamy(self, value):
        self.set_flag(4, value)

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

    def update_wound_penalties(self):
        WOUND_PENALTIES_NAMES = [
            self.tr("Healthy"),
            self.tr("Nicked"),
            self.tr("Grazed"),
            self.tr("Hurt"),
            self.tr("Injured"),
            self.tr("Crippled"),
            self.tr("Down"),
        ]

        for i in reversed(range(0, 7)):
            if i < 7:
                penalty = api.rules.get_wound_penalties(i)
                text = u"{0} (+{1})".format(WOUND_PENALTIES_NAMES[i], penalty)
            else:
                text = WOUND_PENALTIES_NAMES[i]
            self.wounds[i][0].setText(text)

        # TODO Create a generate mechanism for data-pack defined bonus to penalties.
        # TODO toku bushi school removes some penalties

    def display_health(self):
        settings = L5RCMSettings()
        method = settings.app.health_method
        if method == 'default':
            self.display_health_default()
        elif method == 'wounds':
            self.display_total_wounds()
        else:
            self.display_health_stacked()


    def display_health_default(self):
        wounds_table = api.rules.get_wounds_table()
        if not wounds_table:
            return        
        for i, (i_inc, i_total, i_stacked, i_inc_wounds, i_total_wounds, i_stacked_wounds) in enumerate(wounds_table):
            self.wounds[i][1].setText(str(i_inc))
            self.wounds[i][2].setText(str(i_inc_wounds) if i_inc_wounds else '')


    def display_health_stacked(self):
        wounds_table = api.rules.get_wounds_table()
        if not wounds_table:
            return
        for i, (i_inc, i_total, i_stacked, i_inc_wounds, i_total_wounds, i_stacked_wounds) in enumerate(wounds_table):
            self.wounds[i][1].setText(str(i_total))
            self.wounds[i][2].setText(str(i_total_wounds) if i_total_wounds else '')


    def display_total_wounds(self):
        wounds_table = api.rules.get_wounds_table()
        if not wounds_table:
            return
        for i, (i_inc, i_total, i_stacked, i_inc_wounds, i_total_wounds, i_stacked_wounds) in enumerate(wounds_table):
            self.wounds[i][1].setText(str(i_stacked))
            self.wounds[i][2].setText(str(i_stacked_wounds) if i_stacked_wounds else '')

    def advise_successfull_import(self, count):
        settings = L5RCMSettings()
        if not settings.app.advise_successful_import:
            return
        msgBox = QtWidgets.QMessageBox(self)
        msgBox.setWindowTitle('L5R: CM')
        msgBox.setText(
            self.tr("{0} data pack(s) imported succesfully.").format(count))
        do_not_prompt_again = QtWidgets.QCheckBox(
            self.tr("Do not prompt again"), msgBox)
        # PREVENT MSGBOX TO CLOSE ON CLICK
        do_not_prompt_again.blockSignals(True)
        msgBox.addButton(QtWidgets.QMessageBox.Ok)
        msgBox.addButton(do_not_prompt_again, QtWidgets.QMessageBox.ActionRole)
        msgBox.setDefaultButton(QtWidgets.QMessageBox.Ok)
        msgBox.setIcon(QtWidgets.QMessageBox.Information)
        msgBox.exec_()
        if do_not_prompt_again.checkState() == QtCore.Qt.Checked:
            settings.app.advise_successful_import = False

    def advise_error(self, message, dtl=None):
        msgBox = QtWidgets.QMessageBox(self)
        msgBox.setWindowTitle('L5R: CM')
        msgBox.setTextFormat(QtCore.Qt.RichText)
        msgBox.setText(message)
        if dtl:
            msgBox.setInformativeText(dtl)
        msgBox.setIcon(QtWidgets.QMessageBox.Critical)
        msgBox.setDefaultButton(QtWidgets.QMessageBox.Ok)
        msgBox.exec_()

    def advise_warning(self, message, dtl=None):
        msgBox = QtWidgets.QMessageBox(self)
        msgBox.setTextFormat(QtCore.Qt.RichText)
        msgBox.setWindowTitle('L5R: CM')
        msgBox.setText(message)
        if dtl:
            msgBox.setInformativeText(dtl)
        msgBox.setIcon(QtWidgets.QMessageBox.Warning)
        msgBox.setDefaultButton(QtWidgets.QMessageBox.Ok)
        msgBox.exec_()

    def ask_warning(self, message, dtl=None):
        msgBox = QtWidgets.QMessageBox(self)
        msgBox.setTextFormat(QtCore.Qt.RichText)
        msgBox.setWindowTitle('L5R: CM')
        msgBox.setText(message)
        if dtl:
            msgBox.setInformativeText(dtl)
        msgBox.setIcon(QtWidgets.QMessageBox.Warning)
        msgBox.addButton(QtWidgets.QMessageBox.Ok)
        msgBox.addButton(QtWidgets.QMessageBox.Cancel)
        msgBox.setDefaultButton(QtWidgets.QMessageBox.Cancel)
        return msgBox.exec_() == QtWidgets.QMessageBox.Ok

    def ask_to_save(self):
        msgBox = QtWidgets.QMessageBox(self)
        msgBox.setWindowTitle('L5R: CM')
        msgBox.setText(self.tr("The character has been modified."))
        msgBox.setInformativeText(self.tr("Do you want to save your changes?"))
        msgBox.addButton(QtWidgets.QMessageBox.Save)
        msgBox.addButton(QtWidgets.QMessageBox.Discard)
        msgBox.addButton(QtWidgets.QMessageBox.Cancel)
        msgBox.setDefaultButton(QtWidgets.QMessageBox.Save)
        return msgBox.exec_()

    def ask_to_upgrade(self, target_version):
        msgBox = QtWidgets.QMessageBox(self)
        msgBox.setWindowTitle('L5R: CM')
        msgBox.setText(
            self.tr("L5R: CM v%s is available for download.") % target_version)
        msgBox.setInformativeText(
            self.tr("Do you want to open the download page?"))
        msgBox.addButton(QtWidgets.QMessageBox.Yes)
        msgBox.addButton(QtWidgets.QMessageBox.No)
        msgBox.setDefaultButton(QtWidgets.QMessageBox.No)
        return msgBox.exec_()

    def not_enough_xp_advise(self, parent=None):
        if parent is None:
            parent = self
        QtWidgets.QMessageBox.warning(parent, self.tr("Not enough XP"),
                                  self.tr("Cannot purchase.\nYou've reached the XP Limit."))
        return

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

    def select_save_path(self):
        settings = L5RCMSettings()
        last_dir = settings.app.last_open_dir
        char_name = self.get_character_full_name()
        proposed = os.path.join(last_dir, char_name)

        fileName = QtWidgets.QFileDialog.getSaveFileName(
            self,
            self.tr("Save Character"),
            proposed,
            self.tr("L5R Character files (*.l5r)"))

        # user pressed cancel or didn't enter a name
        if not fileName:
            return None

        # on pyqt5 it returns a tuple (fname, filter)
        if type(fileName) is tuple:
            fileName = fileName[0]

        if fileName:
            settings.app.last_open_dir = os.path.dirname(fileName)

        if fileName.endswith('.l5r'):
            return fileName
        return fileName + '.l5r'

    def select_load_path(self):
        settings = L5RCMSettings()
        last_dir = settings.app.last_open_dir
        fileName = QtWidgets.QFileDialog.getOpenFileName(
            self,
            self.tr("Load Character"),
            last_dir,
            self.tr("L5R Character files (*.l5r)"))

        # user pressed cancel or didn't enter a name
        if not fileName:
            return None

        # on pyqt5 it returns a tuple (fname, filter)
        if type(fileName) is tuple:
            fileName = fileName[0]

        if fileName:
            settings.app.last_open_dir = os.path.dirname(fileName)
        return fileName

    def select_export_file(self, file_ext='.txt'):
        supported_ext = ['.pdf']
        supported_filters = [self.tr("PDF Files(*.pdf)")]

        settings = L5RCMSettings()
        last_dir = settings.app.last_open_dir
        char_name = self.get_character_full_name()
        proposed = os.path.join(last_dir, char_name)

        fileName = QtWidgets.QFileDialog.getSaveFileName(
            self,
            self.tr("Export Character"),
            proposed,
            ";;".join(supported_filters))

        # user pressed cancel or didn't enter a name
        if not fileName:
            return None

        # on pyqt5 it returns a tuple (fname, filter)
        if type(fileName) is tuple:
            fileName = fileName[0]

        if fileName:
            settings.app.last_open_dir = os.path.dirname(fileName)

        if fileName.endswith(file_ext):
            return fileName
        return fileName + file_ext

    def select_import_data_pack(self):
        supported_ext = ['.zip', '.l5rcmpack']
        supported_filters = [self.tr("L5R:CM Data Pack(*.l5rcmpack *.zip)"),
                             self.tr("Zip Archive(*.zip)")]

        settings = L5RCMSettings()
        last_data_dir = settings.app.last_open_data_dir

        files = QtWidgets.QFileDialog.getOpenFileNames(
            self,
            self.tr("Load data pack"),
            last_data_dir,
            ";;".join(supported_filters))

        if type(files) is tuple:
            files = files[0]

        if not files:
            return None

        if files[0]:
            settings.app.last_open_data_dir = os.path.dirname(files[0])

        return files

    def on_change_insight_calculation(self):
        method = self.sender().checkedAction().property('method')
        api.character.set_insight_calculation_method(method)
        self.update_from_model()

    def on_change_health_visualization(self):
        method = self.sender().checkedAction().property('method')
        settings = L5RCMSettings()
        settings.app.health_method = method
        self.update_from_model()

    def create_new_character(self):
        self.sink1.new_character()
        self.pc.unsaved = False

    def get_health_rank(self, idx):
        return self.wounds[idx][1].text()

    def warn_about_missing_books(self):

        text = self.tr("<h3>Missing books</h3>")
        text += self.tr("<p>To load this character you need this additional books:</p>")
        dtl_text = u"<ul>"
        for b in api.character.books.get_missing_dependencies():
            dtl_text += "<li>{book_nm} &gt;= {book_ver}</li>".format(
                book_nm=b.name, book_ver=b.version)
        dtl_text += u"</ul>"

        self.advise_error(text, dtl_text)


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

        log.app.info(u"START")

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
