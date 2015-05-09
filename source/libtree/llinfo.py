# coding=utf-8
# -----------------
# file      : llinfo.py
# date      : 2012/12/16
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

from __future__ import unicode_literals

__author__ = 'Victor Zarubkin'
__copyright__ = 'Copyright (C) 2012  Victor Zarubkin'
__credits__ = ['Victor Zarubkin']
__license__ = ['GPLv3']
__version__ = '1.3.0'  # this is last application version when this script file was changed
__email__ = 'victor.zarubkin@gmail.com'

from PySide import QtCore

from PySide.QtCore import *
from PySide.QtGui import *
from extensions.widgets import *

from treenode import *

import copy
import datetime
from time import sleep

from language import globalLanguage, Language, trStr

########################################################################################################################
########################################################################################################################


class ItemAction(QAction):
    clicked = QtCore.Signal(QTreeWidgetItem, int)

    def __init__(self, item, column, title, tooltip='', parent=None):
        QAction.__init__(self, title, parent)
        self.setCheckable(False)
        if tooltip:
            self.setToolTip(tooltip)
        self._item = item
        self._column = column
        self.triggered.connect(self.__onTrigger)

    def item(self):
        return self._item

    def column(self):
        return self._column

    @QtCore.Slot()
    def __onTrigger(self):
        self.clicked.emit(self._item, self._column)

########################################################################################################################
########################################################################################################################


class LibInfoWidget(QWidget):
    updateWidget = QtCore.Signal(list, str, bool)

    def __init__(self, libs, libname, editMode=False, parent=None):
        QWidget.__init__(self, parent)
        globalLanguage.languageChanged.connect(self.__onLanguageChange)
        self.__libs = libs
        self.__libname = libname

        if type(editMode) is bool:
            self.__editMode = editMode
        else:
            self.__editMode = False

        self.__EditName = QLineEdit(self.__libname)
        self.__EditName.textEdited.connect(self.__onNameEditing)

        self.__Tree = QTreeWidget()
        self.__Tree.setHeaderLabels([trStr('Nodes', 'Узлы').text()])
        self.__Tree.setAlternatingRowColors(True)
        self.__treeFocusProxy = scrollProxy(self.__Tree)

        lib = self.__libs[self.__libname]

        classes = globals.project.alphabet.getClasses()
        for classname in classes:
            newItem = QTreeWidgetItem()
            nodes = lib.getAll(classname)
            for n in nodes:
                item = QTreeWidgetItem()
                item.setText(0, nodes[n].name)
                if nodes[n].description:
                    item.setToolTip(0, nodes[n].description)
                newItem.addChild(item)
            newItem.setText(0, '{0}s ({1})'.format(classname, newItem.childCount()))
            self.__Tree.addTopLevelItem(newItem)

        self.__Tree.sortItems(0, Qt.AscendingOrder)
        self.__Tree.expandAll()

        mainLayout = QGridLayout()
        mainLayout.setContentsMargins(5, 5, 5, 5)
        mainLayout.addWidget(trLabel(trStr('Library name:', 'Название библиотеки:')), 0, 0, Qt.AlignRight)
        mainLayout.addWidget(self.__EditName, 0, 1)
        # mainLayout.addWidget(QLabel(u'Attributes:'), 1, 0, 1, 2, Qt.AlignLeft)
        mainLayout.addWidget(self.__Tree, 1, 0, 1, 2)

        # vLayout = QVBoxLayout()
        # vLayout.addLayout(mainLayout)
        # vLayout.addStretch(2)

        globals.librarySignals.nodeRenamed.connect(self.__onNodeRenameExternal)
        globals.librarySignals.nodeRemoved.connect(self.__onNodeRemoveExternal)
        globals.librarySignals.libraryExcluded.connect(self.__onLibraryExcludeExternal)
        globals.librarySignals.nodeAdded.connect(self.__onNodeAdd)
        globals.librarySignals.libraryRenamed.connect(self.__onLibraryRename)

        globals.historySignals.undoMade.connect(self.__reload)
        globals.historySignals.redoMade.connect(self.__reload)

        self.setLayout(mainLayout)

    @QtCore.Slot()
    def __reload(self):
        self.updateWidget.emit(self.__libs, self.__libname, self.__editMode)

    @QtCore.Slot(str)
    def __onNameEditing(self, name):
        if not self.__editMode:
            self.__EditName.undo()

    @QtCore.Slot(str)
    def __onLibraryExcludeExternal(self, libname):
        if self.__libname == libname:
            self.updateWidget.emit(None, None, False)

    @QtCore.Slot(str, str, str)
    def __onNodeRemoveExternal(self, libname, nodename, nodeClass):
        if self.__libname == libname:
            self.updateWidget.emit(None, None, False)

    @QtCore.Slot(str, str, str)
    def __onNodeRenameExternal(self, libname, oldname, newname):
        if self.__libname == libname:
            self.updateWidget.emit(None, None, False)

    @QtCore.Slot(str, str)
    def __onNodeAdd(self, libname, nodename):
        if self.__libname == libname:
            self.updateWidget.emit(self.__libs, self.__libname, self.__editMode)

    @QtCore.Slot(str, str)
    def __onLibraryRename(self, oldName, newName):
        if self.__libname == oldName:
            self.updateWidget.emit(self.__libs, newName, self.__editMode)

    @QtCore.Slot(str)
    def __onLanguageChange(self, lang):
        self.__Tree.setHeaderLabels([trStr('Nodes', 'Узлы').text()])

########################################################################################################################
########################################################################################################################


class AttrDialogEnumTree(QTreeWidget):
    requestItemAdd = QtCore.Signal()
    requestItemDelete = QtCore.Signal(QTreeWidgetItem)

    def __init__(self, typeClass, parent=None):
        QTreeWidget.__init__(self, parent)
        self._typeClass = typeClass
        self._focusProxy = scrollProxy(self)

    def setTypeClass(self, typeClass):
        self._typeClass = typeClass

    def contextMenuEvent(self, *args, **kwargs):
        menu = QMenu(self)

        item = self.currentItem()  # None if there is no item under cursor
        column = self.currentColumn()  # -1 if there is no item under cursor

        actions = []  # need because of PySide bug: if you'll not save new action somewhere except QMenu, it will be garbage collected

        action = ItemAction(item, column, trStr('Add value', 'Добавить значение').text())
        action.setIcon(QIcon('/'.join([globals.applicationIconsPath, 'add-3.png'])))
        action.clicked.connect(self.__onAddClicked)
        menu.addAction(action)
        actions.append(action)

        isBool = self._typeClass == AttrTypeData.BOOL

        if isBool:
            action.setEnabled(False)

        action = ItemAction(item, column, trStr('Delete value', 'Удалить значение').text())
        action.setIcon(QIcon('/'.join([globals.applicationIconsPath, 'cancel-1.png'])))
        action.clicked.connect(self.__onDeleteClicked)
        menu.addAction(action)
        actions.append(action)

        if item is None or isBool:
            action.setEnabled(False)

        menu.exec_(QCursor.pos())

    @QtCore.Slot(QTreeWidgetItem, int)
    def __onAddClicked(self, item, column):
        self.requestItemAdd.emit()

    @QtCore.Slot(QTreeWidgetItem, int)
    def __onDeleteClicked(self, item, column):
        self.requestItemDelete.emit(item)

########################################################################################################################


class AttrEditDialogData(object):
    def __init__(self, attribute):
        self.modified = False
        self.attribute = attribute.deepcopy()

########################################################################################################################


