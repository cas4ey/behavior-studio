# coding=utf-8
# -----------------
# file      : llitem.py
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
from PySide.QtGui import *
from PySide.QtCore import *
from application_palette import global_colors
import globals

##############################################################
##############################################################


class LL_AbstractItem(QTreeWidgetItem):
    def __init__(self, parent=None):
        QTreeWidgetItem.__init__(self, parent)
        self.defaultColor = QBrush(global_colors[QPalette.Text][0])
        self.setForeground(0, self.defaultColor)
        self.parentWidget = parent
        self.children = []

    def row(self):
        if self.parent() is not None:
            return self.parent().indexOfChild(self)
        return 0

    def onChildInit(self, columns):
        while self.columnCount() < columns:
            self.setText(self.columnCount(), '')
        if self.parentWidget is not None:
            self.parentWidget.onChildInit(self.columnCount())

    def setColor(self, color):
        self.setForeground(0, QBrush(color))

    def resetColor(self):
        self.setForeground(0, self.defaultColor)

    def setBold(self, value):
        myFont = self.font(0)
        myFont.setBold(value)
        self.setFont(0, myFont)

    def flush(self, dataModel):
        self.parentWidget = None

##############################################################
##############################################################


class _ItemProxy(QtCore.QObject):
    def __init__(self, onNodeRename, onDescriptionChange, onShapeChange):
        QtCore.QObject.__init__(self)
        self._onNodeRename = onNodeRename
        self._onDescriptionChange = onDescriptionChange
        self._onShapeChange = onShapeChange
        globals.librarySignals.nodeRenamed.connect(self.__onNodeRename)
        globals.librarySignals.nodeDescriptionChanged.connect(self.__onDescriptionChange)
        globals.librarySignals.nodeShapeChanged.connect(self.__onShapeChange)

    @QtCore.Slot(str, str, str)
    def __onNodeRename(self, libname, oldname, newname):
        self._onNodeRename(libname, oldname, newname)

    @QtCore.Slot(str, str, str)
    def __onDescriptionChange(self, libname, nodename, description):
        self._onDescriptionChange(libname, nodename, description)

    @QtCore.Slot(str, str, str)
    def __onShapeChange(self, libname, nodename, shapeName):
        self._onShapeChange(libname, nodename, shapeName)


# Item containing one tree node description
class LL_TreeNodeItem(LL_AbstractItem):
    # Constructor
    def __init__(self, nodedesc, parentItem=None):
        LL_AbstractItem.__init__(self, parentItem)
        self.node = nodedesc

        if self.node is not None:
            self.setText(0, self.node.name)
            # self.setToolTip(0, self.node.description)
            self.setToolTip(0, self.node.description.replace('\n', '<br/>'))
            if self.node.icon is not None:
                self.setIcon(0, self.node.icon)
        else:
            self.setText(0, 'UNKNOWN')

        if self.parentWidget is not None:
            self.parentWidget.onChildInit(self.columnCount())

        self._proxy = _ItemProxy(self.__onNodeRename, self.__onDescriptionChange, self.__onShapeChange)

    def __eq__(self, other):
        return other is self

    def setDesc(self, nodedesc):
        self.node = nodedesc
        self.setText(0, self.node.name)
        self.setToolTip(0, self.node.description)
        if self.parentWidget is not None:
            self.parentWidget.onChildInit(self.columnCount())

    def update(self):
        if self.node is not None:
            self.setText(0, self.node.name)
            self.setToolTip(0, self.node.description)
            if self.node.icon is not None:
                self.setIcon(0, self.node.icon)
        else:
            self.setText(0, 'UNKNOWN')
            self.setToolTip(0, 'None')
            self.setIcon(0, None)

    def __onNodeRename(self, libname, oldname, newname):
        if self.node is not None and self.node.libname == libname and self.node.name == newname:
            self.update()
            self.parent().sortChildren(0, Qt.AscendingOrder)

    def __onDescriptionChange(self, libname, nodename, description):
        if self.node is not None and self.node.name == nodename and self.node.libname == libname:
            self.update()

    def __onShapeChange(self, libname, nodename, shapeName):
        if self.node is not None and self.node.name == nodename and self.node.libname == libname:
            self.update()

