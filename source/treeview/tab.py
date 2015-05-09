# coding=utf-8
# -----------------
# file      : tab.py
# date      : 2012/10/06
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
############################################################################

from PySide import QtCore
from PySide.QtGui import *
from PySide.QtCore import *

from treenode import TreeNode

from .diagram import TreeGraphicsView
from .connector import ConnectorType

import globals

#######################################################################################################################
#######################################################################################################################


class TabBar(QTabBar):
    def __init__(self, parent=None):
        QTabBar.__init__(self, parent)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MidButton:
            self.tabCloseRequested.emit(self.tabAt(event.pos()))
        QTabBar.mouseReleaseEvent(self, event)

#######################################################################################################################
#######################################################################################################################


class TreeTab(QTabWidget):
    tabAdded = QtCore.Signal()
    tabRemoved = QtCore.Signal(int)
    tabActivated = QtCore.Signal(int)

    itemSelected = QtCore.Signal(int, TreeNode, bool)
    nothingSelected = QtCore.Signal(int)

    def __init__(self, horizontalMode, dragMode, justifyMode, connector, connectorType, parent=None):
        QTabWidget.__init__(self, parent)
        self.setTabBar(TabBar(self))
        self.currentChanged.connect(self.onActiveTabChange)
        self.__currentTab = -10

        self.__proj = None
        self.__tabs = dict()
        self.__tabWidgets = []

        self.hMode = horizontalMode
        self.dragMode = dragMode
        self.justifyMode = justifyMode
        self.connectorTool = connector
        self.connectorType = ConnectorType(connectorType)

        self.setTabsClosable(True)
        self.tabCloseRequested.connect(self.closeTab)

        globals.behaviorTreeSignals.treeRenamed.connect(self.onReferenceRename)
        globals.behaviorTreeSignals.treeDeleted.connect(self.tabRemoving)
        globals.treeListSignals.doubleClicked.connect(self.tabQuery)

        globals.treeListSignals.branchGrabbed.connect(self.onBranchGrab)
        globals.treeListSignals.branchReleased.connect(self.onNodeRelease)
        globals.treeListSignals.branchMove.connect(self.onGrabbedNodeMove)

        globals.nodeListSignals.nodeGrabbed.connect(self.onNodeGrab)
        globals.nodeListSignals.nodeReleased.connect(self.onNodeRelease)
        globals.nodeListSignals.grabMove.connect(self.onGrabbedNodeMove)

        # self.__tabs['test tab'] = QLabel(u'test tab')
        # self.__tabs['test tab 2'] = QLabel(u'test tab 2')
        # self.addTab(self.__tabs['test tab'],u'label')
        # self.addTab(self.__tabs['test tab 2'],u'label 2')
        self.setMovable(False)

    @staticmethod
    def defaultWidget():
        return TreeGraphicsView(None, '')

    @QtCore.Slot()
    def refreshAll(self):
        rmlist = []
        for tab in self.__tabWidgets:
            if tab.branchname in self.__proj.trees:
                tab.refresh()
            else:
                rmlist.append(tab.branchname)
        for rm in rmlist:
            self.tabRemoving(rm)

    def setProject(self, proj):
        if self.__proj is not None and proj is not None and self.__proj == proj:
            return
        self.__tabs.clear()
        self.__tabWidgets = []
        self.clear()
        self.setMovable(False)
        self.__proj = proj
        globals.historySignals.undoMade.connect(self.refreshAll)
        globals.historySignals.redoMade.connect(self.refreshAll)

    @QtCore.Slot(str)
    def tabQuery(self, for_branch):
        if for_branch not in self.__tabs:
            if self.__proj is not None and for_branch in self.__proj.trees:
                uid = self.__proj.trees.get(for_branch)
                theTree = self.__proj.nodes.get(uid)

                newTab = TreeGraphicsView(self.__proj, theTree.fullRefName(), self)
                newTab.itemSelected.connect(self.onItemSelection)
                newTab.noneSelected.connect(self.onCancelSelection)

                self.__tabs[for_branch] = newTab
                self.__tabWidgets.append(newTab)

                self.addTab(newTab, theTree.refname())
                self.setTabToolTip(self.count() - 1, theTree.path())
                newTab.setDisplayMode(self.hMode)
                newTab.setDragMode(self.dragMode)
                newTab.setJustifyMode(self.justifyMode)
                newTab.setConnectorMode(self.connectorTool)
                newTab.setConnectorType(self.connectorType.val)

                self.setCurrentIndex(self.count() - 1)

                self.tabAdded.emit()
                globals.behaviorTreeSignals.treeOpened.emit(theTree.path(), theTree.refname())
            self.setMovable(self.count() > 1)
        else:
            widget = self.__tabs[for_branch]
            index = self.indexOf(widget)
            self.setCurrentIndex(index)

    def empty(self):
        return not self.__tabWidgets

    @QtCore.Slot(str)
    def tabRemoving(self, for_branch):
        if for_branch in self.__tabs:
            index = self.indexOf(self.__tabs[for_branch])
            self.closeTab(index)

    @QtCore.Slot(int)
    def closeTab(self, index):
        widget = self.widget(index)
        widget_treename = widget.treename()
        widget.flush()
        i = self.__tabWidgets.index(widget)
        if self.__currentTab == i:
            self.__currentTab = -10

        if self.__proj is not None:
            uid = self.__proj.trees.get(widget_treename)
            theTree = self.__proj.nodes.get(uid)
        else:
            theTree = None

        if widget_treename in self.__tabs:
            del self.__tabs[widget_treename]

        self.__tabWidgets.remove(widget)
        self.removeTab(index)

        self.tabRemoved.emit(i)
        if theTree is not None:
            globals.behaviorTreeSignals.treeClosed.emit(theTree.path(), theTree.refname())

        del widget
        self.setMovable(self.count() > 1)

    @QtCore.Slot(bool)
    def viewTrigger(self, horizontal):
        if self.hMode != horizontal:
            self.hMode = horizontal
            for tab in self.__tabWidgets:
                tab.setDisplayMode(horizontal)

    @QtCore.Slot(bool)
    def dragModeTrigger(self, drag):
        if self.dragMode != drag:
            self.dragMode = drag
            for tab in self.__tabWidgets:
                tab.setDragMode(drag)

    @QtCore.Slot(bool)
    def justifyModeTrigger(self, justify):
        if self.justifyMode != justify:
            self.justifyMode = justify
            for tab in self.__tabWidgets:
                tab.setJustifyMode(justify)

    @QtCore.Slot(bool)
    def connectorToolTrigger(self, turnOn):
        if self.connectorTool != turnOn:
            self.connectorTool = turnOn
            for tab in self.__tabWidgets:
                tab.setConnectorMode(turnOn)

    @QtCore.Slot(int)
    def onConnectorTypeChange(self, value):
        prevVal = self.connectorType.val
        self.connectorType.val = value
        if prevVal != self.connectorType.val:
            for tab in self.__tabWidgets:
                tab.setConnectorType(self.connectorType.val)

    @QtCore.Slot(int)
    def onActiveTabChange(self, index):
        if self.__tabWidgets:
            widget = self.widget(index)
            i = self.__tabWidgets.index(widget)
            if self.__currentTab != i:
                if widget is not None:
                    widget.setFocused(True)
                if 0 <= self.__currentTab < len(self.__tabWidgets):
                    self.__tabWidgets[self.__currentTab].setFocused(False)
                self.__currentTab = i
                self.tabActivated.emit(i)

    @QtCore.Slot(QGraphicsView, TreeNode)
    def onItemSelection(self, senderTab, node, editable):
        index = self.indexOf(senderTab)
        if index >= 0 and self.__tabWidgets:
            widget = self.widget(index)
            i = self.__tabWidgets.index(widget)
            if self.__currentTab != i:
                self.__currentTab = i
            self.tabActivated.emit(i)
            self.itemSelected.emit(i, node, editable)

    @QtCore.Slot(QGraphicsView)
    def onCancelSelection(self, senderTab):
        index = self.indexOf(senderTab)
        if index >= 0 and self.__tabWidgets:
            widget = self.widget(index)
            i = self.__tabWidgets.index(widget)
            # if self.__currentTab != i:
            #     self.__currentTab = i
            # self.tabActivated.emit(i)
            self.nothingSelected.emit(i)

    @QtCore.Slot(bool)
    def updateTabsItems(self, full):
        for tab in self.__tabWidgets:
            tab.updateItems(full)

    @QtCore.Slot(str, str)
    def onReferenceRename(self, oldname, newname):
        if oldname in self.__tabs:
            self.__tabs[newname] = self.__tabs[oldname]
            strings = newname.split('/')
            self.setTabText(self.indexOf(self.__tabs[newname]), strings[-1])
            self.__tabs[newname].branchname = newname
            self.__tabs[newname].scene().branchname = newname
            del self.__tabs[oldname]
        self.refreshAll()

    @QtCore.Slot(str, str)
    def onNodeGrab(self, libname, nodename):
        if self.__currentTab < 0:
            return
        widget = self.widget(self.__currentTab)
        if widget is not None:
            widget.onNodeGrab(libname, nodename)

    @QtCore.Slot(str)
    def onBranchGrab(self, treename):
        if self.__currentTab < 0:
            return
        widget = self.widget(self.__currentTab)
        if widget is not None:
            widget.onBranchGrab(treename)

    @QtCore.Slot(int, int)
    def onNodeRelease(self, x, y):
        if self.__currentTab < 0:
            return
        widget = self.widget(self.__currentTab)
        if widget is not None:
            widget.onGrabbedRelease(x, y)

    @QtCore.Slot(int, int)
    def onGrabbedNodeMove(self, x, y):
        if self.__currentTab < 0:
            return
        widget = self.widget(self.__currentTab)
        if widget is not None:
            widget.onGrabbedNodeMove(x, y)

#######################################################################################################################
#######################################################################################################################