class AttrEditDialog(QDialog):
    def __init__(self, attr, parent):
        QDialog.__init__(self, parent)
        self.setObjectName('libraryAttributeEditDialog')
        self.setWindowTitle(trStr('Attribute type edit', 'Редактирование типа параметра').text())

        self.__data = attr

        self.__combo = QComboBox()
        self.__combo.addItems(ATTRIBUTE_TYPES)
        # self.__combo.addItem('dynamic')
        self.__comboFocusProxy = comboBoxScrollProxy(self.__combo)

        if self.__data.attribute.isDynamic():
            typeName = 'dynamic'
            QTimer.singleShot(5, self.reject)
            print('warning: editing dynamic types is not supported yet!')
        else:
            typeName = self.__data.attribute.typeName()

        self.__typeIndex = self.__combo.findText(typeName)
        self.__combo.setCurrentIndex(self.__typeIndex)

        self.__combo.currentIndexChanged.connect(self.__onTypeChange)

        self.__arrayCheckbox = QCheckBox(trStr('Array', 'Массив').text())
        self.__arrayCheckbox.setToolTip(
            trStr('If checked then attribute is an array', 'Если выбрано, то параметр является массивом').text())
        self.__arrayCheckbox.setChecked(self.__data.attribute.isArray())
        self.__arrayCheckbox.toggled.connect(self.__onArrayToggle)

        if not self.__data.attribute.isDynamic():
            typeinfo = self.__data.attribute.typeInfo()
            min_value = self.__data.attribute.value2str(self.__data.attribute.minValue())
            max_value = self.__data.attribute.value2str(self.__data.attribute.maxValue())
            default = self.__data.attribute.value2str(self.__data.attribute.defaultValue())
        else:
            typeinfo = None
            min_value = ''
            max_value = ''
            default = ''

        self.__minEdit = QLineEdit(min_value)
        self.__minEdit.editingFinished.connect(self.__minEdited)

        self.__maxEdit = QLineEdit(max_value)
        self.__maxEdit.editingFinished.connect(self.__maxEdited)

        self.__defaultEditLabel = QLabel(trStr('default value:', 'значение по-умолчанию:').text())
        self.__defaultEdit = QLineEdit(default)
        self.__defaultEdit.editingFinished.connect(self.__defaultEdited)

        self.__defaultBoxLabel = QLabel(trStr('default value:', 'значение по-умолчанию:').text())
        self.__defaultBoxEditing = False
        self.__defaultBox = QComboBox()
        self.__defaultBoxFocusProxy = comboBoxScrollProxy(self.__defaultBox)
        self.__defaultIndex = -1

        self.__availableTreeCheckbox = QCheckBox(trStr('Available values', 'Доступные значения').text())

        self.__editItem = None
        self.__editColumn = -1
        self.__editItemText = ''
        self.__availableTree = AttrDialogEnumTree(self.__data.attribute.typeClass())
        self.__availableTree.setMinimumHeight(70)
        self.__availableTree.setAlternatingRowColors(True)
        self.__availableTree.setRootIsDecorated(False)
        self.__availableTree.setColumnCount(3)
        self.__availableTree.setHeaderLabels(
            [trStr('value', 'значение').text(), trStr('text', 'текст').text(), trStr('hint', 'подсказка').text()])
        self.__availableTree.requestItemAdd.connect(self.__onAddValueClicked)
        self.__availableTree.requestItemDelete.connect(self.__onDeleteValueClicked)
        # self.__availableTreeFocusProxy = scrollProxy(self.__availableTree)

        self.__fillDefaultCombo()
        self.__defaultBox.currentIndexChanged.connect(self.__defaultSelected)

        self.__availableTreeCheckbox.setChecked(self.__defaultBox.count() > 0)
        self.__modifying = False
        self.__availableTreeCheckbox.toggled.connect(self.__onAvailableCheckboxToggle)

        self.__availableTree.setEnabled(self.__availableTreeCheckbox.isChecked())
        self.__availableTree.itemDoubleClicked.connect(self.__onItemDoubleClicked)
        self.__availableTree.itemChanged.connect(self.__onItemChange)
        self.__availableTree.itemClicked.connect(self.__onItemClicked)

        self.__minText = self.__minEdit.text()
        self.__maxText = self.__maxEdit.text()
        self.__defaultText = self.__defaultEdit.text()

        if typeinfo is None or typeinfo.classType in (AttrTypeData.BOOL, AttrTypeData.STR)\
                or self.__data.attribute.availableValues():
            self.__minEdit.setEnabled(False)
            self.__maxEdit.setEnabled(False)

        self.__submitButton = SubmitButton(trStr('Submit', 'Подтвердить'))
        self.__submitButton.setEnabled(False)

        self.__descriptionEdit = QTextEdit()
        self.__descriptionEdit.setMinimumHeight(50)
        self.__descriptionEdit.setAcceptRichText(True)
        self.__descriptionEdit.setText(self.__data.attribute.description)
        self.__descriptionEdit.textChanged.connect(self.__onDescriptionChange)
        self.__descriptionEditFocusProxy = scrollProxy(self.__descriptionEdit)

        buttonBox = QDialogButtonBox(Qt.Horizontal)
        buttonBox.addButton(self.__submitButton, QDialogButtonBox.AcceptRole)
        buttonBox.addButton(QPushButton(trStr('Cancel', 'Отменить').text()), QDialogButtonBox.RejectRole)
        buttonBox.rejected.connect(self.reject)
        buttonBox.accepted.connect(self.accept)

        labelText = trStr('<h3>Attribute <u><b><i>{0}</i></b></u></h3>'.format(self.__data.attribute.name()), \
                          '<h3>Параметр <u><b><i>{0}</i></b></u></h3>'.format(self.__data.attribute.name())).text()

        gridLayout = QGridLayout()
        gridLayout.setContentsMargins(5, 5, 5, 5)
        gridLayout.addWidget(QLabel(labelText), 0, 0, 1, 3, Qt.AlignHCenter)
        gridLayout.addWidget(QLabel(trStr('Type:', 'Тип:').text()), 1, 0, Qt.AlignRight)
        gridLayout.addWidget(self.__combo, 1, 1)
        gridLayout.addWidget(self.__arrayCheckbox, 1, 2)
        gridLayout.addWidget(QLabel(trStr('min value:', 'мин. значение:').text()), 2, 0, Qt.AlignRight)
        gridLayout.addWidget(self.__minEdit, 2, 1, 1, 2)
        gridLayout.addWidget(QLabel(trStr('max value:', 'макс. значение:').text()), 3, 0, Qt.AlignRight)
        gridLayout.addWidget(self.__maxEdit, 3, 1, 1, 2)
        gridLayout.addWidget(self.__defaultEditLabel, 4, 0, Qt.AlignRight)
        gridLayout.addWidget(self.__defaultEdit, 4, 1, 1, 2)
        gridLayout.addWidget(self.__defaultBoxLabel, 5, 0, Qt.AlignRight)
        gridLayout.addWidget(self.__defaultBox, 5, 1, 1, 2)
        gridLayout.addWidget(self.__availableTreeCheckbox, 6, 0, 1, 3, Qt.AlignLeft)
        gridLayout.addWidget(self.__availableTree, 7, 0, 1, 3)
        gridLayout.addWidget(QLabel(trStr('Descriprion:', 'Описание:').text()), 8, 0, 1, 3, Qt.AlignLeft)
        gridLayout.addWidget(self.__descriptionEdit, 9, 0, 1, 3)
        gridLayout.setColumnStretch(1, 1)
        gridLayout.setColumnStretch(2, 1)

        if self.__defaultBox.count() == 0:
            self.__defaultBoxLabel.hide()
            self.__defaultBox.hide()
        else:
            self.__defaultEditLabel.hide()
            self.__defaultEdit.hide()

        vbox = QVBoxLayout()
        vbox.addLayout(gridLayout)
        vbox.addStretch(1)
        vbox.addWidget(buttonBox)

        self.setLayout(vbox)
        self.readSettings()

    def closeEvent(self, *args, **kwargs):
        self.saveSettings()
        QDialog.closeEvent(self, *args, **kwargs)

    def saveSettings(self):
        settings = QSettings('Victor Zarubkin', 'Behavior Studio')
        settings.beginGroup('libraryAttributeEditDialog')
        settings.setValue('geometry', self.saveGeometry())
        settings.endGroup()

    def readSettings(self):
        settings = QSettings('Victor Zarubkin', 'Behavior Studio')
        settings.beginGroup('libraryAttributeEditDialog')
        geometry = settings.value('geometry')
        if geometry is not None:
            self.restoreGeometry(geometry)
        settings.endGroup()

    def __fillDefaultCombo(self, validateTree=True):
        self.__defaultBoxEditing = True

        self.__defaultIndex = -1
        self.__defaultBox.clear()

        if validateTree:
            self.__availableTree.clear()

        if self.__data.attribute.availableValues():
            typeinfo = self.__data.attribute.typeInfo()
            for v in self.__data.attribute.availableValues():
                text = self.__data.attribute.value2str2(v)
                self.__defaultBox.addItem(text, v)
                if validateTree:
                    _, _, hint, userText, _ = self.__data.attribute.valueHint(v)
                    item = QTreeWidgetItem()
                    item.setText(0, text)
                    item.setText(1, userText)
                    item.setText(2, hint)
                    item.setData(0, Qt.UserRole, (v, v in typeinfo.enums))
                    item.setData(1, Qt.UserRole, (None, False))
                    item.setData(2, Qt.UserRole, (None, False))
                    self.__availableTree.addTopLevelItem(item)
            index = self.__defaultBox.findData(self.__data.attribute.defaultValue())
            if index >= 0:
                self.__defaultIndex = index
                self.__defaultBox.setCurrentIndex(index)

        self.__defaultBoxEditing = False

    def keyPressEvent(self, *args, **kwargs):
        """ No keys for this dialog! """
        pass

    @QtCore.Slot()
    def __onDescriptionChange(self):
        self.__data.modified = True
        self.__submitButton.setEnabled(True)
        self.__data.attribute.description = self.__descriptionEdit.toPlainText()

    @QtCore.Slot(bool)
    def __onArrayToggle(self, checked):
        self.__data.modified = True
        self.__submitButton.setEnabled(True)
        self.__data.attribute.setArray(checked)

    @QtCore.Slot()
    def __minEdited(self):
        text = self.__minEdit.text()
        if self.__minText != text:
            if self.__data.attribute.minValue() is not None:
                previous = self.__data.attribute.value2str(self.__data.attribute.minValue())
            else:
                previous = ''

            self.__data.attribute.setMin(text)

            if self.__data.attribute.minValue() is not None:
                current = self.__data.attribute.value2str(self.__data.attribute.minValue())
            else:
                current = ''

            self.__minEdit.setText(current)
            self.__minText = current
            if current != previous:
                print('debug: minimum value edited')
                self.__data.modified = True
                self.__submitButton.setEnabled(True)

    @QtCore.Slot()
    def __maxEdited(self):
        text = self.__maxEdit.text()
        if self.__maxText != text:
            if self.__data.attribute.maxValue() is not None:
                previous = self.__data.attribute.value2str(self.__data.attribute.maxValue())
            else:
                previous = ''

            self.__data.attribute.setMax(text)

            if self.__data.attribute.maxValue() is not None:
                current = self.__data.attribute.value2str(self.__data.attribute.maxValue())
            else:
                current = ''

            self.__maxEdit.setText(current)
            self.__maxText = current
            if current != previous:
                print('debug: maximum value edited')
                self.__data.modified = True
                self.__submitButton.setEnabled(True)

    @QtCore.Slot()
    def __defaultEdited(self):
        text = self.__defaultEdit.text()
        if self.__defaultText != text:
            previous = self.__data.attribute.value2str(self.__data.attribute.defaultValue())
            self.__data.attribute.setDefaultValue(text)
            current = self.__data.attribute.value2str(self.__data.attribute.defaultValue())

            self.__defaultEdit.setText(current)
            self.__defaultText = current
            if current != previous:
                print('debug: default value edited')
                self.__data.modified = True
                self.__submitButton.setEnabled(True)

    @QtCore.Slot(int)
    def __defaultSelected(self, index):
        if self.__defaultIndex != index and not self.__defaultBoxEditing:
            value = self.__defaultBox.itemData(index)

            previous = self.__data.attribute.defaultValue()
            self.__data.attribute.setActualDefaultValue(value)
            current = self.__data.attribute.defaultValue()

            if current is not None:
                currentIndex = self.__defaultBox.findData(current)
            else:
                currentIndex = -1
            if currentIndex != index:
                self.__defaultBoxEditing = True
                self.__defaultIndex = currentIndex
                self.__defaultBox.setCurrentIndex(currentIndex)
                self.__defaultBoxEditing = False

            if previous != current:
                print('debug: default value edited')
                self.__data.modified = True
                self.__submitButton.setEnabled(True)

    @QtCore.Slot(QTreeWidgetItem, int)
    def __onItemDoubleClicked(self, item, column):
        if self.__editItem is not None:
            self.__finishItemEdit()
        _, isRestricted = item.data(column, Qt.UserRole)
        if not isRestricted:
            self.__editItem = item
            self.__editColumn = column
            self.__editItemText = item.text(column)
            self.__availableTree.openPersistentEditor(item, column)
        else:
            print('warning: can\'t modify value \'{0}\' because it is restricted by attribute type \'{1}\''
                  .format(item.text(column), self.__data.attribute.typeName()))

    @QtCore.Slot(QTreeWidgetItem, int)
    def __onItemChange(self, item, column):
        if self.__editItem is not None:
            self.__finishItemEdit()

    @QtCore.Slot(QTreeWidgetItem, int)
    def __onItemClicked(self, item, column):
        if self.__editItem is not None:
            if self.__editColumn != column or item is not self.__editItem:
                self.__finishItemEdit()

    @QtCore.Slot(bool)
    def __onAvailableCheckboxToggle(self, checked):
        if not self.__modifying:
            if not checked:
                typeinfo = self.__data.attribute.typeInfo()
                if typeinfo.enums:
                    self.__modifying = True
                    self.__availableTreeCheckbox.setChecked(True)
                    self.__modifying = False
                else:
                    self.__data.attribute.clearAvailableValues()
                    self.__data.modified = True
                    self.__submitButton.setEnabled(True)

                    self.__defaultBoxLabel.hide()
                    self.__defaultBox.hide()
                    self.__availableTree.clear()

                    self.__defaultEditLabel.show()
                    self.__defaultEdit.show()

                    default = ''
                    if self.__data.attribute.defaultValue() != typeinfo.default:
                        default = self.__data.attribute.value2str(self.__data.attribute.defaultValue())
                    self.__defaultEdit.setText(default)
                    self.__defaultText = default

                    if typeinfo.classType in (AttrTypeData.BOOL, AttrTypeData.STR):
                        self.__minEdit.setEnabled(False)
                        self.__maxEdit.setEnabled(False)
                    else:
                        self.__minEdit.setEnabled(True)
                        self.__maxEdit.setEnabled(True)
            else:
                self.__data.modified = True
                self.__submitButton.setEnabled(True)
                self.__data.attribute.appendAvailableValue(self.__data.attribute.defaultValue())
                self.__defaultBoxLabel.show()
                self.__defaultBox.show()
                self.__defaultEditLabel.hide()
                self.__defaultEdit.hide()
                self.__fillDefaultCombo()
            self.__availableTree.setEnabled(self.__availableTreeCheckbox.isChecked())

    @QtCore.Slot()
    def __onAddValueClicked(self):
        if self.__data.attribute.typeClass() != AttrTypeData.BOOL:
            item = QTreeWidgetItem()
            item.setData(0, Qt.UserRole, (None, False))
            item.setData(1, Qt.UserRole, (None, True))
            item.setData(2, Qt.UserRole, (None, True))
            self.__availableTree.addTopLevelItem(item)

    @QtCore.Slot(QTreeWidgetItem)
    def __onDeleteValueClicked(self, item):
        if item is not None and self.__data.attribute.typeClass() != AttrTypeData.BOOL:
            value, isRestricted = item.data(0, Qt.UserRole)
            if value is not None:
                if self.__data.attribute.removeAvailableValue(value):
                    print('debug: item \'{0}\' changed!'.format(item.text(0)))
                    self.__data.modified = True
                    self.__submitButton.setEnabled(True)
                    self.__modifying = True
                    # self.__availableTree.takeTopLevelItem(self.__availableTree.indexOfTopLevelItem(item))
                    # self.__fillDefaultCombo(False)
                    self.__fillDefaultCombo()
                    if self.__defaultBox.count() == 0:
                        self.__defaultEditLabel.show()
                        self.__defaultEdit.show()
                        self.__defaultBoxLabel.hide()
                        self.__defaultBox.hide()
                        self.__availableTreeCheckbox.setChecked(False)
                        self.__availableTree.setEnabled(False)

                        typeinfo = self.__data.attribute.typeInfo()
                        default = ''
                        if self.__data.attribute.defaultValue() != typeinfo.default:
                            default = self.__data.attribute.value2str(self.__data.attribute.defaultValue())
                        self.__defaultEdit.setText(default)
                        self.__defaultText = default

                        if typeinfo.classType in (AttrTypeData.BOOL, AttrTypeData.STR):
                            self.__minEdit.setEnabled(False)
                            self.__maxEdit.setEnabled(False)
                        else:
                            self.__minEdit.setEnabled(True)
                            self.__maxEdit.setEnabled(True)
                    self.__modifying = False
            else:
                self.__availableTree.takeTopLevelItem(self.__availableTree.indexOfTopLevelItem(item))

    def __finishItemEdit(self):
        self.__availableTree.closePersistentEditor(self.__editItem, self.__editColumn)
        currentText = self.__editItem.text(self.__editColumn)
        if currentText != self.__editItemText:
            item, self.__editItem = self.__editItem, None
            column, self.__editColumn = self.__editColumn, -1
            text, self.__editItemText = self.__editItemText, ''
            value, isRestricted = item.data(0, Qt.UserRole)
            change = False
            if column == 0:
                # value edited
                newValue = self.__data.attribute.str2value(currentText)
                if value is not None:
                    if not isRestricted and self.__data.attribute.changeAvailableValue(value, newValue):
                        change = True
                else:
                    if self.__data.attribute.appendAvailableValue(newValue):
                        change = True
                        item.setData(1, Qt.UserRole, (None, False))
                        item.setData(2, Qt.UserRole, (None, False))
            elif column == 1:
                # text edited
                if value is not None and self.__data.attribute.setText(value, currentText):
                    change = True
            elif column == 2:
                # hint edited
                if value is not None and self.__data.attribute.setHint(value, currentText):
                    change = True
            if change:
                print('debug: item \'{0}\' changed!'.format(item.text(0)))
                self.__data.modified = True
                self.__submitButton.setEnabled(True)
                self.__fillDefaultCombo()

    @QtCore.Slot(int)
    def __onTypeChange(self, index):
        if index != self.__typeIndex:
            if not self.__data.attribute.isDynamic():
                self.__data.modified = True
                self.__submitButton.setEnabled(True)

                self.__typeIndex = index
                attribute = self.__data.attribute.deepcopy()
                current_type = attribute.typeInfo()

                # Making backup for values set by user
                min_value = ''
                max_value = ''
                default = ''
                if attribute.minValue() is not None \
                        and (current_type.minValue is None or attribute.minValue() != current_type.minValue):
                    min_value = attribute.value2str(attribute.minValue())
                if attribute.maxValue() is not None \
                        and (current_type.maxValue is None or attribute.maxValue() != current_type.maxValue):
                    max_value = attribute.value2str(attribute.maxValue())
                if attribute.defaultValue() != current_type.default:
                    default = attribute.value2str(attribute.defaultValue())

                # Making backup for available enums and hints:
                if attribute.availableValues():
                    available = []
                    for value in attribute.availableValues():
                        text = attribute.value2str(value)
                        found, editorText, hint, userText, isDefault = attribute.valueHint(value)
                        if found and not isDefault:
                            available.append((text, userText, hint))
                        else:
                            available.append((text, '', ''))
                else:
                    available = []

                # Change type. After that all enums, min, max and default values will be erased.
                self.__data.attribute.setType(self.__combo.itemText(index), self.__data.attribute.isArray())

                # Trying to restore values set by user for previous type
                if available:
                    self.__data.attribute.setAvailableValuesByText(available)

                if self.__data.attribute.typeClass() \
                        not in (AttrTypeData.BOOL, AttrTypeData.STR) and not self.__data.attribute.availableValues():
                    if min_value:
                        self.__data.attribute.setMin(min_value)
                    if max_value:
                        self.__data.attribute.setMin(max_value)

                if default:
                    self.__data.attribute.setDefaultValue(default)

                min_value = ''
                if self.__data.attribute.minValue() is not None:
                    min_value = self.__data.attribute.value2str(self.__data.attribute.minValue())

                max_value = ''
                if self.__data.attribute.maxValue() is not None:
                    max_value = self.__data.attribute.value2str(self.__data.attribute.maxValue())

                default = self.__data.attribute.value2str(self.__data.attribute.defaultValue())

                self.__minEdit.setText(min_value)
                self.__maxEdit.setText(max_value)
                self.__defaultEdit.setText(default)

                if self.__data.attribute.typeClass() \
                        in (AttrTypeData.BOOL, AttrTypeData.STR) or self.__data.attribute.availableValues():
                    self.__minEdit.setEnabled(False)
                    self.__maxEdit.setEnabled(False)
                else:
                    self.__minEdit.setEnabled(True)
                    self.__maxEdit.setEnabled(True)

                self.__minText = self.__minEdit.text()
                self.__maxText = self.__maxEdit.text()
                self.__defaultText = self.__defaultEdit.text()

                self.__modifying = True
                self.__availableTree.setTypeClass(self.__data.attribute.typeClass())
                if self.__data.attribute.availableValues():
                    self.__fillDefaultCombo()
                    self.__defaultEditLabel.hide()
                    self.__defaultEdit.hide()
                    self.__defaultBoxLabel.show()
                    self.__defaultBox.show()
                    self.__availableTreeCheckbox.setChecked(True)
                else:
                    self.__defaultEditLabel.show()
                    self.__defaultEdit.show()
                    self.__defaultBoxLabel.hide()
                    self.__defaultBox.hide()
                    self.__availableTreeCheckbox.setChecked(False)
                self.__availableTree.setEnabled(self.__availableTreeCheckbox.isChecked())
                self.__modifying = False

