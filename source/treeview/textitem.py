# coding=utf-8
# -----------------
# file      : textitem.py
# date      : 2012/09/29
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

__author__ = 'Victor Zarubkin'
__copyright__ = 'Copyright (C) 2012  Victor Zarubkin'
__credits__ = ['Victor Zarubkin']
__license__ = ['GPLv3']
__version__ = '1.3.0'  # this is last application version when this script file was changed
__email__ = 'victor.zarubkin@gmail.com'
############################################################################

from PySide.QtGui import *
from PySide.QtCore import *

from compat_2to3 import *
from .colors import DiagramColor

#######################################################################################################################
#######################################################################################################################


class TextItem(QGraphicsTextItem):
    def __init__(self, invert_flag, text, ref=u'', parent=None, scene=None):
        self.__invert_flag = invert_flag

        fulltext = u''
        if invert_flag:
            fulltext += u'Not '

        if ref:
            fulltext += u'\"{0}\" '.format(unicode(ref))

        if text is None:
            text = u''
        self.noTextChange = (len(text) < 1)
        self.__displayText = text
        fulltext += text

        QGraphicsTextItem.__init__(self, fulltext, parent, scene)

        if ref:
            self.color = DiagramColor.defaultRefColor
        else:
            self.color = DiagramColor.defaultTextColor
        QGraphicsTextItem.setDefaultTextColor(self, self.color)
        self.alignment = Qt.AlignCenter

        self.ref = ref

        self.setFlag(QGraphicsItem.ItemIsMovable, False)
        self.setFlag(QGraphicsItem.ItemIsSelectable, False)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, False)
        self.setFlag(QGraphicsItem.ItemIsFocusable, False)

        self.setZValue(500.0)

    def setDefaultTextColor(self, color):
        self.color = color
        QGraphicsTextItem.setDefaultTextColor(self, color)

    def setSize(self, sz):
        f = QFont(self.font())
        f.setPointSizeF(sz)
        self.setFont(f)

    def setBold(self, b):
        f = QFont(self.font())
        f.setBold(b)
        self.setFont(f)

    def setWeight(self, w):
        f = QFont(self.font())
        f.setWeight(w)
        self.setFont(f)

    def setItalic(self, i):
        f = QFont(self.font())
        f.setItalic(i)
        self.setFont(f)

    def paint(self, painter, option, widget=None):
        # painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(self.defaultTextColor())
        painter.setFont(self.font())
        painter.drawText(self.boundingRect(), self.text(), QTextOption(self.alignment))

    def setText(self, invert_flag, text, ref=u'', internal=False):
        self.__invert_flag = invert_flag

        fulltext = u''
        if invert_flag:
            fulltext += u'Not '

        if ref:
            fulltext += u'\"{0}\" '.format(unicode(ref))

        if text is None:
            text = u''

        if not internal:
            self.noTextChange = (text is None or len(text) < 1)

        self.__displayText = text
        fulltext += text

        self.ref = ref

        # self.toPlainText(fulltext)
        self.setPlainText(fulltext)

        # QGraphicsSimpleTextItem.setText(self, fulltext)

    def text(self):
        return self.toPlainText()

    def displayText(self):
        return self.__displayText

    def inverse(self):
        return self.__invert_flag

#######################################################################################################################


class NodeTextItem(TextItem):
    def makeSelected(self, isSelected, isParent=False):
        if isSelected:
            if isParent:
                if not self.ref:
                    self.setDefaultTextColor(DiagramColor.greengray)
            else:
                self.setDefaultTextColor(DiagramColor.selectedColor)
        elif self.ref:
            self.setDefaultTextColor(DiagramColor.defaultRefColor)
        else:
            self.setDefaultTextColor(DiagramColor.defaultTextColor)

#######################################################################################################################
#######################################################################################################################

