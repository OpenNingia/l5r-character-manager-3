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

import os
import shutil
from tempfile import mkstemp

from qtpy import QtCore, QtGui, QtWidgets

import l5r.models as models
import l5r.exporters as exporters

import l5rdal as dal
import l5rdal.dataimport

from l5r.util import log, osutil
from l5r.util.fsutil import (
    APP_NAME,
    HERE,
    MY_CWD,
    get_app_file,
    get_app_icon_path,
    get_icon_path,
    get_tab_icon,
)
import l5r.api as api
import l5r.api.data
import l5r.api.data.families
import l5r.api.character
import l5r.api.character.powers
import l5r.api.rules
from l5r.api.data import CMErrors
from l5r.l5rcmcore.qtsignalsutils import (
    QtSignalLock,
    pause_signals,
    resume_signals,
)
from l5r.util.settings import L5RCMSettings

from qtpy.QtGui import QDesktopServices
from qtpy.QtCore import QUrl

# PyPDF
from pypdf import PdfReader, PdfWriter
from pypdf.generic import ArrayObject, NameObject

APP_NAME = 'l5rcm'
APP_DESC = 'Legend of the Five Rings: Character Manager'
APP_VERSION = '4.0.0'
DB_VERSION = '3.20'
APP_ORG = 'openningia'

PROJECT_PAGE_LINK = 'https://github.com/OpenNingia/l5r-character-manager-3'
BUGTRAQ_LINK = 'https://github.com/OpenNingia/l5r-character-manager-3/issues'
PROJECT_PAGE_NAME = 'Project Page'
AUTHOR_NAME = 'Daniele Simonetti'
L5R_RPG_HOME_PAGE = 'https://www.legendofthefiverings.com/products/roleplaying-games/legend-of-the-five-rings/'
COMPANY_HOME_PAGE = 'https://www.fantasyflightgames.com/'
DATA_PACKS_DOWNLOADS_LINK = 'https://github.com/OpenNingia/l5rcm-data-packs/releases/latest'
DONATE_LINK = 'https://www.paypal.com/cgi-bin/webscr?cmd=_donations&business=Q87Q5BVS3ZKTE&lc=US&item_name=Daniele%20Simonetti&item_number=l5rcm_donate&currency_code=EUR&bn=PP%2dDonationsBF%3abtn_donate_SM%2egif%3aNonHosted'