##############################################################
##############################################################


# Item containing a group of nodes (Tasks, Conditions, Composites, etc.)
class LL_TreeGroupItem(LL_AbstractItem):
    # Constructor
    # groupname - name of nodes group ("Tasks", "Conditions")
    # data - dict({'node name': treenode.TreeNodeDesc, ...})
    # parentItem - LL_TreeLibItem
    def __init__(self, data, groupname, ncount=0, parentItem=None):
        LL_AbstractItem.__init__(self, parentItem)
        self.groupName = groupname
        for node in data:
            self.children.append(LL_TreeNodeItem(data[node], self))
            LL_AbstractItem.addChild(self, self.children[-1])
        self.setText(0, '{0}s ({1})'.format(groupname, len(self.children)))
        if self.childCount() > 1:
            self.sortChildren(0, Qt.AscendingOrder)

    def setName(self, groupname, ncount=0):
        self.groupName = groupname
        self.setText(0, '{0}s ({1})'.format(groupname, ncount))

    def addNode(self, nodedesc):
        for child in self.children:
            if nodedesc.name == child.node.name:
                print('debug: node with name \'{0}\' already exist'.format(nodedesc.name))
                return
        self.addChild(LL_TreeNodeItem(nodedesc, self))

    def removeNode(self, nodeName, nodeClass):
        for child in self.children:
            if nodeName == child.node.name:
                self.children.remove(child)
                self.removeChild(child)
                self.setText(0, '{0}s ({1})'.format(self.groupName, len(self.children)))
                return
        print('debug: node with name \'{0}\' does not exist'.format(nodeName))

    def flush(self, dataModel):
        num = len(self.children)
        for child in self.children:
            # row = child.row()
            child.flush(dataModel)
            self.removeChild(child)
            # dataModel.removeRow(row)
            del child
        for i in range(num):
            self.children.pop()
        self.children = []
        LL_AbstractItem.flush(self, dataModel)

    def addChild(self, child):
        self.children.append(child)
        LL_AbstractItem.addChild(self, child)
        self.setText(0, '{0}s ({1})'.format(self.groupName, len(self.children)))
        self.sortChildren(0, Qt.AscendingOrder)

##############################################################
##############################################################


# Item containing one node library
class LL_TreeTopLevelItem(LL_AbstractItem):
    # Constructor
    # nodelib - class treenode.NodeLibrary
    # parent - LL_AbstractItem
    def __init__(self, nodelib, parent=None):
        LL_AbstractItem.__init__(self, parent)

        self.libname = nodelib.libname

        self.setText(0, nodelib.libname)
        self.setToolTip(0, nodelib.path())
        # self.setText(1,nodelib.path())
        # self.setToolTip(1,nodelib.path())

        classes = globals.project.alphabet.getClasses()
        for classname in classes:
            nodes = nodelib.getAll(classname)
            self.addChild(LL_TreeGroupItem(nodes, classname, len(nodes), self))

        if self.parentWidget is not None:
            self.parentWidget.onChildInit(self.columnCount())

    def addChild(self, child):
        self.children.append(child)
        LL_AbstractItem.addChild(self, child)

    def addNode(self, nodedesc):
        for child in self.children:
            if child.groupName == nodedesc.nodeClass:
                child.addNode(nodedesc)
                return

    def removeNode(self, nodeName, nodeClass):
        for child in self.children:
            if child.groupName == nodeClass:
                child.removeNode(nodeName, nodeClass)
                return

    def rename(self, newName):
        self.libname = newName
        self.setText(0, self.libname)

    def flush(self, dataModel):
        num = len(self.children)
        for child in self.children:
            # row = child.row()
            child.flush(dataModel)
            self.removeChild(child)
            # dataModel.removeRow(row)
            del child
        for i in range(num):
            self.children.pop()
        self.children = []
        LL_AbstractItem.flush(self, dataModel)

##############################################################
##############################################################
