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

import shutil
from tempfile import mkstemp
import subprocess

import l5r.models as models
import l5r.exporters as exporters

import l5rdal as dal
import l5rdal.dataimport

from l5r.util import log, osutil
from l5r.util.fsutil import *
import l5r.api as api
import l5r.api.data
import l5r.api.data.families
import l5r.api.character
import l5r.api.rules
from l5r.api.data import CMErrors
from l5r.l5rcmcore.qtsignalsutils import *
from l5r.util.settings import L5RCMSettings

from PyQt5.QtGui import QDesktopServices
from PyQt5.QtCore import QUrl

APP_NAME = 'l5rcm'
APP_DESC = 'Legend of the Five Rings: Character Manager'
APP_VERSION = '3.15.0'
DB_VERSION = '3.15'
APP_ORG = 'openningia'

PROJECT_PAGE_LINK = 'https://github.com/OpenNingia/l5r-character-manager-3'
BUGTRAQ_LINK = 'https://github.com/OpenNingia/l5r-character-manager-3/issues'
PROJECT_PAGE_NAME = 'Project Page'
AUTHOR_NAME = 'Daniele Simonetti'
L5R_RPG_HOME_PAGE = 'http://www.l5r.com/rpg/'
ALDERAC_HOME_PAGE = 'http://www.alderac.com/'
PROJECT_DOWNLOADS_LINK = 'https://sourceforge.net/projects/l5rcm/'

L5RCM_GPLUS_PAGE = "https://plus.google.com/114911686277310621574"
L5RCM_GPLUS_COMM = "https://plus.google.com/communities/107752342280671357654"


