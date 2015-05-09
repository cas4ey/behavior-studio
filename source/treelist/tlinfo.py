# coding=utf-8
# -----------------
# file      : tlinfo.py
# date      : 2012/11/04
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

from extensions.widgets import trButton, SubmitButton, trDockWidget, scrollProxy

from project.proj import *
from treenode import *
from .infotree import *

from language import globalLanguage, Language, trStr

import globals

#######################################################################################################################

contentsMargin = 1
rowHeight = 20
minimumWidth = 50

#######################################################################################################################
#######################################################################################################################


class SizeHintedTree(QTreeWidget):
    def __init__(self, columns, headers, parent=None):
        QTreeWidget.__init__(self, parent)
        self._focusProxy = scrollProxy(self)
        self.setMinimumHeight(30)
        self.setSelectionMode(QAbstractItemView.NoSelection)
        self.setRootIsDecorated(False)
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(False)
        if headers:
            self.setHeaderLabels(headers)
        else:
            self.header().close()
        self.setColumnCount(columns)
        self.setContentsMargins(contentsMargin, contentsMargin, contentsMargin, contentsMargin)
        self.preferredHeight = 0
        self.preferredWidth = 0

    def sizeHint(self, *args, **kwargs):
        sizehint = QTreeWidget.sizeHint(self, *args, **kwargs)
        if self.preferredHeight > 0:
            sizehint.setHeight(self.preferredHeight + 10)
        if self.preferredWidth > 0:
            sizehint.setWidth(self.preferredWidth)
        return sizehint

    def setHeight(self, height):
        # self.resize(self.width(),height)
        self.setMinimumHeight(height)
        self.setMinimumHeight(30)

#######################################################################################################################


class TreeWithDotLine(SizeHintedTree):
    def __init__(self, parent=None):
        SizeHintedTree.__init__(self, 2, ['type', 'data'], parent)
        self.drawLineAt = None
        self.__onLanguageChange(globalLanguage.language)
        globalLanguage.languageChanged.connect(self.__onLanguageChange)

    def predelete(self):
        try:
            globalLanguage.languageChanged.disconnect(self.__onLanguageChange)
        except RuntimeError:
            pass

    def drawRow(self, painter, option, index):
        SizeHintedTree.drawRow(self, painter, option, index)
        item = self.itemFromIndex(index)
        if self.drawLineAt is not None and self.drawLineAt is item:
            rect = self.visualRect(index)
            h = self.rowHeight(index)
            w = self.columnWidth(0) + self.columnWidth(1)
            # painter.setPen(QPen(Qt.gray, 1))
            painter.setPen(QPen(Qt.gray, 1, Qt.DotLine))
            painter.drawLine(0, rect.y() + 0.5 * h * 0.9, w + 10, rect.y() + 0.5 * h * 0.9)
            painter.drawLine(1, rect.y() + 0.5 * h * 1.1, w + 10 - 1, rect.y() + 0.5 * h * 1.1)
            # painter.setPen(QPen(Qt.black,1))
            # painter.drawText(0,rect.y(),w,h,int(Qt.AlignCenter),u'attributes')#,QRect(0,0,w,h))

    @QtCore.Slot(str)
    def __onLanguageChange(self, lang):
        if globalLanguage.language == Language.English:
            self.setHeaderLabels(['type', 'data'])
        elif globalLanguage.language == Language.Russian:
            self.setHeaderLabels(['тип', 'данные'])

#######################################################################################################################


class MyTreeWidgetItem(QTreeWidgetItem):
    def __init__(self, *args, **kwargs):
        QTreeWidgetItem.__init__(self, *args, **kwargs)
        self.__userData = None

    def hide(self):
        self.setHidden(True)

    def show(self):
        self.setHidden(False)

    def setUserData(self, data):
        self.__userData = data

    def userData(self):
        return self.__userData

#######################################################################################################################
#######################################################################################################################


