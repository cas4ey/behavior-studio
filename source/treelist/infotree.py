# coding=utf-8
# -----------------
# file      : infotree.py
# date      : 2012/11/25
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
from extensions.widgets import comboBoxScrollProxy

from treenode import AttrTypeData

######################################################################################################################

TREE_ITEMS_HEIGHT = 15

#######################################################################################################################
#######################################################################################################################


class LowCombobox(QComboBox):
    def __init__(self, *args, **kwargs):
        QComboBox.__init__(self, *args, **kwargs)
        self._focusProxy = comboBoxScrollProxy(self)

    def sizeHint(self, *args, **kwargs):
        sizehint = QComboBox.sizeHint(self, *args, **kwargs)
        sizehint.setHeight(TREE_ITEMS_HEIGHT)
        return sizehint

#######################################################################################################################
#######################################################################################################################


class TreeDataEdit(QLineEdit):
#{
    valueChange = QtCore.Signal(QLineEdit, QTreeWidgetItem, int, str)

    def __init__(self, item, column, attrDescriptor, data, parent):
    #{
        QLineEdit.__init__(self, attrDescriptor.value2str2(data), parent)

        self.item = item
        self.column = column
        self.data = data
        self.desc = attrDescriptor
        self.__invalidText = False
        self.__tooltip = ''

        validator = None
        if self.desc.typeClass() == AttrTypeData.INT:
            validator = QIntValidator()
            if self.desc.minValue() is not None:
                validator.setBottom(self.desc.minValue())
            if self.desc.maxValue() is not None:
                validator.setTop(self.desc.maxValue())
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
                validator.setTop(self.desc.maxValue())
        else:
            validator = None

        if validator is not None:
            self.setValidator(validator)

        self.__prevText = self.text()
        self.textEdited.connect(self.onTextEditing)
    #}

    def getInvalid(self):
        return self.__invalidText

    def setInvalid(self, val):
        self.__invalidText = val

    invalid = QtCore.Property(bool, getInvalid, setInvalid)

    def sizeHint(self, *args, **kwargs):
        if self.desc.typeClass() != AttrTypeData.STR or len(self.text()) < 20:
            return QSize(len(self.text()) * 7, TREE_ITEMS_HEIGHT)  # self.height())
        sizehint = QLineEdit.sizeHint(self)
        sizehint.setHeight(TREE_ITEMS_HEIGHT)
        return sizehint

    @QtCore.Slot(str)
    def onTextEditing(self, text):
        valid, validtext = self.validateValue(text)
        if not valid:
            if not self.__invalidText:
                self.__tooltip = self.toolTip()
                self.setToolTip('Неверное значение! Нужно ввести: {0}'.format(validtext))
                self.invalid = True
                self.setStyle(QApplication.style())
            return
        else:
            if self.__invalidText:
                self.setToolTip(self.__tooltip)
                self.__tooltip = ''
                self.invalid = False
                self.setStyle(QApplication.style())
            if self.text() != self.__prevText:
                self.valueChange.emit(self, self.item, self.column, validtext)
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
#};

#######################################################################################################################
#######################################################################################################################


class TreeValueCombo(QComboBox):
#{
    valueChange = QtCore.Signal(QComboBox, QTreeWidgetItem, int)

    def __init__(self, item, column, value, attrDescriptor, defaultTooltip, parent):
        QComboBox.__init__(self, parent)
        self._focusProxy = comboBoxScrollProxy(self)
        #self.setEditable(True)
        #self.setInsertPolicy(QComboBox.NoInsert)
        self.setEnabled(True)
        self.item = item
        self.column = column
        self.defaultTooltip = defaultTooltip
        self.desc = attrDescriptor
        i = int(0)
        for v in attrDescriptor.availableValues():
            got, text, hint, _, _ = attrDescriptor.valueHint(v)
            self.addItem(text, v)
            if got and hint:
                self.setItemData(i, hint, Qt.ToolTipRole)
            i += int(1)
        self.setCurrentIndex(self.findData(value))
        self.value = value
        hint = self.itemData(self.currentIndex(), Qt.ToolTipRole)
        if hint is not None and hint:
            self.item.setToolTip(self.column, hint)
        self.currentIndexChanged.connect(self.onIndexChange)

    def getValue(self):
        return self.value

    @QtCore.Slot(int)
    def onIndexChange(self, index):
        self.value = self.itemData(index)
        hint = self.itemData(index, Qt.ToolTipRole)
        if hint is not None and len(hint) > 0:
            self.item.setToolTip(self.column, hint)
        else:
            self.item.setToolTip(self.column, self.defaultTooltip)
        self.valueChange.emit(self, self.item, self.column)

    def sizeHint(self, *args, **kwargs):
        return QSize(48, TREE_ITEMS_HEIGHT)
#};

#######################################################################################################################
#######################################################################################################################


class AttributeAction(QAction):
    clicked = QtCore.Signal(QTreeWidgetItem)

    def __init__(self, item, title, parent=None):
        QAction.__init__(self, title, parent)
        self.item = item
        self.triggered.connect(self.onTrigger)

    @QtCore.Slot()
    def onTrigger(self):
        self.clicked.emit(self.item)

#######################################################################################################################
#######################################################################################################################