########################################################################################################################
########################################################################################################################


class ItemLineEdit(QLineEdit):
    edited = QtCore.Signal(QTreeWidgetItem, int, str)
    finished = QtCore.Signal(QTreeWidgetItem, int, str)

    def __init__(self, item, column):
        self.__invalid = False
        QLineEdit.__init__(self)
        self._done = False
        self._item = item
        self._column = column
        self.editingFinished.connect(self.__finish)
        self.textEdited.connect(self.__onEdit)

    def isInvalid(self):
        return self.__invalid

    def setInvalid(self, val):
        if self.__invalid != val:
            self.__invalid = val
            self.setStyle(QApplication.style())

    invalid = QtCore.Property(bool, isInvalid, setInvalid)

    def item(self):
        return self._item

    def column(self):
        return self._column

    def setText(self, text):
        QLineEdit.setText(self, text)
        self.invalid = False

    def undo(self):
        QLineEdit.undo(self)
        self.invalid = False

    @QtCore.Slot()
    def __finish(self):
        if not self._done:
            self._done = True
            self.finished.emit(self._item, self._column, self.text())

    @QtCore.Slot(str)
    def __onEdit(self, text):
        if self._done:
            self.undo()
        else:
            self.edited.emit(self._item, self._column, text)

    def setVisible(self, visible):
        QLineEdit.setVisible(self, visible)
        self._done = not visible
        if visible:
            self._onShow()
            self.setFocus()
        else:
            self._onHide()

    def _onHide(self):
        pass

    def _onShow(self):
        self.setText(self._item.text(self._column))

