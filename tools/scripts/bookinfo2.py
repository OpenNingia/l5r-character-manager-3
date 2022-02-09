#! /usr/bin/env python

import xml.etree.ElementTree as ET
import shutil
import sys
import os

from PyQt5 import QtCore, QtGui, QtWidgets

class PackItemModel(object):
    def __init__(self):
        self.item_id = None
        self.name = ""
        self.page = ""
        self.desc = ""
        self.data = None

class PackItemViewModel(QtCore.QAbstractTableModel):

    def __init__(self, parent=None):
        super(PackItemViewModel, self).__init__(parent)

        self.items = []
        self.headers = [
            "Name",
            "Page",
            "Description"]

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self.items)

    def columnCount(self, parent=QtCore.QModelIndex()):
        return len(self.headers)

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        if orientation != QtCore.Qt.Horizontal:
            return None
        if role == QtCore.Qt.DisplayRole:
            return self.headers[section]
        return None

    def set_root(self, tree, file_name):
        self.tree = tree
        self.file_name = file_name

    def save(self):
        self.tree.write(self.file_name)

    def add_item(self, itm):
        row = self.rowCount()
        self.beginInsertRows(QtCore.QModelIndex(), row, row)
        self.items.append(itm)
        self.endInsertRows()

    def add_items(self, items):
        row = self.rowCount()
        self.beginInsertRows(QtCore.QModelIndex(), row, row + len(items) - 1)
        self.items += items
        self.endInsertRows()

    def clean(self):
        self.beginResetModel()
        self.items = []
        self.endResetModel()

    def data(self, index, role):
        if not index.isValid() or index.row() >= len(self.items):
            return None
        item = self.items[index.row()]
        if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole or role == QtCore.Qt.ToolTipRole:
            if index.column() == 0:
                return item.attrib['name']
            if index.column() == 1:
                return get_page_number(item)
            if index.column() == 2:
                return get_description(item)
        elif role == QtCore.Qt.UserRole:
            return item
        return None

    def setData(self, index, value, role):
        if not index.isValid():
            return False

        item = self.items[index.row()]
        ret = False
        if role == QtCore.Qt.EditRole:
            if index.column() == 1:
                item.attrib['page'] = value
                ret = True
            if index.column() == 2:
                set_description(item, value)
                ret = True
            else:
                ret = super(PackItemViewModel, self).setData(index, value, role)

            if ret:
                self.save()

        return ret

    def flags(self, index):
        if not index.isValid():
            return QtCore.Qt.ItemIsDropEnabled
        flags = QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled
        if index.column() == 1 or index.column() == 2:
            flags |= QtCore.Qt.ItemIsEditable
        return flags


class BookInfoEditor(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(BookInfoEditor, self).__init__(parent)

        self.setWindowTitle("Book info editor")
        self.model = PackItemViewModel()
        read_items(self.model)
        self.setMinimumSize(800, 600)
        table = self.build_grid()
        
        self.setCentralWidget(table)

        table.setVisible(False)
        table.resizeColumnsToContents()
        table.setVisible(True)        

    def build_grid(self):
        item_view = QtWidgets.QTableView()
        item_view.setSortingEnabled(True)
        item_view.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.Interactive)
        item_view.horizontalHeader().setStretchLastSection(True)
        item_view.horizontalHeader().setCascadingSectionResizes(True)
        item_view.doubleClicked.connect(self.on_item_activated)

        self._sort_model = QtCore.QSortFilterProxyModel(self)
        self._sort_model.setDynamicSortFilter(True)
        self._sort_model.setSourceModel(self.model)

        item_view.setModel(self._sort_model)
        item_view.setMinimumSize(600, 600)
        return item_view

    def on_item_activated(self, index):
        pass

def main():
    app = QtWidgets.QApplication(sys.argv)
    editor = BookInfoEditor()
    editor.show()

    sys.exit(app.exec_())

def read_input(prompt):
    print(prompt)
    buffer = []    
    prev = None
    while True:
        line = sys.stdin.readline().rstrip('\n')
        if line == '' and prev == '':
            break
        else:
            buffer.append(line)
            prev = line
    return ' '.join(buffer)

def read_sub_element_text(xml_element, sub_element_name, default_value=None):
    return xml_element.find(sub_element_name).text if (
    xml_element.find(sub_element_name) is not None) else default_value

def write_sub_element_text(xml_element, sub_element_name, text=""):
    sub_elem = xml_element.find(sub_element_name)
    if sub_elem is None:
        sub_elem = ET.Element(sub_element_name)
        sub_elem.text = text
        xml_element.append(sub_elem)
    else:
        print(f'set text sub element {sub_element_name}')
        sub_elem.text = text

def get_page_number(elem):
    if 'page' in elem.attrib:
        return elem.attrib['page']
    return ''

def set_page_number(elem, pg):
    elem.attrib['page'] = pg

def get_description(elem):
    return read_sub_element_text(elem, "Description")

def set_description(elem, text):
    lines = text.split()
    text = ' '.join(lines)
    write_sub_element_text(elem, "Description", text)

def read_items(model):
    file_name = sys.argv[1]

    # backup original
    backup_file = file_name + '.bak'
    if not os.path.exists(backup_file):
        shutil.copyfile(file_name, backup_file)

    tree = ET.parse(file_name)
    root = tree.getroot()
    model.set_root(tree, file_name)

    for elem in root:
        model.add_item(elem)
        #normalize, just one run
        #desc = get_description(elem)
        #if desc:
        #    set_description(elem, desc)
    #tree.write(file_name)


if __name__ == '__main__':
    main()