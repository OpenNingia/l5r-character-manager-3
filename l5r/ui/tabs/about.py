# -*- coding: utf-8 -*-
# Copyright (C) 2014-2026 Daniele Simonetti
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# Tab 12 — About page. Extracted from l5r/main.py during the Phase 4
# split — no behaviour changes.

from qtpy import QtCore, QtGui, QtWidgets

from l5r.l5rcmcore import (
    COMPANY_HOME_PAGE,
    APP_DESC,
    AUTHOR_NAME,
    BUGTRAQ_LINK,
    L5R_RPG_HOME_PAGE,
    PROJECT_PAGE_LINK,
    PROJECT_PAGE_NAME,
)
from l5r.util.fsutil import get_app_icon_path


class AboutTabMixin:
    """Tab 12: project info, links, version, credits."""

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
                  <a href="%s">Fantasy Flight Games</a>
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
                                       COMPANY_HOME_PAGE, AUTHOR_NAME)
        lb_info = QtWidgets.QLabel(info, self)
        lb_info.setOpenExternalLinks(True)
        lb_info.setWordWrap(True)
        hbox.addWidget(lb_info)

        vbox.addLayout(hbox)

        self.tabs.addTab(mfr, self.tr("About"))