########################################################################################################################
########################################################################################################################


class AttrNameLineEdit(ItemLineEdit):
    def _onShow(self):
        attr = self._item.data(0, Qt.UserRole)
        if attr is not None:
            self.setText(attr.fullname)
        else:
            print('ERROR: No attribute for item \'{0} {1}\'!'.format(self._item.text(0), self._item.text(1)))
            self.setText(self._item.text(self._column))

########################################################################################################################
########################################################################################################################


class ItemCombobox(QComboBox):
    finished = QtCore.Signal(QTreeWidgetItem, int)
    changed = QtCore.Signal(QTreeWidgetItem, int, int)

    def __init__(self, item, column):
        QComboBox.__init__(self)
        self._focusProxy = comboBoxScrollProxy(self)
        self._item = item
        self._column = column
        self._popup = False
        self.currentIndexChanged.connect(self._onCurrentChange)

    def item(self):
        return self._item

    def column(self):
        return self._column

    def showPopup(self, *args, **kwargs):
        self._popup = True
        QComboBox.showPopup(self, *args, **kwargs)

    def hidePopup(self, *args, **kwargs):
        self._popup = False
        QComboBox.hidePopup(self, *args, **kwargs)

    def focusOutEvent(self, event):
        QComboBox.focusOutEvent(self, event)
        if not self._popup:
            self.finished.emit(self._item, self._column)

    @QtCore.Slot(int)
    def _onCurrentChange(self, index):
        self.changed.emit(self._item, self._column, index)

########################################################################################################################
########################################################################################################################


class AttrTypeCombobox(ItemCombobox):
    def __init__(self, item, column):
        ItemCombobox.__init__(self, item, column)
        global TYPE_INFO
        types = list(TYPE_INFO.keys())
        types.sort()
        self.addItems(types)
        for t in types:
            self.addItem('array<{0}>'.format(t))
        if 'dynamic' not in types:
            self.addItem('dynamic')
            self.addItem('array<dynamic>')
        if item.text(0) not in types:
            self.addItem(item.text(0))
        self.setCurrentIndex(self.findText(item.text(0)))

########################################################################################################################
########################################################################################################################


class AttrTree(QTreeWidget):
    attributeRenamed = QtCore.Signal(str, str, bool)
    attributeChanged = QtCore.Signal(str, object)
    attributeDeleted = QtCore.Signal(str)
    attributeAdded = QtCore.Signal(str, object)

    def __init__(self, libname, nodename, attrs, editMode=False, parent=None):
        QTreeWidget.__init__(self, parent)
        self._focusProxy = scrollProxy(self)
        globalLanguage.languageChanged.connect(self.__onLanguageChange)

        if type(editMode) is bool:
            self.__editMode = editMode
        else:
            self.__editMode = False

        self.setRootIsDecorated(False)
        self.setAlternatingRowColors(True)
        self.setDragEnabled(False)

        self.__libname = libname
        self.__nodename = nodename
        self.__attributes = dict()
        for name in attrs:
            self.__attributes[name] = attrs[name].deepcopy()

        self.__nameEdit = None

        self.setHeaderLabels(['type', 'name'])
        self.__onLanguageChange(globalLanguage.language)
        for name in self.__attributes:
            attr = self.__attributes[name]
            item = QTreeWidgetItem()
            self.__setItemData(item, attr)
            self.addTopLevelItem(item)

        if self.__editMode:
            self.itemDoubleClicked.connect(self.__onDoubleClicked)

    def attributes(self):
        return self.__attributes

    def addAttribute(self, attr):
        if attr.fullname not in self.__attributes:
            self.__attributes[attr.fullname] = attr
            item = QTreeWidgetItem(self)
            self.__setItemData(item, attr)
            self.addTopLevelItem(item)

    def __setItemData(self, item, attr):
        if not attr.isDynamic():
            if attr.isArray():
                item.setText(0, 'array<{0}>'.format(attr.typeName()))
            else:
                item.setText(0, attr.typeName())
            item.setText(1, attr.attrname)
            item.setData(0, Qt.UserRole, attr)
            if attr.isArray():
                header = 'array<{0}> {1};'.format(attr.typeName(), attr.fullname)
            else:
                header = '{0} {1};'.format(attr.typeName(), attr.fullname)
            if attr.description:
                tooltip = '{0}\n{1}'.format(header, attr.description)
            else:
                tooltip = header
            if attr.minValue() is not None or attr.maxValue() is not None:
                tooltip += '\n----------'
                if attr.minValue() is not None:
                    tooltip += '\nmin = {0}'.format(attr.minValue())
                if attr.maxValue() is not None:
                    tooltip += '\nmax = {0}'.format(attr.maxValue())
            item.setToolTip(0, tooltip)
            item.setToolTip(1, tooltip)
        else:
            if attr.isArray():
                item.setText(0, 'array<dynamic>')
            else:
                item.setText(0, 'dynamic')
            item.setText(1, attr.attrname)
            item.setData(0, Qt.UserRole, attr)
            if attr.isArray():
                header = 'array<dynamic> {0};'.format(attr.fullname)
            else:
                header = 'dynamic {0};'.format(attr.fullname)
            if attr.description:
                tooltip = '{0}\n{1}'.format(header, attr.description)
            else:
                tooltip = header
            if attr.typesTip():
                tooltip += '\n----------\n{0}'.format(attr.typesTip())
            item.setToolTip(0, tooltip)
            item.setToolTip(1, tooltip)

    def contextMenuEvent(self, *args, **kwargs):
        if not self.__editMode:
            return

        menu = QMenu(self)

        item = self.currentItem()  # None if there is no item under cursor
        column = self.currentColumn()  # -1 if there is no item under cursor

        print('debug: column = {0}'.format(column))

        actions = []  # need because of PySide bug: if you'll not save new action somewhere except QMenu, it will be garbage collected

        action = ItemAction(item, 1, trStr('Rename', 'Переименовать').text())
        action.setIcon(QIcon('/'.join([globals.applicationIconsPath, 'page_edit.png'])))
        action.clicked.connect(self.__onDoubleClicked)
        menu.addAction(action)
        actions.append(action)

        if item is None:
            action.setEnabled(False)

        action = ItemAction(item, 0, trStr('Modify type', 'Изменить тип').text())
        action.setIcon(QIcon('/'.join([globals.applicationIconsPath, 'wrench_orange.png'])))
        action.clicked.connect(self.__onDoubleClicked)
        menu.addAction(action)
        actions.append(action)

        if item is None:
            action.setEnabled(False)

        menu.addSeparator()

        action = ItemAction(item, column, trStr('Add attribute', 'Добавить параметр').text())
        action.setIcon(QIcon('/'.join([globals.applicationIconsPath, 'add-3.png'])))
        action.clicked.connect(self.__onAddClicked)
        menu.addAction(action)
        actions.append(action)

        action = ItemAction(item, column, trStr('Delete attribute', 'Удалить параметр').text())
        action.setIcon(QIcon('/'.join([globals.applicationIconsPath, 'cancel-1.png'])))
        action.clicked.connect(self.__onDeleteClicked)
        menu.addAction(action)
        actions.append(action)

        if item is None:
            action.setEnabled(False)

        menu.exec_(QCursor.pos())

    @QtCore.Slot(QTreeWidgetItem, int)
    def __onDoubleClicked(self, item, column):
        print('debug: clicked item \'{0} {1}\' column {2}'.format(item.text(0), item.text(1), column))
        if column == 0:
            self.__startEditAttributeType(item, column)
        elif column == 1:
            self.__startEditAttributeName(item, column)

    def __startEditAttributeName(self, item, column):
        if self.__nameEdit is None or item is not self.__nameEdit.item():
            if self.__nameEdit is not None:
                self.__finishEditItemNameLite(self.__nameEdit.item(), self.__nameEdit.column(), self.__nameEdit.text())
            editor = self.itemWidget(item, column)
            if editor is None:
                editor = AttrNameLineEdit(item, column)
                editor.finished.connect(self.__finishEditItemName)
                editor.edited.connect(self.__onItemNameEdit)
                self.setItemWidget(item, column, editor)
            self.__nameEdit = editor
            editor.show()

    def __startEditAttributeType(self, item, column):
        attr = item.data(0, Qt.UserRole)
        if attr is not None:
            data = AttrEditDialogData(attr)
            dialog = AttrEditDialog(data, self)
            if dialog.exec_() == QDialog.Accepted:
                print('debug: attribute type dialog accept')
                if data.modified:
                    print('debug: attribute \'{0}\' changed'.format(attr.name()))
                    self.__attributes[attr.name(True)] = data.attribute
                    self.__setItemData(item, data.attribute)
                    self.attributeChanged.emit(attr.name(True), data.attribute)
                else:
                    print('debug: attribute \'{0}\' not changed'.format(attr.name()))
            else:
                print('debug: attribute type dialog cancel')

    @QtCore.Slot(QTreeWidgetItem, int, str)
    def __finishEditItemNameLite(self, item, column, text):
        self.itemWidget(item, column).hide()
        if text:
            attr = item.data(0, Qt.UserRole)
            oldname = attr.fullname
            newname = text.replace('\\', '/')  # attr.getFullName(text)
            if newname != oldname and newname not in self.__attributes:
                self.__attributes[newname] = self.__attributes[oldname]
                del self.__attributes[oldname]
                attr = self.__attributes[newname]
                attr.rename(newname, True)
                item.setText(column, attr.name())
                item.setData(0, Qt.UserRole, attr)
                self.attributeRenamed.emit(oldname, newname, True)

    @QtCore.Slot(QTreeWidgetItem, int, str)
    def __finishEditItemName(self, item, column, text):
        self.__nameEdit = None
        self.__finishEditItemNameLite(item, column, text)

    @QtCore.Slot(QTreeWidgetItem, int, str)
    def __onItemNameEdit(self, item, column, text):
        attr = item.data(0, Qt.UserRole)
        oldname = attr.fullname
        newname = text.replace('\\', '/')
        if oldname and (oldname == newname or newname not in self.__attributes):
            self.itemWidget(item, column).invalid = False
        else:
            self.itemWidget(item, column).invalid = True

    @QtCore.Slot(QTreeWidgetItem, int)
    def __onAddClicked(self, item, column):
        name = 'attribute_{0}'.format(datetime.datetime.now().time())
        while name in self.__attributes:
            sleep(0.01)
            name = 'attribute_{0}'.format(datetime.datetime.now().time())
        newAttribute = NodeAttrDesc(name)
        self.__attributes[name] = newAttribute
        item = QTreeWidgetItem()
        self.__setItemData(item, newAttribute)
        self.addTopLevelItem(item)
        self.attributeAdded.emit(name, newAttribute)

    @QtCore.Slot(QTreeWidgetItem, int)
    def __onDeleteClicked(self, item, column):
        attr = item.data(0, Qt.UserRole)
        name = attr.fullName()
        if name in self.__attributes:
            del self.__attributes[name]
            self.takeTopLevelItem(self.indexOfTopLevelItem(item))
            self.attributeDeleted.emit(name)

    @QtCore.Slot(str)
    def __onLanguageChange(self, lang):
        self.setHeaderLabels([trStr('type', 'тип').text(), trStr('name', 'имя').text()])

