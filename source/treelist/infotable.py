# coding=utf-8
# -----------------
# file      : infotable.py
# date      : 2012/11/18
# author    : Victor Zarubkin
# contact   : victor.zarubkin@gmail.com
# copyright : Copyright (C) 2012  Victor Zarubkin
# license   : This file is part of BehaviorStudio.
#           :
#           : BehaviorStudio is free software: you can redistribute it and/or modify
#           : it under the terms of the GNU General Public License as published by
#           : the Free Software Foundation, either version 3 of the License, or
#           : (at your option) any later version.
#           :
#           : BehaviorStudio is distributed in the hope that it will be useful,
#           : but WITHOUT ANY WARRANTY; without even the implied warranty of
#           : MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#           : GNU General Public License for more details.
#           :
#           : You should have received a copy of the GNU General Public License
#           : along with BehaviorStudio. If not, see <http://www.gnu.org/licenses/>.
#           :
#           : A copy of the GNU General Public License can be found in file COPYING.
############################################################################

"""

"""

from __future__ import unicode_literals

__author__ = 'Victor Zarubkin'
__copyright__ = 'Copyright (C) 2012  Victor Zarubkin'
__credits__ = ['Victor Zarubkin']
__license__ = ['GPLv3']
__version__ = '1.3.0'  # this is last application version when this script file was changed
__email__ = 'victor.zarubkin@gmail.com'
############################################################################

from PySide import QtCore
from PySide.QtCore import *
from PySide.QtGui import *

from treenode import AttrTypeData

#######################################################################################################################
#######################################################################################################################


class TableDataEdit(QLineEdit):
    valueChange = QtCore.Signal(int, int, str)

    def __init__(self, row, column, attrDesc, data, parent=None):
        QLineEdit.__init__(self, attrDesc.value2str2(data), parent)

        self.row = row
        self.column = column
        self.data = data
        self.desc = attrDesc

        if self.desc.typeClass() == AttrTypeData.INT:
            self.setValidator(QIntValidator())
        elif self.desc.typeClass() == AttrTypeData.REAL:
            self.setValidator(QDoubleValidator())

        validator = None
        if self.desc.typeClass() == AttrTypeData.INT:
            validator = QIntValidator()
            if self.desc.minValue() is not None:
                validator.setBottom(self.desc.minValue())
            if self.desc.maxValue() is not None:
                validator.setBottom(self.desc.maxValue())
        elif self.desc.typeClass() == AttrTypeData.EXT:
            if self.desc.minValue() is not None and self.desc.minValue() >= 0:
                self.setInputMask('9000000000')
            elif self.desc.maxValue() is not None and self.desc.maxValue() < 0:
                self.setInputMask('-9000000000')
            else:
                self.setInputMask('#9000000000')
        elif self.desc.typeClass() == AttrTypeData.CINT64:
            if self.desc.minValue() is not None and self.desc.minValue() >= 0:
                self.setInputMask('\\0\\xHHHHHHHHHHHHHHHH ULL;.')
            elif self.desc.maxValue() is not None and self.desc.maxValue() < 0:
                self.setInputMask('-\\0\\xHHHHHHHHHHHHHHHH LL;.')
            else:
                self.setInputMask('#\\0\\xHHHHHHHHHHHHHHHH LL;.')
        elif self.desc.typeClass() == AttrTypeData.LONG:
            if self.desc.minValue() is not None and self.desc.minValue() >= 0:
                self.setInputMask('9000000000000000000000000000000000000000')
            elif self.desc.maxValue() is not None and self.desc.maxValue() < 0:
                self.setInputMask('-9000000000000000000000000000000000000000')
            else:
                self.setInputMask('#9000000000000000000000000000000000000000')
        elif self.desc.typeClass() == AttrTypeData.REAL:
            validator = QDoubleValidator()
            validator.setDecimals(12)
            if self.desc.minValue() is not None:
                validator.setBottom(self.desc.minValue())
            if self.desc.maxValue() is not None:
                validator.setBottom(self.desc.maxValue())
        else:
            validator = None

        if validator is not None:
            self.setValidator(validator)

        self.__prevText = self.text()
        self.textEdited.connect(self.onTextEditing)

    def sizeHint(self):
        if self.desc.typeClass() != AttrTypeData.STR:
            return QSize(len(self.text()) * 7, self.height())
        return QLineEdit.sizeHint(self)

    @QtCore.Slot(str)
    def onTextEditing(self, text):
        valid, validtext = self.validateValue(text)
        if valid:
            if self.text() != self.__prevText:
                self.valueChange.emit(self.row, self.column, validtext)
            self.__prevText = self.text()

    def validateValue(self, text):
        valid = True
        if self.desc.typeClass() == AttrTypeData.STR:
            return valid, text
        validText = text.lower()
        if 'ull' in validText:
            validText = validText.replace('ull', '')
        elif 'll' in validText:
            validText = validText.replace('ll', '')
        validText = validText.strip()
        if len(validText) < 1 or validText in ('-', '+'):
            valid = False
            validText = '<input number>'
        else:
            negative = (validText[0] == '-')
            if self.desc.typeClass() == AttrTypeData.REAL:
                if 'e' in validText:
                    texts = validText.split('e')
                    if len(texts[1]) < 1 or texts[1] in ('-', '+') or len(texts[0]) < 1:
                        valid = False
            elif self.desc.typeClass() == AttrTypeData.CINT64:
                if 'x' in validText:
                    texts = validText.split('x')
                    if len(texts[1]) < 1 or len(texts[0]) < 1 or texts[0] not in ('-0', '+0', '0'):
                        valid = False
                        if negative:
                            validText = '-0xHHHHHHHHHHHHHHHH'
                        else:
                            validText = '0xHHHHHHHHHHHHHHHH'
            if valid and self.desc.minValue() is not None:
                f = self.desc.str2value(validText)
                if f < self.desc.minValue():
                    validText = self.desc.value2str2(self.desc.minValue())
                    valid = False
            if valid and self.desc.maxValue() is not None:
                f = self.desc.str2value(validText)
                if f > self.desc.maxValue():
                    validText = self.desc.value2str2(self.desc.maxValue())
                    valid = False
        return valid, validText

