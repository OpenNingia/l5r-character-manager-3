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

from PySide import QtGui, QtCore
import dal
import dal.query

class TechItemModel(object):
    def __init__(self):
        self.name        = ''
        self.school_name = ''
        self.rank        = ''
        self.desc        = ''
        self.id          = ''

    def __str__(self):
        return self.name

    def __lt__(self, obj):
        return self.rank < obj.rank

    def __eq__(self, obj):
        return self.rank == obj.rank

    def __ne__(self, obj):
        return not self.__eq__(obj)

    def __hash__(self):
        return self.rank.__hash__()

class TechViewModel(QtCore.QAbstractListModel):
    def __init__(self, dstore, parent = None):
        super(TechViewModel, self).__init__(parent)

        self.dstore = dstore
        self.items = []
        self.text_color = QtGui.QBrush(QtGui.QColor(0x15, 0x15, 0x15))
        self.bg_color   = [ QtGui.QBrush(QtGui.QColor(0xFF, 0xEB, 0x82)),
                            QtGui.QBrush(QtGui.QColor(0xEB, 0xFF, 0x82)) ]
        self.item_size = QtCore.QSize(32, 32)

    def rowCount(self, parent = QtCore.QModelIndex()):
        return len(self.items)

    def build_item_model(self, tech_id, adjusted_rank = 0):
        itm = TechItemModel()

        school, tech = dal.query.get_tech(self.dstore, tech_id)
        if tech and school:
            itm.name         = tech.name
            itm.id           = tech_id
            itm.school_name  = school.name
            if adjusted_rank == 0:
                itm.rank         = str(tech.rank)
            else:
                itm.rank         = str(adjusted_rank)
        return itm

    def add_item(self, item_id, adjusted_rank):
        row = self.rowCount()
        self.beginInsertRows(QtCore.QModelIndex(), row, row)
        self.items.append(self.build_item_model(item_id, adjusted_rank))
        self.endInsertRows()

    def clean(self):
        self.beginResetModel()
        self.items = []
        self.endResetModel()

    def update_from_model(self, model):
        self.clean()
        for tech in model.get_techs():
            adjusted_rank = self.adjust_tech_rank(model, tech)
            self.add_item(tech, adjusted_rank)
        # sort by rank
        self.items.sort()

    def adjust_tech_rank(self, model, tech_id):
        paths = [x for x in model.schools if x.is_path and tech_id in x.techs]
        if len(paths):
            return paths[0].path_rank
        return 0

    def data(self, index, role):
        if not index.isValid() or index.row() >= len(self.items):
            return None
        item = self.items[index.row()]
        if role == QtCore.Qt.DisplayRole:
            return item.name
        elif role == QtCore.Qt.ForegroundRole:
            return self.text_color
        elif role == QtCore.Qt.BackgroundRole:
            return self.bg_color[ index.row() % 2 ]
        elif role == QtCore.Qt.SizeHintRole:
            return self.item_size
        elif role == QtCore.Qt.UserRole:
            return item
        return None

class TechItemDelegate(QtGui.QStyledItemDelegate):
    def __init__(self, parent = None):
        super(TechItemDelegate, self).__init__(parent)

    def paint(self, painter, option, index):
        if not index.isValid():
            super(TechItemDelegate, self).paint(painter, option, index)
            return

        item       = index.data(QtCore.Qt.UserRole)
        text_color = index.data(QtCore.Qt.ForegroundRole)
        bg_color   = index.data(QtCore.Qt.BackgroundRole)
        hg_color   = QtGui.QBrush(bg_color)
        hg_color.setStyle(QtCore.Qt.Dense3Pattern)

        painter.save()

        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, True);

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

        margin = 15

        # paint the airdate with a smaller font over the item name
        # suppose to have 24 pixels in vertical
        main_font.setBold(True)
        painter.setFont(main_font)
        font_metric = painter.fontMetrics()
        tech_nm      = item.name
        tech_nm_rect = font_metric.boundingRect(tech_nm)
        rank         = item.rank

        rank_pen = QtGui.QPen(text_color, 2)
        painter.setPen(rank_pen)
        rank_rect = QtCore.QRectF( float(option.rect.left() + margin),
                                   float(option.rect.top() + 5),
                                   float(option.rect.height() - 10), float(option.rect.height() - 10) )
        painter.drawRect ( rank_rect )
        painter.drawText ( rank_rect.adjusted(8, 3.5, 0, 0), rank)

        margin += rank_rect.width() + margin

        text_pen = QtGui.QPen(text_color, 1)

        painter.setPen(text_pen)
        painter.drawText(margin + option.rect.left(), option.rect.top() + tech_nm_rect.height(), tech_nm)

        # paint adv type & cost
        painter.setFont(sub_font)
        font_metric    = painter.fontMetrics()
        school_nm      = item.school_name
        school_nm_rect = font_metric.boundingRect(school_nm)
        painter.drawText(margin + option.rect.left(),
                         option.rect.top() + tech_nm_rect.height() + school_nm_rect.height(),
                         school_nm)

        painter.restore()
