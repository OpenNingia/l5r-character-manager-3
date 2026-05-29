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

    def create_form_fields(self, exporter):
        exporter.set_form(self)
        exporter.set_model(self.pc)
        return exporter.get_fields()


    def fill_pdf(self, form_fields, source_pdf, target_pdf, target_suffix=None):
        basen = os.path.splitext(os.path.basename(target_pdf))[0]
        based = os.path.dirname(target_pdf)

        if target_suffix:
            target_pdf = os.path.join(based, basen) + '_%s.pdf' % target_suffix
        else:
            target_pdf = os.path.join(based, basen) + '.pdf'

        try:
            reader = PdfReader(source_pdf)
            writer = PdfWriter()
            writer.append(reader)

            writer.update_page_form_field_values(
                None,
                form_fields,
                auto_regenerate=False,
                flatten=True,
            )

            self._strip_form_widgets(writer)

            with open(target_pdf, "wb") as output_stream:
                writer.write(output_stream)

            log.app.info('created pdf %s', target_pdf)
            return True
        finally:
            pass
        #except Exception as ex:
        #    log.app.error('could not generate output pdf. exception: %s', ex)
        #    return False

    @staticmethod
    def _strip_form_widgets(writer):
        """Remove form widget annotations and /AcroForm from a flattened PDF.

        pypdf's ``update_page_form_field_values(..., flatten=True)`` bakes the
        appearance stream into the page contents but leaves the widget
        annotations in place, so the now-empty field overlays still render on
        top. Drop them to get a truly flattened, no-form output.
        """
        for p in writer.pages:
            if "/Annots" not in p:
                continue
            kept = [
                a for a in p["/Annots"]
                if a.get_object().get("/Subtype") != "/Widget"
            ]
            p[NameObject("/Annots")] = ArrayObject(kept)
        if "/AcroForm" in writer._root_object:
            del writer._root_object[NameObject("/AcroForm")]

    def merge_pdf(self, input_files, output_file):
        try:
            merger = PdfWriter()

            for pdf in input_files:
                merger.append(pdf)

            merger.write(output_file)
            merger.close()
        finally:
            for f in input_files:
                self.try_remove(f)

    def try_remove(self, fpath):
        try:
            os.remove(fpath)
            log.app.debug('deleted temp file: {0}'.format(fpath))
        except:
            log.app.error('cannot delete temp file: {0}'.format(fpath), exc_info=1, stack_info=True)

    def write_pdf(self, source, exporter):
        source_pdf = get_app_file(source)
        form_fields = self.create_form_fields(exporter)

        fd, fpath = mkstemp(suffix='.pdf')
        os.fdopen(fd, 'wb').close()
        self.fill_pdf(form_fields, source_pdf, fpath)
        self.temp_files.append(fpath)

    def commit_pdf_export(self, export_file):
        if os.path.exists(export_file):
            os.remove(export_file)

        if len(self.temp_files) > 1:
            self.merge_pdf(self.temp_files, export_file)
        elif len(self.temp_files) == 1:
            shutil.move(self.temp_files[0], export_file)

    def export_npc_characters(self, npc_files, export_file):
        self.temp_files = []

        pcs = []
        for f in npc_files:
            c = l5r.models.AdvancedPcModel()
            if c.load_from(f):
                pcs.append(c)

        self.write_pdf(
            'sheet_npc.pdf', exporters.FDFExporterTwoNPC(pcs))
        self.commit_pdf_export(export_file)

    def export_as_pdf(self, export_file):
        self.temp_files = []

        # GENERIC SHEET
        source_pdf = get_app_file('sheet_all.pdf')
        form_fields = self.create_form_fields(exporters.FDFExporterAll())
        fd, fpath = mkstemp(suffix='.pdf')
        os.fdopen(fd, 'wb').close()

        self.fill_pdf(form_fields, source_pdf, fpath)
        self.temp_files.append(fpath)

        # SAMURAI MONKS ALSO FITS IN THE BUSHI CHARACTER SHEET
        is_monk, is_brotherhood = api.character.is_monk()
        is_samurai_monk = is_monk and not is_brotherhood
        is_shugenja = api.character.is_shugenja()
        is_bushi = api.character.is_bushi()
        is_courtier = api.character.is_courtier()
        is_ninja = api.character.is_ninja()
        spell_offset = 0
        spell_count = len(api.character.spells.get_all())
        kihos = api.character.powers.get_all_kiho()
        kiho_count = min(12, len(kihos))

        # SHUGENJA/BUSHI/MONK SHEET
        if is_shugenja:
            self.write_pdf('sheet_shugenja.pdf', exporters.FDFExporterShugenja())
        elif is_bushi:
            self.write_pdf('sheet_bushi.pdf', exporters.FDFExporterBushi())
        elif is_ninja:
            self.write_pdf('sheet_bushi.pdf', exporters.FDFExporterBushi())            
        elif is_samurai_monk:
            self.write_pdf('sheet_bushi.pdf', exporters.FDFExporterBushi())
        elif is_monk:
            self.write_pdf('sheet_monk.pdf', exporters.FDFExporterMonk())
        elif is_courtier:
            self.write_pdf('sheet_bushi.pdf', exporters.FDFExporterCourtier())

        if kiho_count > 0:
            self.write_pdf('sheet_monk.pdf', exporters.FDFExporterMonk())

        # SPELLS
        # we use as many extra spells sheet as needed

        if is_shugenja:
            # spell_count = api.character.spells.get_all()
            # spell_offset = 0

            while spell_count > 0:
                _exporter = exporters.FDFExporterSpells(spell_offset)
                self.write_pdf('sheet_spells.pdf', _exporter)
                spell_offset += _exporter.spell_per_page
                spell_count -= _exporter.spell_per_page

        # DEDICATED SKILL SHEET
        skill_count = len(api.character.skills.get_all())
        skill_offset = 0

        while skill_count > 0:
            _exporter = exporters.FDFExporterSkills(skill_offset)
            self.write_pdf('sheet_skill.pdf', _exporter)
            skill_offset += _exporter.skills_per_page
            skill_count -= _exporter.skills_per_page

        # WEAPONS
        weapons_count = len(self.pc.weapons)
        weapons_offset = 0
        if weapons_count > 2:
            while weapons_count > 0:
                _exporter = exporters.FDFExporterWeapons(weapons_offset)
                self.write_pdf('sheet_weapons.pdf', _exporter)
                weapons_offset += _exporter.weapons_per_page
                weapons_count -= _exporter.weapons_per_page

        self.commit_pdf_export(export_file)           

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
        donate_url = QtCore.QUrl(
            "https://www.paypal.com/cgi-bin/webscr?cmd=_donations&business=Q87Q5BVS3ZKTE&lc=US&item_name=Daniele%20Simonetti&item_number=l5rcm_donate&currency_code=EUR&bn=PP%2dDonationsBF%3abtn_donate_SM%2egif%3aNonHosted")
        QtGui.QDesktopServices.openUrl(donate_url)

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