########################################################################################################################
########################################################################################################################


class EventsTree(QTreeWidget):
    eventRenamed = QtCore.Signal(str, str, str)
    eventDeleted = QtCore.Signal(str, str)
    eventAdded = QtCore.Signal(str, str)

    def __init__(self, libs, libname, nodename, editMode, parent=None):
        QTreeWidget.__init__(self, parent)
        self._focusProxy = scrollProxy(self)

        globalLanguage.languageChanged.connect(self.__onLanguageChange)

        self.setRootIsDecorated(False)
        self.setAlternatingRowColors(True)
        self.setDragEnabled(False)
        self.setHeaderLabels(['type', 'name'])

        self.__editMode = editMode
        self.__nameEdit = None

        self.__incomingItems = []
        self.__outgoingItems = []

        if libs is not None and libname in libs and nodename in libs[libname]:
            self.__nodeDesc = libs[libname][nodename]
        else:
            self.__nodeDesc = None
        if self.__nodeDesc is not None:
            incomingEvents = self.__nodeDesc.incomingEvents
            outgoingEvents = self.__nodeDesc.outgoingEvents
        else:
            incomingEvents = []
            outgoingEvents = []

        for event in incomingEvents:
            item = QTreeWidgetItem()
            item.setText(0, trStr('incoming', 'входящее').text())
            item.setText(1, event)
            item.setData(0, Qt.UserRole, 'in')
            self.addTopLevelItem(item)
            self.__incomingItems.append(item)

        for event in outgoingEvents:
            item = QTreeWidgetItem()
            item.setText(0, trStr('outgoing', 'исходящее').text())
            item.setText(1, event)
            item.setData(0, Qt.UserRole, 'out')
            self.addTopLevelItem(item)
            self.__outgoingItems.append(item)

        self.__onLanguageChange(globalLanguage.language)

        if self.__editMode:
            self.itemDoubleClicked.connect(self.__onDoubleClicked)

    def __startEditEventName(self, item, column):
        if self.__nameEdit is None or item is not self.__nameEdit.item():
            if self.__nameEdit is not None:
                self.__finishEditItemNameLite(self.__nameEdit.item(), self.__nameEdit.column(), self.__nameEdit.text())
            editor = self.itemWidget(item, column)
            if editor is None:
                editor = ItemLineEdit(item, column)
                editor.finished.connect(self.__finishEditItemName)
                self.setItemWidget(item, column, editor)
            self.__nameEdit = editor
            editor.show()

    def contextMenuEvent(self, *args, **kwargs):
        if self.__nodeDesc is None or not self.__editMode:
            return

        menu = QMenu(self)

        item = self.currentItem()  # None if there is no item under cursor
        column = self.currentColumn()  # -1 if there is no item under cursor

        print('debug: column = {0}'.format(column))

        actions = []  # need because of PySide bug: if you'll not save new action somewhere except QMenu, it will be garbage collected

        action = ItemAction(item, 1, trStr('Rename', 'Переименовать').text())
        action.setIcon(QIcon('/'.join([globals.applicationIconsPath, 'page_edit.png'])))
        action.clicked.connect(self.__onDoubleClicked)
        menu.addAction(action)
        actions.append(action)

        if item is None:
            action.setEnabled(False)

        menu.addSeparator()

        action = ItemAction(item, column, trStr('Add incoming event', 'Добавить входящее событие').text())
        action.setIcon(QIcon('/'.join([globals.applicationIconsPath, 'add-3.png'])))
        action.clicked.connect(self.__onAddIncomingEventClicked)
        menu.addAction(action)
        actions.append(action)

        action = ItemAction(item, column, trStr('Add outgoing event', 'Добавить исходящее событие').text())
        action.setIcon(QIcon('/'.join([globals.applicationIconsPath, 'add-3.png'])))
        action.clicked.connect(self.__onAddOutgoingEventClicked)
        menu.addAction(action)
        actions.append(action)

        menu.addSeparator()

        action = ItemAction(item, column, trStr('Remove selected', 'Удалить выбранное событие').text())
        action.setIcon(QIcon('/'.join([globals.applicationIconsPath, 'cancel-1.png'])))
        action.clicked.connect(self.__onDeleteEventClicked)
        menu.addAction(action)
        actions.append(action)

        if item is None:
            action.setEnabled(False)

        menu.exec_(QCursor.pos())

    @QtCore.Slot(QTreeWidgetItem, int)
    def __onAddIncomingEventClicked(self, item, column):
        eventName = 'IncomingEvent{0}'.format(len(self.__incomingItems) + 1)
        newItem = QTreeWidgetItem()
        newItem.setText(0, trStr('incoming', 'входящее').text())
        newItem.setText(1, eventName)
        newItem.setData(0, Qt.UserRole, 'in')
        self.addTopLevelItem(newItem)
        self.sortItems(0, Qt.AscendingOrder)  # using because of insertTopLevelItem() works same as addTopLevelItem()
        self.__incomingItems.append(newItem)
        self.eventAdded.emit('in', eventName)

    @QtCore.Slot(QTreeWidgetItem, int)
    def __onAddOutgoingEventClicked(self, item, column):
        eventName = 'OutgoingEvent{0}'.format(len(self.__outgoingItems) + 1)
        newItem = QTreeWidgetItem()
        newItem.setText(0, trStr('outgoing', 'исходящее').text())
        newItem.setText(1, eventName)
        newItem.setData(0, Qt.UserRole, 'out')
        self.addTopLevelItem(newItem)
        self.__outgoingItems.append(newItem)
        self.eventAdded.emit('out', eventName)

    @QtCore.Slot(QTreeWidgetItem, int)
    def __onDeleteEventClicked(self, item, column):
        event_type = item.data(0, Qt.UserRole)
        if event_type == 'in':
            # removing incoming event
            self.__incomingItems.remove(item)
        else:
            # removing outgoing event
            self.__outgoingItems.remove(item)
        event_name = item.text(1)
        self.takeTopLevelItem(self.indexOfTopLevelItem(item))
        self.eventDeleted.emit(event_type, event_name)

    @QtCore.Slot(QTreeWidgetItem, int)
    def __onDoubleClicked(self, item, column):
        print('INFO: Clicked item \'{0} {1}\' column {2}'.format(item.text(0), item.text(1), column))
        if column == 1 and self.__nodeDesc is not None:
            self.__startEditEventName(item, column)

    @QtCore.Slot(QTreeWidgetItem, int, str)
    def __finishEditItemNameLite(self, item, column, text):
        self.itemWidget(item, column).hide()
        if text:
            oldname = item.text(column)
            newname = text
            if newname != oldname:
                event_type = item.data(0, Qt.UserRole)
                if event_type == 'in':
                    if newname not in self.__nodeDesc.incomingEvents:
                        item.setText(column, newname)
                        self.eventRenamed.emit(event_type, oldname, newname)
                else:
                    if newname not in self.__nodeDesc.outgoingEvents:
                        item.setText(column, newname)
                        self.eventRenamed.emit(event_type, oldname, newname)

    @QtCore.Slot(QTreeWidgetItem, int, str)
    def __finishEditItemName(self, item, column, text):
        self.__nameEdit = None
        self.__finishEditItemNameLite(item, column, text)

    @QtCore.Slot(str)
    def __onLanguageChange(self, lang):
        if globalLanguage.language == Language.English:
            self.setHeaderLabels(['type', 'name'])
        elif globalLanguage.language == Language.Russian:
            self.setHeaderLabels(['тип', 'имя'])
        for item in self.__incomingItems:
            item.setText(0, trStr('incoming', 'входящее').text())
        for item in self.__outgoingItems:
            item.setText(0, trStr('outgoing', 'исходящее').text())

########################################################################################################################
########################################################################################################################


class NodeLineEdit(QLineEdit):
    edited = QtCore.Signal(str)

    def __init__(self, text, editMode, parent=None):
        self.__invalid = False
        self.__editing = False
        self.__undoing = False
        QLineEdit.__init__(self, text, parent)
        self.__editMode = editMode
        self.__tooltip = trStr('Double click to edit', 'Двойной щелчок для редактирования')
        self.__tooltipEdit = trStr('Editing...', 'Редактирование...')
        if self.__editMode:
            self.setToolTip(self.__tooltip.text())
            self.editingFinished.connect(self.__onEditFinish)
        self.textEdited.connect(self.__onEdit)
        globalLanguage.languageChanged.connect(self.__onLanguageChange)

    def isEditing(self):
        return self.__editing

    def setEditing(self, val):
        if self.__editing != val:
            if val:
                self.setToolTip(self.__tooltipEdit.text())
            else:
                self.setToolTip(self.__tooltip.text())
            self.__editing = val
            self.setStyle(QApplication.style())

    editing = QtCore.Property(bool, isEditing, setEditing)

    def isInvalid(self):
        return self.__invalid

    def setInvalid(self, val):
        if self.__invalid != val:
            self.__invalid = val
            self.setStyle(QApplication.style())

    invalid = QtCore.Property(bool, isInvalid, setInvalid)

    def keyPressEvent(self, event):
        if self.__editing or event.key() in (Qt.Key_Left, Qt.Key_Right, Qt.Key_Shift):
            QLineEdit.keyPressEvent(self, event)
        elif self.__editMode and event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.editing = True

    def mouseDoubleClickEvent(self, event):
        if self.__editing or not self.__editMode:
            QLineEdit.mouseDoubleClickEvent(self, event)
        else:
            self.editing = True

    def undo(self):
        if not self.__undoing:
            self.__undoing = True
            QLineEdit.undo(self)
            self.invalid = False
            self.__undoing = False

    def setText(self, text):
        QLineEdit.setText(self, text)
        self.invalid = False

    @QtCore.Slot()
    def __onEditFinish(self):
        self.editing = False

    @QtCore.Slot(str)
    def __onEdit(self, text):
        if not self.__editing:
            self.undo()
        else:
            self.edited.emit(text)

    @QtCore.Slot(str)
    def __onLanguageChange(self, language):
        if self.__editMode:
            if self.__editing:
                self.setToolTip(self.__tooltipEdit.text())
            else:
                self.setToolTip(self.__tooltip.text())

