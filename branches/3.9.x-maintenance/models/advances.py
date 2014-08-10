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
from datetime import datetime
import time

class Advancement(object):
    BUY_FOR_FREE = False
    @staticmethod
    def set_buy_for_free(flag):
        Advancement.BUY_FOR_FREE = flag
        print 'set buy for free? %s ' % Advancement.BUY_FOR_FREE

    @staticmethod
    def get_buy_for_free():
        print 'get buy for free? %s ' % Advancement.BUY_FOR_FREE
        return Advancement.BUY_FOR_FREE
        
    def __init__(self, tag, cost):
        self.type      = tag               
        self.desc      = ''
        self.rule      = None
        self.timestamp = time.time()
        
        if Advancement.get_buy_for_free():
            self.cost = 0
        else:
            self.cost  = cost

    def __str__(self):
        return self.desc

class AttribAdv(Advancement):
    def __init__(self, attrib, cost):
        super(AttribAdv, self).__init__('attrib', cost)
        self.attrib = attrib

class VoidAdv(Advancement):
    def __init__(self, cost):
        super(VoidAdv, self).__init__('void', cost)

class SkillAdv(Advancement):
    def __init__(self, skill, cost):
        super(SkillAdv, self).__init__('skill', cost)
        self.skill = skill

class SkillEmph(Advancement):
    def __init__(self, skill, text, cost):
        super(SkillEmph, self).__init__('emph', cost)
        self.skill = skill
        self.text  = text
        
class PerkAdv(Advancement):        
    def __init__(self, perk, rank, cost, tag = None):
        super(PerkAdv, self).__init__('perk', cost)
        self.perk  = perk
        self.rank  = rank
        self.tag   = tag
        self.extra = ''
        
class KataAdv(Advancement):        
    def __init__(self, kata_id, rule, cost):
        super(KataAdv, self).__init__('kata', cost)        
        self.kata = kata_id
        self.rule = rule
        
class KihoAdv(Advancement):        
    def __init__(self, kiho_id, rule, cost):
        super(KihoAdv, self).__init__('kiho', cost)        
        self.kiho = kiho_id
        self.rule = rule        
        
class MemoSpellAdv(Advancement):        
    def __init__(self, spell_id, cost):
        super(MemoSpellAdv, self).__init__('memo_spell', cost)        
        self.spell = spell_id

class AdvancementViewModel(QtCore.QAbstractListModel):
    def __init__(self, parent = None):
        super(AdvancementViewModel, self).__init__(parent)

        self.items = []
        self.text_color = QtGui.QBrush(QtGui.QColor(0x15, 0x15, 0x15))
        self.bg_color   = [ QtGui.QBrush(QtGui.QColor(0xFF, 0xEB, 0x82)),
                            QtGui.QBrush(QtGui.QColor(0xEB, 0xFF, 0x82)) ]
        self.item_size = QtCore.QSize(32, 32)

    def rowCount(self, parent = QtCore.QModelIndex()):
        return len(self.items)

    def add_item(self, item):
        row = self.rowCount()
        self.beginInsertRows(QtCore.QModelIndex(), row, row)
        self.items.append(item)
        self.endInsertRows()

    def clean(self):
        self.beginResetModel()
        self.items = []
        self.endResetModel()

    def update_from_model(self, model):
        self.clean()
        for adv in reversed(model.advans):
            self.add_item(adv)

    def data(self, index, role):
        if not index.isValid() or index.row() >= len(self.items):
            return None
        item = self.items[index.row()]
        if role == QtCore.Qt.DisplayRole:
            return item.type
        elif role == QtCore.Qt.ForegroundRole:
            return self.text_color
        elif role == QtCore.Qt.BackgroundRole:
            return self.bg_color[ index.row() % 2 ]
        elif role == QtCore.Qt.SizeHintRole:
            return self.item_size
        elif role == QtCore.Qt.UserRole:
            return item
        return None

class AdvancementItemDelegate(QtGui.QStyledItemDelegate):
    def __init__(self, parent = None):
        super(AdvancementItemDelegate, self).__init__(parent)

    def paint(self, painter, option, index):
        if not index.isValid():
            super(AdvancementItemDelegate, self).paint(painter, option, index)
            return

        item       = index.data(QtCore.Qt.UserRole)
        text_color = index.data(QtCore.Qt.ForegroundRole)
        bg_color   = index.data(QtCore.Qt.BackgroundRole)
        hg_color   = QtGui.QBrush(bg_color)
        hg_color.setStyle(QtCore.Qt.Dense3Pattern)

        painter.save()

        # fill the background color
        if option.state & QtGui.QStyle.State_Selected == QtGui.QStyle.State_Selected:
             painter.fillRect(option.rect, option.palette.highlight())
             text_color = option.palette.highlightedText()
        else:
            painter.fillRect(option.rect, bg_color)

        grid_pen = QtGui.QPen( QtCore.Qt.lightGray, 1 )
        painter.setPen(grid_pen)
        painter.drawLine(option.rect.bottomLeft(), option.rect.bottomRight())

        main_font = painter.font()
        sub_font = QtGui.QFont().resolve(main_font)
        sub_font.setPointSize(7)

        left_margin  = 15
        right_margin = 15

        # paint the airdate with a smaller font over the item name
        # suppose to have 24 pixels in vertical
        painter.setFont(sub_font)
        font_metric = painter.fontMetrics()
        adv_tp      = item.type
        adv_tp_rect = font_metric.boundingRect(adv_tp)

        text_pen = QtGui.QPen(text_color, 1)

        painter.setPen(text_pen)
        painter.drawText(left_margin + option.rect.left(), option.rect.top() + adv_tp_rect.height(), adv_tp)

        # paint adv type & cost
        #main_font.setBold(True)
        painter.setFont(main_font)
        font_metric = painter.fontMetrics()
        
        try:
            tmp = unicode(item).split(u',')
        except:        
            tmp = str(item).split(',')
            
        adv_time      = None        
        if hasattr(item, 'timestamp') and item.timestamp is not None:
            adv_time = "{0:%Y}-{0:%m}-{0:%d} {0:%H}:{0:%M}:{0:%S}".format(datetime.fromtimestamp(item.timestamp))
        
        if adv_time:
            adv_time_rect = font_metric.boundingRect(adv_time)
            painter.drawText(left_margin + option.rect.left(),
                             option.rect.top() + adv_tp_rect.height() + adv_time_rect.height(),
                             adv_time)
            left_margin += adv_time_rect.width() + left_margin
        
        main_font.setBold(True)  
        painter.setFont  (main_font)        
        
        adv_nm      = tmp[0]
        adv_nm_rect = font_metric.boundingRect(adv_nm)
        painter.drawText(left_margin + option.rect.left(),
                         option.rect.top() + adv_tp_rect.height() + adv_nm_rect.height(),
                         adv_nm)

        main_font.setBold(False)
        painter.setFont(main_font)
        adv_nm      = tmp[1]
        adv_nm_rect = font_metric.boundingRect(adv_nm)
        painter.drawText(option.rect.right()-adv_nm_rect.width()-right_margin,
                         option.rect.top() + adv_tp_rect.height() + adv_nm_rect.height(),
                         adv_nm)

        painter.restore()