class L5RCMCore(QtWidgets.QMainWindow):
    dstore = None

    def __init__(self, locale, parent=None):
        super(L5RCMCore, self).__init__(parent)
        # print(repr(self))
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
                                        "<p>Download a datapack from <a href=\"{0}\">{0}</a>.</p>"
                                        .format(PROJECT_DOWNLOADS_LINK)))

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

    def create_fdf(self, exporter):

        exporter.set_form(self)
        exporter.set_model(self.pc)

        fd, fpath = mkstemp(suffix='.fdf', text=False)
        with os.fdopen(fd, 'wb') as fobj:
            exporter.export(fobj)

        return fpath

    def flatten_pdf(self, fdf_file, source_pdf, target_pdf, target_suffix=None):
        basen = os.path.splitext(os.path.basename(target_pdf))[0]
        based = os.path.dirname(target_pdf)

        if target_suffix:
            target_pdf = os.path.join(based, basen) + '_%s.pdf' % target_suffix
        else:
            target_pdf = os.path.join(based, basen) + '.pdf'

        # call pdftk
        args_ = [self.get_pdftk(), source_pdf, 'fill_form',
                 fdf_file, 'output', target_pdf, 'flatten']

        log.app.debug('call %s', args_)

        ret = subprocess.call(args_)
        self.try_remove(fdf_file)

        if ret == 0:            
            log.app.info('created pdf %s', target_pdf)
        else:
            log.app.warn('could not flatten pdf. pdftk exited with error code: %d', ret)

        return ret == 0

    def merge_pdf(self, input_files, output_file):
        # call pdftk
        args_ = [self.get_pdftk()] + input_files + ['output', output_file]

        log.app.debug('call %s', args_)
        subprocess.call(args_)
        for f in input_files:
            self.try_remove(f)

    def get_pdftk(self):
        if sys.platform == 'win32':
            return os.path.join(MY_CWD, 'tools', 'pdftk.exe')
        elif sys.platform == 'linux' or sys.platform == 'linux2':
            sys_path = '/usr/bin/pdftk'
            loc_path = os.path.join(MY_CWD, 'tools', 'pdftk')
            if os.path.exists(sys_path):
                return sys_path
            else:
                return loc_path
        elif sys.platform == 'darwin':
            return os.path.join(MY_CWD, 'tools', 'pdftk')
        return None

    def try_remove(self, fpath):
        try:
            os.remove(fpath)
            print('deleted temp file: {0}'.format(fpath))
        except:
            print('cannot delete temp file: {0}'.format(fpath))

    def write_pdf(self, source, exporter):
        source_pdf = get_app_file(source)
        source_fdf = self.create_fdf(exporter)
        fd, fpath = mkstemp(suffix='.pdf')
        os.fdopen(fd, 'wb').close()
        self.flatten_pdf(source_fdf, source_pdf, fpath)
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
        source_fdf = self.create_fdf(exporters.FDFExporterAll())
        fd, fpath = mkstemp(suffix='.pdf')
        os.fdopen(fd, 'wb').close()

        self.flatten_pdf(source_fdf, source_pdf, fpath)
        self.temp_files.append(fpath)

        # SAMURAI MONKS ALSO FITS IN THE BUSHI CHARACTER SHEET
        is_monk, is_brotherhood = api.character.is_monk()
        is_samurai_monk = is_monk and not is_brotherhood
        is_shugenja = api.character.is_shugenja()
        is_bushi = api.character.is_bushi()
        is_courtier = api.character.is_courtier()
        spell_offset = 0
        spell_count = len(api.character.spells.get_all())

        # SHUGENJA/BUSHI/MONK SHEET
        if is_shugenja:
            self.write_pdf(
                'sheet_shugenja.pdf', exporters.FDFExporterShugenja())
        elif is_bushi or is_samurai_monk:
            self.write_pdf('sheet_bushi.pdf', exporters.FDFExporterBushi())
        elif is_monk:
            self.write_pdf('sheet_monk.pdf', exporters.FDFExporterMonk())
        if is_courtier:
            self.write_pdf(
                'sheet_courtier.pdf', exporters.FDFExporterCourtier())

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
        if len(self.pc.weapons) > 2:
            self.write_pdf('sheet_weapons.pdf', exporters.FDFExporterWeapons())

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
        self.pc.health_multiplier = val
        self.update_from_model()

    def damage_health(self, val):
        self.pc.wounds += val
        if self.pc.wounds < 0:
            self.pc.wounds = 0
        if self.pc.wounds > api.rules.get_max_wounds():
            self.pc.wounds = api.rules.get_max_wounds()

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
        adv = models.KataAdv(kata.id, kata.id, kata.mastery)
        adv.desc = self.tr('{0}, Cost: {1} xp').format(kata.name, adv.cost)

        if adv.cost > api.character.xp_left():
            return CMErrors.NOT_ENOUGH_XP

        self.pc.add_advancement(adv)
        self.update_from_model()

        return CMErrors.NO_ERROR

    def buy_kiho(self, kiho):
        kiho_cost = api.rules.calculate_kiho_cost(kiho.id)
        adv = models.KihoAdv(kiho.id, kiho.id, kiho_cost)
        adv.desc = self.tr('{0}, Cost: {1} xp').format(kiho.name, adv.cost)

        # monks can get free kihos
        free_kiho_ = api.character.rankadv.get_gained_kiho_count()

        if free_kiho_ > 0:
            adv.cost = 0
            free_kiho_ -= 1
            api.character.rankadv.set_gained_kiho_count(free_kiho_)
            log.app.info(u"free kiho left: %d", free_kiho_)

        if adv.cost > api.character.xp_left():
            return CMErrors.NOT_ENOUGH_XP

        self.pc.add_advancement(adv)
        self.update_from_model()

        return CMErrors.NO_ERROR

    def buy_tattoo(self, kiho):
        adv = models.KihoAdv(kiho.id, kiho.id, 0)
        adv.desc = self.tr('{0} Tattoo').format(kiho.name)

        self.pc.add_advancement(adv)
        self.update_from_model()

        return CMErrors.NO_ERROR

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