class TaskInfoWidget(QWidget):
    attributeChanged = QtCore.Signal()
    updateWidget = QtCore.Signal(Project, TreeNode, bool, bool, bool)

    def __init__(self, project, treenode, editMode=False, parent=None, wndFlags=0):
        QWidget.__init__(self, parent, wndFlags)

        self.treeWidget = TreeWithDotLine()
        self.setContentsMargins(contentsMargin, contentsMargin, contentsMargin, contentsMargin)

        if type(editMode) is bool:
            self.__editMode = editMode
        else:
            self.__editMode = False

        if not self.__editMode:
            self.treeWidget.header().close()
        else:
            self.treeWidget.preferredHeight += rowHeight

        self.__attributeItems = []
        self.__attributeBaseItems = dict()

        self.attributeChanged.connect(self.onAttributeChange)

        self.__updating = False
        self.isChanged = False

        self.__proj = project
        self.__node = treenode
        self.__class = self.__node.nodeClass
        self.__type = self.__node.nodeType
        self.__debugMode = False
        self.__singleBlock = False
        self.__invertMode = False
        self.__nodeDescRef = treenode.nodeDesc()

        self.__targetPath = ''
        self.__targetRef = self.__node.target
        texts = self.__targetRef.split('/')
        if len(texts) > 1:
            texts.pop()
            self.__targetPath = '/'.join(texts)
        else:
            self.__targetPath = self.__node.target

        self.__attributes = self.__node.getAttributesCopy()

        self.CommitButton = None
        self.UndoButton = None

        if self.__editMode:
            self.CommitButton = SubmitButton(trStr('Submit', 'Подтвердить'))
            self.UndoButton = trButton(trStr('Undo', 'Отменить'))
            self.CommitButton.clicked.connect(self.commitChanges)
            self.UndoButton.clicked.connect(self.undoChanges)
            self.CommitButton.setEnabled(False)
            self.UndoButton.setEnabled(False)

        self.__DebugModeCombobox = None
        self.__SingleblockModeCombobox = None
        self.__InvertModeCombobox = None
        self.__NodeCombobox = None
        self.__TypeCombobox = None
        self.__PathCombobox = None
        self.__RefCombobox = None
        self.__refConnected = False

        self.__debugComboIndex = -1
        self.__singleBlockComboIndex = -1
        self.__invertComboIndex = -1
        self.__nodeComboIndex = -1
        self.__typeComboIndex = -1
        self.__pathComboIndex = -1
        self.__refComboIndex = -1

        self.singleblockItem = None

        # uid item
        uidItem = MyTreeWidgetItem(self.treeWidget, ['uid', str(self.__node.uid())])
        self.treeWidget.addTopLevelItem(uidItem)
        self.treeWidget.preferredHeight += rowHeight

        # class item
        self.classItem = MyTreeWidgetItem(self.treeWidget, ['class', self.__class])
        self.treeWidget.addTopLevelItem(self.classItem)
        self.treeWidget.preferredHeight += rowHeight
        self.attributesPreferredHeight = 0.0

        # debug mode item
        nodeClassRef = self.__node.cls()
        if nodeClassRef is not None:
            if nodeClassRef.debuggable:
                self.__debugMode = self.__node.debugMode()
                self.debugItem = MyTreeWidgetItem(self.treeWidget)
                self.debugItem.setText(0, 'debugMode')
                self.treeWidget.addTopLevelItem(self.debugItem)
                self.treeWidget.preferredHeight += rowHeight
                if not self.__editMode:
                    if self.__debugMode is True:
                        self.debugItem.setText(1, 'True')
                    else:
                        self.debugItem.setText(1, 'False')
                else:
                    self.__DebugModeCombobox = LowCombobox()
                    self.__DebugModeCombobox.setInsertPolicy(QComboBox.NoInsert)
                    self.__DebugModeCombobox.setMinimumWidth(minimumWidth)
                    self.__fillDebugCombobox()
                    self.__DebugModeCombobox.currentIndexChanged.connect(self.onDebugModeChange)
                    self.treeWidget.setItemWidget(self.debugItem, 1, self.__DebugModeCombobox)

            nodeTypeRef = self.__node.type()
            if not self.__editMode:
                if nodeTypeRef is not None and nodeTypeRef.singleblockEnabled:
                    self.__singleBlock = self.__node.singleBlock()
                    self.singleblockItem = MyTreeWidgetItem(self.treeWidget)
                    self.singleblockItem.setText(0, 'singleBlock')
                    self.treeWidget.addTopLevelItem(self.singleblockItem)
                    self.treeWidget.preferredHeight += rowHeight
                    if self.__singleBlock is True:
                        self.singleblockItem.setText(1, 'True')
                    else:
                        self.singleblockItem.setText(1, 'False')
            else:
                self.singleblockItem = MyTreeWidgetItem(self.treeWidget)
                self.singleblockItem.setText(0, 'singleBlock')
                self.treeWidget.addTopLevelItem(self.singleblockItem)
                self.treeWidget.preferredHeight += rowHeight
                self.__SingleblockModeCombobox = LowCombobox()
                self.__SingleblockModeCombobox.setInsertPolicy(QComboBox.NoInsert)
                self.__SingleblockModeCombobox.setMinimumWidth(minimumWidth)
                if nodeTypeRef is not None and nodeTypeRef.singleblockEnabled:
                    self.__singleBlock = self.__node.singleBlock()
                else:
                    self.__SingleblockModeCombobox.hide()
                    self.singleblockItem.hide()
                self.__fillSingleblockCombobox()
                self.__SingleblockModeCombobox.currentIndexChanged.connect(self.onSingleblockModeChange)
                self.treeWidget.setItemWidget(self.singleblockItem, 1, self.__SingleblockModeCombobox)

            if nodeClassRef.invertible:
                self.__invertMode = self.__node.isInverse()
                self.invertItem = MyTreeWidgetItem(self.treeWidget)
                self.invertItem.setText(0, 'inverse')
                self.treeWidget.addTopLevelItem(self.invertItem)
                self.treeWidget.preferredHeight += rowHeight
                if not self.__editMode:
                    if self.__invertMode is True:
                        self.invertItem.setText(1, 'True')
                    else:
                        self.invertItem.setText(1, 'False')
                else:
                    self.__InvertModeCombobox = LowCombobox()
                    self.__InvertModeCombobox.setInsertPolicy(QComboBox.NoInsert)
                    self.__InvertModeCombobox.setMinimumWidth(minimumWidth)
                    self.__fillInvertCombobox()
                    self.__InvertModeCombobox.currentIndexChanged.connect(self.onInvertModeChange)
                    self.treeWidget.setItemWidget(self.invertItem, 1, self.__InvertModeCombobox)

        # type item
        self.typeItem = MyTreeWidgetItem(self.treeWidget)
        self.typeItem.setText(0, 'type')
        self.treeWidget.addTopLevelItem(self.typeItem)
        self.treeWidget.preferredHeight += rowHeight
        if not self.__editMode:
            text = 'Unknown'
            if self.__node.type() is not None:
                if self.__node.type().isLink():
                    text = self.__type
                else:
                    text = '{0} {1}'.format(self.__type, self.__class)
            self.typeItem.setText(1, text)
        else:
            self.__TypeCombobox = LowCombobox()
            self.__TypeCombobox.setInsertPolicy(QComboBox.NoInsert)
            self.__TypeCombobox.setMinimumWidth(minimumWidth)
            self.__fillTypeCombobox()
            self.__TypeCombobox.currentIndexChanged.connect(self.onTypeChange)
            self.treeWidget.setItemWidget(self.typeItem, 1, self.__TypeCombobox)

        # node
        self.nodeItem = MyTreeWidgetItem(self.treeWidget)
        self.nodeItem.setText(0, 'node')
        self.treeWidget.addTopLevelItem(self.nodeItem)
        self.treeWidget.preferredHeight += rowHeight
        if not self.__editMode:
            text = 'Unknown'
            if self.__nodeDescRef is not None:
                text = self.__nodeDescRef.name
            self.nodeItem.setText(1, text)
        else:
            self.__NodeCombobox = LowCombobox()
            self.__NodeCombobox.setInsertPolicy(QComboBox.NoInsert)
            self.__NodeCombobox.setMinimumWidth(minimumWidth)
            self.__fillNodeCombobox()
            self.__NodeCombobox.currentIndexChanged.connect(self.onNodeChange)
            self.treeWidget.setItemWidget(self.nodeItem, 1, self.__NodeCombobox)

        # path
        self.pathItem = MyTreeWidgetItem(self.treeWidget)
        self.pathItem.setText(0, 'path')
        self.treeWidget.addTopLevelItem(self.pathItem)
        self.treeWidget.preferredHeight += rowHeight
        if not self.__editMode:
            texts = self.__targetPath.split('/')
            if texts:
                self.pathItem.setText(1, texts[len(texts) - 1])
            else:
                self.pathItem.setText(1, self.__targetPath)
            self.pathItem.setToolTip(1, self.__targetPath)
        else:
            self.__PathCombobox = LowCombobox()
            self.__PathCombobox.setInsertPolicy(QComboBox.NoInsert)
            self.__PathCombobox.setMinimumWidth(minimumWidth)
            self.__PathCombobox.addItem('<select file>', '')
            k = 0
            paths = self.__proj.trees.getFilesList(self.__proj.nodes)
            for path in paths:
                k += 1
                texts = path.split('/')
                if texts:
                    self.__PathCombobox.addItem(texts[len(texts) - 1], path)
                else:
                    self.__PathCombobox.addItem(path, path)
                self.__PathCombobox.setItemData(k, path, Qt.ToolTipRole)
            self.__PathCombobox.model().sort(0)
            i = self.__PathCombobox.findData(self.__targetPath)
            if i < 0:
                i = 0
            self.__PathCombobox.setCurrentIndex(i)
            self.__pathComboIndex = self.__PathCombobox.currentIndex()
            self.__PathCombobox.currentIndexChanged.connect(self.onReferencePathChange)
            self.treeWidget.setItemWidget(self.pathItem, 1, self.__PathCombobox)

        # reference
        self.refItem = MyTreeWidgetItem(self.treeWidget)
        self.refItem.setText(0, 'target')
        self.treeWidget.addTopLevelItem(self.refItem)
        self.treeWidget.preferredHeight += rowHeight
        if not self.__editMode:
            texts = self.__targetRef.split('/')
            if texts:
                self.refItem.setText(1, texts[len(texts) - 1])
            else:
                self.refItem.setText(1, '')
        else:
            self.__RefCombobox = LowCombobox()
            self.__RefCombobox.setEditable(True)
            self.__RefCombobox.setInsertPolicy(QComboBox.NoInsert)
            self.__RefCombobox.setMinimumWidth(minimumWidth)
            #self.__RefCombobox.setMaximumWidth(150)
            self.__fillRefCombobox(self.__targetPath)
            self.treeWidget.setItemWidget(self.refItem, 1, self.__RefCombobox)

        # attributes
        self.attrsHeaderItem = MyTreeWidgetItem(self.treeWidget, ['', ''])  # ['attributes:',''])
        # trColor = QColor(Qt.darkRed)
        # trColor.setAlpha(64)
        # self.attrsHeaderItem.setBackground(0,trColor)
        # self.attrsHeaderItem.setBackground(1,trColor)
        self.treeWidget.addTopLevelItem(self.attrsHeaderItem)
        self.treeWidget.drawLineAt = self.attrsHeaderItem
        self.attrsHeaderItem.hide()
        self.refreshAttributesItems()

        # layout
        buttonBox = None
        if self.CommitButton is not None and self.UndoButton is not None:
            buttonBox = QHBoxLayout()
            buttonBox.setContentsMargins(5, 3, 5, 5)
            buttonBox.addStretch(1)
            buttonBox.addWidget(self.CommitButton, 0)
            buttonBox.addWidget(self.UndoButton, 0)

        mainLayout = QVBoxLayout()
        mainLayout.setContentsMargins(contentsMargin, contentsMargin, contentsMargin, contentsMargin)
        mainLayout.addWidget(self.treeWidget)
        if buttonBox is not None:
            # mainLayout.addStretch(1)
            mainLayout.addLayout(buttonBox)

        if not self.__node.type().isLink():
            self.pathItem.hide()
            self.refItem.hide()
        else:
            self.nodeItem.hide()
        self.treeWidget.preferredHeight -= rowHeight

        globals.librarySignals.nodeRenamed.connect(self.__onNodeRename)
        globals.librarySignals.attribueRenamed.connect(self.__onAttributeRename)
        globals.librarySignals.attribueChanged.connect(self.__onAttributeChange)
        globals.librarySignals.attribueAdded.connect(self.__onAttributeAddDelete)
        globals.librarySignals.attribueDeleted.connect(self.__onAttributeAddDelete)
        globals.librarySignals.nodeRemoved.connect(self.__onNodeRemove)
        globals.librarySignals.nodeTypeChanged.connect(self.__onNodeTypeChangeExternal)
        globals.librarySignals.libraryExcluded.connect(self.__onLibraryExclude)

        self.setLayout(mainLayout)

    def __del__(self):
        try:
            self.treeWidget.predelete()
        finally:
            self.treeWidget = None

    def __reload(self):
        self.updateWidget.emit(self.__proj, self.__node, self.__editMode, False, False)

    def __close(self):
        self.updateWidget.emit(None, None, False, False, False)

    def showAll(self):
        if self.classItem.isHidden():
            self.classItem.show()
            self.treeWidget.preferredHeight += rowHeight
        if self.typeItem.isHidden():
            self.typeItem.show()
            self.treeWidget.preferredHeight += rowHeight
        if not self.__node.type().isLink():
            if self.nodeItem.isHidden():
                self.nodeItem.show()
                self.treeWidget.preferredHeight += rowHeight
        self.refreshAttributesItems()
        hgt = min(self.treeWidget.preferredHeight, self.height() * 0.9)
        self.treeWidget.setHeight(int(hgt))

    def showOnlyAttributes(self):
        if not self.classItem.isHidden():
            self.classItem.hide()
            self.treeWidget.preferredHeight -= rowHeight
        if not self.typeItem.isHidden():
            self.typeItem.hide()
            self.treeWidget.preferredHeight -= rowHeight
        if not self.__node.type().isLink():
            if not self.nodeItem.isHidden():
                self.nodeItem.hide()
                self.treeWidget.preferredHeight -= rowHeight
        if not self.attrsHeaderItem.isHidden():
            self.attrsHeaderItem.hide()
            self.treeWidget.preferredHeight -= rowHeight

    def refreshAttributesItems(self):
        self.__attributeBaseItems.clear()

        self.treeWidget.preferredHeight -= self.attributesPreferredHeight

        for item in self.__attributeItems:
            #self.attrsHeaderItem.removeChild(item)
            row = self.treeWidget.indexOfTopLevelItem(item)
            self.treeWidget.model().removeRow(row)
            del item
        self.__attributeItems = []

        self.attributesPreferredHeight = 0.0
        for a in self.__attributes:
            attrDesc = self.__attributes[a].attrDesc()
            if attrDesc is None:
                continue

            value = self.__attributes[a].value()

            if not isinstance(value, list):
                values = [value]
            else:
                values = value

            i = int(0)
            if not values:
                if attrDesc.isArray():
                    item = MyTreeWidgetItem(self.treeWidget)
                    item.setText(0, attrDesc.attrname)
                    item.setText(1, 'empty')
                    item.setUserData(a)

                    if attrDesc.description:
                        item.setToolTip(0, attrDesc.description)
                        item.setToolTip(1, attrDesc.description)

                    self.attributesPreferredHeight += rowHeight

                    self.__attributeItems.append(item)
                    self.__attributeBaseItems[a] = item
            else:
                for val in values:
                    item = MyTreeWidgetItem(self.treeWidget)
                    self.treeWidget.addTopLevelItem(item)
                    if attrDesc.isArray():
                        item.setText(0, '{0}[{1}]'.format(attrDesc.attrname, i))
                    else:
                        item.setText(0, attrDesc.attrname)
                    item.setUserData(a)

                    if attrDesc.description:
                        item.setToolTip(0, attrDesc.description)
                        item.setToolTip(1, attrDesc.description)

                    self.attributesPreferredHeight += rowHeight

                    if not self.__editMode:
                        item.setText(1, str(val))
                    else:
                        if attrDesc.availableValues():
                            widget = TreeValueCombo(item, 1, val, attrDesc, attrDesc.description, self.treeWidget)
                            self.treeWidget.setItemWidget(item, 1, widget)
                            widget.valueChange.connect(self.onAttrComboChange)
                        else:
                            widget = TreeDataEdit(item, 1, attrDesc, val, self.treeWidget)
                            self.treeWidget.setItemWidget(item, 1, widget)
                            widget.valueChange.connect(self.onAttrEditChange)

                    self.__attributeItems.append(item)
                    if a not in self.__attributeBaseItems:
                        self.__attributeBaseItems[a] = item

                    i += 1

        self.treeWidget.preferredHeight += self.attributesPreferredHeight

        if self.__attributeItems:
            if self.attrsHeaderItem.isHidden():
                self.attrsHeaderItem.show()
                self.treeWidget.preferredHeight += rowHeight
        elif not self.attrsHeaderItem.isHidden():
            self.attrsHeaderItem.hide()
            self.treeWidget.preferredHeight -= rowHeight

        self.treeWidget.resizeColumnToContents(0)
        self.treeWidget.resizeColumnToContents(1)

    def contextMenuEvent(self, event):
        item = self.treeWidget.currentItem()
        if item is None:
            return QWidget.contextMenuEvent(self, event)

        attrName = item.userData()
        if attrName is None or not attrName or attrName not in self.__attributes:
            return QWidget.contextMenuEvent(self, event)

        attribute = self.__attributes[attrName]
        attrDesc = attribute.attrDesc()
        if not attrDesc.isArray():
            return QWidget.contextMenuEvent(self, event)

        appendAction = AttributeAction(item, 'Append new element', None)
        appendAction.clicked.connect(self.onActionAppend)

        if attribute.value():
            insertAction = AttributeAction(item, 'Insert new element', None)
            insertAction.clicked.connect(self.onActionInsert)
            eraseAction = AttributeAction(item, 'Erase selected', None)
            eraseAction.clicked.connect(self.onActionErase)
        else:
            insertAction = None
            eraseAction = None

        cmenu = QMenu(self)

        #cmenu.addAction(QAction(attrName, cmenu))
        cmenu.addAction(appendAction)
        if insertAction is not None:
            cmenu.addAction(insertAction)
        if eraseAction is not None:
            cmenu.addAction(eraseAction)

        cmenu.exec_(QCursor.pos())

    @QtCore.Slot(QTreeWidgetItem)
    def onActionAppend(self, item):
        attrName = item.userData()
        if attrName is not None and attrName and attrName in self.__attributes:
            attr = self.__attributes[attrName]
            if attr.appendActualValue(None):
                self.refreshAttributesItems()
                self.attributeChanged.emit()

    @QtCore.Slot(QTreeWidgetItem)
    def onActionInsert(self, item):
        attrName = item.userData()
        if attrName is not None and attrName and attrName in self.__attributes:
            attr = self.__attributes[attrName]
            baseIndex = self.treeWidget.indexOfTopLevelItem(self.__attributeBaseItems[attrName])
            currentIndex = self.treeWidget.indexOfTopLevelItem(item)
            i = currentIndex - baseIndex
            if attr.insertActualValueAt(None, i):
                self.refreshAttributesItems()
                self.attributeChanged.emit()

    @QtCore.Slot(QTreeWidgetItem)
    def onActionErase(self, item):
        attrName = item.userData()
        if attrName is not None and attrName and attrName in self.__attributes:
            attr = self.__attributes[attrName]
            baseIndex = self.treeWidget.indexOfTopLevelItem(self.__attributeBaseItems[attrName])
            currentIndex = self.treeWidget.indexOfTopLevelItem(item)
            i = currentIndex - baseIndex
            if attr.setActualValueAt(None, i):
                self.refreshAttributesItems()
                self.attributeChanged.emit()

    @QtCore.Slot(QComboBox, QTreeWidgetItem, int)
    def onAttrComboChange(self, sender, item, col):
        attrName = item.userData()
        if attrName is not None and attrName and attrName in self.__attributes:
            attr = self.__attributes[attrName]
            if attr.isArray():
                if attrName in self.__attributeBaseItems:
                    baseIndex = self.treeWidget.indexOfTopLevelItem(self.__attributeBaseItems[attrName])
                    currentIndex = self.treeWidget.indexOfTopLevelItem(item)
                    i = currentIndex - baseIndex
                    if attr.setActualValueAt(sender.getValue(), i):
                        self.attributeChanged.emit()
            elif attr.setActualValue(sender.getValue()):
                self.attributeChanged.emit()
        else:
            sender.undo()

    @QtCore.Slot(QLineEdit, QTreeWidgetItem, int, str)
    def onAttrEditChange(self, sender, item, col, text):
        attrName = item.userData()
        if attrName is not None and attrName and attrName in self.__attributes:
            text.strip()
            if not text or text in ('-', '+'):
                return
            attr = self.__attributes[attrName]
            if attr.isArray():
                if attrName in self.__attributeBaseItems:
                    baseIndex = self.treeWidget.indexOfTopLevelItem(self.__attributeBaseItems[attrName])
                    currentIndex = self.treeWidget.indexOfTopLevelItem(item)
                    i = currentIndex - baseIndex
                    if attr.setValueAt(text, i):
                        self.attributeChanged.emit()
            elif attr.setValue(text):
                self.attributeChanged.emit()
        else:
            sender.undo()

    @QtCore.Slot()
    def onAttributeChange(self):
        self.isChanged = True
        if self.CommitButton is not None:
            self.CommitButton.setEnabled(True)
        if self.UndoButton is not None:
            self.UndoButton.setEnabled(True)

    @QtCore.Slot(int)
    def onNodeChange(self, index):
        if not self.__updating:
            self.__updating = True

            nodeDesc = None
            text = self.__NodeCombobox.itemText(index)
            if text:
                for lib in self.__proj.libraries:
                    if text in self.__proj.libraries[lib]:
                        nodeDesc = self.__proj.libraries[lib][text]
                        break

            if nodeDesc is not None:
                self.isChanged = True
                self.CommitButton.setEnabled(True)
                self.UndoButton.setEnabled(True)
                self.__nodeComboIndex = index
                self.__nodeDescRef = nodeDesc
                self.__attributes = dict()
                attrDescriptors = self.__nodeDescRef.attributes()
                for a in attrDescriptors:
                    self.__attributes[a] = NodeAttr(a, self.__nodeDescRef.name, self.__nodeDescRef.libname, self.__proj)
                self.refreshAttributesItems()
                hgt = min(self.treeWidget.preferredHeight, self.height() * 0.9)
                self.treeWidget.setHeight(int(hgt))
            else:
                self.__NodeCombobox.setCurrentIndex(self.__nodeComboIndex)

            self.__updating = False

    @QtCore.Slot(int)
    def onDebugModeChange(self, index):
        self.__updating = True

        self.__debugMode = self.__DebugModeCombobox.itemData(index)
        self.__debugComboIndex = index

        self.isChanged = True
        self.CommitButton.setEnabled(True)
        self.UndoButton.setEnabled(True)

        self.__updating = False

    @QtCore.Slot(int)
    def onSingleblockModeChange(self, index):
        if self.__updating:
            return

        self.__updating = True

        self.__singleBlock = self.__SingleblockModeCombobox.itemData(index)
        self.__singleBlockComboIndex = index

        self.isChanged = True
        self.CommitButton.setEnabled(True)
        self.UndoButton.setEnabled(True)

        self.__updating = False

    @QtCore.Slot(int)
    def onInvertModeChange(self, index):
        self.__updating = True

        self.__invertMode = self.__InvertModeCombobox.itemData(index)
        self.__invertComboIndex = index

        self.isChanged = True
        self.CommitButton.setEnabled(True)
        self.UndoButton.setEnabled(True)

        self.__updating = False

    @QtCore.Slot(int)
    def onTypeChange(self, index):
        cls = self.__proj.alphabet.getClass(self.__class)
        if not self.__updating and cls is not None:
            self.__updating = True
            ok = False

            nodeType = self.__TypeCombobox.itemData(index)
            subType = cls.get(nodeType)
            if subType is not None:
                if subType.isLink():
                    ok = True
                    self.isChanged = True
                    self.CommitButton.setEnabled(True)
                    self.UndoButton.setEnabled(True)

                    self.__typeComboIndex = index
                    self.__type = nodeType
                    self.__nodeDescRef = None
                    self.__fillNodeCombobox()

                    self.__attributes = dict()
                    self.refreshAttributesItems()
                    hgt = min(self.treeWidget.preferredHeight, self.height() * 0.9)
                    self.treeWidget.setHeight(int(hgt))

                    self.pathItem.show()
                    self.refItem.show()
                    self.nodeItem.hide()

                    if not self.singleblockItem.isHidden():
                        self.__singleBlock = False
                        self.__validateSingleblockCombobox()
                        self.__SingleblockModeCombobox.hide()
                        self.singleblockItem.hide()
                else:
                    if self.singleblockItem.isHidden():
                        self.__validateSingleblockCombobox()
                        self.singleblockItem.show()
                        self.__SingleblockModeCombobox.show()

                    nodeDesc = self.__getNodeDesc(self.__class, nodeType)
                    if nodeDesc is not None:
                        ok = True
                        self.isChanged = True
                        self.CommitButton.setEnabled(True)
                        self.UndoButton.setEnabled(True)

                        self.__targetPath = ''
                        self.__targetRef = ''
                        self.pathItem.hide()
                        self.refItem.hide()
                        self.nodeItem.show()

                        self.__typeComboIndex = index
                        self.__type = nodeType
                        self.__nodeDescRef = nodeDesc
                        self.__fillNodeCombobox()

                        self.__attributes = dict()
                        attrDescriptors = self.__nodeDescRef.attributes()
                        for a in attrDescriptors:
                            self.__attributes[a] = NodeAttr(a, self.__nodeDescRef.name, self.__nodeDescRef.libname,
                                                            self.__proj)
                        self.refreshAttributesItems()
                        hgt = min(self.treeWidget.preferredHeight, self.height() * 0.9)
                        self.treeWidget.setHeight(int(hgt))
            else:
                if not self.singleblockItem.isHidden():
                    self.__singleBlock = False
                    self.__validateSingleblockCombobox()
                    self.__SingleblockModeCombobox.hide()
                    self.singleblockItem.hide()

            if not ok:
                self.__TypeCombobox.setCurrentIndex(self.__typeComboIndex)

            self.__updating = False

    @QtCore.Slot(int)
    def onReferenceChange(self, index):
        if not self.__updating:
            self.__updating = True

            if index != self.__refComboIndex:
                ref = self.__RefCombobox.itemData(index)
                if ref in self.__proj.trees:
                    self.isChanged = True
                    self.CommitButton.setEnabled(True)
                    self.UndoButton.setEnabled(True)

                    self.__refComboIndex = index
                    self.__targetRef = ref
                else:
                    self.__RefCombobox.setCurrentIndex(self.__refComboIndex)

            self.__updating = False

    @QtCore.Slot(int)
    def onReferencePathChange(self, index):
        if not self.__updating:
            self.__updating = True

            if index != self.__pathComboIndex:
                path = self.__PathCombobox.itemData(index)
                if path in self.__proj.trees.getFilesList(self.__proj.nodes):
                    self.isChanged = True
                    self.CommitButton.setEnabled(True)
                    self.UndoButton.setEnabled(True)

                    self.__pathComboIndex = index
                    self.__targetPath = path
                    self.__fillRefCombobox(path)
                else:
                    self.__PathCombobox.setCurrentIndex(self.__pathComboIndex)

            self.__updating = False

    @QtCore.Slot()
    def undoChanges(self):
        self.__reload()

    @QtCore.Slot()
    def commitChanges(self):
        self.isChanged = False

        if self.__nodeDescRef is not None:
            lib = self.__nodeDescRef.libname
            nodename = self.__nodeDescRef.name
            classname = self.__nodeDescRef.nodeClass
            typename = self.__nodeDescRef.nodeType
        else:
            lib = ''
            nodename = ''
            classname = self.__class
            typename = self.__type

        refreshName = False
        fullRefresh = False
        if self.__targetRef != self.__node.target:
            fullRefresh = True
        elif (self.__node.nodeDesc() is None and self.__nodeDescRef is not None) or \
                (self.__node.nodeDesc() is not None and self.__nodeDescRef is None) or \
                        self.__class != self.__node.nodeClass or self.__type != self.__node.nodeType:
            fullRefresh = True
        elif self.__nodeDescRef is not None:
            if self.__node.nodeClass != self.__nodeDescRef.nodeClass:
                fullRefresh = True
            elif self.__node.nodeName != self.__nodeDescRef.name:
                refreshName = True

        if fullRefresh and self.__invertMode:
            self.__invertMode = False
            self.__InvertModeCombobox.currentIndexChanged.disconnect(self.onInvertModeChange)
            self.__validateInvertCombobox()
            self.__InvertModeCombobox.currentIndexChanged.connect(self.onInvertModeChange)

        globals.historySignals.pushState.emit('Change attributes for node \'{0}\''.format(self.__node.nodeName))

        self.__node.setDebugMode(self.__debugMode)
        self.__node.setSingleblock(self.__singleBlock)
        self.__node.setInverse(self.__invertMode)
        self.__node.target = self.__targetRef
        self.__node.nodeClass = self.__class
        self.__node.nodeType = self.__type
        self.__node.setLibName(lib)
        self.__node.setNodeName(nodename)

        for a in self.__attributes:
            self.__attributes[a].update(self.__attributes)

        self.__node.setAttributes(self.__attributes)
        globals.project.modified = True

        self.updateWidget.emit(self.__proj, self.__node, self.__editMode, True, fullRefresh)

    @QtCore.Slot(str, str, str)
    def __onNodeRename(self, libname, oldname, newname):
        if self.__nodeDescRef is not None and self.__nodeDescRef.libname == libname:
            if self.__nodeDescRef.name == oldname or self.__nodeDescRef.name == newname:
                self.__reload()

    @QtCore.Slot(str, str, str)
    def __onNodeRemove(self, libname, nodename, nodeClass):
        if self.__node is not None and self.__node.libname == libname and self.__node.nodeName == nodename:
            self.__close()

    @QtCore.Slot(str)
    def __onLibraryExclude(self, libname):
        if self.__nodeDescRef is not None and self.__nodeDescRef.libname == libname:
            self.__close()

    @QtCore.Slot(str, str, str, str)
    def __onNodeTypeChangeExternal(self, libname, nodename, typeOld, typeNew):
        if self.__nodeDescRef is not None and self.__nodeDescRef.libname == libname and self.__nodeDescRef.name == nodename:
            self.__reload()

    @QtCore.Slot(str, str, str, str)
    def __onAttributeRename(self, libname, nodename, oldname, newname):
        if self.__nodeDescRef is not None and self.__nodeDescRef.libname == libname and self.__nodeDescRef.name == nodename:
            self.__reload()

    @QtCore.Slot(str, str, str, object)
    def __onAttributeChange(self, libname, nodename, attributeName, attributeOldDescriptor):
        if self.__nodeDescRef is not None and self.__nodeDescRef.libname == libname and self.__nodeDescRef.name == nodename:
            self.__reload()

    @QtCore.Slot(str, str, str)
    def __onAttributeAddDelete(self, libname, nodename, attributeName):
        if self.__nodeDescRef is not None and self.__nodeDescRef.libname == libname and self.__nodeDescRef.name == nodename:
            self.__reload()

    def __validateDebugCombobox(self):
        i = self.__DebugModeCombobox.findData(self.__debugMode)
        if i < 0:
            i = 1
        self.__DebugModeCombobox.setCurrentIndex(i)
        self.__debugComboIndex = self.__DebugModeCombobox.currentIndex()

    def __validateSingleblockCombobox(self):
        i = self.__SingleblockModeCombobox.findData(self.__singleBlock)
        if i < 0:
            i = 1
        self.__SingleblockModeCombobox.setCurrentIndex(i)
        self.__singleBlockComboIndex = self.__SingleblockModeCombobox.currentIndex()

    def __fillDebugCombobox(self):
        self.__DebugModeCombobox.clear()
        self.__DebugModeCombobox.addItem('True', True)
        self.__DebugModeCombobox.addItem('False', False)
        self.__validateDebugCombobox()

    def __fillSingleblockCombobox(self):
        self.__SingleblockModeCombobox.clear()
        self.__SingleblockModeCombobox.addItem('True', True)
        self.__SingleblockModeCombobox.addItem('False', False)
        self.__validateSingleblockCombobox()

    def __validateInvertCombobox(self):
        i = self.__InvertModeCombobox.findData(self.__invertMode)
        if i < 0:
            i = 1
        self.__InvertModeCombobox.setCurrentIndex(i)
        self.__invertComboIndex = self.__InvertModeCombobox.currentIndex()

    def __fillInvertCombobox(self):
        self.__InvertModeCombobox.clear()
        self.__InvertModeCombobox.addItem('True', True)
        self.__InvertModeCombobox.addItem('False', False)
        self.__validateInvertCombobox()

    def __fillTypeCombobox(self):
        self.__TypeCombobox.clear()
        self.__TypeCombobox.addItem('<select type>', '')

        i = 0
        cls = self.__proj.alphabet.getClass(self.__class)
        if cls is not None:
            links = []
            for t in cls.types:
                subType = cls.types[t]
                if subType.isLink():
                    #self.__TypeCombobox.addItem(subType.name,subType.name)
                    links.append([subType.name, subType.name])
                else:
                    self.__TypeCombobox.addItem('{0} {1}'.format(subType.name, cls.name), subType.name)
            for l in links:
                self.__TypeCombobox.addItem(l[0], l[1])
            i = self.__TypeCombobox.findData(self.__type)
            if i < 0:
                i = 0

        self.__TypeCombobox.setCurrentIndex(i)
        self.__typeComboIndex = self.__TypeCombobox.currentIndex()

    def __fillNodeCombobox(self):
        self.__NodeCombobox.clear()
        self.__NodeCombobox.addItem('<select node>', '')
        k = 0
        if self.__nodeDescRef is not None:
            for libname in self.__proj.libraries:
                lib = self.__proj.libraries[libname]
                nodes = lib.getAll(self.__class, self.__type)
                for n in nodes:
                    self.__NodeCombobox.addItem(n)
                    k += 1
                    if nodes[n].description:
                        self.__NodeCombobox.setItemData(k, nodes[n].description, Qt.ToolTipRole)
            self.__NodeCombobox.model().sort(0)

        i = 0
        if self.__nodeDescRef is not None:
            i = self.__NodeCombobox.findText(self.__nodeDescRef.name)
            if i < 0:
                i = 0

        self.__NodeCombobox.setCurrentIndex(i)
        self.__nodeComboIndex = self.__NodeCombobox.currentIndex()

    def __fillRefCombobox(self, path):
        if self.__refConnected:
            self.__RefCombobox.currentIndexChanged.disconnect()
            self.__refConnected = False

        self.__RefCombobox.clear()
        self.__RefCombobox.addItem('<select branch>', '')
        k = 0
        treesByPath = self.__proj.trees.getBranchesByFile(path, self.__proj.nodes)
        for branchname in treesByPath:
            k += 1
            branch = treesByPath[branchname]
            self.__RefCombobox.addItem(branch.refname(), branchname)
            self.__RefCombobox.setItemData(k, branchname, Qt.ToolTipRole)
        self.__RefCombobox.model().sort(0)
        i = self.__RefCombobox.findData(self.__targetRef)
        if i < 0:
            i = 0
        self.__RefCombobox.setCurrentIndex(i)
        self.__refComboIndex = self.__RefCombobox.currentIndex()

        self.__RefCombobox.currentIndexChanged.connect(self.onReferenceChange)
        self.__refConnected = True

    def __getNodeDesc(self, nodeClass, nodeType):
        nodeDesc = None
        for libname in self.__proj.libraries:
            lib = self.__proj.libraries[libname]

            nodes = lib.getAll(nodeClass, nodeType)
            for n in nodes:
                nodeDesc = nodes[n]
                break

            if nodeDesc is not None:
                break
        return nodeDesc

