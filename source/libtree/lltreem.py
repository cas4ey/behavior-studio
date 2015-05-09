# coding=utf-8
# -----------------
# file      : lltreem.py
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

from PySide.QtCore import *
from PySide.QtGui import *

from . import llitem

##############################################################
##############################################################


# Tree widget containing all loaded libraries
class LL_Tree(QAbstractItemModel):
    # Constructor
    # parent - QWidget
    def __init__(self, parent=None):
        QAbstractItemModel.__init__(self, parent)
        self.__libs = dict()
        self.__header = llitem.LL_AbstractItem()
        self.__header.setText(0, "Available nodes")
        # self.__header.setText(1,"Description")

    ##################################################################################
    # NodeLibrary setcion:

    # Add new lib
    # lib - class treenode.NodeLibrary
    def addLib(self, lib):
        if lib.libname not in self.__libs:
            self.__libs[lib.libname] = llitem.LL_TreeTopLevelItem(lib, self.__header)
            self.__header.addChild(self.__libs[lib.libname])
            self.layoutChanged.emit()
            return True
        return False

    # Remove lib with name "libname"
    # libname - string
    def removeLib(self, libname):
        if libname in self.__libs:
            self.__header.removeChild(self.__libs[libname])
            del self.__libs[libname]
            self.layoutChanged.emit()
            return True
        return False

    # Check for existing lib with name "libname"
    # libname - string
    def gotLib(self, libname):
        return libname in self.__libs

    ##################################################################################
    # QAbstractItemModel setcion:

    # Redefinition of QAbstractItemModel.columnCount()
    # Get columns count of specified item
    # index - QModelIndex
    def columnCount(self, index=QModelIndex()):
        if index.isValid():
            cc = index.internalPointer().columnCount()
            return cc
        return self.__header.columnCount()

    # Redefinition of QAbstractItemModel.rowCount()
    # Get rows count of specified item
    # index - QModelIndex
    def rowCount(self, index=QModelIndex()):
        if index.column() > 0:
            return 0
        if not index.isValid():
            item = self.__header
        else:
            item = index.internalPointer()
        cc = item.childCount()
        return cc

    # Redefinition of QAbstractItemModel.data
    # Get data stored in specified item
    # index - QModelIndex
    def data(self, index, role):
        if not index.isValid():
            return None
        dta = index.internalPointer().data(index.column(), role)
        return dta

    # Redefinition of QAbstractItemModel.flags
    # Get flags of specified item
    # index - QModelIndex
    def flags(self, index):
        if index.isValid():
            fl = index.internalPointer().flags()
            return fl
        return 0

    # Redefinition of QAbstractItemModel.headerData
    # Get header data of specified column
    def headerData(self, column, orientation, role=Qt.DisplayRole):
        if orientation is Qt.Horizontal:
            return self.__header.data(column, role)
        return None

    # Redefinition of QAbstractItemModel.index
    # Get QModelIndex of item in specified row and column
    # parent - QModelIndex of parent item
    def index(self, row, column, parent=QModelIndex()):
        if not self.hasIndex(row, column, parent):
            return QModelIndex()
        if not parent.isValid():
            parentItem = self.__header
        else:
            parentItem = parent.internalPointer()
        childItem = parentItem.child(row)
        if childItem is not None:
            return self.createIndex(row, column, childItem)
        return QModelIndex()

    # Redefinition of QAbstractItemModel.parent
    # Get parent of item with specified index
    # index - QModelIndex
    def parent(self, index):
        if not index.isValid():
            return QModelIndex()
        item = index.internalPointer()
        parentItem = item.parent()
        if parentItem is self.__header:
            return QModelIndex()
        return self.createIndex(parentItem.row(), 0, parentItem)

##############################################################
##############################################################


# Dock widget containing tree libs
class LL_TreeDock(QDockWidget):
    def __init__(self, title, parent=None):
        QDockWidget.__init__(self, title, parent)
        self.setFeatures(self.DockWidgetMovable | self.DockWidgetFloatable)
        self.__libTreeModel = LL_Tree(self)
        self.__treeView = QTreeView()
        self.__treeView.setModel(self.__libTreeModel)
        self.setWidget(self.__treeView)

    def getTree(self):
        return self.__libTreeModel

##############################################################
##############################################################