#######################################################################################################################
#######################################################################################################################


class TaskBoolCombo(QComboBox):
    valueChange = QtCore.Signal(int, int, bool)

    def __init__(self, row, column, value, parent=None):
        QComboBox.__init__(self, parent)
        self.row = row
        self.column = column
        self.addItem('True', True)
        self.addItem('False', False)
        self.setCurrentIndex(self.findData(value))
        self.value = value
        self.currentIndexChanged.connect(self.onIndexChange)

    def onIndexChange(self, index):
        self.value = self.itemData(index)
        self.valueChange.emit(self.row, self.column, self.value)

#######################################################################################################################
#######################################################################################################################


class TaskAttributesTable(QTableWidget):
    attributeChanged = QtCore.Signal()

    def __init__(self, attrs, editMode=False, parent=None):
        QTableWidget.__init__(self, parent)
        self.setSortingEnabled(False)
        self.setSelectionMode(QAbstractItemView.NoSelection)
        self.verticalHeader().hide()
        self.__editMode = False
        self.__attributes = attrs
        self.__indexes = []
        self.updateData(attrs, editMode)

    def onComboChange(self, row, col, bool_value):
        self.__attributes[self.__indexes[row]].setActualValue(bool_value)
        self.attributeChanged.emit()

    def onEditChange(self, row, col, text):
        text.strip()
        if len(text) < 1 or text == '-' or text == '+':
            text = '0'
        self.__attributes[self.__indexes[row]].setValue(text)
        self.attributeChanged.emit()

    def updateData(self, attrs, editMode=False):
        self.clear()

        if type(editMode) is bool:
            self.__editMode = editMode
        else:
            self.__editMode = False

        self.__attributes = attrs
        self.__indexes = []

        self.setColumnCount(3)
        self.setRowCount(len(self.__attributes))
        self.setHorizontalHeaderLabels(['type', 'name', 'value'])

        row = 0
        for a in self.__attributes:
            item0 = QTableWidgetItem(self.__attributes[a].attrDesc().typeName())
            item0.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            if self.__attributes[a].attrDesc().description:
                item0.setToolTip(self.__attributes[a].attrDesc().description)
            self.setItem(row, 0, item0)

            item1 = QTableWidgetItem(self.__attributes[a].attrDesc().name())
            item1.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            if self.__attributes[a].attrDesc().description:
                item1.setToolTip(self.__attributes[a].attrDesc().description)
            self.setItem(row, 1, item1)

            if not self.__editMode:
                item2 = QTableWidgetItem(str(self.__attributes[a].value()))
                item2.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                self.setItem(row, 2, item2)
            elif self.__attributes[a].attrDesc().typeClass() == AttrTypeData.BOOL:
                item2 = TaskBoolCombo(row, 2, self.__attributes[a].value(), self)
                self.setCellWidget(row, 2, item2)
                item2.valueChange.connect(self.onComboChange)
            else:
                item2 = TableDataEdit(row, 2, self.__attributes[a].attrDesc(), self.__attributes[a].value(), self)
                self.setCellWidget(row, 2, item2)
                item2.valueChange.connect(self.onEditChange)
            if self.__attributes[a].attrDesc().description:
                item2.setToolTip(self.__attributes[a].attrDesc().description)

            self.__indexes.append(a)
            row += 1

        self.resizeColumnsToContents()
        self.resizeRowsToContents()

#######################################################################################################################
#######################################################################################################################
