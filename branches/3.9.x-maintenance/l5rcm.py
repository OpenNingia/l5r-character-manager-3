# -*- coding: iso-8859-1 -*-
# Copyright (C) 2011 Daniele Simonetti
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

import sys
import os

import rules
import models
import widgets
import dialogs
import autoupdate
import sinks
import dal
import dal.query
import mimetypes

from PySide import QtGui, QtCore
#from models.chmodel import models.ATTRIBS

from l5rcmcore import *

def new_small_le(parent = None, ro = True):
    le = QtGui.QLineEdit(parent)
    le.setSizePolicy( QtGui.QSizePolicy.Maximum,
                      QtGui.QSizePolicy.Maximum )
    le.setMaximumSize( QtCore.QSize(32, 24) )
    le.setReadOnly(ro)
    return le

def new_horiz_line(parent = None):
    line = QtGui.QFrame(parent)
    line.setObjectName("hline")
    line.setGeometry(QtCore.QRect(3, 3, 3, 3))
    line.setFrameShape(QtGui.QFrame.Shape.HLine)
    line.setFrameShadow(QtGui.QFrame.Sunken)
    line.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed)
    return line

def new_vert_line(parent = None):
    line = QtGui.QFrame(parent)
    line.setObjectName("vline")
    line.setGeometry(QtCore.QRect(320, 150, 118, 3))
    line.setFrameShape(QtGui.QFrame.Shape.VLine)
    line.setFrameShadow(QtGui.QFrame.Sunken)
    return line

def new_item_groupbox(name, widget):
    grp  = QtGui.QGroupBox(name, widget.parent())
    vbox = QtGui.QVBoxLayout(grp)
    vbox.addWidget(widget)
    return grp

def new_small_plus_bt(parent = None):
    bt = QtGui.QToolButton(parent)
    bt.setAutoRaise(True)
    bt.setText('+')
    bt.setIcon( QtGui.QIcon.fromTheme('gtk-add', QtGui.QIcon( get_icon_path('add', (16,16)))) )
    bt.setMaximumSize(16,16)
    bt.setMinimumSize(16,16)
    bt.setToolButtonStyle(QtCore.Qt.ToolButtonFollowStyle)
    return bt

def pause_signals(wdgs):
    for w in wdgs: w.blockSignals(True)

def resume_signals(wdgs):
    for w in wdgs: w.blockSignals(False)

class ZoomableView(QtGui.QGraphicsView):
    '''A QGraphicsView that zoom on CTRL+MouseWheel'''

    def __init__(self, parent = None):
        super(ZoomableView, self).__init__(parent)
        self.wp   = None

    def wheelEvent(self, ev):
        if ( ev.modifiers() & QtCore.Qt.ControlModifier ):
            factor = pow(1.16, ev.delta() / 240.0)
            self.scale(factor, factor)
        else:
            super(ZoomableView, self).wheelEvent(ev)

    def keyPressEvent(self, ev):
        super(ZoomableView, self).keyPressEvent(ev)
        if ( ev.modifiers() & QtCore.Qt.ControlModifier ):
            if ( ev.key() == QtCore.Qt.Key_0 ):
                self.resetTransform()
            elif ( ev.key() == QtCore.Qt.Key_Minus ):
                self.scale(0.80, 0.80)
            elif ( ev.key() == QtCore.Qt.Key_Plus ):
                self.scale(1.20, 1.20)

    def set_wallpaper(self, image):
        self.wp = image
        self.viewport().update()

    def drawBackground(self, painter, rect):
        super(ZoomableView, self).drawBackground(painter, rect)

        def zoom_image():
            sx, sy = 0, 0
            tx, ty = rect.x(), rect.y()
            sh, sw = self.wp.height(), self.wp.width()

            if self.wp.width() > rect.width():
                sx = (self.wp.width() - rect.width()) / 2
                sw -= sx*2
            else:
                tx += (rect.width() - self.wp.width()) / 2

            if self.wp.height() > rect.height():
                sy = (self.wp.height() - rect.height()) / 2
                sh -= sy*2
            else:
                ty += (rect.height() - self.wp.height()) / 2

            return QtCore.QRectF(sx, sy, sw, sh), QtCore.QPointF(tx, ty)

        if self.wp:
            source_rect, target_point = zoom_image()

            painter.drawImage( target_point, self.wp, source_rect )

