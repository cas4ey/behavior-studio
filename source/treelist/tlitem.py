# coding=utf-8
# -----------------
# file      : tlitem.py
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

__author__ = 'Victor Zarubkin'
__copyright__ = 'Copyright (C) 2012  Victor Zarubkin'
__credits__ = ['Victor Zarubkin']
__license__ = ['GPLv3']
__version__ = '1.2.5'  # this is last application version when this script file was changed
__email__ = 'victor.zarubkin@gmail.com'
############################################################################

from PySide.QtGui import *
from PySide.QtCore import *
from application_palette import global_colors

import os
from auxtypes import toUnixPath, joinPath
import globals

#######################################################################################################################
#######################################################################################################################


class TL_AbstractItem(QTreeWidgetItem):
    def __init__(self, parent=None):
        QTreeWidgetItem.__init__(self, parent)
        self.defaultColor = QBrush(global_colors[QPalette.Text][0])
        self.setForeground(0, self.defaultColor)
        self.parentWidget = parent

    def setColor(self, color):
        self.setForeground(0, QBrush(color))

    def resetColor(self):
        self.setForeground(0, self.defaultColor)

    def setBold(self, value):
        myFont = self.font(0)
        myFont.setBold(value)
        self.setFont(0, myFont)

    def enter(self):
        pass

    def leave(self):
        pass

#######################################################################################################################
#######################################################################################################################


class TL_TaskItem(TL_AbstractItem):
    def __init__(self, node, parent=None):
        TL_AbstractItem.__init__(self, parent)
        self.node = node
        self.path = node.path()
        self.__inactiveIcon = QIcon(joinPath(globals.applicationIconsPath, 'tree70.png'))
        self.__activeIcon = QIcon(joinPath(globals.applicationIconsPath, 'tree71.png'))
        self.update()
        self.setIcon(0, self.__inactiveIcon)

    def update(self):
        self.clear()
        if self.node.refname():
            self.setText(0, self.node.refname())
        elif self.node.isEmpty():
            self.setText(0, 'new node')
        elif self.node.nodeDesc() is not None:
            self.setText(0, self.node.nodeDesc().name)
        else:
            self.setText(0, 'unknown node')

    def clear(self):
        children = self.takeChildren()
        for i in range(len(children)):
            children.pop()

    def enter(self):
        self.setIcon(0, self.__activeIcon)

    def leave(self):
        self.setIcon(0, self.__inactiveIcon)

#######################################################################################################################
#######################################################################################################################


class TL_TreeFileItem(TL_AbstractItem):
    def __init__(self, project, filename, parent=None):
        TL_AbstractItem.__init__(self, parent)
        self.path = filename

        filedir = toUnixPath(os.path.dirname(filename)) + '/'
        # text = filename
        text = filename.replace(filedir, '')

        self.setText(0, text)
        self.setToolTip(0, self.path)

        subbranches = project.trees.getBranchesByFile(self.path, project.nodes)
        if subbranches:
            for t in subbranches:
                TL_AbstractItem.addChild(self, TL_TaskItem(subbranches[t], self))
            if self.childCount() > 1:
                self.sortChildren(0, Qt.AscendingOrder)

    def addChild(self, *args, **kwargs):
        TL_AbstractItem.addChild(self, *args, **kwargs)
        self.sortChildren(0, Qt.AscendingOrder)

#######################################################################################################################
#######################################################################################################################

