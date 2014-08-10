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

import iconloader

from toolbar_rc import *

class SimpleRichEditor(QtGui.QWidget):
    def __init__(self, parent = None):
        super(SimpleRichEditor, self).__init__(parent)
        self.text_area = QtGui.QTextEdit(self)
        self.text_area.setFrameShadow(QtGui.QFrame.Plain)
        self.text_area.setAutoFormatting(QtGui.QTextEdit.AutoAll)
        self.text_area.setUndoRedoEnabled(True)
        self.text_area.setReadOnly(False)
        self.text_area.setTextInteractionFlags(
                       QtCore.Qt.LinksAccessibleByKeyboard |
                       QtCore.Qt.LinksAccessibleByMouse |
                       QtCore.Qt.TextBrowserInteraction |
                       QtCore.Qt.TextEditable |
                       QtCore.Qt.TextEditorInteraction |
                       QtCore.Qt.TextSelectableByMouse)
        vbox = QtGui.QVBoxLayout(self)
        vbox.addWidget(self.create_toolbar())
        vbox.addWidget(self.text_area)

        self.text_area.cursorPositionChanged.connect(self.update_format_buttons)
        self.text_area.cursorPositionChanged.connect(self.update_font_combo)

    def create_toolbar(self):
        bts = []
        tb_frame = QtGui.QFrame(self)
        tb_hbox  = QtGui.QHBoxLayout(tb_frame)

        # EDIT
        bts.append(self.create_tb_button("edit-clear", self.text_area.clear))
        bts.append(self.create_tb_button("edit-copy" , self.text_area.copy ))
        bts.append(self.create_tb_button("edit-cut"  , self.text_area.cut  ))
        bts.append(self.create_tb_button("edit-paste", self.text_area.paste))
        bts.append(None)

        # FORMAT
        bts.append(self.create_tb_button("format-indent-less",
                                         self.format_indent_less))
        bts.append(self.create_tb_button("format-indent-more",
                                         self.format_indent_more))
        bts.append(self.create_tb_button("format-justify-left",
                                         self.format_justify_left))
        bts.append(self.create_tb_button("format-justify-center",
                                         self.format_justify_center))
        bts.append(self.create_tb_button("format-justify-right",
                                         self.format_justify_right))
        bts.append(self.create_tb_button("format-justify-fill",
                                         self.format_justify_fill))
        bts.append(None)
        self.bt_bold   = self.create_tb_button("format-text-bold",
                                         self.format_text_bold,
                                         True)
        self.bt_italic = self.create_tb_button("format-text-italic",
                                         self.format_text_italic,
                                         True)
        self.bt_uline  = self.create_tb_button("format-text-underline",
                                         self.format_text_underline,
                                         True)
        self.bt_strike = self.create_tb_button("format-text-strikethrough",
                                         self.format_text_strikethrough,
                                         True)
        bts += [self.bt_bold, self.bt_italic, self.bt_uline, self.bt_strike]
        bts.append(None)

        # INSERT
        #bts.append(self.create_tb_button("insert-link", self.insert_link))
        bts.append(self.create_tb_button("list-enum", self.list_enum))
        bts.append(self.create_tb_button("list-bullet", self.list_bullet))

        for tb in bts:
            if tb is None:
                tb_hbox.addSpacing(20)
            else:
                tb_hbox.addWidget(tb)

        tb_hbox.addSpacing(20)

        # FONT COMBOBOX
        self.cb_fonts = QtGui.QFontComboBox(self)
        self.cb_fonts.activated.connect(self.text_area.setFontFamily)
        tb_hbox.addWidget(self.cb_fonts)

        # FONT SIZES
        self.cb_font_size = QtGui.QComboBox(self)
        for i in xrange(6, 17):
            self.cb_font_size.addItem( str(i) )
        for i in xrange(18, 96, 2):
            self.cb_font_size.addItem( str(i) )
        self.cb_font_size.activated.connect(self.set_font_size)
        tb_hbox.addWidget(self.cb_font_size)
        tb_hbox.setContentsMargins(0,5,0,5)
        tb_hbox.setSpacing(2)

        return tb_frame

    def create_tb_button(self, icon_text, actv_slot, is_toggle = False):
        tb = QtGui.QToolButton(self)
        tb.setIcon(iconloader.icon(icon_text,
                                       QtGui.QIcon(':/icons/%s.png' % icon_text)
                                       ))
        tb.setCheckable(is_toggle)
        if is_toggle:
            tb.toggled.connect(actv_slot)
        else:
            tb.clicked.connect(actv_slot)
        return tb

    def format_indent_less(self):
        cursor = QtGui.QTextCursor(self.text_area.textCursor())
        block_fmt = cursor.blockFormat()
        if block_fmt.indent() <= 0:
            return
        block_fmt.setIndent(block_fmt.indent()-1)
        cursor.beginEditBlock()
        cursor.setBlockFormat(block_fmt)

        if cursor.currentList():
            bfmt = QtGui.QTextBlockFormat()
            bfmt.setObjectIndex(-1)
            cursor.mergeBlockFormat(bfmt)

            if (cursor.currentList().format().style() ==
                QtGui.QTextListFormat.ListDecimal):
                self.update_enum_list(cursor, block_fmt)
            else:
                self.update_bullet_list(cursor, block_fmt)

        cursor.endEditBlock()

    def format_indent_more(self):
        cursor = QtGui.QTextCursor(self.text_area.textCursor())
        block_fmt = cursor.blockFormat()
        block_fmt.setIndent(block_fmt.indent()+1)
        cursor.beginEditBlock()
        cursor.setBlockFormat(block_fmt)

        if cursor.currentList():
            if (cursor.currentList().format().style() ==
                QtGui.QTextListFormat.ListDecimal):
                self.update_enum_list(cursor, block_fmt)
            else:
                self.update_bullet_list(cursor, block_fmt)

        cursor.endEditBlock()

    def format_justify_left(self):
        self.text_area.setAlignment(QtCore.Qt.AlignLeft)

    def format_justify_center(self):
        self.text_area.setAlignment(QtCore.Qt.AlignCenter)

    def format_justify_right(self):
        self.text_area.setAlignment(QtCore.Qt.AlignRight)

    def format_justify_fill(self):
        self.text_area.setAlignment(QtCore.Qt.AlignJustify)

    def format_text_bold(self, flag):
        self.text_area.setFontWeight( QtGui.QFont.Bold if flag else 0 )

    def format_text_italic(self, flag):
        self.text_area.setFontItalic(flag)

    def format_text_underline(self, flag):
        self.text_area.setFontUnderline(flag)

    def format_text_strikethrough(self, flag):
        format = self.text_area.currentCharFormat()
        format.setFontStrikeOut(flag)
        self.text_area.mergeCurrentCharFormat(format)

    def insert_link(self):
        pass

    def get_bullet_style(self, indent):
        if indent == 0:
            return QtGui.QTextListFormat.ListDisc
        elif indent == 1:
            return QtGui.QTextListFormat.ListCircle
        else:
            return QtGui.QTextListFormat.ListSquare

    def list_enum(self):
        cursor = QtGui.QTextCursor(self.text_area.textCursor())
        style    = QtGui.QTextListFormat.ListDecimal

        cursor.beginEditBlock()
        block_fmt = cursor.blockFormat()
        list_fmt  = QtGui.QTextListFormat()

        if cursor.currentList():
            list_fmt = cursor.currentList().format()
        else:
            list_fmt.setIndent(block_fmt.indent() + 1)
            block_fmt.setIndent(0)
            cursor.setBlockFormat(block_fmt)

        list_fmt.setStyle(style)
        cursor.createList(list_fmt)
        cursor.endEditBlock()

    def list_bullet(self):
        cursor = QtGui.QTextCursor(self.text_area.textCursor())
        block_fmt = cursor.blockFormat()
        style    = self.get_bullet_style(block_fmt.indent())
        cursor.beginEditBlock()
        list_fmt  = QtGui.QTextListFormat()

        if cursor.currentList():
            list_fmt = cursor.currentList().format()
        else:
            list_fmt.setIndent(block_fmt.indent() + 1)
            block_fmt.setIndent(0)
            cursor.setBlockFormat(block_fmt)

        list_fmt.setStyle(style)
        cursor.createList(list_fmt)
        cursor.endEditBlock()

    def set_font_size(self, value):
        try:
            size_ = float(value)
            self.text_area.setFontPointSize(size_)
        except:
            pass

    def update_bullet_list(self, cursor, block_fmt):
        list_fmt = cursor.currentList().format()
        style    = self.get_bullet_style(block_fmt.indent())
        list_fmt.setStyle(style)
        cursor.createList(list_fmt)

    def update_enum_list(self, cursor, block_fmt):
        list_fmt = cursor.currentList().format()
        style    = QtGui.QTextListFormat.ListDecimal
        list_fmt.setStyle(style)
        cursor.createList(list_fmt)

    def update_font_combo(self):
        font = self.text_area.currentFont()
        self.cb_fonts.setCurrentFont(font)
        self.cb_font_size.setCurrentIndex(
            self.cb_font_size.findText(str(font.pointSize())))

    def update_format_buttons(self):
        self.bt_bold  .setChecked(True if self.text_area.fontWeight() >=
                                QtGui.QFont.Bold else False)
        self.bt_italic.setChecked(self.text_area.fontItalic())
        self.bt_uline .setChecked(self.text_area.fontUnderline())

        cursor = QtGui.QTextCursor(self.text_area.textCursor())
        block_fmt = cursor.charFormat()
        self.bt_strike.setChecked(block_fmt.fontStrikeOut())

    def set_content(self, stuff):
        self.text_area.setHtml(stuff)

    def get_content(self):
        return self.text_area.toHtml()

    def get_plain_text(self):
        return self.text_area.toPlainText()

def test():
    import sys
    app = QtGui.QApplication(sys.argv)

    dlg = QtGui.QDialog()
    vbox = QtGui.QVBoxLayout(dlg)
    vbox.addWidget( SimpleRichEditor() )
    dlg.show()

    sys.exit(app.exec_())

if __name__ == '__main__':
    test()