#######################################################################################################################
#######################################################################################################################


class TaskDock(trDockWidget):
    updateView = QtCore.Signal(bool)

    def __init__(self, title, parent=None):
        trDockWidget.__init__(self, title, parent)
        self.Stack = QStackedWidget()
        self.Stack.addWidget(QListWidget())
        self.Stack.setCurrentIndex(0)
        self.widgets = []
        self.setWidget(self.Stack)
        self.__timer = QTimer(self)
        self.__timer.setSingleShot(True)
        self.__timer.timeout.connect(self.__onTimeout)
        self.__replaceData = None

    def clear(self):
        self.Stack.setCurrentIndex(0)
        for widget in self.widgets:
            self.Stack.removeWidget(widget)
        self.widgets = []

    def currentIndex(self):
        return self.Stack.currentIndex() - 1

    def setCurrent(self, index):
        if index < len(self.widgets):
            self.Stack.setCurrentIndex(index + 1)

    def addEmptyWidget(self):
        self.addWidget()

    def addWidget(self, proj=None, treenode=None, editMode=False):
        if treenode is not None and proj is not None:
            newWidget = TaskInfoWidget(proj, treenode, editMode)
            newWidget.updateWidget.connect(self.replaceCurrentWidgetDelayed)
        else:
            newWidget = QListWidget()
        self.widgets.append(newWidget)
        self.Stack.addWidget(newWidget)

    def replaceCurrentWidgetDelayed(self, proj=None, treenode=None, editMode=False, updateView=False, full=False):
        self.__replaceData = (proj, treenode, editMode, updateView, full)
        self.__timer.start(5)

    @QtCore.Slot()
    def __onTimeout(self):
        if self.__replaceData is not None:
            proj, treenode, editMode, updateView, full = self.__replaceData
            self.__replaceData = None
            self.replaceCurrentWidget(proj, treenode, editMode)
            if updateView:
                self.updateView.emit(full)

    def replaceCurrentWidget(self, proj=None, treenode=None, editMode=False):
        currIndex = self.Stack.currentIndex()
        index = currIndex - 1
        if index >= 0:
            oldWidget = self.widgets[index]
            if treenode is not None and proj is not None:
                newWidget = TaskInfoWidget(proj, treenode, editMode)
                newWidget.updateWidget.connect(self.replaceCurrentWidgetDelayed)
            else:
                # чтобы не изменился порядок виджетов (их индексы), виджет не удаляется, а заменяется пустышкой
                newWidget = QListWidget()
            self.widgets[index] = newWidget
            self.Stack.insertWidget(currIndex, newWidget)
            self.Stack.setCurrentIndex(currIndex)
            self.Stack.removeWidget(oldWidget)

    @QtCore.Slot(int)
    def removeWidget(self, index):
        if index < len(self.widgets):
            self.Stack.removeWidget(self.widgets[index])
            self.widgets.pop(index)

#######################################################################################################################
#######################################################################################################################