########################################################################################################################
########################################################################################################################


class _GlobalNodeInfoChecks(object):
    def __init__(self):
        self.displayAttributes = True
        self.displayDescription = True
        self.displayEvents = True
        self.displayExtended = False


nodeChecks = _GlobalNodeInfoChecks()

########################################################################################################################
########################################################################################################################


class NodeInfoWidget(QWidget):
    updateWidget = QtCore.Signal(list, str, str, bool)

    __warnings = (trStr('', ''),\
                  trStr('Node with such name is already exist!', 'Узел с таким именем уже существует!'))

    __keyName = 'name'
    __keyType = 'type'
    __keyCreator = 'creator'
    __keyDescription = 'description'
    __keyAttributes = 'attributes'
    __keyEvents = 'events'
    __keyChildren = 'children'
    __keyShape = 'shape'

    __actionAdd = 0
    __actionRename = 1
    __actionDelete = 2
    __actionChange = 3

    def __init__(self, libs, libname, nodename, editMode=False, parent=None):
        QWidget.__init__(self, parent)

        global nodeChecks

        self.__changesDict = dict()
        self.__changesDict[self.__keyName] = [None, self.__changeName]
        self.__changesDict[self.__keyType] = [None, self.__changeType]
        self.__changesDict[self.__keyCreator] = [None, self.__changeCreator]
        self.__changesDict[self.__keyDescription] = [None, self.__changeDescription]
        self.__changesDict[self.__keyAttributes] = [None, self.__changeAttributes]
        self.__changesDict[self.__keyEvents] = [None, self.__changeEvents]
        self.__changesDict[self.__keyChildren] = [None, self.__changeChildren]
        self.__changesDict[self.__keyShape] = [None, self.__changeShape]

        self.__libs = libs
        self.__libname = libname
        self.__nodename = nodename
        self.__creator = ''
        nodeDesc = self.__nodeDesc(self.__nodename)

        if nodeDesc is not None:
            descriptionText = nodeDesc.description
            self.__creator = nodeDesc.creator
            attrs = nodeDesc.attributes()
        else:
            descriptionText = ''
            attrs = dict()

        if type(editMode) is bool:
            self.__editMode = editMode
        else:
            self.__editMode = False

        if self.__editMode:
            self.__submitButton = SubmitButton(trStr('Submit', 'Подтвердить'))
            self.__undoButton = trButton(trStr('Undo', 'Отменить'))
            self.__submitButton.clicked.connect(self.__submit)
            self.__undoButton.clicked.connect(self.__reload)
            self.__submitButton.setEnabled(False)
            self.__undoButton.setEnabled(False)
        else:
            self.__submitButton = None
            self.__undoButton = None

        self.__changingType = False
        self.__typeWidget = None
        self.__typeWidgetFocusProxy = None
        if nodeDesc is None or nodeDesc.nodeClass not in globals.project.alphabet or nodeDesc.nodeType not in \
                globals.project.alphabet[nodeDesc.nodeClass]:
            if nodeDesc is not None:
                print('debug: Corrupted node! Node {0}::{1} class=\'{2}\' type=\'{3}\''
                      .format(self.__libname, self.__nodename, nodeDesc.nodeClass, nodeDesc.nodeType))
            else:
                print('debug: Unknown node {0}::{1}!'.format(self.__libname, self.__nodename))
            self.__typeWidget = trLabel(trStr('unknown', 'неизвестно'))
        else:
            types = globals.project.alphabet[nodeDesc.nodeClass].getTypeNames(False)
            if nodeDesc.nodeType not in types:
                print('debug: Wrong node type! Node {0}::{1} class=\'{2}\' type=\'{3}\''
                      .format(self.__libname, self.__nodename, nodeDesc.nodeClass, nodeDesc.nodeType))
                self.__typeWidget = trLabel(trStr('wrong', 'ошибка'))
            elif self.__editMode:
                self.__typeWidget = QComboBox()
                self.__typeWidgetFocusProxy = comboBoxScrollProxy(self.__typeWidget)
                self.__typeWidget.addItems(types)
                self.__typeWidget.setCurrentIndex(self.__typeWidget.findText(nodeDesc.nodeType))
                self.__typeWidget.currentIndexChanged.connect(self.__onTypeBoxChange)
            else:
                self.__typeWidget = QLabel(nodeDesc.nodeType)

        self.__EditName = NodeLineEdit(self.__nodename, self.__editMode)
        self.__EditName.edited.connect(self.__onNameEdit)
        self.__EditName.editingFinished.connect(self.__onNameEditDone)

        self.__creatorLabel = trLabel(trStr('Creator:', 'Создатель:'))
        self.__creatorLabel.setToolTip(trStr('Class name which will be used to create new instance of \
            node on \'C++\' side.<br/>If it\'s empty, then node name will be used for that purpose.', \
            '<b/>Имя класса, по которому будет создаваться новый экземпляр узла на стороне \'C++\'.\
            <br/>Если не задано, то для этой цели будет использовано имя самого узла.'))
        self.__EditCreator = NodeLineEdit(self.__creator, self.__editMode)
        self.__EditCreator.editingFinished.connect(self.__onCreatorEditDone)

        self.__AttrTree = AttrTree(self.__libname, self.__nodename, attrs, self.__editMode, self)
        self.__AttrTree.setMinimumHeight(60)
        self.__AttrTree.attributeRenamed.connect(self.__onAttributeRenameInternal)
        self.__AttrTree.attributeChanged.connect(self.__onAttributeChangeInternal)
        self.__AttrTree.attributeAdded.connect(self.__onAttributeAddInternal)
        self.__AttrTree.attributeDeleted.connect(self.__onAttributeDeleteInternal)

        self.__EventsTree = EventsTree(libs, libname, nodename, self.__editMode, self)
        self.__EventsTree.setMinimumHeight(50)
        self.__EventsTree.eventRenamed.connect(self.__onEventRenameInternal)
        self.__EventsTree.eventDeleted.connect(self.__onEventDeleteInternal)
        self.__EventsTree.eventAdded.connect(self.__onEventAddInternal)

        self.attributesCheckbox = trCheckbox(trStr('Attributes:', 'Параметры:'))
        self.attributesCheckbox.setChecked(nodeChecks.displayAttributes)
        self.attributesCheckbox.stateChanged.connect(self.__onAttrCheck)

        self.__eventsCheckbox = trCheckbox(trStr('Events:', 'События:'))
        self.__eventsCheckbox.setChecked(nodeChecks.displayEvents)
        self.__eventsCheckbox.stateChanged.connect(self.__onEventsCheck)

        self.__Description = QTextEdit()
        self.__Description.setMinimumHeight(50)
        self.__Description.setAcceptRichText(True)
        self.__Description.setText(descriptionText)
        self.__Description.textChanged.connect(self.__onDescriptionChange)
        self.__descriptionFocusProxy = scrollProxy(self.__Description)
        self.__descriptionEditing = False

        self.descriptionCheckbox = trCheckbox(trStr('Description:', 'Описание:'))
        self.descriptionCheckbox.setChecked(nodeChecks.displayDescription)
        self.descriptionCheckbox.stateChanged.connect(self.__onDescrCheck)

        self.__extendedCheckbox = trCheckbox(trStr('Extended options:', 'Расширенные настройки:'))
        self.__extendedCheckbox.setChecked(nodeChecks.displayExtended)
        self.__extendedCheckbox.stateChanged.connect(self.__onExtendedCheck)

        self.__classBoxesLabel = trLabel(trStr('Possible child nodes:', 'Возможные дочерние узлы:'))

        visibleBoxes = []
        self.__classBoxes = dict()
        for className in globals.project.alphabet.getClasses():
            cb = QCheckBox(className)
            cb.setChecked(False)
            cb.setEnabled(False)
            self.__classBoxes[className] = cb

        if nodeDesc is not None:
            for cls_name in nodeDesc.childClasses:
                if cls_name in self.__classBoxes:
                    self.__classBoxes[cls_name].setChecked(True)
            node_class = globals.project.alphabet[nodeDesc.nodeClass]
            if node_class is not None:
                node_type = node_class[nodeDesc.nodeType]
                if node_type is not None:
                    for cls_name in node_type.children:
                        if cls_name in self.__classBoxes:
                            child_elem = node_type.children[cls_name]
                            if child_elem.used():
                                cb = self.__classBoxes[cls_name]
                                if self.__editMode or cb.isChecked():
                                    visibleBoxes.append(cls_name)
                                if self.__editMode and not child_elem.obligatory():
                                    cb.setEnabled(True)
                                    cb.stateChanged.connect(self.__onChildClassesChecked)
        else:
            node_class = None

        self.__shapeLabel = trLabel(trStr('Sign:', 'Значок:'))
        self.__shapeBox = QComboBox()
        self.__shapeBoxFocusProxy = comboBoxScrollProxy(self.__shapeBox)
        self.__shapeBox.setEnabled(False)
        if globals.project.shapelib is not None:
            for shape in globals.project.shapelib.shapes:
                sign = globals.project.shapelib.shapes[shape]
                if node_class is not None:
                    color = node_class.defaultState().colorEnabled
                else:
                    color = None
                icon = sign.icon(color)
                if icon is not None:
                    self.__shapeBox.addItem(icon, shape)
                else:
                    self.__shapeBox.addItem(shape)
            if nodeDesc is not None and nodeDesc.shape is not None:
                index = self.__shapeBox.findText(nodeDesc.shape.name())
                self.__shapeBox.setCurrentIndex(index)
            if self.__editMode:
                self.__shapeBox.setEnabled(True)
                self.__shapeBox.currentIndexChanged.connect(self.__onShapeIndexChange)

        if not nodeChecks.displayExtended:
            self.__shapeLabel.hide()
            self.__shapeBox.hide()
            self.__classBoxesLabel.hide()
            for cb in self.__classBoxes:
                self.__classBoxes[cb].hide()
        elif not visibleBoxes:
            self.__classBoxesLabel.hide()
            for cb in self.__classBoxes:
                self.__classBoxes[cb].hide()
        else:
            for cb in self.__classBoxes:
                if cb not in visibleBoxes:
                    self.__classBoxes[cb].hide()

        self.__Warning = 0
        self.__statusBar = None
        #if self.__mode == NodeInfoWidget.ModeEdit:
        #	self.__statusBar = QStatusBar()

        typeLabel = trLabel(trStr('Node type:', 'Тип узла:'))
        nameLabel = trLabel(trStr('Node name:', 'Имя узла:'))
        nameLabel.setToolTip(trStr('Text identifier of node in node library.<br/>In addition, it can be used to \
            create new instance of node on \'C++\' side, if there are no \'Creator\' specified.', \
            'Строковый идентификатор узла в библиотеке узлов.<br/>Кроме того, используется для создания нового \
            экземпляра узла на стороне \'C++\' при отсутствии \'Создателя\'.'))

        mainLayout = QGridLayout()
        mainLayout.setContentsMargins(5, 5, 5, 5)
        mainLayout.addWidget(typeLabel, 0, 0, Qt.AlignRight)
        mainLayout.addWidget(self.__typeWidget, 0, 1)
        mainLayout.addWidget(nameLabel, 1, 0, Qt.AlignRight)
        mainLayout.addWidget(self.__EditName, 1, 1)
        mainLayout.addWidget(self.__creatorLabel, 2, 0, Qt.AlignRight)
        mainLayout.addWidget(self.__EditCreator, 2, 1)
        mainLayout.addWidget(self.attributesCheckbox, 3, 0, 1, 2, Qt.AlignLeft)
        mainLayout.addWidget(self.__AttrTree, 4, 0, 1, 2)
        mainLayout.addWidget(self.descriptionCheckbox, 5, 0, 1, 2, Qt.AlignLeft)
        mainLayout.addWidget(self.__Description, 6, 0, 1, 2)
        mainLayout.addWidget(self.__eventsCheckbox, 7, 0, 1, 2, Qt.AlignLeft)
        mainLayout.addWidget(self.__EventsTree, 8, 0, 1, 2)
        mainLayout.addWidget(self.__extendedCheckbox, 9, 0, 1, 2, Qt.AlignLeft)
        mainLayout.addWidget(self.__classBoxesLabel, 10, 0, 1, 2, Qt.AlignLeft)
        row = 11
        for className in self.__classBoxes:
            mainLayout.addWidget(self.__classBoxes[className], row, 0, 1, 2, Qt.AlignLeft)
            row += 1
        mainLayout.addWidget(self.__shapeLabel, row, 0, Qt.AlignRight)
        mainLayout.addWidget(self.__shapeBox, row, 1)
        row += 1
        mainLayout.setRowStretch(3, 3)

        vLayout = QVBoxLayout()
        vLayout.setContentsMargins(0, 0, 0, 0)
        vLayout.addLayout(mainLayout)
        vLayout.addStretch(1)
        if self.__editMode:
            buttonBox = QHBoxLayout()
            buttonBox.setContentsMargins(5, 3, 5, 5)
            buttonBox.addStretch(1)
            buttonBox.addWidget(self.__submitButton, 0)
            buttonBox.addWidget(self.__undoButton, 0)
            vLayout.addLayout(buttonBox)

        #if self.__statusBar is not None:
        #	vLayout.addWidget(self.__statusBar)

        if not nodeChecks.displayAttributes:
            self.__AttrTree.hide()

        if not nodeChecks.displayDescription:
            self.__Description.hide()

        if not nodeChecks.displayEvents:
            self.__EventsTree.hide()

        if not self.__editMode:
            if not self.__creator:
                self.__creatorLabel.hide()
                self.__EditCreator.hide()

        globals.librarySignals.nodeRenamed.connect(self.__onNodeRenameExternal)
        globals.librarySignals.nodeRemoved.connect(self.__onNodeRemoveExternal)
        globals.librarySignals.libraryExcluded.connect(self.__onLibraryExcludeExternal)
        globals.librarySignals.creatorChanged.connect(self.__onCreatorChangeExternal)
        globals.librarySignals.nodeTypeChanged.connect(self.__onNodeTypeChangeExternal)
        globals.librarySignals.attribueRenamed.connect(self.__onAttributeRenameExternal)
        globals.librarySignals.attribueChanged.connect(self.__onAttributeChangeExternal)
        globals.librarySignals.attribueAdded.connect(self.__onAttributeAddDeleteExternal)
        globals.librarySignals.attribueDeleted.connect(self.__onAttributeAddDeleteExternal)
        globals.librarySignals.editPermissionChanged.connect(self.__onEditPermissionChange)

        globals.historySignals.undoMade.connect(self.__reload)
        globals.historySignals.redoMade.connect(self.__reload)

        self.__reloadTimer = QTimer(self)
        self.__reloadTimer.setSingleShot(True)
        self.__reloadTimer.timeout.connect(self.__reload)

        self.setLayout(vLayout)

    @QtCore.Slot()
    def __close(self):
        self.__reloadTimer.stop()
        self.updateWidget.emit(None, None, None, False)

    @QtCore.Slot()
    def __reload(self):
        self.__reloadTimer.stop()
        self.updateWidget.emit(self.__libs, self.__libname, self.__nodename, self.__editMode)

    @QtCore.Slot()
    def __submit(self):
        for k in self.__changesDict:
            if self.__changesDict[k][0] is not None:
                self.__changesDict[k][1]()
        self.__reload()

    def __changeName(self):
        globals.librarySignals.renameNode.emit(self.__libname, self.__nodename, self.__changesDict[self.__keyName][0])

    def __changeCreator(self):
        globals.librarySignals.changeCreator.emit(self.__libname, self.__nodename,\
                                                  self.__changesDict[self.__keyCreator][0])

    def __changeType(self):
        globals.librarySignals.changeNodeType.emit(self.__libname, self.__nodename,\
                                                   self.__changesDict[self.__keyType][0])

    def __changeDescription(self):
        globals.librarySignals.changeNodeDescription.emit(self.__libname, self.__nodename,\
                                                          self.__changesDict[self.__keyDescription][0])

    def __changeShape(self):
        globals.librarySignals.changeNodeShape.emit(self.__libname, self.__nodename,\
                                                    self.__changesDict[self.__keyShape][0])

    def __changeChildren(self):
        globals.librarySignals.changeNodeChildren.emit(self.__libname, self.__nodename,\
                                                       self.__changesDict[self.__keyChildren][0])

    def __changeAttributes(self):
        for action_type, data in self.__changesDict[self.__keyAttributes][0]:
            if action_type == self.__actionRename:
                oldname, newname, full = data
                globals.librarySignals.renameAttribute.emit(self.__libname, self.__nodename, oldname, newname, full)
            elif action_type == self.__actionAdd:
                attrName, attrDesc = data
                globals.librarySignals.addAttribute.emit(self.__libname, self.__nodename, attrName, attrDesc)
            elif action_type == self.__actionDelete:
                attrName = data
                globals.librarySignals.deleteAttribute.emit(self.__libname, self.__nodename, attrName)
            elif action_type == self.__actionChange:
                attrName, attrDesc = data
                globals.librarySignals.changeAttribute.emit(self.__libname, self.__nodename, attrName, attrDesc)

    def __changeEvents(self):
        for action_type, event_type, data in self.__changesDict[self.__keyEvents][0]:
            if action_type == self.__actionRename:
                oldname, newname = data
                if event_type == 'in':
                    globals.librarySignals.renameIncomingEvent.emit(self.__libname, self.__nodename, oldname, newname)
                else:
                    globals.librarySignals.renameOutgoingEvent.emit(self.__libname, self.__nodename, oldname, newname)
            elif action_type == self.__actionAdd:
                name = data
                if event_type == 'in':
                    globals.librarySignals.addIncomingEvent.emit(self.__libname, self.__nodename, name)
                else:
                    globals.librarySignals.addOutgoingEvent.emit(self.__libname, self.__nodename, name)
            elif action_type == self.__actionDelete:
                name = data
                if event_type == 'in':
                    globals.librarySignals.deleteIncomingEvent.emit(self.__libname, self.__nodename, name)
                else:
                    globals.librarySignals.deleteOutgoingEvent.emit(self.__libname, self.__nodename, name)

    def __nodeDesc(self, name):
        if self.__libs is not None and self.__libname in self.__libs and name in self.__libs[self.__libname]:
            return self.__libs[self.__libname][name]
        return None

    @QtCore.Slot(bool)
    def __onEditPermissionChange(self, enableEdit):
        self.__editMode = enableEdit
        self.__reload()

    @QtCore.Slot(str)
    def __onNameEdit(self, name):
        if name and self.__nodename == name or name not in self.__libs[self.__libname]:
            self.__EditName.invalid = False
        else:
            self.__EditName.invalid = True

    @QtCore.Slot()
    def __onNameEditDone(self):
        if not self.__editMode or not self.__EditName.text() or self.__EditName.invalid:
            self.__EditName.undo()
        elif self.__nodename != self.__EditName.text():
            self.__changesDict[self.__keyName][0] = self.__EditName.text()
            self.__submitButton.setEnabled(True)
            self.__undoButton.setEnabled(True)

    @QtCore.Slot(str, str, str)
    def __onNodeRenameExternal(self, libname, oldname, newname):
        if self.__libname == libname and self.__nodename == oldname:
            self.__nodename = newname
            self.__EditName.setText(newname)

    @QtCore.Slot(str, str, str)
    def __onNodeRemoveExternal(self, libname, nodename, nodeClass):
        if self.__libname == libname and self.__nodename == nodename:
            self.__close()

    @QtCore.Slot(str)
    def __onLibraryExcludeExternal(self, libname):
        if self.__libname == libname:
            self.__close()

    @QtCore.Slot()
    def __onCreatorEditDone(self):
        if not self.__editMode:
            self.__EditCreator.undo()
        elif self.__creator != self.__EditCreator.text():
            self.__changesDict[self.__keyCreator][0] = self.__EditCreator.text()
            self.__submitButton.setEnabled(True)
            self.__undoButton.setEnabled(True)

    @QtCore.Slot(str, str, str, str)
    def __onCreatorChangeExternal(self, libname, nodename, creatorOld, creator):
        if self.__libname == libname and self.__nodename == nodename:
            self.__creator = creator
            self.__EditCreator.setText(creator)

    @QtCore.Slot(str, str, str, str)
    def __onNodeTypeChangeExternal(self, libname, nodename, typeOld, typeNew):
        if self.__libname == libname and self.__nodename == nodename:
            self.__reloadTimer.start(10)

    @QtCore.Slot(str, str, str, str)
    def __onAttributeRenameExternal(self, libname, nodename, oldname, newname):
        if self.__libname == libname and self.__nodename == nodename:
            self.__reloadTimer.start(10)

    @QtCore.Slot(str, str, str, object)
    def __onAttributeChangeExternal(self, libname, nodename, attributeName, attributeOldDescriptor):
        if self.__libname == libname and self.__nodename == nodename:
            self.__reloadTimer.start(10)

    @QtCore.Slot(str, str, str)
    def __onAttributeAddDeleteExternal(self, libname, nodename, attributeName):
        if self.__libname == libname and self.__nodename == nodename:
            self.__reloadTimer.start(10)

    @QtCore.Slot(str, str, bool)
    def __onAttributeRenameInternal(self, oldname, newname, full):
        changes = self.__changesDict[self.__keyAttributes]
        if changes[0] is None:
            changes[0] = []
        data = (oldname, newname, full)
        entry = (self.__actionRename, data)
        changes[0].append(entry)
        self.__submitButton.setEnabled(True)
        self.__undoButton.setEnabled(True)

    @QtCore.Slot(str, object)
    def __onAttributeChangeInternal(self, attributeName, attributeDescriptor):
        changes = self.__changesDict[self.__keyAttributes]
        if changes[0] is None:
            changes[0] = []
        data = (attributeName, attributeDescriptor.deepcopy())
        entry = (self.__actionChange, data)
        changes[0].append(entry)
        self.__submitButton.setEnabled(True)
        self.__undoButton.setEnabled(True)

    @QtCore.Slot(str, object)
    def __onAttributeAddInternal(self, attributeName, attributeDescriptor):
        changes = self.__changesDict[self.__keyAttributes]
        if changes[0] is None:
            changes[0] = []
        data = (attributeName, attributeDescriptor.deepcopy())
        entry = (self.__actionAdd, data)
        changes[0].append(entry)
        self.__submitButton.setEnabled(True)
        self.__undoButton.setEnabled(True)

    @QtCore.Slot(str)
    def __onAttributeDeleteInternal(self, attributeName):
        changes = self.__changesDict[self.__keyAttributes]
        if changes[0] is None:
            changes[0] = []
        data = attributeName
        entry = (self.__actionDelete, data)
        changes[0].append(entry)
        self.__submitButton.setEnabled(True)
        self.__undoButton.setEnabled(True)

    @QtCore.Slot(str, str, str)
    def __onEventRenameInternal(self, event_type, oldname, newname):
        changes = self.__changesDict[self.__keyEvents]
        if changes[0] is None:
            changes[0] = []
        data = (oldname, newname)
        entry = (self.__actionRename, event_type, data)
        changes[0].append(entry)
        self.__submitButton.setEnabled(True)
        self.__undoButton.setEnabled(True)

    @QtCore.Slot(str, str)
    def __onEventDeleteInternal(self, event_type, event_name):
        changes = self.__changesDict[self.__keyEvents]
        if changes[0] is None:
            changes[0] = []
        entry = (self.__actionDelete, event_type, event_name)
        changes[0].append(entry)
        self.__submitButton.setEnabled(True)
        self.__undoButton.setEnabled(True)

    @QtCore.Slot(str, str)
    def __onEventAddInternal(self, event_type, event_name):
        changes = self.__changesDict[self.__keyEvents]
        if changes[0] is None:
            changes[0] = []
        entry = (self.__actionAdd, event_type, event_name)
        changes[0].append(entry)
        self.__submitButton.setEnabled(True)
        self.__undoButton.setEnabled(True)

    @QtCore.Slot()
    def __onDescriptionChange(self):
        if not self.__descriptionEditing:
            self.__descriptionEditing = True
            if not self.__editMode:
                self.__Description.undo()
            else:
                self.__changesDict[self.__keyDescription][0] = self.__Description.toPlainText()
                self.__submitButton.setEnabled(True)
                self.__undoButton.setEnabled(True)
            self.__descriptionEditing = False

    @QtCore.Slot(int)
    def __onTypeBoxChange(self, index):
        self.__changesDict[self.__keyType][0] = self.__typeWidget.itemText(index)
        self.__submitButton.setEnabled(True)
        self.__undoButton.setEnabled(True)

    @QtCore.Slot()
    def __onDescrCheck(self):
        global nodeChecks
        nodeChecks.displayDescription = self.descriptionCheckbox.isChecked()
        if nodeChecks.displayDescription:
            self.__Description.show()
        else:
            self.__Description.hide()

    @QtCore.Slot()
    def __onChildClassesChecked(self):
        if self.__editMode:
            checks = []
            for cls_name in self.__classBoxes:
                cb = self.__classBoxes[cls_name]
                if cb.isVisible() and cb.isChecked():
                    checks.append(cls_name)
            self.__changesDict[self.__keyChildren][0] = checks
            self.__submitButton.setEnabled(True)
            self.__undoButton.setEnabled(True)

    @QtCore.Slot()
    def __onAttrCheck(self):
        global nodeChecks
        nodeChecks.displayAttributes = self.attributesCheckbox.isChecked()
        if nodeChecks.displayAttributes:
            self.__AttrTree.show()
        else:
            self.__AttrTree.hide()

    @QtCore.Slot()
    def __onEventsCheck(self):
        global nodeChecks
        nodeChecks.displayEvents = self.__eventsCheckbox.isChecked()
        if nodeChecks.displayEvents:
            self.__EventsTree.show()
        else:
            self.__EventsTree.hide()

    @QtCore.Slot()
    def __onExtendedCheck(self):
        global nodeChecks
        nodeChecks.displayExtended = self.__extendedCheckbox.isChecked()
        if nodeChecks.displayExtended:
            if self.__editMode:
                self.__classBoxesLabel.show()
                for className in self.__classBoxes:
                    self.__classBoxes[className].show()
            else:
                visible_count = 0
                for className in self.__classBoxes:
                    if self.__classBoxes[className].isChecked():
                        self.__classBoxes[className].show()
                        visible_count += 1
                if visible_count > 0:
                    self.__classBoxesLabel.show()
            self.__shapeLabel.show()
            self.__shapeBox.show()
        else:
            self.__classBoxesLabel.hide()
            for className in self.__classBoxes:
                self.__classBoxes[className].hide()
            self.__shapeLabel.hide()
            self.__shapeBox.hide()

    @QtCore.Slot(int)
    def __onShapeIndexChange(self, index):
        if self.__editMode:
            self.__changesDict[self.__keyShape][0] = self.__shapeBox.itemText(index)
            self.__submitButton.setEnabled(True)
            self.__undoButton.setEnabled(True)

