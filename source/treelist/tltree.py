# coding=utf-8
# -----------------
# file      : tltree.py
# date      : 2012/11/03
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
from PySide.QtGui import *
from PySide.QtCore import *

from . import tlitem
from . import tldialog

from language import globalLanguage, Language, trStr

from extensions.widgets import trDockWidget, scrollProxy, trMenuWithTooltip

from treenode import Uid

from auxtypes import joinPath

import globals

########################################################################################################################
########################################################################################################################


# Tree widget containing all loaded libraries
class TL_Tree(QTreeWidget):

    # Constructor
    # parent - QWidget
    def __init__(self, *args, **kwargs):
        QTreeWidget.__init__(self, *args, **kwargs)
        self._focusProxy = scrollProxy(self)

        self.setHeaderLabel('Behavior Trees')
        self.setAlternatingRowColors(True)
        self.setAnimated(True)
        self.header().close()

        self.highlighted = []
        self.mb = None
        self.__grab = False
        self.__grabFullRefname = ''
        self.__grabSentSignal = False
        self.__project = None
        self.__treesWidgets = dict()

        self.editingItem = None
        self.editingText = ''

        self.itemDoubleClicked.connect(self.__onDoubleClick)
        self.itemChanged.connect(self.onItemChange)
        self.currentItemChanged.connect(self.__onCurrentChanged)

        self._icons = {
            'copy': QIcon(joinPath(globals.applicationIconsPath, 'copy3.png')),
            'edit': QIcon(joinPath(globals.applicationIconsPath, 'page_edit.png')),
            'cancel': QIcon(joinPath(globals.applicationIconsPath, 'cancel-1.png')),
            'add': QIcon(joinPath(globals.applicationIconsPath, 'chart_add.png')),
            'add2': QIcon(joinPath(globals.applicationIconsPath, 'chart_add2.png'))
        }

        globals.behaviorTreeSignals.treeOpened.connect(self.__onTreeOpen)
        globals.behaviorTreeSignals.treeClosed.connect(self.__onTreeClose)
        globals.behaviorTreeSignals.treeRootChanged.connect(self.__onTreeRootChange)

    def setSource(self, proj):
        if self.mb is not None:
            self.mb.reject()
            self.mb = None
        self.__project = proj
        if self.__project is not None:
            for filename in self.__project.tree_paths:  # trees.getFilesList():
                self.__treesWidgets[filename] = tlitem.TL_TreeFileItem(self.__project, filename, self)
                self.addTopLevelItem(self.__treesWidgets[filename])

    def clearTrees(self):
        if self.mb is not None:
            self.mb.reject()
            self.mb = None

        trees = []
        for tree in self.__treesWidgets:
            trees.append(tree)

        for tree in trees:
            row = self.indexOfTopLevelItem(self.__treesWidgets[tree])
            data = self.model()
            data.removeRow(row)
            del self.__treesWidgets[tree]
            # if self.__trees is not None:
            #     self.removed.emit()

    def removeTree(self, treename):
        dependents = self.__project.trees.whoDependsOn(treename, self.__project.nodes)
        if dependents:
            strings = treename.split('/')
            shortname = strings[-1]
            lenDep = len(dependents)

            text = 'Following <b>{0}</b> branches:'.format(lenDep)
            if globalLanguage.language == Language.Russian:
                brtxt = 'ветвей'
                nexttxt = 'Следующие'
                if lenDep == 1:
                    nexttxt = ''
                    brtxt = 'ветвь'
                elif 1 < lenDep < 5:
                    brtxt = 'ветви'
                text = '{0} <b>{1}</b> {2}:'.format(nexttxt, lenDep, brtxt)
            for d in dependents:
                strings = d.split('/')
                text += '<br/>- \"<i><font color=\"red\">{0}</font></i>\",'.format(strings[-1])
            text = text.rstrip(',')

            title = ''
            if globalLanguage.language == Language.English:
                text += '<br/>refers to \"<b>{0}</b>\".'.format(shortname)
                text += '<br/>Remove all dependencies first!'
                title = 'Remove error!'
            elif globalLanguage.language == Language.Russian:
                reftxt = 'ссылаются'
                if lenDep == 1:
                    reftxt = 'ссылается'
                text += '<br/>{0} на \"<b>{1}</b>\".'.format(reftxt, shortname)
                text += '<br/>Сначала нужно убрать все зависимости!'
                title = 'Ошибка при удалении!'

            items = []
            if lenDep > 0:
                num = self.topLevelItemCount()
                for i in range(num):
                    isSet = False
                    topItem = self.topLevelItem(i)
                    numChildren = topItem.childCount()
                    for j in range(numChildren):
                        item = topItem.child(j)
                        for d in dependents:
                            if item.node is not None and item.node.fullRefName() == d:
                                item.setColor(Qt.red)
                                items.append(item)
                                isSet = True
                                break
                    if isSet:
                        topItem.setColor(Qt.darkRed)
                        items.append(topItem)

            QMessageBox.critical(self, title, text)

            for item in items:
                item.resetColor()
        else:
            branch_uid = self.__project.trees.get(treename)
            if branch_uid is not None and branch_uid in self.__project.nodes:
                branch = self.__project.nodes[branch_uid]
                topItem = self.__treesWidgets.get(branch.path())
                if topItem is not None:
                    numChildren = topItem.childCount()
                    for j in range(numChildren):
                        item = topItem.child(j)
                        if item.node.fullRefName() == branch.fullRefName():
                            topItem.removeChild(item)
                            break
                self.__project.trees.remove(treename)
                self.__project.nodes.remove(branch, recursive=True)

    def setTempTree(self, tree):
        self.__tempTree = tree

    # Create context menu on RigthButton click
    def contextMenuEvent(self, event):
        cmenu = trMenuWithTooltip('', self)

        actions = []

        action = QAction(trStr('Open existing tree file...', 'Открыть файл с деревом...').text(), None)
        action.setToolTip(trStr('Open existing tree file and\ninclude it into project',
                                'Открыть существующий файл с деревом\nи добавить его в проект').text())
        action.setIcon(QIcon(self._icons['add2']))
        action.triggered.connect(globals.treeListSignals.openExistingTreeFile)
        cmenu.addAction(action)
        actions.append(action)

        action = QAction(trStr('Create new tree file...', 'Создать файл с деревом...').text(), None)
        action.setToolTip(trStr('Create new tree file and\ninclude it into project',
                                'Создать новый файл с деревом\nи добавить его в проект').text())
        action.setIcon(QIcon(self._icons['add']))
        action.triggered.connect(globals.treeListSignals.createNewTreeFile)
        cmenu.addAction(action)
        actions.append(action)

        cmenu.addSeparator()

        if self.topLevelItemCount() > 0:
            currItem = self.currentItem()
            if currItem is not None:
                action = QAction(trStr('Create', 'Создать').text(), None)
                action.setToolTip(trStr('Create new tree in selected tree file',
                                        'Создать новое дерево в выбранном файле').text())
                action.setIcon(QIcon(self._icons['add2']))
                action.triggered.connect(self.__onCreateClicked)
                cmenu.addAction(action)
                actions.append(action)

                if self.indexOfTopLevelItem(currItem) < 0:
                    action = QAction(trStr('Copy', 'Копировать').text(), None)
                    action.setToolTip(trStr('Create a full copy of selected tree',
                                            'Создать полную копию выбранного дерева').text())
                    action.setIcon(QIcon(self._icons['copy']))
                    action.triggered.connect(self.__onCreateCopyClicked)
                    cmenu.addAction(action)
                    actions.append(action)

                    cmenu.addSeparator()

                    action = QAction(trStr('Rename', 'Переименовать').text(), None)
                    action.setToolTip(trStr('Rename selected tree', 'Переименовать выбранное дерево').text())
                    action.setIcon(QIcon(self._icons['edit']))
                    action.triggered.connect(self.__onRenameClicked)
                    cmenu.addAction(action)
                    actions.append(action)

                    action = QAction(trStr('Delete', 'Удалить').text(), None)
                    action.setToolTip(
                        trStr('Permanently delete selected tree and remove all links to it in all other trees',
                              'Удалить выбранное дерево и убрать все ссылки на него в других деревьях').text()
                    )
                    action.setIcon(QIcon(self._icons['cancel']))
                    action.triggered.connect(self.__onDeleteClicked)
                    cmenu.addAction(action)
                    actions.append(action)

                    cmenu.addSeparator()

                    action = QAction(trStr('Show usages', 'Показать где используется').text(), None)
                    action.setToolTip(trStr('Show other trees which uses the selected tree',
                                            'Показать деревья, в которых задействовано выбранное дерево').text())
                    action.triggered.connect(self.__onShowWhoDependsOnClicked)
                    cmenu.addAction(action)
                    actions.append(action)

                    action = QAction(trStr('Show dependence from', 'Показать от кого зависит').text(), None)
                    action.setToolTip(trStr('Show trees that are used inside the selected tree',
                                            'Показать деревья, которые используются внутри выбранного дерева').text())
                    action.triggered.connect(self.__onShowDependenciesClicked)
                    cmenu.addAction(action)
                    actions.append(action)

        cmenu.exec_(QCursor.pos())

    # "Create new tree" click handler
    @QtCore.Slot()
    def __onCreateClicked(self):
        currItem = self.currentItem()
        if currItem is not None:
            filename = currItem.path
        elif self.enteredItem is not None:
            filename = self.enteredItem.path
        else:
            filename = ''

        if filename and filename in self.__treesWidgets:
            treeDialog = tldialog.TL_CreateDialog(self.__project, filename, self)
            if treeDialog.exec_() == QDialog.Accepted:
                if self.__tempTree is not None:
                    item = self.__treesWidgets[filename]
                    if self.__project.trees.add(branch=self.__tempTree):
                        self.__project.nodes.add(self.__tempTree)
                        item.addChild(tlitem.TL_TaskItem(self.__tempTree, item))
            self.__tempTree = None

    # "Create copy of selected tree" click handler
    @QtCore.Slot()
    def __onCreateCopyClicked(self):
        currItem = self.currentItem()
        if currItem is None or self.indexOfTopLevelItem(currItem) >= 0 or currItem.node is None:
            return

        filename = currItem.path
        if filename and filename in self.__treesWidgets:
            treeDialog = tldialog.TL_CreateDialog(self.__project, filename, self)
            if treeDialog.exec_() == QDialog.Accepted:
                if self.__tempTree is not None:
                    newTree = currItem.node.deepcopy(False)
                    newTree.setRefName(self.__tempTree.refname())
                    item = self.__treesWidgets[filename]
                    if self.__project.trees.add(branch=newTree):
                        self.__project.nodes.add(newTree, recursive=True)
                        item.addChild(tlitem.TL_TaskItem(newTree, item))
                    del self.__tempTree
            self.__tempTree = None

    # "Delete selected tree" click handler
    @QtCore.Slot()
    def __onDeleteClicked(self):
        currItem = self.currentItem()
        if currItem is not None:
            self.removeTree(currItem.node.fullRefName())

    @QtCore.Slot()
    def __onRenameClicked(self):
        currItem = self.currentItem()
        if currItem is not None:
            self.editingItem = currItem
            self.editingText = currItem.text(0)
            self.openPersistentEditor(currItem)

    @QtCore.Slot(str, str)
    def __onTreeOpen(self, path, name):
        topItem = self.__treesWidgets.get(path)
        if topItem is not None:
            numChildren = topItem.childCount()
            for j in range(numChildren):
                item = topItem.child(j)
                if item.node.refname() == name:
                    item.enter()
                    break

    @QtCore.Slot(str, str)
    def __onTreeClose(self, path, name):
        topItem = self.__treesWidgets.get(path)
        if topItem is not None:
            numChildren = topItem.childCount()
            for j in range(numChildren):
                item = topItem.child(j)
                if item.node.refname() == name:
                    item.leave()
                    break

    @QtCore.Slot(str, str, Uid, Uid)
    def __onTreeRootChange(self, path, name, oldRootUid, newRootUid):
        topItem = self.__treesWidgets.get(path)
        if topItem is not None:
            newRoot = globals.project.nodes.get(newRootUid.value)
            if newRoot is not None:
                numChildren = topItem.childCount()
                for j in range(numChildren):
                    item = topItem.child(j)
                    if item.node.uid() == oldRootUid.value:
                        item.node = newRoot
                        break

    @QtCore.Slot(QTreeWidgetItem, QTreeWidgetItem)
    def __onCurrentChanged(self, current, previous):
        pass
        # if previous is not None:
        # 	previous.leave()
        # if current is not None:
        # 	current.enter()

    @QtCore.Slot(QTreeWidgetItem)
    def onItemChange(self, item):
        if self.editingItem is not None and item is self.editingItem:
            self.closePersistentEditor(self.editingItem)
            text = self.editingItem.text(0)
            text = text.replace(' ', '')
            revert = False

            fullname = '{0}/{1}'.format(self.editingItem.path, text)
            if text != self.editingText:
                if not text or fullname in self.__project.trees:
                    revert = True

            if not revert:
                oldname = '{0}/{1}'.format(self.editingItem.path, self.editingText)
                if self.__project.trees.rename(oldname, fullname):
                    fileItem = self.editingItem.parent()
                    if fileItem is not None:
                        fileItem.sortChildren(0, Qt.AscendingOrder)
                    uid = self.__project.trees.get(fullname)
                    if uid in self.__project.nodes:
                        self.editingItem.node = self.__project.nodes[uid]
                    else:
                        revert = True
                else:
                    revert = True

            if revert:
                self.editingItem.setText(0, self.editingText)
                title = trStr('Rename error!', 'Ошибка при изменении имени!').text()
                message = trStr('Branch with name \"<b>{0}</b>\"<br/>is already exist!'.format(text), \
                                'Ветвь с именем \"<b>{0}</b>\"<br/>уже существует!'.format(text)).text()
                QMessageBox.critical(self, title, message)

            self.editingItem = None

    #
    def __onShowWhoDependsOnClicked(self):
        if self.mb is not None:
            self.mb.reject()
            self.mb = None

        item = self.currentItem()
        if self.indexOfTopLevelItem(item) < 0:
            treename = item.node.fullRefName()
            strings = treename.split('/')
            shortname = strings[-1]
            dependents = self.__project.trees.whoDependsOn(treename, self.__project.nodes)
            lenDep = len(dependents)

            if lenDep > 0:
                text = 'Following <b>{0}</b> branches:'.format(len(dependents))
                if globalLanguage.language == Language.Russian:
                    brtxt = 'ветвей'
                    nexttxt = 'Следующие'
                    if lenDep == 1:
                        nexttxt = ''
                        brtxt = 'ветвь'
                    elif 1 < lenDep < 5:
                        brtxt = 'ветви'
                    text = '{0} <b>{1}</b> {2}:'.format(nexttxt, lenDep, brtxt)
                for d in dependents:
                    strings = d.split('/')
                    text += '<br/>- \"<i><font color=\"red\">{0}</font></i>\",'.format(strings[-1])
                text = text.rstrip(',')
            else:
                text = '<b>No</b> branches'
                if globalLanguage.language == Language.Russian:
                    text = '<b>0</b> ветвей'

            title = ''
            if globalLanguage.language == Language.English:
                text += '<br/>depends on \"<b>{0}</b>\".'.format(shortname)
                title = 'List of dependents'
            elif globalLanguage.language == Language.Russian:
                reftxt = 'ссылаются'
                if lenDep == 1:
                    reftxt = 'ссылается'
                text += '<br/>{0} на \"<b>{1}</b>\".'.format(reftxt, shortname)
                title = 'Список зависимых деревьев'

            item.setColor(Qt.yellow)
            item.setBold(True)

            items = [item]
            if lenDep > 0:
                num = self.topLevelItemCount()
                for i in range(num):
                    isSet = False
                    topItem = self.topLevelItem(i)
                    numChildren = topItem.childCount()
                    for j in range(numChildren):
                        item = topItem.child(j)
                        for d in dependents:
                            if item.node is not None and item.node.fullRefName() == d:
                                item.setColor(Qt.red)
                                item.setBold(True)
                                items.append(item)
                                isSet = True
                                break
                    if isSet:
                        topItem.setColor(Qt.blue)
                        topItem.setBold(True)
                        items.append(topItem)

            self.highlighted = items
            self.mb = QMessageBox(QMessageBox.Information, title, text, QMessageBox.Ok, self)
            self.mb.setModal(False)
            self.mb.finished.connect(self.onMBClose)
            self.mb.show()

    def __onShowDependenciesClicked(self):
        if self.mb is not None:
            self.mb.reject()
            self.mb = None

        item = self.currentItem()
        if self.indexOfTopLevelItem(item) < 0:
            treename = item.node.fullRefName()
            strings = treename.split('/')
            shortname = strings[-1]
            dependsOn = self.__project.trees.getDependantsOf(treename, self.__project.nodes)
            lenDep = len(dependsOn)

            text = 'Branch \"<b>{0}</b>\"<br/>depends on <b>{1}</b> other branches'.format(shortname, lenDep)
            if globalLanguage.language == Language.Russian:
                brtxt = 'ветвей'
                if lenDep == 1:
                    brtxt = 'ветвь'
                elif 1 < lenDep < 5:
                    brtxt = 'ветви'
                text = 'Ветвь \"<b>{0}</b>\"<br/>ссылается на <b>{1}</b> {2}'.format(shortname, lenDep, brtxt)

            if lenDep > 0:
                text += ':'
                for d in dependsOn:
                    strings = d.split('/')
                    text += '<br/>- \"<i><font color=\"YellowGreen\">{0}</font></i>\",'.format(strings[-1])
                text = text.rstrip(',')
            text += '.'

            title = 'Dependencies list'
            if globalLanguage.language == Language.Russian:
                title = 'Список зависимостей'

            item.setColor(Qt.yellow)
            item.setBold(True)

            items = [item]
            if lenDep > 0:
                num = self.topLevelItemCount()
                for i in range(num):
                    isSet = False
                    topItem = self.topLevelItem(i)
                    numChildren = topItem.childCount()
                    for j in range(numChildren):
                        item = topItem.child(j)
                        for d in dependsOn:
                            if item.node is not None and item.node.fullRefName() == d:
                                item.setColor(Qt.darkGreen)
                                item.setBold(True)
                                items.append(item)
                                isSet = True
                                break
                    if isSet:
                        topItem.setColor(Qt.blue)
                        topItem.setBold(True)
                        items.append(topItem)

            self.highlighted = items
            self.mb = QMessageBox(QMessageBox.Information, title, text, QMessageBox.Ok, self)
            self.mb.setModal(False)
            self.mb.finished.connect(self.onMBClose)
            self.mb.show()

    @QtCore.Slot(int)
    def onMBClose(self, result):
        for item in self.highlighted:
            item.resetColor()
            item.setBold(False)
        del self.highlighted[:]
        self.mb.finished.disconnect(self.onMBClose)
        self.mb = None

    def expandedItems(self):
        explist = []
        for i in range(self.topLevelItemCount()):
            item = self.topLevelItem(i)
            if item.isExpanded():
                explist.append(item.path)
        return explist

    def expandItems(self, filenames):
        for f in filenames:
            if f in self.__treesWidgets:
                self.expandItem(self.__treesWidgets[f])

    def __onDoubleClick(self, item, col):
        if self.indexOfTopLevelItem(item) < 0:
            if item.node.refname():
                globals.treeListSignals.doubleClicked.emit(item.node.fullRefName())

    def mousePressEvent(self, event):
        pressedItem = self.itemAt(event.pos())
        if pressedItem is not None and self.indexOfTopLevelItem(pressedItem) < 0:
            self.__grabSentSignal = False
            self.__grabFullRefname = pressedItem.node.fullRefName()
            self.__grab = True
        #globals.treeListSignals.branchGrabbed.emit(pressedItem.node.fullRefName())
        QTreeView.mousePressEvent(self, event)

    def mouseReleaseEvent(self, event):
        if self.__grab:
            self.__grab = False
            self.__grabFullRefname = ''
            if self.__grabSentSignal:
                self.__grabSentSignal = False
                globals.treeListSignals.branchReleased.emit(event.globalX(), event.globalY())
        QTreeView.mouseReleaseEvent(self, event)

    def mouseMoveEvent(self, event):
        if self.__grab:
            if not self.__grabSentSignal:
                globalPos = QPoint(event.globalX(), event.globalY())
                localPos = self.mapFromGlobal(globalPos)
                if not self.rect().contains(localPos):
                    self.__grabSentSignal = True
                    globals.treeListSignals.branchGrabbed.emit(self.__grabFullRefname)
            if self.__grabSentSignal:
                globals.treeListSignals.branchMove.emit(event.globalX(), event.globalY())
        QTreeView.mouseMoveEvent(self, event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Enter or event.key() == Qt.Key_Return:
            item = self.currentItem()
            if item is not self.editingItem:
                self.__onDoubleClick(item, 1)
        QTreeView.keyPressEvent(self, event)

########################################################################################################################
########################################################################################################################


# Dock widget containing loaded or created behavior trees
class TL_TreeDock(trDockWidget):
    def __init__(self, title, parent=None):
        trDockWidget.__init__(self, title, parent)
        self.__project = None
        self.tree = TL_Tree(self)
        self.setWidget(self.tree)

    def setProject(self, proj):
        if self.__project is not None:
            globals.historySignals.undoMade.disconnect(self.updateView)
            globals.historySignals.redoMade.disconnect(self.updateView)
        self.__project = proj
        self.updateView()
        if self.__project is not None:
            globals.historySignals.undoMade.connect(self.updateView)
            globals.historySignals.redoMade.connect(self.updateView)

    @QtCore.Slot()
    def updateView(self):
        expandedItems = self.tree.expandedItems()
        self.tree.setSource(None)
        self.tree.clearTrees()
        self.tree.setSource(self.__project)
        self.tree.expandItems(expandedItems)

########################################################################################################################
########################################################################################################################