class L5RMain(L5RCMCore):

    default_size       = QtCore.QSize(820, 720)
    default_point_size = 8.25
    num_tabs           = 10

    def __init__(self, locale = None, parent = None):
        super(L5RMain, self).__init__(locale, parent)

        # character file save path
        self.save_path = ''

        # slot sinks
        self.sink1 = sinks.Sink1(self) # Menu Sink
        self.sink2 = sinks.Sink2(self) # MeritFlaw Sink
        self.sink3 = sinks.Sink3(self) # Weapons Sink
        self.sink4 = sinks.Sink4(self) # Weapons Sink

        # Build interface and menus
        self.build_ui()
        self.build_menu()

        # Build page 1
        self.build_ui_page_1 ()
        self.build_ui_page_2 ()
        self.build_ui_page_3 ()
        self.build_ui_page_4 ()
        self.build_ui_page_5 ()
        self.build_ui_page_6 ()
        self.build_ui_page_7 ()
        self.build_ui_page_8 ()
        self.build_ui_page_9 ()
        self.build_ui_page_10()
        self.build_ui_page_about()

        self.tabs.setIconSize(QtCore.QSize(24,24))
        tabs_icons = ['samurai', 'music', 'burn', 'powers', 'userinfo', 'book', 'katana', 'disk', 'text', 'bag']
        for i in xrange(0, self.num_tabs):
            self.tabs.setTabIcon(i, QtGui.QIcon(get_tab_icon(tabs_icons[i])))
            self.tabs.setTabText(i, '')

        # about = app_icon
        self.tabs.setTabIcon(self.num_tabs, QtGui.QIcon(get_app_icon_path()))
        self.tabs.setTabText(self.num_tabs, '')

        # donate button
        self.setup_donate_button()

        self.connect_signals()

    def build_ui(self):
        # Main interface widgets
        self.view = ZoomableView(self)
        settings = QtCore.QSettings()

        #Set Background Color        
        lBackgroundColor = settings.value('backgroundcolor')
        color = QtGui.QColor()
        if(lBackgroundColor is not None):
            color = QtGui.QColor(lBackgroundColor)
        if(not color.isValid()):
            color = QtGui.QColor('#000000')
        self.view.setStyleSheet("background-color:%s;" % color.name())

        self.widgets = QtGui.QFrame()
        self.widgets.setFrameShape( QtGui.QFrame.StyledPanel )
        self.widgets.setLineWidth ( 1 )
        self.tabs = QtGui.QTabWidget(self)
        self.scene = QtGui.QGraphicsScene(self)
        proxy_widget = self.scene.addWidget(self.widgets, QtCore.Qt.Widget)
        proxy_widget.setOpacity(float(settings.value('opacity', 0.96)))
        self.view.setScene(self.scene)
        self.view.setInteractive(True)
        self.setCentralWidget(self.view)
        self.nicebar = None
        mvbox = QtGui.QVBoxLayout(self.widgets)
        logo = QtGui.QLabel(self)

        #Set Banner
        lIsBannerEnabled = settings.value('isbannerenabled')
        if(lIsBannerEnabled) is None:
            lIsBannerEnabled = 1
        settings.setValue('isbannerenabled', lIsBannerEnabled)
        logo.setScaledContents(True)
        logo.setPixmap( QtGui.QPixmap( get_app_file('banner.png') ) )
        logo.setObjectName('BANNER')
        if(lIsBannerEnabled == 0):
            logo.hide()
        mvbox.addWidget(logo)


        mvbox.addWidget(self.tabs)
        self.mvbox = mvbox

        # LOAD SETTINGS
        geo = settings.value('geometry')

        if geo is not None:
            self.restoreGeometry(geo)
        else:
            self.reset_geometry()

        self.ic_idx = int(settings.value('insight_calculation', 1))-1
        ic_calcs    = [rules.insight_calculation_1,
                       rules.insight_calculation_2,
                       rules.insight_calculation_3]
        if self.ic_idx not in range(0, 3):
            self.ic_idx = 0
        self.ic_calc_method = ic_calcs[self.ic_idx]

        self.update_background_image()

    def update_background_image(self):
        settings   = QtCore.QSettings()
        wallpaper_ = settings.value('background_image', '')
        if os.path.exists( wallpaper_ ):
            self.view.set_wallpaper( QtGui.QImage( wallpaper_ ) )

    def reset_geometry(self):
        self.setGeometry( QtCore.QRect(100, 100, 820, 720) )

    def reset_layout_geometry(self):
        self.mvbox.setGeometry( QtCore.QRect(1, 1, 727, 573) )

    def build_ui_page_1(self):

        mfr = QtGui.QFrame(self)
        self.tabs.addTab(mfr, self.tr("Character"))

        mvbox = QtGui.QVBoxLayout(mfr)
        mvbox.setContentsMargins(0,0,0,0)

        def add_pc_info(row, col):
            fr_pc_info   = QtGui.QFrame(self)
            fr_pc_info.setSizePolicy(QtGui.QSizePolicy.Preferred,
                                    QtGui.QSizePolicy.Maximum)

            grid = QtGui.QGridLayout(fr_pc_info)
            self.tx_pc_name   = QtGui.QLineEdit(self)
            self.tx_pc_rank   = QtGui.QLineEdit(self)
            self.cb_pc_clan   = QtGui.QComboBox(self)
            self.cb_pc_family = QtGui.QComboBox(self)
            self.cb_pc_school = QtGui.QComboBox(self)
            self.tx_pc_exp    = QtGui.QLineEdit(self)
            self.tx_pc_ins    = QtGui.QLineEdit(self)

            # 1st column
            fr_school = QtGui.QFrame(self)
            hb_school = QtGui.QHBoxLayout(fr_school)
            hb_school.setContentsMargins(0,0,0,0)
            lb_school = QtGui.QLabel(self.tr("School"), self)
            bt_lock   = QtGui.QToolButton( self )
            bt_lock.setCheckable(True)
            bt_lock.setToolTip(self.tr("Toggle show schools from all the clans"))
            bt_lock.setAutoRaise(True)
            bt_lock.setIcon( QtGui.QIcon(get_icon_path('lock_close',(16,16))) )
            hb_school.addWidget(lb_school)
            hb_school.addWidget(bt_lock)

            # Place "generate random name" near the Name label
            lb_name            = QtGui.QLabel(self.tr("Name"), self)
            bt_generate_male   = QtGui.QToolButton( self )
            bt_generate_male.setIcon( QtGui.QIcon(get_icon_path('male',(16,16))) )
            bt_generate_female = QtGui.QToolButton( self )
            bt_generate_female.setIcon( QtGui.QIcon(get_icon_path('female',(16,16))) )
            bt_generate_male  .setAutoRaise(True)
            bt_generate_male  .setToolTip  (self.tr("Random male name"))
            bt_generate_female.setAutoRaise(True)
            bt_generate_female.setToolTip  (self.tr("Random female name"))
            hb_name = QtGui.QHBoxLayout()
            hb_name.addWidget(lb_name)
            hb_name.addWidget(bt_generate_male)
            hb_name.addWidget(bt_generate_female)

            # gender tag, connect signals
            bt_generate_male  .setProperty('gender', 'male')
            bt_generate_female.setProperty('gender', 'female')
            bt_generate_male  .clicked.connect( self.sink1.generate_name )
            bt_generate_female.clicked.connect( self.sink1.generate_name )

            #grid.addWidget( QtGui.QLabel(self.tr("Name"  ), self), 0, 0 )
            grid.addLayout( hb_name, 0, 0 )
            grid.addWidget( QtGui.QLabel(self.tr("Clan"  ), self), 1, 0 )
            grid.addWidget( QtGui.QLabel(self.tr("Family"), self), 2, 0 )
            grid.addWidget( fr_school, 3, 0 )

            self.bt_school_lock          = bt_lock

            # 3rd column
            grid.addWidget( QtGui.QLabel(self.tr("Rank")       , self), 0, 3 )
            grid.addWidget( QtGui.QLabel(self.tr("Exp. Points"), self), 1, 3 )
            grid.addWidget( QtGui.QLabel(self.tr("Insight")    , self), 2, 3 )

            # 2nd column
            grid.addWidget( self.tx_pc_name, 0, 1, 1, 2  )
            grid.addWidget( self.cb_pc_clan, 1, 1 , 1, 2 )
            grid.addWidget( self.cb_pc_family, 2, 1, 1, 2)
            grid.addWidget( self.cb_pc_school, 3, 1, 1, 2)

            # 4th column
            grid.addWidget( self.tx_pc_rank, 0, 4, 1, 2)
            grid.addWidget( self.tx_pc_exp, 1, 4, 1, 2 )
            grid.addWidget( self.tx_pc_ins, 2, 4, 1, 2 )

            self.tx_pc_rank.setReadOnly(True)
            self.tx_pc_exp.setReadOnly(True)
            self.tx_pc_ins.setReadOnly(True)

            fr_pc_info.setLayout(grid)
            mvbox.addWidget(fr_pc_info)

        def build_trait_frame():
            fr = QtGui.QFrame(self)
            fr.setSizePolicy(QtGui.QSizePolicy.Preferred,
                            QtGui.QSizePolicy.Maximum)
            hbox = QtGui.QHBoxLayout(fr)
            grp = QtGui.QGroupBox(self.tr("Rings and Attributes"), self)
            grid = QtGui.QGridLayout(grp)
            grid.setSpacing(1)

            # rings
            rings = []
            rings.append( ( self.tr("Earth"), new_small_le(self) ) )
            rings.append( ( self.tr("Air"  ), new_small_le(self) ) )
            rings.append( ( self.tr("Water"), new_small_le(self) ) )
            rings.append( ( self.tr("Fire" ), new_small_le(self) ) )
            rings.append( ( self.tr("Void" ), new_small_le(self) ) )

            # keep reference to the rings
            self.rings = rings

            for i in xrange(0, 4):
                grid.addWidget( QtGui.QLabel( rings[i][0] ), i, 0 )
                grid.addWidget( rings[i][1], i, 1 )

            # void ring with plus button
            void_fr   = QtGui.QFrame(self)
            void_hbox = QtGui.QHBoxLayout(void_fr)
            void_hbox.setContentsMargins(0,0,0,0)
            void_bt  = new_small_plus_bt(self)
            void_hbox.addWidget(rings[4][1])
            void_hbox.addWidget(void_bt)
            void_bt.clicked.connect(self.on_void_increase)
            grid.addWidget( QtGui.QLabel( rings[4][0] ), 4, 0 )
            grid.addWidget( void_fr, 4, 1 )

            attribs = []
            # Earth ring
            attribs.append( (self.tr("Stamina"  ), new_small_le(self)) )
            attribs.append( (self.tr("Willpower"), new_small_le(self)) )
            attribs[0][1].setProperty('attrib_id', models.ATTRIBS.STAMINA)
            attribs[1][1].setProperty('attrib_id', models.ATTRIBS.WILLPOWER)
            # Air ring
            attribs.append( (self.tr("Reflexes" ), new_small_le(self)) )
            attribs.append( (self.tr("Awareness"), new_small_le(self)) )
            attribs[2][1].setProperty('attrib_id', models.ATTRIBS.REFLEXES)
            attribs[3][1].setProperty('attrib_id', models.ATTRIBS.AWARENESS)
            # Water ring
            attribs.append( (self.tr("Strength"  ), new_small_le(self)) )
            attribs.append( (self.tr("Perception"), new_small_le(self)) )
            attribs[4][1].setProperty('attrib_id', models.ATTRIBS.STRENGTH)
            attribs[5][1].setProperty('attrib_id', models.ATTRIBS.PERCEPTION)
            # Fire ring
            attribs.append( (self.tr("Agility"     ), new_small_le(self)) )
            attribs.append( (self.tr("Intelligence"), new_small_le(self)) )
            attribs[6][1].setProperty('attrib_id', models.ATTRIBS.AGILITY)
            attribs[7][1].setProperty('attrib_id', models.ATTRIBS.INTELLIGENCE)

            self.attribs = attribs

            # map increase trait signals
            self.trait_sig_mapper = QtCore.QSignalMapper(self)

            def _attrib_frame(i):
                fr   = QtGui.QFrame(self)
                hbox = QtGui.QHBoxLayout(fr)
                hbox.setContentsMargins(3,0,9,0)
                # small plus button
                tag = str(attribs[i][1].property('attrib_id'))
                bt  = new_small_plus_bt(self)
                hbox.addWidget( attribs[i][1] )
                hbox.addWidget( bt )
                self.trait_sig_mapper.setMapping(bt, tag)
                bt.connect(QtCore.SIGNAL("clicked()"), self.trait_sig_mapper, QtCore.SLOT("map()"))
                return fr

            for i in xrange(0, 8, 2):
                grid.addWidget( QtGui.QLabel( attribs[i][0] ),
                                (i//2) , 2, 1, 1, QtCore.Qt.AlignLeft )
                grid.addWidget( _attrib_frame(i), (i//2), 3, 1, 1,
                                QtCore.Qt.AlignLeft )

                grid.addWidget( QtGui.QLabel( attribs[i+1][0] ),
                                (i//2), 4, 1, 1, QtCore.Qt.AlignLeft )
                grid.addWidget( _attrib_frame(i+1), (i//2), 5, 1, 1,
                                QtCore.Qt.AlignLeft )
            grid.addWidget( QtGui.QLabel(self.tr("<b>Void Points</b>")),
                            4, 2, 1, 3,
                            QtCore.Qt.AlignHCenter )

            self.void_points = widgets.CkNumWidget(count=10, parent=self)
            grid.addWidget( self.void_points, 5, 2, 1, 3,
                            QtCore.Qt.AlignHCenter)

            hbox.addWidget(grp)

            return fr

        def build_flags_frame():
            tx_flags = [self.tr("Honor" ), self.tr("Glory"           ),
                        self.tr("Status"), self.tr("Shadowland Taint"),
                        self.tr("Infamy"           )]

            ob_flags_p = []
            ob_flags_r = []
            fr = QtGui.QFrame(self)
            #fr.setFrameShape(QtGui.QFrame.StyledPanel)
            vbox = QtGui.QVBoxLayout(fr)
            vbox.setContentsMargins(0,0,0,0)
            vbox.setSpacing(0)
            row = 1
            for f in tx_flags:
                fr_ = QtGui.QFrame(self)
                lay = QtGui.QGridLayout(fr_)
                lay.setContentsMargins(0,0,0,0)
                lay.setSpacing(0)
                lay.addWidget(QtGui.QLabel('<b>%s</b>' % f), row, 0)
                l = new_small_le(self, False)
                lay.addWidget(l, row, 1)
                w = widgets.CkNumWidget(count=9, parent=self)
                lay.addWidget(w, row+1, 0, 1, 2, QtCore.Qt.AlignHCenter)
                ob_flags_p.append(w)
                ob_flags_r.append(l)
                vbox.addWidget(fr_)
            self.pc_flags_points = ob_flags_p
            self.pc_flags_rank   = ob_flags_r

            return fr

        def add_traits_and_flags():
            trait_frame = build_trait_frame()
            flags_frame = build_flags_frame()

            fr   = QtGui.QFrame(self)
            hbox = QtGui.QHBoxLayout(fr)

            fr.setSizePolicy(QtGui.QSizePolicy.Expanding,
                            QtGui.QSizePolicy.Maximum)

            hbox.addWidget(trait_frame)
            hbox.addWidget(flags_frame)

            mvbox.addWidget(fr)

        def add_pc_quantities(row, col):
            fr = QtGui.QFrame(self)
            fr.setSizePolicy(QtGui.QSizePolicy.Expanding,
                            QtGui.QSizePolicy.Maximum)
            hbox = QtGui.QHBoxLayout(fr)

            monos_ = QtGui.QFont('Monospace')
            monos_.setStyleHint( QtGui.QFont.Courier )

            # fr.setFont(monos_)

            # initiative
            grp  = QtGui.QGroupBox(self.tr("Initiative"), self)
            #grp.setSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Maximum)
            grd  = QtGui.QFormLayout(grp)

            self.tx_base_init = QtGui.QLineEdit(self)
            self.tx_mod_init  = QtGui.QLineEdit(self)
            self.tx_cur_init  = QtGui.QLineEdit(self)

            self.tx_base_init.setReadOnly(True)
            self.tx_mod_init .setReadOnly(True)
            self.tx_cur_init .setReadOnly(True)

            grd.addRow( self.tr("Base"    ), self.tx_base_init)
            grd.addRow( self.tr("Modifier"), self.tx_mod_init)
            grd.addRow( self.tr("Current" ), self.tx_cur_init)

            hbox.addWidget(grp, 1)

            # Armor TN
            grp = QtGui.QGroupBox(self.tr("Armor TN"), self)
            #grp.setSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Maximum)
            grd  = QtGui.QFormLayout(grp)

            self.tx_armor_nm = QtGui.QLineEdit(self)
            self.tx_base_tn  = QtGui.QLineEdit(self)
            self.tx_armor_tn = QtGui.QLineEdit(self)
            self.tx_armor_rd = QtGui.QLineEdit(self)
            self.tx_cur_tn   = QtGui.QLineEdit(self)

            self.tx_armor_nm.setReadOnly(True)
            self.tx_base_tn .setReadOnly(True)
            self.tx_armor_tn.setReadOnly(True)
            self.tx_armor_rd.setReadOnly(True)
            self.tx_cur_tn  .setReadOnly(True)

            grd.addRow( self.tr("Name"     ), self.tx_armor_nm)
            grd.addRow( self.tr("Base"     ), self.tx_base_tn)
            grd.addRow( self.tr("Armor"    ), self.tx_armor_tn)
            grd.addRow( self.tr("Reduction"), self.tx_armor_rd)
            grd.addRow( self.tr("Current"  ), self.tx_cur_tn)

            hbox.addWidget(grp, 1)

            # Wounds
            grp = QtGui.QGroupBox(self.tr("Wounds"), self)
            #grp.setSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Maximum)
            grd  = QtGui.QGridLayout(grp)

            wnd = []
            wnd.append( (QtGui.QLabel(self), new_small_le(self), new_small_le(self)) )
            wnd.append( (QtGui.QLabel(self), new_small_le(self), new_small_le(self)) )
            wnd.append( (QtGui.QLabel(self), new_small_le(self), new_small_le(self)) )
            wnd.append( (QtGui.QLabel(self), new_small_le(self), new_small_le(self)) )
            wnd.append( (QtGui.QLabel(self), new_small_le(self), new_small_le(self)) )
            wnd.append( (QtGui.QLabel(self), new_small_le(self), new_small_le(self)) )
            wnd.append( (QtGui.QLabel(self), new_small_le(self), new_small_le(self)) )
            wnd.append( (QtGui.QLabel(self.tr("Out"), self),
                         new_small_le(self), new_small_le(self)) )

            self.wounds = wnd
            self.wnd_lb = grp

            row_ = 0
            col_ = 0
            for i in xrange(0, len(wnd)):
                if i == 4:
                    col_ = 3
                    row_ = 0

                grd.addWidget( wnd[i][0], row_, col_ )
                grd.addWidget( wnd[i][0], row_, col_ )
                grd.addWidget( wnd[i][1], row_, col_+1 )
                grd.addWidget( wnd[i][2], row_, col_+2 )
                row_ += 1

            hbox.addWidget(grp, 2)

            mvbox.addWidget(fr)

        add_pc_info(0, 0)
        mvbox.addWidget(new_horiz_line(self))
        add_traits_and_flags()
        mvbox.addWidget(new_horiz_line(self))
        add_pc_quantities(4, 0)

    def _build_generic_page(self, models_):
        mfr    = QtGui.QFrame(self)
        vbox   = QtGui.QVBoxLayout(mfr)
        views_ = []

        for k, t, m, d, tb in models_:
            grp    = QtGui.QGroupBox(k, self)
            hbox   = QtGui.QHBoxLayout(grp)
            view   = None
            if t == 'table':
                view  = QtGui.QTableView(self)
                view.setSortingEnabled(True)
                view.horizontalHeader().setResizeMode(QtGui.QHeaderView.Interactive)
                view.horizontalHeader().setStretchLastSection(True)
                view.horizontalHeader().setCascadingSectionResizes(True)
                if d is not None and len(d) == 2:
                    col_ = d[0]
                    obj_ = d[1]
                    view.setItemDelegateForColumn(col_, obj_)
            elif t == 'list':
                view = QtGui.QListView(self)
            view.setModel(m)
            if d is not None:
                view.setItemDelegate(d)

            if tb is not None:
                hbox.addWidget(tb)
            hbox.addWidget(view)
            vbox.addWidget(grp)
            views_.append(view)
        return mfr, views_

    def _build_spell_frame(self, model, layout):
        grp    = QtGui.QGroupBox(self.tr("Spells"), self)
        hbox   = QtGui.QHBoxLayout(grp)

        fr_    = QtGui.QFrame(self)
        vbox   = QtGui.QVBoxLayout(fr_)
        vbox.setContentsMargins(3,3,3,3)

        # advantages/disadvantage vertical toolbar
        def _make_vertical_tb():
            vtb = widgets.VerticalToolBar(self)
            vtb.addStretch()

            cb_buy    = self.act_buy_spell
            cb_remove = self.act_del_spell
            cb_memo   = self.act_memo_spell

            self.add_spell_bt = vtb.addButton(
                                QtGui.QIcon(get_icon_path('buy',(16,16))),
                                self.tr("Add new spell"), cb_buy)

            self.del_spell_bt = vtb.addButton(
                                QtGui.QIcon(get_icon_path('minus',(16,16))),
                                self.tr("Remove spell"), cb_remove)

            self.memo_spell_bt = vtb.addButton(
                                 QtGui.QIcon(get_icon_path('book',(16,16))),
                                 self.tr("Memorize/Forget spell"), cb_memo)


            self.del_spell_bt.setEnabled(False)

            vtb.addStretch()
            return vtb

        # View
        view  = QtGui.QTableView(fr_)
        view.setSizePolicy( QtGui.QSizePolicy.Expanding,
                              QtGui.QSizePolicy.Expanding )
        view.setSortingEnabled(True)
        view.horizontalHeader().setResizeMode(QtGui.QHeaderView.Interactive)
        view.horizontalHeader().setStretchLastSection(True)
        view.horizontalHeader().setCascadingSectionResizes(True)
        view.setModel(model)
        # FIXME: this line segfaults on PySide 1.1.2
        #view.selectionModel().currentRowChanged.connect(self.on_spell_selected)
        sm = view.selectionModel()
        sm.currentRowChanged.connect(self.on_spell_selected)
        self.spell_table_view = view

        # Affinity/Deficiency
        self.lb_affin = QtGui.QLabel(self.tr("None"), self)
        self.lb_defic = QtGui.QLabel(self.tr("None"), self)

        aff_fr = QtGui.QFrame(self)
        aff_fr.setSizePolicy( QtGui.QSizePolicy.Preferred,
                              QtGui.QSizePolicy.Maximum )
        fl     = QtGui.QFormLayout(aff_fr)
        fl.addRow(self.tr("<b><i>Affinity</i></b>"  ), self.lb_affin)
        fl.addRow(self.tr("<b><i>Deficiency</i></b>"), self.lb_defic)
        fl.setHorizontalSpacing(60)
        fl.setVerticalSpacing  ( 5)
        fl.setContentsMargins(0, 0, 0, 0)

        vbox.addWidget(aff_fr)
        vbox.addWidget(view)

        hbox.addWidget(_make_vertical_tb())
        hbox.addWidget(fr_)
        layout.addWidget(grp)

        view.doubleClicked.connect( self.sink4.on_spell_item_activate )

        return view

    def _build_tech_frame(self, model, layout):
        grp    = QtGui.QGroupBox(self.tr("Techs"), self)
        vbox   = QtGui.QVBoxLayout(grp)

        # View
        view  = QtGui.QListView(self)
        view.setModel(model)
        view.setItemDelegate(models.TechItemDelegate(self))
        vbox.addWidget(view)
        layout.addWidget(grp)

        view.doubleClicked.connect( self.sink4.on_tech_item_activate )

        return view

    def _build_kata_frame(self, model, layout):
        grp    = QtGui.QGroupBox(self.tr("Kata"), self)
        hbox   = QtGui.QHBoxLayout(grp)

        fr_    = QtGui.QFrame(self)
        vbox   = QtGui.QVBoxLayout(fr_)
        vbox.setContentsMargins(3,3,3,3)

        # advantages/disadvantage vertical toolbar
        def _make_vertical_tb():
            vtb = widgets.VerticalToolBar(self)
            vtb.addStretch()

            cb_buy    = self.sink2.act_buy_kata
            cb_remove = self.sink2.act_del_kata

            self.add_kata_bt = vtb.addButton(
                                QtGui.QIcon(get_icon_path('buy',(16,16))),
                                self.tr("Add new Kata"), cb_buy)

            self.del_kata_bt  = vtb.addButton(
                                QtGui.QIcon(get_icon_path('minus',(16,16))),
                                self.tr("Remove Kata"), cb_remove)

            self.add_kata_bt.setEnabled(True)
            self.del_kata_bt.setEnabled(True)

            vtb.addStretch()
            return vtb

        # View
        view  = QtGui.QTableView(self)
        view.setSizePolicy( QtGui.QSizePolicy.Expanding,
                              QtGui.QSizePolicy.Expanding )
        view.setSortingEnabled(True)
        view.horizontalHeader().setResizeMode(QtGui.QHeaderView.Interactive)
        view.horizontalHeader().setStretchLastSection(True)
        view.horizontalHeader().setCascadingSectionResizes(True)
        view.setModel(model)
        self.ka_table_view = view

        vbox.addWidget(view)

        hbox.addWidget(_make_vertical_tb())
        hbox.addWidget(fr_)

        layout.addWidget(grp)

        return view

    def _build_kiho_frame(self, model, layout):
        grp    = QtGui.QGroupBox(self.tr("Kiho"), self)
        hbox   = QtGui.QHBoxLayout(grp)

        fr_    = QtGui.QFrame(self)
        vbox   = QtGui.QVBoxLayout(fr_)
        vbox.setContentsMargins(3,3,3,3)

        # advantages/disadvantage vertical toolbar
        def _make_vertical_tb():
            vtb = widgets.VerticalToolBar(self)
            vtb.addStretch()

            cb_buy        = self.sink2.act_buy_kiho
            cb_remove     = self.sink2.act_del_kiho
            cb_buy_tattoo = self.sink2.act_buy_tattoo

            self.add_kiho_bt   = vtb.addButton(
                                QtGui.QIcon(get_icon_path('buy',(16,16))),
                                self.tr("Add new Kiho"), cb_buy)

            self.add_tattoo_bt = vtb.addButton(
                                QtGui.QIcon(get_icon_path('buy',(16,16))),
                                self.tr("Add new Tattoo"), cb_buy_tattoo)

            self.del_kiho_bt   = vtb.addButton(
                                QtGui.QIcon(get_icon_path('minus',(16,16))),
                                self.tr("Remove Kiho"), cb_remove)

            self.add_kiho_bt.setEnabled(True)
            self.del_kiho_bt.setEnabled(True)

            vtb.addStretch()
            return vtb

        # View
        view  = QtGui.QTableView(self)
        view.setSizePolicy( QtGui.QSizePolicy.Expanding,
                              QtGui.QSizePolicy.Expanding )
        view.setSortingEnabled(True)
        view.horizontalHeader().setResizeMode(QtGui.QHeaderView.Interactive)
        view.horizontalHeader().setStretchLastSection(True)
        view.horizontalHeader().setCascadingSectionResizes(True)
        view.setModel(model)
        self.ki_table_view = view

        vbox.addWidget(view)

        hbox.addWidget(_make_vertical_tb())
        hbox.addWidget(fr_)

        layout.addWidget(grp)

        return view

    def build_ui_page_2(self):
        self.sk_view_model = models.SkillTableViewModel(self.dstore, self)
        self.ma_view_model = models.MaViewModel        (self.dstore, self)

        # enable sorting through a proxy model
        sk_sort_model = models.ColorFriendlySortProxyModel(self)
        sk_sort_model.setDynamicSortFilter(True)
        sk_sort_model.setSourceModel(self.sk_view_model)

        # skills vertical toolbar
        vtb = widgets.VerticalToolBar(self)
        vtb.addStretch()
        vtb.addButton(QtGui.QIcon(get_icon_path('add',(16,16))),
                      self.tr("Add skill rank"), self.on_buy_skill_rank)
        vtb.addButton(QtGui.QIcon(get_icon_path('buy',(16,16))),
                      self.tr("Buy skill emphasys"), self.show_buy_emph_dlg)
        vtb.addButton(QtGui.QIcon(get_icon_path('buy',(16,16))),
                      self.tr("Buy another skill"), self.show_buy_skill_dlg)
        vtb.addStretch()

        models_ = [ ("Skills", 'table', sk_sort_model, None, vtb),
                    (self.tr("Mastery Abilities"),  'list', self.ma_view_model,
                    models.MaItemDelegate(self), None) ]

        frame_, views_ = self._build_generic_page(models_)

        if len(views_) > 0:
            self.skill_table_view = views_[0]

        self.tabs.addTab(frame_, self.tr("Skills"))

    def build_ui_page_3(self):
        self.sp_view_model = models.SpellTableViewModel(self.dstore, self)
        self.th_view_model = models.TechViewModel      (self.dstore, self)

        # enable sorting through a proxy model
        sp_sort_model = models.ColorFriendlySortProxyModel(self)
        sp_sort_model.setDynamicSortFilter(True)
        sp_sort_model.setSourceModel(self.sp_view_model)

        frame_ = QtGui.QFrame(self)
        vbox   = QtGui.QVBoxLayout(frame_)

        self._build_spell_frame(sp_sort_model     , vbox)
        self._build_tech_frame (self.th_view_model, vbox)

        self.tabs.addTab(frame_, self.tr("Techniques"))

    def build_ui_page_4(self):
        self.ka_view_model = models.KataTableViewModel(self.dstore, self)
        self.ki_view_model = models.KihoTableViewModel(self.dstore, self)

        # enable sorting through a proxy model
        ka_sort_model = models.ColorFriendlySortProxyModel(self)
        ka_sort_model.setDynamicSortFilter(True)
        ka_sort_model.setSourceModel(self.ka_view_model)

        ki_sort_model = models.ColorFriendlySortProxyModel(self)
        ki_sort_model.setDynamicSortFilter(True)
        ki_sort_model.setSourceModel(self.ki_view_model)

        frame_ = QtGui.QFrame(self)
        vbox   = QtGui.QVBoxLayout(frame_)

        self.kata_view = self._build_kata_frame(ka_sort_model     , vbox)
        self.kiho_view = self._build_kiho_frame(ki_sort_model     , vbox)

        self.tabs.addTab(frame_, self.tr("Powers"))

    def build_ui_page_5(self):
        mfr    = QtGui.QFrame(self)
        vbox   = QtGui.QVBoxLayout(mfr)

        # advantages/disadvantage vertical toolbar
        def _make_vertical_tb(tag, has_edit, has_remove):
            vtb = widgets.VerticalToolBar(self)
            vtb.addStretch()

            cb_buy  = (self.sink2.act_buy_merit if tag == 'merit'
                                        else self.sink2.act_buy_flaw)
            cb_edit = (self.sink2.act_edit_merit if tag == 'merit'
                                        else self.sink2.act_edit_flaw)
            cb_remove = (self.sink2.act_del_merit if tag == 'merit'
                                        else self.sink2.act_del_flaw)

            vtb.addButton(QtGui.QIcon(get_icon_path('buy',(16,16))),
                         self.tr("Add Perk"), cb_buy)

            if has_edit:
                vtb.addButton(QtGui.QIcon(get_icon_path('edit',(16,16))),
                              self.tr("Edit Perk"), cb_edit)

            if has_remove:
                vtb.addButton(QtGui.QIcon(get_icon_path('minus',(16,16))),
                              self.tr("Remove Perk"), cb_remove)

            vtb.addStretch()
            return vtb

        self.merits_view_model = models.PerkViewModel(self.dstore, 'merit')
        self.flaws_view_model  = models.PerkViewModel(self.dstore, 'flaws')

        merit_view = QtGui.QListView(self)
        merit_view.setModel(self.merits_view_model)
        merit_view.setItemDelegate(models.PerkItemDelegate(self))
        merit_vtb  = _make_vertical_tb('merit', True, True)
        fr_        = QtGui.QFrame(self)
        hb_        = QtGui.QHBoxLayout(fr_)
        hb_.setContentsMargins(3,3,3,3)
        hb_.addWidget(merit_vtb)
        hb_.addWidget(merit_view)
        vbox.addWidget(new_item_groupbox(self.tr("Advantages"), fr_))

        flaw_view = QtGui.QListView(self)
        flaw_view.setModel(self.flaws_view_model)
        flaw_view.setItemDelegate(models.PerkItemDelegate(self))
        flaw_vtb  = _make_vertical_tb('flaw', True, True)
        fr_        = QtGui.QFrame(self)
        hb_        = QtGui.QHBoxLayout(fr_)
        hb_.setContentsMargins(3,3,3,3)
        hb_.addWidget(flaw_vtb)
        hb_.addWidget(flaw_view)
        vbox.addWidget(new_item_groupbox(self.tr("Disadvantages"), fr_))

        self.merit_view = merit_view
        self.flaw_view  = flaw_view

        self.tabs.addTab(mfr, self.tr("Perks"))

    def build_ui_page_6(self):
        mfr    = QtGui.QFrame(self)
        vbox   = QtGui.QVBoxLayout(mfr)

        fr_    = QtGui.QFrame(self)
        fr_h   = QtGui.QHBoxLayout(fr_)
        fr_h.setContentsMargins(0, 0, 0, 0)
        fr_h.addWidget(QtGui.QLabel(self.tr("""<p><i>Select the advancement to refund and hit the button</i></p>"""), self))
        bt_refund_adv = QtGui.QPushButton(self.tr("Refund"), self)
        bt_refund_adv.setSizePolicy( QtGui.QSizePolicy.Maximum,
                                     QtGui.QSizePolicy.Preferred )
        bt_refund_adv.clicked.connect(self.sink1.refund_advancement)
        fr_h.addWidget(bt_refund_adv)
        vbox.addWidget(fr_)

        self.adv_view_model = models.AdvancementViewModel(self)
        lview = QtGui.QListView(self)
        lview.setModel(self.adv_view_model)
        lview.setItemDelegate(models.AdvancementItemDelegate(self))
        vbox.addWidget(lview)

        self.adv_view = lview

        self.tabs.addTab(mfr, self.tr("Advancements"))

    def build_ui_page_7(self):
        self.melee_view_model  = models.WeaponTableViewModel('melee' , self)
        self.ranged_view_model = models.WeaponTableViewModel('ranged', self)
        self.arrow_view_model  = models.WeaponTableViewModel('arrow' , self)

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
            vtb.addButton(QtGui.QIcon(get_icon_path('buy',(16,16))),
                          self.tr("Add weapon"), self.sink3.show_add_weapon)
            if has_custom:
                vtb.addButton(QtGui.QIcon(get_icon_path('custom',(16,16))),
                              self.tr("Add custom weapon"), self.sink3.show_add_cust_weapon)
            if has_edit:
                vtb.addButton(QtGui.QIcon(get_icon_path('edit',(16,16))),
                              self.tr("Edit weapon"), self.sink3.edit_selected_weapon)
            vtb.addButton(QtGui.QIcon(get_icon_path('minus',(16,16))),
                          self.tr("Remove weapon"), self.sink3.remove_selected_weapon)
            if has_qty:
                vtb.addButton(QtGui.QIcon(get_icon_path('add',(16,16))),
                              self.tr("Increase Quantity"), self.sink3.on_increase_item_qty)
                vtb.addButton(QtGui.QIcon(get_icon_path('minus',(16,16))),
                              self.tr("Decrease Quantity"), self.sink3.on_decrease_item_qty)

            vtb.addStretch()
            return vtb

        melee_vtb  = _make_vertical_tb(True, True, False, 'melee' )
        ranged_vtb = _make_vertical_tb(True, True, False, 'ranged')
        arrow_vtb  = _make_vertical_tb(False, False, True,'arrow' )

        models_ = [ (self.tr("Melee Weapons"), 'table', _make_sortable(self.melee_view_model),
                    None, melee_vtb),
                    (self.tr("Ranged Weapons"), 'table', _make_sortable(self.ranged_view_model),
                    None, ranged_vtb),
                    (self.tr("Arrows"), 'table', _make_sortable(self.arrow_view_model),
                    None, arrow_vtb)]

        frame_, views_ = self._build_generic_page(models_)

        melee_vtb .setProperty('source', views_[0])
        ranged_vtb.setProperty('source', views_[1])
        arrow_vtb .setProperty('source', views_[2])

        self.tabs.addTab(frame_, self.tr("Weapons"))

    def build_ui_page_8(self):
        # modifiers
        self.mods_view_model  = models.ModifiersTableViewModel(self)
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
            vtb.addButton(QtGui.QIcon(get_icon_path('buy',(16,16))),
                          self.tr("Add modifier"), self.sink4.add_new_modifier)
            vtb.addButton(QtGui.QIcon(get_icon_path('edit',(16,16))),
                          self.tr("Edit modifier"), self.sink4.edit_selected_modifier)
            vtb.addButton(QtGui.QIcon(get_icon_path('minus',(16,16))),
                          self.tr("Remove modifier"), self.sink4.remove_selected_modifier)

            vtb.addStretch()
            return vtb

        vtb  = _make_vertical_tb()

        models_ = [ (self.tr("Modifiers"), 'table', _make_sortable(self.mods_view_model),
                    None, vtb) ]

        frame_, views_ = self._build_generic_page(models_)
        self.mod_view = views_[0]

        vtb .setProperty('source', self.mod_view)
        self.tabs.addTab(frame_, self.tr("Modifiers"))

    def build_ui_page_9(self):
        mfr  = QtGui.QFrame(self)
        vbox = QtGui.QVBoxLayout(mfr)
        #vbox.setAlignment(QtCore.Qt.AlignCenter)
        #vbox.setSpacing  (30)

        self.tx_pc_notes = widgets.SimpleRichEditor(self)
        vbox.addWidget(self.tx_pc_notes)

        def build_pers_info():
            grp  = QtGui.QGroupBox(self.tr("Personal Informations"), self)
            grp.setSizePolicy(QtGui.QSizePolicy.Expanding,
                              QtGui.QSizePolicy.Preferred)

            hgrp = QtGui.QHBoxLayout(grp)

            # anagraphic

            afr = QtGui.QFrame(self)
            afl = QtGui.QFormLayout(afr)

            self.tx_pc_sex    = QtGui.QLineEdit(self)
            self.tx_pc_age    = QtGui.QLineEdit(self)
            self.tx_pc_height = QtGui.QLineEdit(self)
            self.tx_pc_weight = QtGui.QLineEdit(self)
            self.tx_pc_hair   = QtGui.QLineEdit(self)
            self.tx_pc_eyes   = QtGui.QLineEdit(self)

            afl.addRow( self.tr("Sex"    ), self.tx_pc_sex   )
            afl.addRow( self.tr("Age"    ), self.tx_pc_age   )
            afl.addRow( self.tr("Height" ), self.tx_pc_height)
            afl.addRow( self.tr("Weight" ), self.tx_pc_weight)
            afl.addRow( self.tr("Hair"   ), self.tx_pc_hair  )
            afl.addRow( self.tr("Eyes"   ), self.tx_pc_eyes  )
            hgrp.addWidget(afr)

            # separator
            hgrp.addWidget(new_vert_line())

            # parents
            bfr = QtGui.QFrame(self)
            bfl = QtGui.QFormLayout(bfr)

            self.tx_pc_father   = QtGui.QLineEdit(self)
            self.tx_pc_mother   = QtGui.QLineEdit(self)
            self.tx_pc_bro      = QtGui.QLineEdit(self)
            self.tx_pc_sis      = QtGui.QLineEdit(self)
            self.tx_pc_marsta   = QtGui.QLineEdit(self)
            self.tx_pc_spouse   = QtGui.QLineEdit(self)
            self.tx_pc_childr   = QtGui.QLineEdit(self)

            bfl.addRow( self.tr("Father"            ), self.tx_pc_father)
            bfl.addRow( self.tr("Mother"            ), self.tx_pc_mother)
            bfl.addRow( self.tr("Brothers"          ), self.tx_pc_bro   )
            bfl.addRow( self.tr("Sisters"           ), self.tx_pc_sis   )
            bfl.addRow( self.tr("Marital Status"    ), self.tx_pc_marsta)
            bfl.addRow( self.tr("Spouse"            ), self.tx_pc_spouse)
            bfl.addRow( self.tr("Children"          ), self.tx_pc_childr)
            hgrp.addWidget(bfr)

            self.pers_info_widgets = [
                         self.tx_pc_sex, self.tx_pc_age,
                         self.tx_pc_height, self.tx_pc_weight,
                         self.tx_pc_hair, self.tx_pc_eyes,
                         self.tx_pc_father, self.tx_pc_mother,
                         self.tx_pc_bro, self.tx_pc_marsta,
                         self.tx_pc_sis, self.tx_pc_spouse, self.tx_pc_childr]

            # link personal information widgets
            self.tx_pc_sex.link    = 'sex'
            self.tx_pc_age.link    = 'age'
            self.tx_pc_height.link = 'height'
            self.tx_pc_weight.link = 'weight'
            self.tx_pc_hair.link   = 'hair'
            self.tx_pc_eyes.link   = 'eyes'
            self.tx_pc_father.link = 'father'
            self.tx_pc_mother.link = 'mother'
            self.tx_pc_bro.link    = 'brothers'
            self.tx_pc_sis.link    = 'sisters'
            self.tx_pc_marsta.link = 'marsta'
            self.tx_pc_spouse.link = 'spouse'
            self.tx_pc_childr.link = 'childr'

            return grp

        vbox.addWidget(build_pers_info())

        self.tabs.addTab(mfr, self.tr("Notes"))

    def build_ui_page_10(self):
        self.equip_view_model  = models.EquipmentListModel(self)
        #self.equip_view_model.user_change.connect(self.update_from_model)

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
            vtb.addButton(QtGui.QIcon(get_icon_path('buy',(16,16))),
                          self.tr("Add equipment"), self.sink4.add_equipment)
            vtb.addButton(QtGui.QIcon(get_icon_path('minus',(16,16))),
                          self.tr("Remove equipment"), self.sink4.remove_selected_equipment)

            vtb.addStretch()
            return vtb

        vtb  = _make_vertical_tb()

        models_ = [ (self.tr("Equipment"), 'list', _make_sortable(self.equip_view_model),
                    None, vtb) ]

        frame_, views_ = self._build_generic_page(models_)
        self.equip_view = views_[0]

        font = self.equip_view.font()
        font.setPointSize(11.5)
        self.equip_view.setFont(font)

        self.money_widget = widgets.MoneyWidget(self)
        frame_.layout().setSpacing(12)
        frame_.layout().addWidget(new_horiz_line(self))
        frame_.layout().addWidget(self.money_widget)
        self.money_widget.valueChanged.connect(self.sink4.on_money_value_changed)

        #self.equip_view.setItemDelegate(models.EquipmentDelegate(self.dstore, self))
        vtb .setProperty('source', self.equip_view)
        self.tabs.addTab(frame_ , self.tr("Equipment"))

    def build_ui_page_about(self):
        mfr    = QtGui.QFrame(self)
        #bfr    = QtGui.QFrame(self)

        #hbox   = QtGui.QHBoxLayout(mfr)
        hbox   = QtGui.QHBoxLayout()
        hbox.setAlignment(QtCore.Qt.AlignCenter)
        #hbox.setMargin   (30)
        hbox.setSpacing  (30)

        logo = QtGui.QLabel(self)
        logo.setPixmap(QtGui.QPixmap(get_app_icon_path((64,64))))
        hbox.addWidget(logo, 0, QtCore.Qt.AlignTop)

        vbox = QtGui.QVBoxLayout(mfr)
        vbox.setAlignment(QtCore.Qt.AlignCenter)
        vbox.setSpacing  (30)

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
                  <p style='color:palette(mid)'>&copy; 2011 %s</p>
                  <p>Special Thanks:</p>
                  <p style="margin-left: 10;">
                  Paul Tar, Jr aka Geiko (Lots of cool stuff)</p>
                  <p style="margin-left: 10;">Derrick D. Cochran (OS X Distro)
                  </p>
                  </body></html>""" % ( APP_DESC,
                                        QtGui.QApplication.applicationVersion(),
                                        PROJECT_PAGE_LINK, PROJECT_PAGE_NAME,
                                        BUGTRAQ_LINK, L5R_RPG_HOME_PAGE,
                                        ALDERAC_HOME_PAGE, AUTHOR_NAME)
        lb_info = QtGui.QLabel(info, self)
        lb_info.setOpenExternalLinks(True)
        lb_info.setWordWrap(True)
        hbox.addWidget(lb_info)

        def on_contact_link_activate():
            url = QtCore.QUrl(L5RCM_GPLUS_PAGE)
            QtGui.QDesktopServices.openUrl(url)

        def on_community_link_activate():
            url = QtCore.QUrl(L5RCM_GPLUS_COMM)
            QtGui.QDesktopServices.openUrl(url)

        bt_contact_gplus = QtGui.QCommandLinkButton("Contact me", "but bring good news", self)
        bt_contact_gplus.setIcon(
            QtGui.QIcon(get_icon_path('new-g-plus-icon',(16, 16))))
        #bt_contact_gplus.setFlat(True)
        bt_contact_gplus.clicked.connect( on_contact_link_activate )

        bt_community_gplus = QtGui.QCommandLinkButton("Join the G+ Community", "for answers and support", self)
        bt_community_gplus.setIcon(
            QtGui.QIcon(get_icon_path('new-g-plus-icon',(16, 16))))
        #bt_community_gplus.setFlat(True)
        bt_community_gplus.clicked.connect( on_community_link_activate )

        gplus_form = QtGui.QVBoxLayout()
        gplus_form.addWidget(bt_contact_gplus  )
        gplus_form.addWidget(bt_community_gplus)

        #gplus_form.setLabelAlignment(QtCore.Qt.AlignRight)
        gplus_form.setSpacing(6)

        gplus_hbox = QtGui.QHBoxLayout()
        gplus_hbox.setContentsMargins(0,0,50,0)
        gplus_hbox.addStretch()
        gplus_hbox.addLayout(gplus_form)

        vbox.addLayout(hbox)
        vbox.addLayout(gplus_hbox)

        self.tabs.addTab(mfr, self.tr("About"))

    def build_menu(self):

        settings = QtCore.QSettings()

        self.app_menu_tb     = QtGui.QToolButton(self.widgets)
        self.app_menu        = QtGui.QMenu("AppMenu", self.app_menu_tb)

        # File Menu
        # actions: new, open, save
        new_act         = QtGui.QAction(self.tr("&New Character"), self)
        open_act        = QtGui.QAction(self.tr("&Open Character..."), self)
        save_act        = QtGui.QAction(self.tr("&Save Character..."), self)
        export_pdf_act  = QtGui.QAction(self.tr("Ex&port as PDF..."), self)
        exit_act        = QtGui.QAction(self.tr("E&xit"), self)

        new_act .setShortcut( QtGui.QKeySequence.New  )
        open_act.setShortcut( QtGui.QKeySequence.Open )
        save_act.setShortcut( QtGui.QKeySequence.Save )
        exit_act.setShortcut( QtGui.QKeySequence.Quit )

        new_act .triggered.connect( self.sink1.new_character  )
        open_act.triggered.connect( self.sink1.load_character )
        save_act.triggered.connect( self.sink1.save_character )
        exit_act.triggered.connect( self.close )

        export_pdf_act .triggered.connect( self.sink1.export_character_as_pdf  )

        # Advancement menu
        # actions buy advancement, view advancements
        resetadv_act = QtGui.QAction(self.tr("&Reset advancements"    ), self)
        refund_act   = QtGui.QAction(self.tr("Refund last advancement"), self)

        refund_act .setShortcut( QtGui.QKeySequence.Undo  )

        resetadv_act.triggered.connect( self.sink1.reset_adv           )
        refund_act  .triggered.connect( self.sink1.refund_last_adv     )

        # Outfit menu
        # actions, select armor, add weapon, add misc item
        sel_armor_act      = QtGui.QAction(self.tr("Wear Armor..."       ), self)
        sel_cust_armor_act = QtGui.QAction(self.tr("Wear Custom Armor..."), self)
        add_weap_act       = QtGui.QAction(self.tr("Add Weapon..."       ), self)
        add_cust_weap_act  = QtGui.QAction(self.tr("Add Custom Weapon..."), self)

        sel_armor_act     .triggered.connect( self.sink1.show_wear_armor      )
        sel_cust_armor_act.triggered.connect( self.sink1.show_wear_cust_armor )
        add_weap_act      .triggered.connect( self.sink3.show_add_weapon      )
        add_cust_weap_act .triggered.connect( self.sink3.show_add_cust_weapon )

        # Rules menu
        set_exp_limit_act  = QtGui.QAction(self.tr("Set Experience Limit..." ), self)
        set_wound_mult_act = QtGui.QAction(self.tr("Set Health Multiplier..."), self)
        damage_act         = QtGui.QAction(self.tr("Cure/Inflict Damage...")  , self)

        # insight calculation submenu
        m_insight_calc   = self.app_menu.addMenu(self.tr("Insight Calculation"))
        self.ic_act_grp  = QtGui.QActionGroup(self)
        ic_default_act   = QtGui.QAction(self.tr("Default"                     ), self)
        ic_no_rank1_1    = QtGui.QAction(self.tr("Ignore Rank 1 Skills"        ), self)
        ic_no_rank1_2    = QtGui.QAction(self.tr("Account Rank 1 School Skills"), self)
        ic_default_act.setProperty('method', rules.insight_calculation_1)
        ic_no_rank1_1 .setProperty('method', rules.insight_calculation_2)
        ic_no_rank1_2 .setProperty('method', rules.insight_calculation_3)
        ic_list = [ic_default_act, ic_no_rank1_1, ic_no_rank1_2]
        for act in ic_list:
            self.ic_act_grp.addAction(act)
            act.setCheckable(True)
            m_insight_calc.addAction (act)
        ic_list[self.ic_idx].setChecked(True)

        # health calculation submenu
        m_health_calc = self.app_menu.addMenu(self.tr("Health Display"))
        self.hm_act_grp   = QtGui.QActionGroup(self)
        hm_default_act    = QtGui.QAction(self.tr("Default"     ), self)
        hm_cumulative_act = QtGui.QAction(self.tr("Health left" ), self)
        hm_totwounds_act  = QtGui.QAction(self.tr("Total wounds"), self)
        hm_default_act   .setProperty('method', 'default')
        hm_cumulative_act.setProperty('method', 'stacked')
        hm_totwounds_act .setProperty('method', 'wounds' )
        hm_list = [hm_default_act, hm_cumulative_act, hm_totwounds_act]
        hm_mode = settings.value('health_method', 'wounds')
        for act in hm_list:
            self.hm_act_grp.addAction(act)
            act.setCheckable(True)
            m_health_calc.addAction  (act)
            if act.property('method') == hm_mode:
                act.setChecked(True)

        set_exp_limit_act .triggered.connect(self.sink1.on_set_exp_limit      )
        set_wound_mult_act.triggered.connect(self.sink1.on_set_wnd_mult       )
        damage_act        .triggered.connect(self.sink1.on_damage_act         )


        # Data menu
        import_data_act   = QtGui.QAction(self.tr("Import Data pack..." ), self)
        manage_data_act   = QtGui.QAction(self.tr("Manage Data packs..."), self)
        reload_data_act   = QtGui.QAction(self.tr("Reload data"         ), self)

        # Options
        m_options                       = self.app_menu.addMenu(self.tr("Options"))
        self.options_act_grp            = QtGui.QActionGroup(self)
        self.options_act_grp.setExclusive(False)

        options_set_background_act       = QtGui.QAction(self.tr("Set background image   " ), self)
        options_rem_background_act       = QtGui.QAction(self.tr("Remove background image" ), self)
        options_set_background_color_act = QtGui.QAction(self.tr("Set background color"    ), self)
        options_banner_act               = QtGui.QAction(self.tr("Toggle banner display"   ), self)
        options_buy_for_free_act         = QtGui.QAction(self.tr("Free Shopping"           ), self)
        options_open_data_dir_act        = QtGui.QAction(self.tr("Open Data Directory"     ), self)
        options_dice_roll_act            = QtGui.QAction(self.tr("Dice &Roller..."         ), self)
        #options_reset_geometry_act       = QtGui.QAction(self.tr("Reset window size"       ), self)

        options_list = [options_set_background_act, options_rem_background_act, options_set_background_color_act, options_banner_act, options_buy_for_free_act, options_open_data_dir_act, options_dice_roll_act] #, options_reset_geometry_act
        for act in options_list:
            self.options_act_grp.addAction(act)
            m_options.addAction(act)
            if(act.text() != 'Set background image   '):
                m_options.addSeparator()

        options_buy_for_free_act.setCheckable(True)
        options_buy_for_free_act.setChecked(False)
        options_set_background_act.triggered.connect(self.sink1.on_set_background)
        options_rem_background_act.triggered.connect(self.sink1.on_rem_background)
        options_set_background_color_act.triggered.connect(self.sink1.on_set_background_color)
        options_banner_act.triggered.connect(self.sink1.on_toggle_display_banner)
        options_buy_for_free_act.toggled.connect(self.sink1.on_toggle_buy_for_free)
        options_open_data_dir_act.triggered.connect(self.sink1.open_data_dir_act)
        options_dice_roll_act.triggered.connect(self.sink1.show_dice_roller)
        #options_reset_geometry_act.triggered.connect(self.sink1.on_reset_geometry)

        # GENERAL MENU
        self.app_menu_tb.setAutoRaise(True)
        self.app_menu_tb.setToolButtonStyle(QtCore.Qt.ToolButtonFollowStyle)
        self.app_menu_tb.setPopupMode( QtGui.QToolButton.InstantPopup )
        self.app_menu_tb.setIconSize( QtCore.QSize(32, 32) )
        self.app_menu_tb.setIcon( QtGui.QIcon.fromTheme("application-menu", QtGui.QIcon(get_icon_path('gear', (32,32))) ))
        self.app_menu_tb.setArrowType( QtCore.Qt.NoArrow )

        # FILE MENU
        self.app_menu.addAction(new_act )
        self.app_menu.addAction(open_act)
        self.app_menu.addAction(save_act)
        self.app_menu.addAction(export_pdf_act)
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
        self.app_menu.addAction(set_exp_limit_act)
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

        import_data_act  .triggered.connect(self.sink4.import_data_act  )
        manage_data_act  .triggered.connect(self.sink4.manage_data_act  )
        reload_data_act  .triggered.connect(self.sink4.reload_data_act  )

    def init(self):
        ''' second step initialization '''
        pass

    def setup_donate_button(self):
        self.statusBar().showMessage(
            self.tr("You can donate to the project by clicking on the button")
        )

        self.paypal_bt = QtGui.QPushButton(self)
        self.paypal_bt.setIcon( QtGui.QIcon(get_icon_path('btn_donate_SM', None)) )
        self.paypal_bt.setIconSize( QtCore.QSize(74, 21) )
        self.paypal_bt.setFlat(True)
        self.paypal_bt.clicked.connect( self.please_donate )
        self.statusBar().addPermanentWidget(self.paypal_bt)

    def connect_signals(self):
        # only user change
        self.cb_pc_clan  .activated.connect( self.on_clan_change   )

        # user and programmatically change
        self.cb_pc_family.currentIndexChanged.connect( self.on_family_change )
        self.cb_pc_school.currentIndexChanged.connect( self.on_school_change )

        # notify only user edit
        self.tx_mod_init.editingFinished.connect( self.update_from_model )

        # update model name
        self.tx_pc_name.editingFinished.connect( self.on_pc_name_change )

        # personal information
        for widget in self.pers_info_widgets:
            widget.editingFinished.connect( self.on_pers_info_change )
        for widget in self.pc_flags_points:
            widget.valueChanged.connect( self.on_flag_points_change )
        for tx in self.pc_flags_rank:
            tx.editingFinished.connect( self.on_flag_rank_change )

        self.void_points.valueChanged.connect( self.on_void_points_change )

        self.trait_sig_mapper.connect(QtCore.SIGNAL("mapped(const QString &)"),
                                      self,
                                      QtCore.SLOT("on_trait_increase(const QString &)"))

        self.ic_act_grp.triggered.connect(self.on_change_insight_calculation )
        self.hm_act_grp.triggered.connect(self.on_change_health_visualization)

        self.bt_school_lock.clicked.connect( self.sink1.on_unlock_school_act )

    def show_nicebar(self, wdgs):
        self.nicebar = QtGui.QFrame(self)
        self.nicebar.setStyleSheet('''
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
        ''')
        self.nicebar.setMinimumSize(0, 32)

        # nicebar layout
        hbox = QtGui.QHBoxLayout(self.nicebar)
        hbox.setContentsMargins(9,1,9,1)

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
        '''raised when user click on the small '+' button near traits'''
        if ( self.increase_trait( int(tag) ) == CMErrors.NOT_ENOUGH_XP ):
            self.not_enough_xp_advise(self)

    def on_void_increase(self):
        '''raised when user click on the small '+' button near void ring'''
        if ( self.increase_void() == CMErrors.NOT_ENOUGH_XP ):
            self.not_enough_xp_advise(self)

    def do_buy_kata(self, kata):
        '''attempt to buy a new kata'''
        if ( self.buy_kata(kata) == CMErrors.NOT_ENOUGH_XP ):
            self.not_enough_xp_advise(self)

    def do_buy_kiho(self, kiho):
        '''attempt to buy a new kiho'''
        if ( self.buy_kiho(kiho) == CMErrors.NOT_ENOUGH_XP ):
            self.not_enough_xp_advise(self)

    def on_clan_change(self, text):
        #print 'on_clan_change %s' % text
        #self.cb_pc_family.clear()
        index = self.cb_pc_clan.currentIndex()
        if index < 0:
            self.pc.clan = None
        else:
            clan_id = self.cb_pc_clan.itemData(index)
            self.pc.clan = clan_id

        self.load_families(self.pc.clan)
        if self.pc.unlock_schools:
            self.load_schools ()
        else:
            self.load_schools(self.pc.clan)
        self.cb_pc_family.setCurrentIndex(0)
        self.cb_pc_school.setCurrentIndex(0)

    def on_family_change(self, text):
        index = self.cb_pc_family.currentIndex()
        if index <= 0:
            self.pc.set_family()
            self.update_from_model()
            return

        uuid  = self.cb_pc_family.itemData(index)
        if uuid == self.pc.get_family():
            return
        # should modify step_1 character
        # get family perk

        family = dal.query.get_family(self.dstore, uuid)
        clan   = dal.query.get_clan  (self.dstore, family.clanid)

        if not family or not clan:
            return

        self.pc.set_family( family.id , family.trait, 1, [family.id, clan.id] )
        self.update_from_model()

    def on_school_change(self, text):
        index = self.cb_pc_school.currentIndex()
        if index <= 0:
            self.pc.set_school()
            self.update_from_model()
            return

        uuid  = self.cb_pc_school.itemData(index)
        if uuid == self.pc.school:
            return

        # should modify step_2 character
        # get school perk
        school = dal.query.get_school(self.dstore, uuid)
        clan   = dal.query.get_clan  (self.dstore, school.clanid)

        try:
            self.pc.set_school(school.id, school.trait, 1, school.honor, school.tags + [school.id, clan.id])
        except:
            self.pc.set_school(uuid, None, None, None)

        for sk in school.skills:
            self.pc.add_school_skill(sk.id, sk.rank, sk.emph)

        # player choose ( aka wildcards )
        for sk in school.skills_pc:
            self.pc.add_pending_wc_skill(sk)

        # get school tech rank 1
        tech0 = dal.query.get_school_tech(school, 1)
        # rule == techid ???

        if tech0:
            self.pc.set_free_school_tech(tech0.id, tech0.id)

        # outfit
        print('outfit', school.outfit)
        self.pc.set_school_outfit( school.outfit, tuple(school.money) )

        # if shugenja get universal spells
        # also player should choose some spells from list

        if 'shugenja' in school.tags:
            count = 0
            for spell in school.spells:
                self.pc.add_free_spell(spell.id)
                count += 1

            for spell in school.spells_pc:
                self.pc.add_pending_wc_spell((spell.element, spell.count, spell.tag))
                count += spell.count

            print('starting spells count are {0}'.format(count))
            self.pc.set_school_spells_qty(count)

            # affinity / deficiency
            print('school: {0}, affinity: {1}, deficiency: {2}'.format(school, school.affinity, school.deficiency))
            self.pc.set_affinity(school.affinity)
            self.pc.set_deficiency(school.deficiency)
            self.pc.get_school().affinity = school.affinity
            self.pc.get_school().deficiency = school.deficiency

        # free kihos ?
        if school.kihos:
            self.pc.set_free_kiho_count( school.kihos.count )

        self.update_from_model()

    def on_pc_name_change(self):
        self.pc.name = self.tx_pc_name.text()

    def on_pers_info_change(self):
        w = self.sender()
        if hasattr(w, 'link'):
            self.pc.set_property(w.link, w.text())

    def on_flag_points_change(self):
        fl  = self.sender()
        pt = fl.value
        if fl == self.pc_flags_points[0]:
            val = int(self.pc_flags_rank[0].text())
            self.pc.set_honor( float(val + float(pt)/10 ) )
        elif fl == self.pc_flags_points[1]:
            val = int(self.pc_flags_rank[1].text())
            self.pc.set_glory( float(val + float(pt)/10 ) )
        elif fl == self.pc_flags_points[2]:
            val = int(self.pc_flags_rank[2].text())
            self.pc.set_status( float(val + float(pt)/10 ) )
        elif fl == self.pc_flags_points[3]:
            val = int(self.pc_flags_rank[3].text())
            self.pc.set_taint( float(val + float(pt)/10 ) )
        else:
            val = int(self.pc_flags_rank[4].text())
            self.pc.set_infamy( float(val + float(pt)/10 ) )

    def on_flag_rank_change(self):
        fl  = self.sender()
        val = int(fl.text())
        if fl == self.pc_flags_rank[0]:
            pt = self.pc_flags_points[0].value
            self.pc.set_honor( float(val + float(pt)/10 ) )
        elif fl == self.pc_flags_rank[1]:
            pt = self.pc_flags_points[1].value
            self.pc.set_glory( float(val + float(pt)/10 ) )
        elif fl == self.pc_flags_rank[2]:
            pt = self.pc_flags_points[2].value
            self.pc.set_status( float(val + float(pt)/10 ) )
        elif fl == self.pc_flags_rank[3]:
            pt = self.pc_flags_points[3].value
            self.pc.set_taint( float(val + float(pt)/10 ) )
        else:
            pt = self.pc_flags_points[4].value
            self.pc.set_infamy( float(val + float(pt)/10 ) )

    def on_void_points_change(self):
        val = self.void_points.value
        self.pc.set_void_points(val)

    def on_buy_skill_rank(self):
        # get selected skill
        sm_ = self.skill_table_view.selectionModel()
        if sm_.hasSelection():
            model_   = self.skill_table_view.model()
            skill_id = model_.data(sm_.currentIndex(), QtCore.Qt.UserRole)

            err_ = self.buy_next_skill_rank(skill_id)
            if err_ != CMErrors.NO_ERROR:
                if err_ == CMErrors.NOT_ENOUGH_XP:
                    self.not_enough_xp_advise(self)
                return

            idx = None
            for i in xrange(0, self.skill_table_view.model().rowCount()):
                idx = self.skill_table_view.model().index(i, 0)
                if model_.data(idx, QtCore.Qt.UserRole) == skill_id:
                    break
            if idx.isValid():
                sm_.setCurrentIndex(idx, (QtGui.QItemSelectionModel.Select |
                                         QtGui.QItemSelectionModel.Rows))

    def act_choose_skills(self):
        dlg = dialogs.SelWcSkills(self.pc, self.dstore, self)
        if dlg.exec_() == QtGui.QDialog.DialogCode.Accepted:
            self.pc.clear_pending_wc_skills()
            self.pc.clear_pending_wc_emphs ()
            self.update_from_model()

    def act_memo_spell(self):
        # get selected spell
        sm_ = self.spell_table_view.selectionModel()
        if sm_.hasSelection():
            model_    = self.spell_table_view.model()
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
            for i in xrange(0, self.spell_table_view.model().rowCount()):
                idx = self.spell_table_view.model().index(i, 0)
                if (model_.data(idx, QtCore.Qt.UserRole).spell_id ==
                    spell_itm.spell_id):
                    break
            if idx.isValid():
                sm_.setCurrentIndex(idx, (QtGui.QItemSelectionModel.Select |
                                         QtGui.QItemSelectionModel.Rows))

    def act_buy_spell(self):
        dlg = dialogs.SpellAdvDialog(self.pc, self.dstore, 'freeform', self)
        dlg.setWindowTitle(self.tr('Add New Spell'))
        dlg.set_header_text(self.tr("<center><h2>Select the spell to learn</h2></center>"))
        if dlg.exec_() == QtGui.QDialog.DialogCode.Accepted:
            self.update_from_model()

    def act_del_spell(self):
        # get selected spell
        sm_ = self.spell_table_view.selectionModel()
        if sm_.hasSelection():
            model_    = self.spell_table_view.model()
            spell_itm = model_.data(sm_.currentIndex(), QtCore.Qt.UserRole)

            if spell_itm.memo: return
            self.remove_spell(spell_itm.spell_id)

    def on_spell_selected(self, current, previous):
        # get selected spell
        model_    = self.spell_table_view.model()
        spell_itm = model_.data(current, QtCore.Qt.UserRole)

        # toggle remove
        self.del_spell_bt.setEnabled(not spell_itm.memo)


    def learn_next_school_tech(self):
        # first of all let's check if the pc has a path for
        # that target rank
        # otherwise proceed with the current school
        path = [x for x in self.pc.schools if x.is_path and x.path_rank == self.pc.get_insight_rank()]

        if len(path):
            path   = path[0]
            print('path', path.school_id)
            # get last learned techs
            last_tech_id = self.pc.get_techs()[-1]
            last_school, last_tech = dal.query.get_tech(self.dstore, last_tech_id)

            school = dal.query.get_school(self.dstore, path.school_id)
            for tech in [ x for x in school.techs if x.rank == (last_tech.rank+1) ]:
                path.techs.append(tech.id)
                print('learn next tech from alternate path {0}. tech: {1}'.format(school.id, tech.id))
        else:
            school, htech = self.get_higher_tech_in_current_school()
            next_rank = htech.rank+1

            last_school = self.pc.schools[-1]
            print('last school', last_school.school_id)
            print('current school', school.id, 'last tech', htech.id)

            #going back from a path?
            if last_school.is_path:
                school = dal.query.get_school(self.dstore, self.pc.schools[-2].school_id)
                hs, ht = self.get_higher_tech()
                next_rank = ht.rank+1
                print('go back to old school', school.id)

            # changed school?
            if self.pc.get_school_id() != school.id:
                school = dal.query.get_school(self.dstore, self.pc.get_school_id())
                next_rank = 1

            for tech in [ x for x in school.techs if x.rank == next_rank ]:
                self.pc.add_tech(tech.id, tech.id)
                print('learn next tech from school {0}. tech: {1}'.format(school.id, tech.id))
                break

        self.pc.recalc_ranks()
        self.pc.set_can_get_other_tech(False)
        self.update_from_model()

    def check_rank_advancement(self):
        if self.nicebar: return

        if self.pc.get_insight_rank() > self.last_rank:
            # HEY, NEW RANK DUDE!

            # get 3 spells each rank
            if self.pc.has_tag('shugenja'):
                self.pc.set_pending_spells_count( self.pc.get_spells_per_rank() )

            lb = QtGui.QLabel(self.tr("You reached the next rank, you have an opportunity"
                                      " to decide your destiny."), self)
            bt = QtGui.QPushButton(self.tr("Advance rank"), self)
            bt.setSizePolicy( QtGui.QSizePolicy.Maximum,
                              QtGui.QSizePolicy.Preferred)
            bt.clicked.connect( self.show_advance_rank_dlg )
            self.show_nicebar([lb, bt])

            # debug
            # dump_slots(self, 'after_a_while.txt')

    def check_school_tech_and_spells(self):
        if self.nicebar: return

        # Show nicebar if can get another school tech
        if (self.pc.can_get_other_techs() and
            self.check_if_tech_available() and
            self.check_tech_school_requirements()):
            self.learn_next_school_tech()
        elif self.pc.can_get_other_spells():
            lb = QtGui.QLabel(self.tr("You now fit the requirements to learn other Spells"), self)
            bt = QtGui.QPushButton(self.tr("Learn Spells"), self)
            bt.setSizePolicy( QtGui.QSizePolicy.Maximum,
                              QtGui.QSizePolicy.Preferred)
            bt.clicked.connect( self.learn_next_school_spells )
            self.show_nicebar([lb, bt])

    def check_free_kihos(self):
        if self.nicebar: return

        # Show nicebar if can get free kihos
        if self.pc.get_free_kiho_count():
            lb = QtGui.QLabel(self.tr("You can learn {0} kihos for free").format(self.pc.get_free_kiho_count()), self)
            bt = QtGui.QPushButton(self.tr("Learn Kihos"), self)
            bt.setSizePolicy( QtGui.QSizePolicy.Maximum,
                              QtGui.QSizePolicy.Preferred)
            bt.clicked.connect( self.learn_next_free_kiho )
            self.show_nicebar([lb, bt])

    def check_missing_requirements(self):
        if self.nicebar: return

        if not self.check_tech_school_requirements():
            lb = QtGui.QLabel(self.tr("You need at least one rank in all school skills"
                                      " to learn the next School Technique"), self)
            bt = QtGui.QPushButton(self.tr("Buy Requirements"), self)
            bt.setSizePolicy( QtGui.QSizePolicy.Maximum,
                              QtGui.QSizePolicy.Preferred)
            bt.clicked.connect( self.buy_school_requirements )
            self.show_nicebar([lb, bt])

    def check_rules(self):
        for t in self.pc.get_techs():
            school, tech = dal.query.get_tech(self.dstore, t)
            if school is not None and tech is not None:
                self.pc.add_tech(tech.id, tech.id)
            else:
                # TODO: alert
                print('cannot load character technique')

        for adv in self.pc.advans:
            if adv.type == 'perk':
                perk = dal.query.get_merit(self.dstore, adv.perk) or dal.query.get_flaw(self.dstore, adv.perk)
                adv.rule = perk.rule

    def check_affinity_wc(self):
        if self.nicebar: return

        print('check affinity wc: {0}'.format(self.pc.get_affinity()))
        if ( 'any' in self.pc.get_affinity() or
             'nonvoid' in self.pc.get_affinity() ):
            lb = QtGui.QLabel(self.tr("You school grant you to choose an elemental affinity."), self)
            bt = QtGui.QPushButton(self.tr("Choose Affinity"), self)
            bt.setSizePolicy( QtGui.QSizePolicy.Maximum,
                              QtGui.QSizePolicy.Preferred)
            bt.clicked.connect( self.show_select_affinity )
            self.show_nicebar([lb, bt])
        elif ('any' in self.pc.get_deficiency() or
              'nonvoid' in self.pc.get_deficiency() ):
            lb = QtGui.QLabel(self.tr("You school grant you to choose an elemental deficiency."), self)
            bt = QtGui.QPushButton(self.tr("Choose Deficiency"), self)
            bt.setSizePolicy( QtGui.QSizePolicy.Maximum,
                              QtGui.QSizePolicy.Preferred)
            bt.clicked.connect( self.show_select_deficiency )
            self.show_nicebar([lb, bt])

    def learn_next_school_spells(self):
        self.pc.recalc_ranks()

        #dlg = dialogs.SelWcSpells(self.pc, self.dstore, self)
        dlg = dialogs.SpellAdvDialog(self.pc, self.dstore, 'bounded', self)
        dlg.setWindowTitle(self.tr('Choose School Spells'))
        dlg.set_header_text(self.tr("<center><h2>Your school has granted you \
                                     the right to choose some spells.</h2> \
                                     <h3><i>Choose with care.</i></h3></center>"))
        if dlg.exec_() == QtGui.QDialog.DialogCode.Accepted:
            self.pc.clear_pending_wc_spells()
            self.pc.set_pending_spells_count(0)
            self.update_from_model()

    def learn_next_free_kiho(self):
        dlg = dialogs.KihoDialog( self.pc, self.dstore, self )
        if dlg.exec_() == QtGui.QDialog.DialogCode.Accepted:
            self.update_from_model()

    def show_advance_rank_dlg(self):
        dlg = dialogs.NextRankDlg(self.pc, self.dstore, self)
        if dlg.exec_() == QtGui.QDialog.DialogCode.Accepted:
            self.last_rank = self.pc.get_insight_rank()
            self.update_from_model()

    def show_buy_skill_dlg(self):
        dlg = dialogs.BuyAdvDialog(self.pc, 'skill',
                                   self.dstore, self)
        dlg.exec_()
        self.update_from_model()

    def show_buy_emph_dlg(self):
        # get selected skill
        sm_ = self.skill_table_view.selectionModel()
        if sm_.hasSelection():
            model_   = self.skill_table_view.model()
            skill_id = model_.data(sm_.currentIndex(), QtCore.Qt.UserRole)

            dlg = dialogs.BuyAdvDialog(self.pc, 'emph',
                                       self.dstore, self)
            dlg.fix_skill_id(skill_id)
            dlg.exec_()
            self.update_from_model()

    def show_select_affinity(self):
        chooses  = None
        if 'nonvoid' in self.pc.get_affinity():
            chooses = [ models.ring_name_from_id(x).capitalize() for x in xrange(0,4) ]
        else:
            chooses = [ models.ring_name_from_id(x).capitalize() for x in xrange(0,5) ]

        affinity, is_ok = QtGui.QInputDialog.getItem(self,
                                              "L5R: CM",
                                              self.tr("Select your elemental affinity"),
                                              chooses, 0, False)
        # print affinity, is_ok
        if is_ok:
            self.set_pc_affinity(affinity)

    def show_select_deficiency(self):
        chooses  = None
        if 'nonvoid' in self.pc.get_deficiency():
            chooses = [ models.ring_name_from_id(x).capitalize() for x in xrange(0,4) ]
        else:
            chooses = [ models.ring_name_from_id(x).capitalize() for x in xrange(0,5) ]

        deficiency, is_ok = QtGui.QInputDialog.getItem(self,
                                              "L5R: CM",
                                              self.tr("Select your elemental deficiency"),
                                              chooses, 0, False)

        if is_ok:
            self.set_pc_deficiency(deficiency)

    def load_character_from(self, path):
        pause_signals( [self.tx_pc_name, self.cb_pc_clan, self.cb_pc_family,
                        self.cb_pc_school] )
        pause_signals( self.pers_info_widgets )

        if not self.pc:
            self.create_new_character()

        if self.pc.load_from(path):
            self.save_path = path

            print('successfully save character. saving file path', self.save_path)

            try:
                self.last_rank = self.pc.last_rank
            except:
                self.last_rank = self.pc.get_insight_rank()

            def school_free_kiho_count():
                school = dal.query.get_school( self.dstore, self.pc.get_school_id(0) )
                if school.kihos == None: return 0
                return school.kihos.count

            # HACK. Fix free kiho for old characters created with 3 free kihos
            if self.pc.get_free_kiho_count() == 3 and school_free_kiho_count() != 3:
                self.pc.set_free_kiho_count(school_free_kiho_count())

            #TODO: checks for books / data extensions

            self.load_families(self.pc.clan)
            if self.pc.unlock_schools:
                self.load_schools ()
            else:
                self.load_schools (self.pc.clan)

            self.tx_pc_notes.set_content(self.pc.extra_notes)
            self.pc.set_insight_calc_method(self.ic_calc_method)
            self.check_rules()
            self.update_from_model()
        else:
            print('character load failure')

        resume_signals( [self.tx_pc_name, self.cb_pc_clan, self.cb_pc_family,
                        self.cb_pc_school] )
        resume_signals( self.pers_info_widgets )

    def load_clans(self):
        # clans
        self.cb_pc_clan.clear()
        self.cb_pc_clan.addItem( self.tr("No Clan"), None )

        for c in self.dstore.clans:
            self.cb_pc_clan.addItem( c.name, c.id )

    def load_schools(self, clan_id = None):
        print('load schools for clan_id {0}'.format(clan_id))

        self.cb_pc_school.clear()
        schools = []

        # TODO: Sort
        schools = dal.query.get_base_schools(self.dstore)
        if clan_id is not None:
            schools = [x for x in schools if x.clanid == clan_id]

        self.cb_pc_school.addItem( self.tr("No School"), None )
        for s in schools:
            self.cb_pc_school.addItem( s.name, s.id )

    def load_families(self, clan_id):
        print('load families for clan_id {0}'.format(clan_id))

        families = []
        self.cb_pc_family.clear()
        if clan_id:
            families = [ x for x in self.dstore.families if x.clanid == clan_id ]

        self.cb_pc_family.addItem( self.tr("No Family"), None )
        for f in families:
            self.cb_pc_family.addItem( f.name, f.id )

    def set_clan(self, clan_id):
        idx = self.cb_pc_clan.currentIndex()
        c_uuid = self.cb_pc_clan.itemData(idx)

        if c_uuid == clan_id:
            return
        for i in xrange(0, self.cb_pc_clan.count()):
            if self.cb_pc_clan.itemData(i) == clan_id:
                self.cb_pc_clan.setCurrentIndex(i)
                return

    def set_family(self, family_id):
        idx = self.cb_pc_family.currentIndex()
        f_uuid = self.cb_pc_family.itemData(idx)

        if f_uuid == family_id:
            return
        for i in xrange(0, self.cb_pc_family.count()):
            if self.cb_pc_family.itemData(i) == family_id:
                self.cb_pc_family.setCurrentIndex(i)
                return

    def set_school(self, school_id):

        idx = self.cb_pc_school.currentIndex()
        s_uuid = self.cb_pc_school.itemData(idx)

        if s_uuid == school_id:
            return

        print('set school to {0}, current school is {1}'.format(school_id, s_uuid))

        found = False
        self.cb_pc_school.blockSignals(True)
        for i in xrange(0, self.cb_pc_school.count()):
            if self.cb_pc_school.itemData(i) == school_id:
                self.cb_pc_school.setCurrentIndex(i)
                found = True
                break

        if not found:
            school = dal.query.get_school(self.dstore, school_id)
            if school:
                self.cb_pc_school.addItem( school.name, school.id )
        self.cb_pc_school.blockSignals(False)

    def set_void_points(self, value):
        if self.void_points.value == value:
            return
        self.void_points.set_value(value)

    def set_flag(self, flag, value):
        rank, points = rules.split_decimal(value)
        # set rank
        self.pc_flags_rank[flag].setText( str(rank) )
        # set points
        self.pc_flags_points[flag].set_value( int(points*10) )

    def set_honor  (self, value): self.set_flag(0, value)
    def set_glory  (self, value): self.set_flag(1, value)
    def set_status (self, value): self.set_flag(2, value)
    def set_taint  (self, value): self.set_flag(3, value)
    def set_infamy (self, value): self.set_flag(4, value)

    def update_from_model(self):

        pause_signals( [self.tx_pc_name, self.cb_pc_clan, self.cb_pc_family,
                        self.cb_pc_school] )
        pause_signals( self.pers_info_widgets )

        self.tx_pc_name.setText( self.pc.name            )
        self.set_clan          ( self.pc.clan            )
        self.set_family        ( self.pc.get_family   () )
        self.set_school        ( self.pc.get_school_id() )

        for w in self.pers_info_widgets:
            if hasattr(w, 'link'):
                w.setText(self.pc.get_property(w.link))

        resume_signals( [self.tx_pc_name, self.cb_pc_clan, self.cb_pc_family,
                        self.cb_pc_school] )
        resume_signals( self.pers_info_widgets )

        pc_xp = self.pc.get_px()
        self.tx_pc_exp.setText( '{0} / {1}'.format( pc_xp, self.pc.exp_limit ) )

        # rings
        for i in xrange(0, 5):
            self.rings[i][1].setText( str(self.pc.get_ring_rank(i)) )

        # attributes
        for i in xrange(0, 8):
            self.attribs[i][1].setText( str(self.pc.get_mod_attrib_rank(i)) )

        # pc rank
        self.tx_pc_rank.setText( str(self.pc.get_insight_rank()) )
        self.tx_pc_ins .setText( str(self.pc.get_insight()) )

        # pc flags
        pause_signals( self.pc_flags_points )
        pause_signals( self.pc_flags_rank   )
        pause_signals( [self.void_points]   )

        self.set_honor  ( self.pc.get_honor()  )
        self.set_glory  ( self.pc.get_glory()  )
        self.set_infamy ( self.pc.get_infamy() )
        self.set_status ( self.pc.get_status() )
        self.set_taint  ( self.pc.get_taint()  )

        self.set_void_points( self.pc.void_points )

        resume_signals( [self.void_points]   )
        resume_signals( self.pc_flags_points )
        resume_signals( self.pc_flags_rank   )

        # armor
        self.tx_armor_nm .setText( str(self.pc.get_armor_name())  )
        self.tx_base_tn  .setText( str(self.pc.get_base_tn())     )
        self.tx_armor_tn .setText( str(self.pc.get_armor_tn())    )
        self.tx_armor_rd .setText( str(self.pc.get_full_rd())    )
        self.tx_cur_tn   .setText( str(self.pc.get_cur_tn())      )
        # armor description
        self.tx_armor_nm.setToolTip( str(self.pc.get_armor_desc()) )

        self.display_health()
        self.update_wound_penalties()
        self.wnd_lb.setTitle(self.tr("Health / Wounds (x%d)") % self.pc.health_multiplier)

        # initiative
        #r, k = self.pc.get_base_initiative()
        self.tx_base_init.setText( rules.format_rtk_t(self.pc.get_base_initiative()) )
        #rtk = self.tx_mod_init.text()
        #r1, k1 = rules.parse_rtk(rtk)
        #if r1 and k1:
        #    self.tx_cur_init.setText( rules.format_rtk(r+r1, k+k1) )
        #    self.pc.mod_init = (r1, k1)
        #else:
        #    self.tx_cur_init.setText( self.tx_base_init.text() )
        self.tx_mod_init.setText( rules.format_rtk_t(self.pc.get_init_modifiers()) )
        self.tx_cur_init.setText( rules.format_rtk_t(self.pc.get_tot_initiative()) )

        # affinity / deficiency
        self.lb_affin.setText(', '.join( [x.capitalize() for x in self.pc.get_affinity  ()] ) )
        self.lb_defic.setText(', '.join( [x.capitalize() for x in self.pc.get_deficiency()] ) )

        # money
        pause_signals( [self.money_widget]   )
        self.money_widget.set_value( self.pc.get_property('money', (0,0,0)) )
        resume_signals( [self.money_widget]   )

        self.hide_nicebar()

        # Show nicebar if pending wildcard skills
        wcs = self.pc.get_pending_wc_skills()
        wce = self.pc.get_pending_wc_emphs ()
        if len(wcs) > 0 or len(wce) > 0:
            lb = QtGui.QLabel(self.tr("Your school gives you the choice of certain skills"), self)
            bt = QtGui.QPushButton(self.tr("Choose Skills"), self)
            bt.setSizePolicy( QtGui.QSizePolicy.Maximum,
                              QtGui.QSizePolicy.Preferred)
            bt.clicked.connect( self.act_choose_skills )
            self.show_nicebar([lb, bt])
        #else:
        #    self.hide_nicebar()

        self.check_affinity_wc()
        self.check_rank_advancement()
        self.check_missing_requirements()
        self.check_school_tech_and_spells()
        self.check_free_kihos()

        # disable step 0-1-2 if any xp are spent
        has_adv = len(self.pc.advans) > 0
        self.cb_pc_clan  .setEnabled( not has_adv )
        self.cb_pc_school.setEnabled( not has_adv )
        self.cb_pc_family.setEnabled( not has_adv )

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

    def update_wound_penalties(self):
        penalties = [0, 3, 5, 10, 15, 20, 40]
        wounds    = [self.tr("Healthy"), self.tr("Nicked"), self.tr("Grazed"),
                     self.tr("Hurt"), self.tr("Injured"), self.tr("Crippled"),
                     self.tr("Down")]
        if self.pc.has_rule('strength_of_earth'):
            # penalties are reduced by 3
            penalties = [ max(0,x-3) for x in penalties]

        for i in xrange(0, len(penalties)):
            self.wounds[i][0].setText(
                unicode.format(u'{0} (+{1})', wounds[i], penalties[i]))

        # TODO toku bushi school removes some penalties

    def display_health        (self):
        settings = QtCore.QSettings()
        method   = settings.value('health_method', 'wounds')
        if method == 'default':
            self.display_health_default()
        elif method == 'wounds':
            self.display_total_wounds  ()
        else:
            self.display_health_stacked()

    def display_health_default(self):
        # health
        for i in xrange(0, 8):
            h = self.pc.get_health_rank(i)
            self.wounds[i][1].setText( str(h) )
            self.wounds[i][2].setText( '' )
        # wounds
        pc_wounds = self.pc.wounds
        hr        = 0
        while pc_wounds and hr < 8:
            w = min(pc_wounds, self.pc.get_health_rank(hr))
            self.wounds[hr][2].setText( str(w) )
            pc_wounds -= w
            hr += 1

    def display_health_stacked(self):
        # fill health level list
        hl = [0]*8
        for i in reversed( range(0, 8) ):
            if i == 7: hl[i] = self.pc.get_health_rank(i)
            else: hl[i] = self.pc.get_health_rank(i) + hl[i+1]
            self.wounds[i][1].setText( str(hl[i]) )

        wounds = self.pc.wounds
        # fill the health left for each wound level
        for i in range(0, 8):
            h = self.pc.get_health_rank(i)
            if h > wounds: self.wounds[i][2].setText( str(h-wounds) )
            else: self.wounds[i][2].setText("")
            wounds -= h
            if wounds < 0: wounds = 0

    def display_total_wounds(self):
        # fill health level list
        hl = [0]*8
        for i in range(0, 8):
            if i == 0: hl[i] = self.pc.get_health_rank(i)
            else: hl[i] = self.pc.get_health_rank(i) + hl[i-1]
            self.wounds[i][1].setText( str(hl[i]) )

        wounds = self.pc.wounds
        h      = 0
        # fill the health left for each wound level
        for i in range(0, 8):
            h += self.pc.get_health_rank(i)
            wound_rank = min(h, wounds)
            if wound_rank > 0:
                self.wounds[i][2].setText( str(wound_rank) )
            if wounds <= h: break

    def advise_conversion(self, *args):
        settings = QtCore.QSettings()
        if settings.value('advise_conversion', 'true') == 'false':
            return
        msgBox = QtGui.QMessageBox(self)
        msgBox.setWindowTitle('L5R: CM')
        msgBox.setText(self.tr("The character has been updated."))
        msgBox.setInformativeText(self.tr("This character was created with an older version of the program.\n"
                                          "I've done my best to convert and update your character, hope you don't mind :).\n"
                                          "I also created a backup of your character file in\n\n%s.") % args)
        do_not_prompt_again = QtGui.QCheckBox(self.tr("Do not prompt again"), msgBox)
        do_not_prompt_again.blockSignals(True) # PREVENT MSGBOX TO CLOSE ON CLICK
        msgBox.addButton(QtGui.QMessageBox.Ok)
        msgBox.addButton(do_not_prompt_again, QtGui.QMessageBox.ActionRole)
        msgBox.setDefaultButton(QtGui.QMessageBox.Ok)
        msgBox.exec_()
        if do_not_prompt_again.checkState() == QtCore.Qt.Checked:
            settings.setValue('advise_conversion', 'false')

    def advise_successfull_import(self, count):
        settings = QtCore.QSettings()
        if settings.value('advise_successfull_import', 'true') == 'false':
            return
        msgBox = QtGui.QMessageBox(self)
        msgBox.setWindowTitle('L5R: CM')
        msgBox.setText(self.tr("{0} data pack(s) imported succesfully.").format(count))
        do_not_prompt_again = QtGui.QCheckBox(self.tr("Do not prompt again"), msgBox)
        do_not_prompt_again.blockSignals(True) # PREVENT MSGBOX TO CLOSE ON CLICK
        msgBox.addButton(QtGui.QMessageBox.Ok)
        msgBox.addButton(do_not_prompt_again, QtGui.QMessageBox.ActionRole)
        msgBox.setDefaultButton(QtGui.QMessageBox.Ok)
        msgBox.setIcon(QtGui.QMessageBox.Information)
        msgBox.exec_()
        if do_not_prompt_again.checkState() == QtCore.Qt.Checked:
            settings.setValue('advise_successfull_import', 'false')

    def advise_error(self, message, dtl = None):
        msgBox = QtGui.QMessageBox(self)
        msgBox.setWindowTitle('L5R: CM')
        msgBox.setTextFormat(QtCore.Qt.RichText)
        msgBox.setText(message)
        if dtl:
            msgBox.setInformativeText(dtl)
        msgBox.setIcon(QtGui.QMessageBox.Critical)
        msgBox.setDefaultButton(QtGui.QMessageBox.Ok)
        msgBox.exec_()

    def advise_warning(self, message, dtl = None):
        msgBox = QtGui.QMessageBox(self)
        msgBox.setTextFormat(QtCore.Qt.RichText)
        msgBox.setWindowTitle('L5R: CM')
        msgBox.setText(message)
        if dtl:
            msgBox.setInformativeText(dtl)
        msgBox.setIcon(QtGui.QMessageBox.Warning)
        msgBox.setDefaultButton(QtGui.QMessageBox.Ok)
        msgBox.exec_()

    def ask_warning(self, message, dtl = None):
        msgBox = QtGui.QMessageBox(self)
        msgBox.setTextFormat(QtCore.Qt.RichText)
        msgBox.setWindowTitle('L5R: CM')
        msgBox.setText(message)
        if dtl:
            msgBox.setInformativeText(dtl)
        msgBox.setIcon(QtGui.QMessageBox.Warning)
        msgBox.addButton(QtGui.QMessageBox.Ok)
        msgBox.addButton(QtGui.QMessageBox.Cancel)
        msgBox.setDefaultButton(QtGui.QMessageBox.Cancel)
        return msgBox.exec_() == QtGui.QMessageBox.Ok

    def ask_to_save(self):
        msgBox = QtGui.QMessageBox(self)
        msgBox.setWindowTitle('L5R: CM')
        msgBox.setText(self.tr("The character has been modified."))
        msgBox.setInformativeText(self.tr("Do you want to save your changes?"))
        msgBox.addButton( QtGui.QMessageBox.Save )
        msgBox.addButton( QtGui.QMessageBox.Discard )
        msgBox.addButton( QtGui.QMessageBox.Cancel )
        msgBox.setDefaultButton(QtGui.QMessageBox.Save)
        return msgBox.exec_()

    def ask_to_upgrade(self, target_version):
        msgBox = QtGui.QMessageBox(self)
        msgBox.setWindowTitle('L5R: CM')
        msgBox.setText(self.tr("L5R: CM v%s is available for download.") % target_version)
        msgBox.setInformativeText(self.tr("Do you want to open the download page?"))
        msgBox.addButton( QtGui.QMessageBox.Yes )
        msgBox.addButton( QtGui.QMessageBox.No )
        msgBox.setDefaultButton(QtGui.QMessageBox.No)
        return msgBox.exec_()

    def not_enough_xp_advise(self, parent = None):
        if parent == None: parent = self
        QtGui.QMessageBox.warning(parent, self.tr("Not enough XP"),
        self.tr("Cannot purchase.\nYou've reached the XP Limit."))
        return

    def closeEvent(self, ev):
        # update interface last time, to set unsaved states
        self.update_from_model()

        # SAVE GEOMETRY
        settings = QtCore.QSettings()
        settings.setValue('geometry', self.saveGeometry())

        if self.pc.insight_calculation == rules.insight_calculation_2:
            settings.setValue('insight_calculation', 2)
        elif self.pc.insight_calculation == rules.insight_calculation_3:
            settings.setValue('insight_calculation', 3)
        else:
            settings.setValue('insight_calculation', 1)

        #print('is model dirty? {0}'.format(self.pc.is_dirty()))

        if self.pc.is_dirty():
            resp = self.ask_to_save()
            if resp == QtGui.QMessageBox.Save:
                self.sink1.save_character()
            elif resp == QtGui.QMessageBox.Cancel:
                ev.ignore()
            else:
                super(L5RMain, self).closeEvent(ev)
        else:
            super(L5RMain, self).closeEvent(ev)

    def select_save_path(self):
        settings = QtCore.QSettings()
        last_dir = settings.value('last_open_dir', QtCore.QDir.homePath())
        fileName = QtGui.QFileDialog.getSaveFileName(
                                self,
                                self.tr("Save Character"),
                                last_dir,
                                self.tr("L5R Character files (*.l5r)"))

        if len(fileName) != 2 or fileName[0] == u'':
            return ''

        last_dir = os.path.dirname(fileName[0])
        if last_dir != '':
            #print 'save last_dir: %s' % last_dir
            settings.setValue('last_open_dir', last_dir)

        if fileName[0].endswith('.l5r'):
            return fileName[0]
        return fileName[0] + '.l5r'

    def select_load_path(self):
        settings = QtCore.QSettings()
        last_dir = settings.value('last_open_dir', QtCore.QDir.homePath())
        fileName = QtGui.QFileDialog.getOpenFileName(
                                self,
                                self.tr("Load Character"),
                                last_dir,
                                self.tr("L5R Character files (*.l5r)"))
        if len(fileName) != 2:
            return ''
        last_dir = os.path.dirname(fileName[0])
        if last_dir != '':
            #print 'save last_dir: %s' % last_dir
            settings.setValue('last_open_dir', last_dir)
        return fileName[0]

    def select_export_file(self, file_ext = '.txt'):
        char_name = self.pc.name
        supported_ext     = ['.pdf']
        supported_filters = [self.tr("PDF Files(*.pdf)")]

        settings = QtCore.QSettings()
        last_dir = settings.value('last_open_dir', QtCore.QDir.homePath())
        fileName = QtGui.QFileDialog.getSaveFileName(
                                self,
                                self.tr("Export Character"),
                                os.path.join(last_dir,char_name),
                                ";;".join(supported_filters))
        if len(fileName) != 2:
            return ''

        last_dir = os.path.dirname(fileName[0])
        if last_dir != '':
            settings.setValue('last_open_dir', last_dir)

        if fileName[0].endswith(file_ext):
            return fileName[0]
        return fileName[0] + file_ext

    def select_import_data_pack(self):
        supported_ext     = ['.zip', '.l5rcmpack']
        supported_filters = [self.tr("L5R:CM Data Pack(*.l5rcmpack *.zip)"),
                             self.tr("Zip Archive(*.zip)")]

        settings = QtCore.QSettings()
        last_data_dir = settings.value('last_open_data_dir', QtCore.QDir.homePath())
        ret = QtGui.QFileDialog.getOpenFileNames(
                                self,
                                self.tr("Load data pack"),
                                last_data_dir,
                                ";;".join(supported_filters))
        
        if len(ret) < 2:
            return None
           
        files = ret[0]
        
        if not len(files):
            return None

        last_data_dir = os.path.dirname(files[0])
        if last_data_dir != '':
            #print 'save last_dir: %s' % last_dir
            settings.setValue('last_open_data_dir', last_data_dir)
        return files

    def check_updates(self):
        update_info = autoupdate.get_last_version()
        need_update = False

        if update_info is None:
            return

        version_str = ''
        # check extended module version
        if 'versionex' in update_info:
            need_update = autoupdate.need_update(APP_VERSION, update_info['versionex'])
            version_str = update_info['versionex']
        else:
            need_update = autoupdate.need_update(APP_VERSION, update_info['version'])
            version_str = update_info['version']

        if need_update and self.ask_to_upgrade(version_str) == QtGui.QMessageBox.Yes:
            import osutil
            osutil.portable_open(PROJECT_DOWNLOADS_LINK)

    def on_change_insight_calculation(self):
        method = self.sender().checkedAction().property('method')
        self.pc.set_insight_calc_method(method)
        self.update_from_model()

    def on_change_health_visualization(self):
        method = self.sender().checkedAction().property('method')
        settings = QtCore.QSettings()
        settings.setValue('health_method', method)
        self.update_from_model()

    def create_new_character(self):
        self.sink1.new_character()
        self.pc.unsaved = False

    def get_health_rank(self, idx):
        return self.wounds[idx][1].text()

### MAIN ###
def dump_slots(obj, out_file):
    with open(out_file, 'wt') as fobj:
        mobj = obj.metaObject()
        for i in xrange( mobj.methodOffset(), mobj.methodCount() ):
            if mobj.method(i).methodType() == QtCore.QMetaMethod.Slot:
                fobj.write(mobj.method(i).signature() + ' ' + mobj.method(i).tag() + '\n')

OPEN_CMD_SWITCH   = '--open'
IMPORT_CMD_SWITCH = '--import'
DATA_CHECK_SWITCH = '--datacheck'
DATA_REPT_SWITCH  = '--datareport'

MIME_L5R_CHAR     = "applications/x-l5r-character"
MIME_L5R_PACK     = "applications/x-l5r-pack"



def main():
    try:
        app = QtGui.QApplication(sys.argv)

        # setup mimetypes
        mimetypes.add_type(MIME_L5R_CHAR, ".l5r")
        mimetypes.add_type(MIME_L5R_PACK, ".l5rcmpack")

        if DATA_CHECK_SWITCH in sys.argv:
            import dal_check
            dc = dal_check.DataCheck()
            dc.check()
            return

        if DATA_REPT_SWITCH in sys.argv:
            import dal.report
            dr = dal.report.ReportBuilder('./data_packs', './data_report')
            dr.build()
            return

        QtCore.QCoreApplication.setApplicationName(APP_NAME)
        QtCore.QCoreApplication.setApplicationVersion(APP_VERSION)
        QtCore.QCoreApplication.setOrganizationName(APP_ORG)

        app.setWindowIcon( QtGui.QIcon( get_app_icon_path() ) )

        # Setup translation
        settings = QtCore.QSettings()
        use_machine_locale = settings.value('use_machine_locale', 1)
        app_translator = QtCore.QTranslator()
        qt_translator  = QtCore.QTranslator()

        print('use_machine_locale', use_machine_locale, QtCore.QLocale.system().name())

        if use_machine_locale == 1:
            use_locale = QtCore.QLocale.system().name()
        else:
            use_locale = settings.value('use_locale')

        print('current locale is {0}'.format(use_locale))

        qt_loc  = 'qt_{0}'.format(use_locale[:2])

        print(qt_loc)
        app_loc = get_app_file('i18n/{0}'.format(use_locale))

        print(QtCore.QLibraryInfo.location(QtCore.QLibraryInfo.TranslationsPath))

        qt_translator .load(qt_loc, QtCore.QLibraryInfo.location(QtCore.QLibraryInfo.TranslationsPath))
        app.installTranslator(qt_translator )
        app_translator.load(app_loc)
        app.installTranslator(app_translator)

        # start main form
        print("create main form")
        l5rcm = L5RMain(use_locale)
        l5rcm.setWindowTitle(APP_DESC + ' v' + APP_VERSION)
        l5rcm.show()
        l5rcm.init()

        # initialize new character
        l5rcm.create_new_character()        

        if len(sys.argv) > 1:
            if OPEN_CMD_SWITCH in sys.argv:
                of   = sys.argv.index(OPEN_CMD_SWITCH)
                l5rcm.load_character_from(sys.argv[of+1])
            elif IMPORT_CMD_SWITCH in sys.argv:
                imf  = sys.argv.index(IMPORT_CMD_SWITCH)
                l5rcm.import_data_pack(sys.argv[imf+1])
            else:
                # check mimetype
                mime = mimetypes.guess_type(sys.argv[1])
                if mime[0] == MIME_L5R_CHAR:
                    l5rcm.load_character_from(sys.argv[1])
                elif mime[0] == MIME_L5R_PACK:
                    l5rcm.import_data_pack(sys.argv[1])

        # alert if not datapacks are installed
        l5rcm.check_datapacks()

        # check for updates
        #if sys.platform != 'linux2':
        l5rcm.check_updates()

        sys.exit(app.exec_())
    except Exception as e:
        print("HOLYMOLY!", e)
    finally:
        print("KTHXBYE")

if __name__ == '__main__':
    main()
