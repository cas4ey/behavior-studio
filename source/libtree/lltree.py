# coding=utf-8
# -----------------
# file      : lltree.py
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

from . import llitem
from . import lldialog
from pattern_generator.tree_node_pattern_gen import PatternGeneratorDialog

from language import globalLanguage, Language, trStr

from extensions.widgets import trDockWidget, trMenuWithTooltip, scrollProxy

from auxtypes import joinPath

import globals

##############################################################
##############################################################


class _InvisibleAction(QAction):
    def __init__(self, *args, **kwargs):
        QAction.__init__(self, *args, **kwargs)
        self.setEnabled(False)
        self.setVisible(False)

##############################################################
##############################################################


# Tree widget containing all loaded libraries
class LL_Tree(QTreeWidget):
    # removed = QtCore.Signal(str)

    def __init__(self, *args, **kwargs):
        """ Constructor
        mode - ...
        parent - QWidget
        """

        QTreeWidget.__init__(self, *args, **kwargs)
        self._focusProxy = scrollProxy(self)
        globalLanguage.languageChanged.connect(self.__onLanguageChange)

        self.setAlternatingRowColors(True)
        self.setAnimated(True)
        # self.itemExpanded.connect(self.onItemExpanded)

        self.__externalSelect = False
        self.__libraries = None
        self.__alphabet = None
        self.__libWidgets = dict()
        self.__tempLib = None
        self.__changed = False
        self.__cleaning = False
        self.__grab = False
        self.__grabbedItemLibrary = ''
        self.__grabbedItemNodename = ''
        self.__grabSentSignal = False

        self._editingItem = None
        self._editingText = ''
        self._editingInternal = False

        self.headers = ['Nodes']  # ['Available nodes','Path']
        self.setHeaderLabels(self.headers)
        self.header().close()

        self.__onLanguageChange(globalLanguage.language)

        # self.itemSelectionChanged.connect(self.__onSelectionChanged)
        self.itemChanged.connect(self.__onItemChange)
        self.currentItemChanged.connect(self.__onCurrentChanged)

        self._icons = {
            'delete': QIcon(joinPath(globals.applicationIconsPath, 'cancel-1.png')),
            'add': QIcon(joinPath(globals.applicationIconsPath, 'add-3.png')),
            'copy': QIcon(joinPath(globals.applicationIconsPath, 'copy3.png')),
            'paste': QIcon(joinPath(globals.applicationIconsPath, 'paste3.png')),
            'binary': QIcon(joinPath(globals.applicationIconsPath, 'binary-1.png')),
            'book': QIcon(joinPath(globals.applicationIconsPath, 'book_open.png')),
            'book_del': QIcon(joinPath(globals.applicationIconsPath, 'book_delete.png')),
            'book_add': QIcon(joinPath(globals.applicationIconsPath, 'book_add.png')),
            'book_edit': QIcon(joinPath(globals.applicationIconsPath, 'book_edit.png'))
        }

        globals.librarySignals.nodeAdded.connect(self.__onNodeAdd)
        globals.librarySignals.libraryExcluded.connect(self.__removeLib)
        globals.librarySignals.nodeRemoved.connect(self.__onNodeRemove)
        globals.librarySignals.libraryRenamed.connect(self.__onLibraryRename)

    def setSource(self, libraries, alphabet):
        self.__libraries = libraries
        self.__alphabet = alphabet
        if self.__libraries is not None and self.__alphabet is not None:
            for lib in self.__libraries:
                self.__addLib(self.__libraries[lib])

    def onChildInit(self, columns):
        while len(self.headers) < columns:
            self.headers.append('')
        self.setHeaderLabels(self.headers)

    def __addLib(self, lib):
        """ Adds new lib
        lib - class treenode.NodeLibrary
        """
        if lib.libname not in self.__libWidgets:
            self.__libWidgets[lib.libname] = llitem.LL_TreeTopLevelItem(lib, self)
            self.addTopLevelItem(self.__libWidgets[lib.libname])
            self.sortItems(0, Qt.AscendingOrder)
            return True
        return False

    @QtCore.Slot(str)
    def __removeLib(self, libname):
        """ Remove lib with name "libname"
        libname - string
        """
        if libname in self.__libWidgets:
            row = self.indexOfTopLevelItem(self.__libWidgets[libname])
            data = self.model()
            self.__libWidgets[libname].flush(data)
            data.removeRow(row)
            del self.__libWidgets[libname]
            return True
        return False

    # Create context menu on RigthButton click
    def contextMenuEvent(self, *args, **kwargs):
        menu = trMenuWithTooltip('', self)

        actions = {}

        action = QAction(trStr('Expand all', 'Раскрыть все').text(), None)
        action.setToolTip(trStr('Expand all items in list', 'Раскрыть все элементы списка').text())
        action.triggered.connect(self.expandAll)
        menu.addAction(action)
        actions['expand all'] = action

        action = QAction(trStr('Collapse all', 'Свернуть все').text(), None)
        action.setToolTip(trStr('Collapse all items in list', 'Свернуть все элементы списка').text())
        action.triggered.connect(self.collapseAll)
        menu.addAction(action)
        actions['collapse all'] = action

        if self.topLevelItemCount() == 0:
            actions['expand all'].setEnabled(False)
            actions['collapse all'].setEnabled(False)

        action = _InvisibleAction(trStr('Expand', 'Раскрыть').text(), None)
        action.setToolTip(trStr('Expand current item', 'Раскрыть текущий элемент списка').text())
        action.triggered.connect(self.__onExpandClicked)
        menu.addAction(action)
        actions['expand'] = action

        action = _InvisibleAction(trStr('Collapse', 'Свернуть').text(), None)
        action.setToolTip(trStr('Collapse current item', 'Свернуть текущий элемент списка').text())
        action.triggered.connect(self.__onCollapseClicked)
        menu.addAction(action)
        actions['collapse'] = action

        menu.addSeparator()

        action = QAction(QIcon(self._icons['book_add']),
                         trStr('Load library...', 'Загрузить библиотеку...').text(), None)
        action.setToolTip(trStr('Open existing library and\nadd it into current project',
                                'Открыть существующую библиотеку узлов\nи включить ее в текущий проект').text())
        action.triggered.connect(globals.nodeListSignals.openExistingLibraryFile)
        menu.addAction(action)
        actions['add lib'] = action

        action = QAction(QIcon(self._icons['book_add']),
                         trStr('Create library...', 'Создать библиотеку...').text(), None)
        action.setToolTip(trStr('Create new library and\nadd it into current project',
                                'Создать новую библиотеку узлов\nи включить ее в текущий проект').text())
        action.triggered.connect(globals.nodeListSignals.createNewLibraryFile)
        menu.addAction(action)
        actions['create lib'] = action

        action = _InvisibleAction(QIcon(self._icons['book_edit']),
                                  trStr('Rename library', 'Переименовать библиотеку').text(), None)
        action.setToolTip(trStr('Rename current library', 'Переименовать текущую библиотеку').text())
        action.triggered.connect(self.__onRenameLibraryClicked)
        menu.addAction(action)
        actions['rename library'] = action

        action = _InvisibleAction(QIcon(self._icons['book_del']),
                                  trStr('Unload library', 'Выгрузить библиотеку').text(), None)
        action.setToolTip(trStr('Unload current library from project',
                                'Выгрузить текущую библиотеку из проекта').text())
        action.triggered.connect(self.__onUnloadClicked)
        menu.addAction(action)
        actions['exclude library'] = action

        menu.addSeparator()

        action = _InvisibleAction(QIcon(self._icons['binary']), trStr('Generate code', 'Генерировать код').text(), None)
        action.setToolTip(trStr('Generate c++ code for current node', 'Генерировать код c++ для текущего узла').text())
        action.triggered.connect(self.__onGenerateCodeClicked)
        menu.addAction(action)
        actions['generate code'] = action

        action = _InvisibleAction(QIcon(self._icons['add']), trStr('Add new node', 'Добавить новый узел').text(), None)
        action.setToolTip(trStr('Add new node into current library',
                                'Добавить новый узел в текущую библиотеку').text())
        action.triggered.connect(self.__onAddNewNodeClicked)
        menu.addAction(action)
        actions['add'] = action

        action = _InvisibleAction(QIcon(self._icons['delete']), trStr('Delete', 'Удалить').text(), None)
        action.setToolTip(trStr('Delete current node', 'Удалить текущий узел').text())
        action.triggered.connect(self.__onDeleteNodeClicked)
        menu.addAction(action)
        actions['delete'] = action

        action = _InvisibleAction(QIcon(self._icons['copy']), trStr('Copy', 'Копировать').text(), None)
        action.setToolTip(trStr('Copy current node to clipboard', 'Копировать текущий узел в буфер обмена').text())
        action.triggered.connect(self.__onCopyClicked)
        menu.addAction(action)
        actions['copy'] = action

        action = _InvisibleAction(QIcon(self._icons['paste']), trStr('Paste', 'Вставить').text(), None)
        action.setToolTip(trStr('Paste copy of node from clipboard', 'Вставить копию узла из буфера обмена').text())
        action.triggered.connect(self.__onPasteClicked)
        menu.addAction(action)
        actions['paste'] = action

        if self.currentItem() is not None:
            if self.currentItem().isExpanded():
                actions['collapse'].setVisible(True)
                actions['collapse'].setEnabled(True)
            else:
                actions['expand'].setVisible(True)
                actions['expand'].setEnabled(True)

            if self.indexOfTopLevelItem(self.currentItem()) >= 0:
                actions['rename library'].setVisible(True)
                actions['exclude library'].setVisible(True)
                if globals.editLibraries:
                    actions['rename library'].setEnabled(True)
                    actions['exclude library'].setEnabled(True)

            if self.currentItem().parent() is not None:
                i = self.indexOfTopLevelItem(self.currentItem().parent().parent())
                if i >= 0:
                    actions['generate code'].setVisible(True)
                    libname = self.topLevelItem(i).text(0)
                    nodename = self.currentItem().text(0)
                    node = self.__libraries[libname][nodename]
                    cls = self.__alphabet.getClass(node.nodeClass)
                    if cls is not None and cls.codegenData is not None:
                        actions['generate code'].setEnabled(True)

                    actions['add'].setVisible(True)
                    actions['delete'].setVisible(True)
                    actions['copy'].setVisible(True)
                    actions['paste'].setVisible(True)

                    if globals.editLibraries and cls is not None:
                        actions['add'].setEnabled(True)
                        actions['delete'].setEnabled(True)
                        actions['copy'].setEnabled(True)
                        if globals.clipboard['node-desc'] is not None\
                                and globals.clipboard['node-desc'].nodeClass == node.nodeClass:
                            actions['paste'].setEnabled(True)
                else:
                    # libname = self.currentItem().parent().text(0)
                    nodeClass = self.currentItem().groupName
                    cls = self.__alphabet.getClass(nodeClass)

                    actions['add'].setVisible(True)
                    actions['paste'].setVisible(True)

                    print('debug: Class is \'{0}\''.format(nodeClass))
                    if globals.editLibraries and cls is not None:
                        actions['add'].setEnabled(True)
                        if globals.clipboard['node-desc'] is not None\
                                and globals.clipboard['node-desc'].nodeClass == nodeClass:
                            actions['paste'].setEnabled(True)
            else:
                actions['paste'].setVisible(True)
                if globals.editLibraries and globals.clipboard['node-desc'] is not None:
                    actions['paste'].setEnabled(True)

        menu.exec_(QCursor.pos())

    @QtCore.Slot()
    def __onAddNewNodeClicked(self):
        if self.currentItem() is not None and self.currentItem().parent() is not None:
            i = self.indexOfTopLevelItem(self.currentItem().parent().parent())
            if i >= 0:
                libname = self.topLevelItem(i).text(0)
                nodename = self.currentItem().text(0)
                node = self.__libraries[libname][nodename]
                nodeClass = node.nodeClass
                nodeType = node.nodeType
            else:
                libname = self.currentItem().parent().text(0)
                nodeClass = self.currentItem().groupName
                nodeType = ''

            cls = self.__alphabet.getClass(nodeClass)
            if cls is not None:
                if not nodeType:
                    theType = cls.getFirstType(False)
                    if theType is not None:
                        nodeType = theType.name
                if nodeType:
                    print('debug: New \'{0} {1}\' node will be added into \'{2}\' library'
                          .format(nodeType, nodeClass, libname))
                    globals.librarySignals.addNewNode.emit(libname, nodeClass, nodeType)

    @QtCore.Slot()
    def __onCopyClicked(self):
        if self.currentItem() is not None and self.currentItem().parent() is not None:
            i = self.indexOfTopLevelItem(self.currentItem().parent().parent())
            if i >= 0:
                libname = self.topLevelItem(i).text(0)
                nodename = self.currentItem().text(0)
                node = self.__libraries[libname][nodename]
                globals.clipboard['node-desc'] = node.deepcopy()
                print('debug: Node \'{0}\' from library \'{1}\' have been copied to clipboard'
                      .format(nodename, libname))

    @QtCore.Slot()
    def __onPasteClicked(self):
        theCopy = globals.clipboard['node-desc']
        if self.currentItem() is not None and theCopy is not None:
            if self.currentItem().parent() is not None:
                i = self.indexOfTopLevelItem(self.currentItem().parent().parent())
                if i >= 0:
                    libname = self.topLevelItem(i).text(0)
                    nodename = self.currentItem().text(0)
                    node = self.__libraries[libname][nodename]
                    nodeClass = node.nodeClass
                else:
                    libname = self.currentItem().parent().text(0)
                    nodeClass = self.currentItem().groupName
                if theCopy.nodeClass == nodeClass:
                    print('info: The copy of \'{0} {1} {2}\' node from '
                          'library \'{3}\' will be added into library \'{4}\''
                          .format(theCopy.nodeType, theCopy.nodeClass, theCopy.name, theCopy.libname, libname))
                    globals.librarySignals.addNode.emit(libname, theCopy.deepcopy())
                else:
                    print('warning: Can\'t add copy of \'{0}\' node into \'{1}s\' list!'
                          .format(theCopy.nodeClass, nodeClass))
            else:
                libname = self.currentItem().text(0)
                print('info: The copy of \'{0} {1} {2}\' node from library \'{3}\' will be added into library \'{4}\''
                      .format(theCopy.nodeType, theCopy.nodeClass, theCopy.name, theCopy.libname, libname))
                globals.librarySignals.addNode.emit(libname, theCopy.deepcopy())

    @QtCore.Slot()
    def __onExpandClicked(self):
        if self.currentItem() is not None:
            self.expandItem(self.currentItem())

    @QtCore.Slot()
    def __onCollapseClicked(self):
        if self.currentItem() is not None:
            self.collapseItem(self.currentItem())

    # "Unload library" click handler
    @QtCore.Slot()
    def __onUnloadClicked(self):
        currItem = self.currentItem()
        if currItem.libname:
            globals.librarySignals.excludeLibrary.emit(currItem.libname)

    @QtCore.Slot()
    def __onRenameLibraryClicked(self):
        currItem = self.currentItem()
        if currItem is not None and currItem.parent() is None:
            self._editingItem = currItem
            self._editingText = currItem.text(0)
            self.openPersistentEditor(currItem)

    @QtCore.Slot()
    def __onDeleteNodeClicked(self):
        currItem = self.currentItem()
        if currItem.node is not None:
            globals.librarySignals.removeNode.emit(currItem.node.libname, currItem.node.name)

    @QtCore.Slot()
    def onCreateLibClicked(self):
        dialog = lldialog.LL_CreateLibDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            if self.__tempLib is not None and self.addLib(self.__tempLib) is True:
                self.__changed = True
        self.__tempLib = None

    @QtCore.Slot()
    def __onEditNodeClicked(self):
        i = self.indexOfTopLevelItem(self.currentItem().parent().parent())
        if i >= 0:
            dialog = lldialog.LL_EditNodeDialog(self.__libraries, self, self.topLevelItem(i).text(0),
                                                self.currentItem().text(0))
            dialog.exec_()

    def setTempLib(self, tmp):
        self.__tempLib = tmp

    def clearLibs(self):
        libs = []
        for lib in self.__libWidgets:
            libs.append(lib)

        self.__cleaning = True
        for lib in libs:
            self.__removeLib(lib)
        self.__libWidgets.clear()
        self.__cleaning = False

    @QtCore.Slot()
    def __onSelectionChanged(self):
        if self.__externalSelect:
            return

        if self.__grab:
            return

        if self.currentItem() is not None and not self.__cleaning:
            if self.indexOfTopLevelItem(self.currentItem()) >= 0:
                globals.nodeListSignals.libSelected.emit(self.currentItem().libname)
            elif self.currentItem().parent() is not None and self.indexOfTopLevelItem(
                    self.currentItem().parent().parent()) >= 0:
                i = self.indexOfTopLevelItem(self.currentItem().parent().parent())
                if i >= 0:
                    globals.nodeListSignals.nodeSelected.emit(self.topLevelItem(i).text(0), self.currentItem().text(0))
                else:
                    globals.nodeListSignals.notSelected.emit()
            else:
                globals.nodeListSignals.notSelected.emit()

    @QtCore.Slot(QTreeWidgetItem, QTreeWidgetItem)
    def __onCurrentChanged(self, current, previous):
        if self.__externalSelect:
            return

        if self.__grab:
            return

        if current is not None and not self.__cleaning:
            if self.indexOfTopLevelItem(current) >= 0:
                globals.nodeListSignals.libSelected.emit(current.libname)
            elif current.parent() is not None and self.indexOfTopLevelItem(current.parent().parent()) >= 0:
                i = self.indexOfTopLevelItem(current.parent().parent())
                if i >= 0:
                    globals.nodeListSignals.nodeSelected.emit(self.topLevelItem(i).text(0), current.text(0))
                else:
                    globals.nodeListSignals.notSelected.emit()
            else:
                globals.nodeListSignals.notSelected.emit()

    @QtCore.Slot(QTreeWidgetItem)
    def __onItemChange(self, item):
        if self._editingItem is not None and item is self._editingItem:
            self.closePersistentEditor(self._editingItem)
            newName = self._editingItem.text(0)
            newName = newName.replace(' ', '')

            if newName == self._editingText:
                return

            revert = False
            if not newName or newName in self.__libraries:
                revert = True

            if not revert:
                self._editingItem = None
                oldName, self._editingText = self._editingText, ''
                self._editingInternal = True
                globals.librarySignals.renameLibrary.emit(oldName, newName)
                self._editingInternal = False
                return

            if revert:
                self._editingItem.setText(0, self._editingText)
                title = trStr('Rename error!', 'Ошибка при изменении имени!').text()
                message = trStr('Library with name \"<b>{0}</b>\"<br/>is already exist!'.format(newName),
                                'Библиотека с именем \"<b>{0}</b>\"<br/>уже существует!'.format(newName)).text()
                QMessageBox.critical(self, title, message)

            self._editingItem = None
            self._editingText = ''

    @QtCore.Slot(str, str, str)
    def __onNodeRemove(self, libname, nodename, nodeClass):
        if libname in self.__libraries and libname in self.__libWidgets:
            self.__libWidgets[libname].removeNode(nodename, nodeClass)

    @QtCore.Slot(str, str)
    def __onNodeAdd(self, libname, nodename):
        if libname in self.__libraries and libname in self.__libWidgets and nodename in self.__libraries[libname]:
            self.__libWidgets[libname].addNode(self.__libraries[libname][nodename])

    @QtCore.Slot(str, str)
    def __onLibraryRename(self, oldName, newName):
        if not self._editingInternal:
            libs, alphabet = self.__libraries, self.__alphabet
            self.setSource(None, None)
            self.clearLibs()
            self.setSource(libs, alphabet)
        elif oldName in self.__libWidgets and newName not in self.__libWidgets:
            self.__libWidgets[newName] = self.__libWidgets[oldName]
            del self.__libWidgets[oldName]
            self.__libWidgets[newName].rename(newName)
            self.sortItems(0, Qt.AscendingOrder)

    def mousePressEvent(self, event):
        pressedItem = self.itemAt(event.pos())
        if pressedItem is not None:
            if self.indexOfTopLevelItem(pressedItem) < 0 and pressedItem.parent() is not None \
                    and self.indexOfTopLevelItem(pressedItem.parent().parent()) >= 0:
                i = self.indexOfTopLevelItem(pressedItem.parent().parent())
                if i >= 0:
                    # globals.nodeListSignals.nodeGrabbed.emit(self.topLevelItem(i).text(0), pressedItem.text(0))
                    self.__grabSentSignal = False
                    self.__grabbedItemLibrary = self.topLevelItem(i).text(0)
                    self.__grabbedItemNodename = pressedItem.text(0)
                    self.__grab = True
        QTreeView.mousePressEvent(self, event)

    def mouseReleaseEvent(self, event):
        if self.__grab:
            self.__grabbedItemLibrary = ''
            self.__grabbedItemNodename = ''
            self.__grab = False
            if self.__grabSentSignal:
                self.__grabSentSignal = False
                globals.nodeListSignals.nodeReleased.emit(event.globalX(), event.globalY())
            self.__onSelectionChanged()
        QTreeView.mouseReleaseEvent(self, event)

    def mouseMoveEvent(self, event):
        if self.__grab:
            if not self.__grabSentSignal:
                globalPos = QPoint(event.globalX(), event.globalY())
                localPos = self.mapFromGlobal(globalPos)
                if not self.rect().contains(localPos):
                    self.__grabSentSignal = True
                    globals.nodeListSignals.nodeGrabbed.emit(self.__grabbedItemLibrary, self.__grabbedItemNodename)
            if self.__grabSentSignal:
                globals.nodeListSignals.grabMove.emit(event.globalX(), event.globalY())
        QTreeView.mouseMoveEvent(self, event)

    def dragEnterEvent(self, event):
        print('debug: drag enter')

    def dragMoveEvent(self, event):
        print('debug: drag move')

    def dropEvent(self, event):
        print('debug: drag drop')

    @QtCore.Slot(str, str)
    def selectNode(self, libname, nodename):
        self.__externalSelect = True

        if libname in self.__libWidgets:
            libItem = self.__libWidgets[libname]
            if libItem.childCount() > 0:
                for i in range(libItem.childCount()):
                    groupItem = libItem.child(i)
                    if groupItem.childCount() < 1:
                        continue
                    for j in range(groupItem.childCount()):
                        nodeItem = groupItem.child(j)
                        if nodeItem.node is not None and nodeItem.node.name == nodename:
                            self.setCurrentItem(nodeItem)
                            QTimer.singleShot(10, self.scrollToCurrentItem)
                            self.__externalSelect = False
                            return

        self.setCurrentItem(None)

        self.__externalSelect = False

    @QtCore.Slot()
    def scrollToCurrentItem(self):
        item = self.currentItem()
        if item is not None:
            self.scrollToItem(self.currentItem())

    @QtCore.Slot()
    def __onGenerateCodeClicked(self):
        if self.currentItem() is not None:
            if self.indexOfTopLevelItem(self.currentItem()) < 0 and self.currentItem().parent() is not None:
                i = self.indexOfTopLevelItem(self.currentItem().parent().parent())
                if i >= 0:
                    libname = self.topLevelItem(i).text(0)
                    nodename = self.currentItem().text(0)
                    node = self.__libraries[libname][nodename]
                    cls = self.__alphabet.getClass(node.nodeClass)
                    dialog = PatternGeneratorDialog(node, cls.codegenData, None)
                    dialog.exec_()

    @QtCore.Slot(str)
    def __onLanguageChange(self, lang):
        pass

##############################################################
##############################################################


# Dock widget containing tree libs
class LL_LibDock(trDockWidget):
    def __init__(self, title, parent=None):
        trDockWidget.__init__(self, title, parent)

        self.__libTree = LL_Tree(self)
        self.setWidget(self.__libTree)

        globals.historySignals.undoMade.connect(self.refresh)
        globals.historySignals.redoMade.connect(self.refresh)

    def setDatasource(self, libs, alphabet):
        self.__libTree.setSource(None, None)
        self.clearLibs()
        self.__libTree.setSource(libs, alphabet)

    def clearLibs(self):
        self.__libTree.clearLibs()

    @QtCore.Slot(str, str)
    def select(self, libname, nodename):
        self.__libTree.selectNode(libname, nodename)

    @QtCore.Slot()
    def refresh(self):
        self.setDatasource(globals.project.libraries, globals.project.alphabet)

    # @QtCore.Slot(str)
    # def __onRemoveClicked(self, libname):
    # 	print u'warning: library', libname, u'was removed'
    # 	self.removed.emit(libname)

##############################################################
##############################################################