########################################################################################################################
########################################################################################################################


class InfoStack(QStackedWidget):
    def __init__(self, parent=None):
        QStackedWidget.__init__(self, parent)
        QStackedWidget.addWidget(self, QListWidget())
        self.setCurrentIndex(0)
        self.widgets = []
        self.__replaceIndex = -1
        self.__replaceData = None
        self.__timer = QTimer(self)
        self.__timer.setSingleShot(True)
        self.__timer.timeout.connect(self.__onTimeout)

    def clear(self):
        self.setCurrentIndex(0)
        for widget in self.widgets:
            self.removeWidget(widget)
        self.widgets = []

    def addWidget(self, widget, setActive=False):
        if widget not in self.widgets:
            self.widgets.append(widget)
            QStackedWidget.addWidget(self, widget)
            if setActive is True:
                self.setCurrentWidget(widget)

    def addNodeWidget(self, libs, libname, nodename, editMode=False):
        if libs is not None and libname is not None and libname in libs \
                and nodename is not None and nodename in libs[libname]:
            widget = NodeInfoWidget(libs, libname, nodename, editMode)
            widget.updateWidget.connect(self.replaceCurrentNodeWidget)
            self.addWidget(widget, True)

    def addLibraryWidget(self, libs, libname, editMode=False):
        if libs is not None and libname is not None and libname in libs:
            widget = LibInfoWidget(libs, libname, editMode)
            widget.updateWidget.connect(self.replaceCurrentLibWidget)
            self.addWidget(widget, True)

    @QtCore.Slot(list, str, str, bool)
    def replaceCurrentNodeWidget(self, libs, libname, nodename, editMode):
        self.__replaceIndex = self.currentIndex()
        self.__replaceData = (libs, libname, nodename, editMode)
        self.__timer.start(5)

    @QtCore.Slot(list, str, bool)
    def replaceCurrentLibWidget(self, libs, libname, editMode):
        self.__replaceIndex = self.currentIndex()
        self.__replaceData = (libs, libname, editMode)
        self.__timer.start(5)

    @QtCore.Slot()
    def __onTimeout(self):
        if self.__replaceIndex < 0 or self.__replaceData is None:
            return
        currIndex = self.__replaceIndex
        index = currIndex - 1
        if index >= 0:
            oldWidget = self.widgets[index]
            widget = None
            if len(self.__replaceData) > 3:
                libs, libname, nodename, editMode = self.__replaceData
                if libs is not None and libname is not None and libname in libs and nodename is not None and nodename in \
                        libs[libname]:
                    widget = NodeInfoWidget(libs, libname, nodename, editMode)
                    widget.updateWidget.connect(self.replaceCurrentNodeWidget)
            else:
                libs, libname, editMode = self.__replaceData
                if libs is not None and libname is not None and libname in libs:
                    widget = LibInfoWidget(libs, libname, editMode)
                    widget.updateWidget.connect(self.replaceCurrentLibWidget)
            if widget is None:
                self.widgets.pop(index)
                self.setCurrentIndex(0)
            else:
                self.widgets[index] = widget
                self.insertWidget(currIndex, widget)
                self.setCurrentIndex(currIndex)
            self.removeWidget(oldWidget)
        self.__replaceIndex = -1
        self.__replaceData = None

########################################################################################################################
########################################################################################################################


class InfoDock(trDockWidget):
    def __init__(self, title='', parent=None):
        trDockWidget.__init__(self, title, parent)
        self.Stack = InfoStack()
        self.setWidget(self.Stack)
        globals.nodeListSignals.notSelected.connect(self.clear)

    @QtCore.Slot()
    def clear(self):
        self.Stack.clear()

    def addWidget(self, widget, setActive=False):
        self.Stack.addWidget(widget, setActive)

    def addNodeWidget(self, libs, libname, nodename, editMode=False):
        self.Stack.addNodeWidget(libs, libname, nodename, editMode)

    def addLibraryWidget(self, libs, libname, editMode=False):
        self.Stack.addLibraryWidget(libs, libname, editMode)

########################################################################################################################
########################################################################################################################
