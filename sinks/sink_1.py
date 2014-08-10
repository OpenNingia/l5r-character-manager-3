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

from PySide import QtCore, QtGui

import rules
import dialogs
import models
import os
import osutil

from l5rcmcore import get_app_file, DB_VERSION, get_icon_path

class Sink1(QtCore.QObject):
    def __init__(self, parent = None):
        super(Sink1, self).__init__(parent)
        self.form = parent

    def new_character(self):
        form = self.form
        
        form.last_rank = 1
        form.save_path = ''
        form.pc = models.AdvancedPcModel()
        form.pc.load_default()
        form.load_clans   (  )
        form.load_families('')
        form.load_schools ('')
        form.tx_pc_notes.set_content('')
        form.pc.set_insight_calc_method(form.ic_calc_method)
        form.update_from_model()

    def load_character(self):        
        form = self.form
        path = form.select_load_path()
        form.load_character_from(path)
        
    def save_character(self):
        form = self.form        
        if form.save_path == '' or not os.path.exists(form.save_path):
            form.save_path = form.select_save_path()

        if form.save_path is not None and len(form.save_path) > 0:
            form.pc.version = DB_VERSION
            form.pc.extra_notes = form.tx_pc_notes.get_content()
            # pending rank advancement?
            form.pc.last_rank = form.last_rank
            form.pc.save_to(form.save_path)
            
    def export_character_as_text(self):
        form = self.form
        
        file_ = form.select_export_file()
        if len(file_) > 0:
            form.export_as_text(file_)

    def export_character_as_pdf(self):
        form = self.form
        
        file_ = form.select_export_file(".pdf")
        if len(file_) > 0:
            form.export_as_pdf(file_)
            
    def switch_to_page_1(self):
        self.form.tabs.setCurrentIndex(0)

    def switch_to_page_2(self):
        self.form.tabs.setCurrentIndex(1)

    def switch_to_page_3(self):
        self.form.tabs.setCurrentIndex(2)

    def switch_to_page_4(self):
        self.form.tabs.setCurrentIndex(3)

    def switch_to_page_5(self):
        self.form.tabs.setCurrentIndex(4)
        
    def switch_to_page_6(self):
        self.form.tabs.setCurrentIndex(5)

    def switch_to_page_7(self):
        self.form.tabs.setCurrentIndex(6)
        
    def reset_adv(self):
        form = self.form
        
        form.pc.advans = []
        form.pc.recalc_ranks()
        form.update_from_model()
        
    def refund_last_adv(self):
        form = self.form
        '''pops last advancement and recalculate ranks'''
        if len(form.pc.advans) > 0:
            adv = form.pc.advans.pop()            
            form.pc.recalc_ranks()
            form.update_from_model()
                    
    def act_buy_perk(self):
        form = self.form
        
        dlg = dialogs.BuyPerkDialog(form.pc, self.sender().property('tag'),
                                    form.dstore, form)
        dlg.exec_()
        form.update_from_model()   

    def generate_name(self):
        '''generate a random name for the character'''        
        form = self.form
        
        gender = self.sender().property('gender')
        name = ''
        if gender == 'male':
            name = rules.get_random_name( get_app_file('male.txt') )
        else:
            name = rules.get_random_name( get_app_file('female.txt') )
        form.pc.name = name
        form.update_from_model()

    def show_dice_roller(self):
        import diceroller
        dlg = diceroller.DiceRoller(self.form)
        dlg.show()        
        
    def show_wear_armor(self):
        form = self.form
        
        dlg = dialogs.ChooseItemDialog(form.pc, 'armor', form.dstore, form)
        if dlg.exec_() == QtGui.QDialog.DialogCode.Accepted:
            form.update_from_model()

    def show_wear_cust_armor(self):
        form = self.form
        
        dlg = dialogs.CustomArmorDialog(form.pc, form)
        if dlg.exec_() == QtGui.QDialog.DialogCode.Accepted:
            form.update_from_model()

    def show_add_misc_item(self):
        pass
        
    def on_set_exp_limit(self):
        form = self.form
        
        ok = False
        val, ok = QtGui.QInputDialog.getInt(form, 'Set Experience Limit',
                                       "XP Limit:", form.pc.exp_limit,
                                        0, 10000, 1)
        if ok:
            form.set_exp_limit(val)

    def on_set_wnd_mult(self):
        form = self.form
        
        ok = False
        val, ok = QtGui.QInputDialog.getInt(form, 'Set Health Multiplier',
                                       "Multiplier:", form.pc.health_multiplier,
                                        2, 5, 1)
        if ok:
            form.set_health_multiplier(val)

    def on_damage_act(self):
        form = self.form
        
        ok = False
        val, ok = QtGui.QInputDialog.getInt(form, 'Cure/Inflict Damage',
                                       "Wounds:", 1,
                                        -1000, 1000, 1)
        if ok:
            form.damage_health(val)

    def on_unlock_school_act(self):
        form = self.form
        form.cb_pc_school.blockSignals(True)
        form.pc.toggle_unlock_schools()
        if form.pc.unlock_schools:
            form.bt_school_lock.setIcon( QtGui.QIcon(get_icon_path('lock_open',(16,16))) )
            form.load_schools ()            
        else:
            form.bt_school_lock.setIcon( QtGui.QIcon(get_icon_path('lock_close',(16,16))) )
            form.load_schools(form.pc.clan or '')
        form.cb_pc_school.blockSignals(False)
        form.update_from_model()

    def warn_about_refund(self):
        form = self.form
        settings = QtCore.QSettings()
        
        if settings.value('warn_about_refund', 'true') == 'false':
            return True
            
        msgBox = QtGui.QMessageBox(form)
        msgBox.setWindowTitle('L5R: CM')
        msgBox.setText(self.tr("Advancements refund."))
        msgBox.setInformativeText(self.tr(  
            "If this advancement is required from other ones\n"
            "removing it might lean to incoherences in your character.\n"
            "Continue anyway?"))
            
        do_not_prompt_again = QtGui.QCheckBox(self.tr("Do not prompt again"), msgBox)
        do_not_prompt_again.blockSignals(True) # PREVENT MSGBOX TO CLOSE ON CLICK
        msgBox.addButton(QtGui.QMessageBox.Yes)
        msgBox.addButton(QtGui.QMessageBox.No)
        msgBox.addButton(do_not_prompt_again, QtGui.QMessageBox.ActionRole)
        msgBox.setDefaultButton(QtGui.QMessageBox.No)
        result = msgBox.exec_()
        if do_not_prompt_again.checkState() == QtCore.Qt.Checked:
            settings.setValue('warn_about_refund', 'false')
        if result == QtGui.QMessageBox.Yes:
            return True
        return False          
          
    def refund_advancement(self, adv_idx = -1):
        '''refund the specified advancement and recalculate ranks'''        
        form = self.form
        
        if adv_idx < 0:
            adv_idx = len(form.pc.advans) - form.adv_view.selectionModel().currentIndex().row() - 1
        if adv_idx >= len(form.pc.advans) or adv_idx < 0:            
            return self.refund_last_adv()

        if self.warn_about_refund():            
            del form.pc.advans[adv_idx]        
            form.pc.recalc_ranks()
            form.update_from_model()
            return True
        return False


    #OPTIONS
    def on_toggle_buy_for_free(self, flag):
        models.Advancement.set_buy_for_free(flag)

    def on_toggle_display_banner(self):
        form = self.form

        settings = QtCore.QSettings()
        lIsBannerEnabled = settings.value('isbannerenabled')

        if(lIsBannerEnabled == 1):
            lIsBannerEnabled = 0
        else:
            lIsBannerEnabled = 1
        settings.setValue('isbannerenabled', lIsBannerEnabled)

        for i in xrange(0, form.mvbox.count()):
            logo = form.mvbox.itemAt(i).widget()
            if (logo.objectName() == 'BANNER'):
                if(lIsBannerEnabled == 1):
                    logo.show()
                else:
                    logo.hide()
                    form.widgets.adjustSize()
                    form.widgets.resize(1,1)
                    form.widgets.setGeometry( QtCore.QRect(0, 0, 727, 573) )
                break
        #form.widgets.adjustSize()

    def open_image_dialog(self):
        supported_ext     = ['.png']
        supported_filters = [self.tr("PNG Images (*.png)")]

        settings = QtCore.QSettings()
        last_data_dir = settings.value('last_open_image_dir', QtCore.QDir.homePath())
        fileName = QtGui.QFileDialog.getOpenFileName(
                                self.form,
                                self.tr("Open image"),
                                last_data_dir,
                                ";;".join(supported_filters))
        if len(fileName) != 2:
            return None

        last_data_dir = os.path.dirname(fileName[0])
        if last_data_dir != '':
            settings.setValue('last_open_image_dir', last_data_dir)
        return fileName[0]

    def open_color_dialog(self):
        form = self.form
        settings = QtCore.QSettings()
        lBackgroundColor = settings.value('backgroundcolor')
        color = QtGui.QColor()

        if(lBackgroundColor is not None):
            color = QtGui.QColor(lBackgroundColor)
        
        if(not color.isValid()):
            color = QtGui.QColor('#000000')

        color = QtGui.QColorDialog.getColor(color, form)
        return color

    def on_set_background_color(self):
        form = self.form
        color = self.open_color_dialog()
        if not color: return

        if color.isValid():
            form.view.setStyleSheet("background-color:%s;" % color.name())
            settings = QtCore.QSettings()
            settings.setValue('backgroundcolor', color.name())

    def on_set_background(self):
        file = self.open_image_dialog()
        if not file: return

        settings = QtCore.QSettings()
        settings.setValue('background_image', file)

        self.form.update_background_image()

    def on_rem_background(self):
        form = self.form
        settings = QtCore.QSettings()
        settings.setValue('background_image', '')
        form.view.set_wallpaper( None )
            
    def open_data_dir_act(self):
        path = os.path.normpath(osutil.get_user_data_path())
        if not os.path.exists(path):
            os.makedirs(path)
        osutil.portable_open(path)

    def on_reset_geometry(self):
        form = self.form
        form.reset_geometry()