class L5RCMCore(QtWidgets.QMainWindow):
    dstore = None

    def __init__(self, locale, parent=None):
        super(L5RCMCore, self).__init__(parent)

        self.pc = None

        # Flag to lock advancement refunds in order
        self.lock_advancements = True

        # current locale
        self.locale = locale

        # set api translator context
        api.set_translation_context(self)

        # load data
        self.reload_data()

    def reload_data(self):
        settings = L5RCMSettings()

        api.data.set_locale(self.locale)
        api.data.set_blacklist(settings.app.data_pack_blacklist)
        api.data.reload()

        # assign Data storage reference, for backward compatibility
        self.dstore = api.data.model()

    def check_datapacks(self):
        if not len(api.data.packs()):
            self.advise_warning(self.tr("No Datapacks installed"),
                                self.tr("Without data packs the software will be of little use."
                                        "<p>Download a datapack from <a href=\"{0}\">Github</a>.</p>"
                                        .format(DATA_PACKS_DOWNLOADS_LINK)))

    def update_from_model(self):
        pass

    def export_as_text(self, export_file):
        pass
        #exporter = exporters.TextExporter()
        #exporter.set_form(self)
        #exporter.set_model(self.pc)

        #f = open(export_file, 'wt')
        #if f is not None:
        #    exporter.export(f)
        #f.close()

    def export_npc_characters(self, npc_files, export_file):
        # Shared, UI-agnostic implementation lives in l5r.exporters.sheet so
        # the QWidget and QML front-ends export through one code path. We pass
        # `self` as the form -- its live view-models / labels feed the FDF
        # exporters; the QML UI hands a ModelExportForm instead.
        from l5r.exporters import sheet
        sheet.export_npc(npc_files, export_file, self)

    def export_as_pdf(self, export_file):
        # Shared implementation in l5r.exporters.sheet (see
        # export_npc_characters for the form rationale).
        from l5r.exporters import sheet
        sheet.export_pdf(export_file, self)

    def remove_advancement_item(self, adv_itm):
        if api.character.remove_advancement(adv_itm):
            self.update_from_model()

    def increase_trait(self, attrib):
        res = api.character.purchase_trait_rank(attrib)
        if res == CMErrors.NO_ERROR:
            self.update_from_model()
        return res

    def increase_void(self):
        res = api.character.purchase_void_rank()
        if res == CMErrors.NO_ERROR:
            self.update_from_model()
        return res

    def set_exp_limit(self, val):
        self.pc.exp_limit = val
        self.update_from_model()

    def set_health_multiplier(self, val):
        api.character.set_health_multiplier(val)
        self.update_from_model()

    def damage_health(self, val):
        api.character.damage_health(val)
        self.update_from_model()

    def buy_next_skill_rank(self, skill_id):
        res = api.character.skills.purchase_skill_rank(skill_id)
        if res == CMErrors.NO_ERROR:
            self.update_from_model()
        return res

    def memo_spell(self, spell_id):
        res = api.character.spells.purchase_memo_spell(spell_id)
        if res == CMErrors.NO_ERROR:
            self.update_from_model()
        return res

    def remove_spell(self, spell_id):
        self.pc.remove_spell(spell_id)
        self.update_from_model()

    def set_pc_affinity(self, affinity):
        if api.character.has_tag('chuda shugenja school'):
            self.pc.set_affinity('maho ' + affinity.lower())
            self.pc.set_deficiency(affinity.lower())
        else:
            self.pc.set_affinity(affinity.lower())
        self.update_from_model()

    def set_pc_deficiency(self, deficiency):
        self.pc.set_deficiency(deficiency.lower())
        self.update_from_model()

    def import_data_packs(self, data_pack_file):

        imported = 0

        for dp in data_pack_file:
            if self.import_data_pack(dp):
                imported += 1

        if imported > 0:
            self.reload_data()
            self.advise_successfull_import(imported)
        else:
            self.advise_error(self.tr("Cannot import data pack."))

    def import_data_pack(self, data_pack_file):
        try:
            dal.dataimport.CM_VERSION = APP_VERSION
            pack = dal.dataimport.DataPack(data_pack_file)
            if not pack.good():
                self.advise_error(self.tr("Invalid data pack."))
            else:
                dest = osutil.get_user_data_path()
                if pack.id == 'core':
                    dest = os.path.join(dest, 'core.data')
                elif pack.language:
                    dest = os.path.join(dest, 'data.' + pack.language)
                else:
                    dest = os.path.join(dest, 'data')

                pack.export_to(dest)
            return True
        except Exception as e:
            return False

    def update_data_blacklist(self):

        api.data.set_blacklist([
            x.id for x in self.dstore.packs if not x.active])

        settings = L5RCMSettings()
        settings.app.data_pack_blacklist = api.data.get_blacklist()

    def please_donate(self):
        QtGui.QDesktopServices.openUrl(QtCore.QUrl(DONATE_LINK))

    def buy_kata(self, kata):
        # Delegates to the shared api purchase path so the QWidget and
        # QML UIs use one implementation (the api setter owns the dirty
        # flag); we only drive the QWidget pull-refresh on success.
        res = api.character.powers.buy_kata(kata.id)
        if res == CMErrors.NO_ERROR:
            self.update_from_model()
        return res

    def buy_kiho(self, kiho):
        # Delegates to the shared api purchase path so the QWidget and
        # QML UIs use one implementation (the api setter owns the dirty
        # flag and the free-kiho discount); we only drive the QWidget
        # pull-refresh on success.
        res = api.character.powers.buy_kiho(kiho.id)
        if res == CMErrors.NO_ERROR:
            self.update_from_model()
        return res

    def buy_tattoo(self, kiho):
        # Delegates to the shared api purchase path so the QWidget and
        # QML UIs use one implementation (the api setter owns the dirty
        # flag); we only drive the QWidget pull-refresh on success.
        res = api.character.powers.buy_tattoo(kiho.id)
        if res == CMErrors.NO_ERROR:
            self.update_from_model()
        return res

    def get_character_full_name(self):

        # if the character has a family name
        # prepend the character name with it
        # e.g. Hida Hiroshi
        # otherwise just 'Hiroshi' will do

        family_obj = api.data.families.get(api.character.get_family())
        if family_obj:
            return "{} {}".format(family_obj.name, self.pc.name)
        return self.pc.name

    def open_pdf_file_as_shell(self, filePath):
        QDesktopServices.openUrl(QUrl("file:///" + filePath, QUrl.TolerantMode))
