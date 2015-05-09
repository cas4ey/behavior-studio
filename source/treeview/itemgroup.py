# coding=utf-8
# -----------------
# file      : itemgroup.py
# date      : 2012/09/30
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

from .diagram import *
from .dispregime import DisplayRegime, GroupType, AlignType

######################################################################################################################
######################################################################################################################

DEFAULT_INTERVAL = 15
DEFAULT_GROUP_INTERVAL = 35


class ItemGroup(object):
    __displayTypes = [GroupType.VerticalGroup, GroupType.HorizontalGroup]

    def __init__(self, scene, parentItem, itemInterval, groupInterval):
        self.__scene = scene
        self.__parentItem = parentItem
        self.__items = []
        self.__type = GroupType.VerticalGroup
        if scene.regime == DisplayRegime.Vertical:
            self.__type = GroupType.HorizontalGroup

        self.itemInterval = DEFAULT_INTERVAL
        self.groupInterval = DEFAULT_GROUP_INTERVAL
        self.setInterval(itemInterval, groupInterval)

        self.__margin = 0.0
        self.__height = 0.0
        self.__width = 0.0

        self.__iter = int(0)

    def items(self):
        return self.__items

    def isVisible(self):
        for item in self.__items:
            if item.isVisible():
                return True
        return False

    def depth(self):
        if not self.isVisible():
            return int(0)
        d = int(1)
        for item in self.__items:
            if item.isVisible():
                if item.childrenGroup() is not None:
                    d = max(d, item.childrenGroup().depth() + int(1))
        return d

    def __firstVisible(self):
        self.__iter = int(0)
        for item in self.__items:
            if item.isVisible():
                return item
            self.__iter += int(1)
        return None

    def __nextVisible(self):
        self.__iter += int(1)
        while self.__iter < len(self.__items):
            item = self.__items[self.__iter]
            if item.isVisible():
                return item
            self.__iter += int(1)
        return None

    def empty(self):
        return len(self.__items) == 0

    def parentItem(self):
        return self.__parentItem

    def setParentItem(self, parentItem):
        self.__parentItem = parentItem

    def type(self):
        return self.__type

    @QtCore.Slot(int)
    def setType(self, displayType):
        if self.__type != displayType and displayType in ItemGroup.__displayTypes:
            self.__type = displayType

    @QtCore.Slot(int)
    def onRegimeChange(self, regime):
        if regime == DisplayRegime.Horizontal:
            self.setType(GroupType.VerticalGroup)
        elif regime == DisplayRegime.Vertical:
            self.setType(GroupType.HorizontalGroup)

    @QtCore.Slot(int, int)
    def setInterval(self, itemInterval, groupInterval):
        if itemInterval <= 0:
            itemInterval = DEFAULT_INTERVAL
        if groupInterval <= 0:
            groupInterval = DEFAULT_GROUP_INTERVAL
        self.itemInterval = itemInterval
        self.groupInterval = groupInterval

    def margin(self):
        return self.__margin

    def itemsHeight(self):
        return self.__height

    def itemsWidth(self):
        return self.__width

    def calcMargins(self):
        theMargin = 0.0
        maxH = -999999.0
        maxW = -999999.0

        n = 0
        for item in self.__items:
            if not item.isVisible():
                continue

            if item.childrenGroup() is not None:
                item.childrenGroup().calcMargins()

            itemH = item.height()
            itemW = item.width()

            if itemW > maxW:
                maxW = itemW
            if itemH > maxH:
                maxH = itemH

            if self.__type == GroupType.VerticalGroup:
                theMargin += itemH
            else:
                theMargin += itemW

            if n != 0:
                theMargin += self.itemInterval

            n += 1

        if n == 0:
            self.__margin = 0.0
            self.__height = 0.0
            self.__width = 0.0
        else:
            self.__margin = theMargin
            if self.__type == GroupType.VerticalGroup:
                self.__width = maxW
                self.__height = theMargin
            else:
                self.__width = theMargin
                self.__height = maxH

    def width(self, d=999999):
        if d < 1:
            return 0.0
        if d > 999990:
            return self.__width
        n = 0
        w = 0.0
        if self.__type == GroupType.VerticalGroup:
            d = int(1)
        for item in self.__items:
            if not item.isVisible():
                continue
            w += item.width(d)
            if n != 0:
                w += self.itemInterval
            n += 1
        return w

    def height(self, d=999999):
        if d < 1:
            return 0.0
        if d > 999990:
            return self.__height
        n = 0
        h = 0.0
        if self.__type == GroupType.HorizontalGroup:
            d = int(1)
        for item in self.__items:
            if not item.isVisible():
                continue
            h += item.height(d)
            if n != 0:
                h += self.itemInterval
            n += 1
        return h

    def calculateMinWidth(self):
        if self.__type == GroupType.VerticalGroup:
            return self.itemsWidth()
        items_number = len(self.__items)
        if items_number < 1:
            return 0.0
        theSize = 0.0
        dpth = self.__items[0].depth()
        d = dpth
        for i in range(items_number):
            current_item = self.__items[i]
            if not current_item.isVisible():
                continue
            j = i + 1
            if j < items_number:
                next_item = self.__items[j]
                dpth_n = next_item.depth()
                d, dpth = min(dpth, dpth_n), dpth_n
            theSize += current_item.width(d)
            if i != 0:
                theSize += self.itemInterval
        return theSize

    def calculateMinHeight(self):
        if self.__type == GroupType.HorizontalGroup:
            return self.itemsHeight()
        items_number = len(self.__items)
        if items_number < 1:
            return 0.0
        theSize = 0.0
        dpth = self.__items[0].depth()
        d = dpth
        for i in range(items_number):
            current_item = self.__items[i]
            if not current_item.isVisible():
                continue
            j = i + 1
            if j < items_number:
                next_item = self.__items[j]
                dpth_n = next_item.depth()
                d, dpth = min(dpth, dpth_n), dpth_n
            theSize += current_item.height(d)
            if i != 0:
                theSize += self.itemInterval
        return theSize

    def moveTo(self, x, y):
        if not self.isVisible():
            return

        item = self.__firstVisible()

        if item is None:
            return

        pos = QPointF(x, y)
        if self.__type == GroupType.VerticalGroup:
            minSize = self.itemsHeight()  # self.calculateMinHeight()
            pos.setY(y - minSize * 0.5)
        else:
            minSize = self.itemsWidth()  # self.calculateMinWidth()
            pos.setX(x - minSize * 0.5)

        first = True
        dpth = item.depth()
        while item is not None:
            nextItem = self.__nextVisible()
            if nextItem is not None:
                dpth_n = nextItem.depth()
                d, dpth = min(dpth, dpth_n), dpth_n
            else:
                d = dpth

            if first:
                if self.__type == GroupType.VerticalGroup:
                    pos.setY(pos.y() + item.height() * 0.5)
                else:
                    pos.setX(pos.x() + item.width() * 0.5)
                first = False

            # Align item:
            itemPos = QPointF(pos.x(), pos.y())
            if True:
                pass
            elif self.__type == GroupType.VerticalGroup:
                # align to left/right
                if not (self.__scene.alignment() & AlignType.CenterH):
                    w = item.boundingRect().width()
                    dw = (self.itemsWidth() - w) * 0.5
                    if dw > 0.001:
                        if self.__scene.alignment() & AlignType.Right:
                            itemPos.setX(pos.x() + dw)  # align to right
                        else:
                            itemPos.setX(pos.x() - dw)  # align to left
            else:
                # align to top/bottom
                if not (self.__scene.alignment() & AlignType.CenterV):
                    h = item.boundingRect().height()
                    dh = (self.itemsHeight() - h) * 0.5
                    if dh > 0.001:
                        if self.__scene.alignment() & AlignType.Bottom:
                            itemPos.setY(pos.y() + dh)  # align to bottom
                        else:
                            itemPos.setY(pos.y() - dh)  # align to top

            # Move item to specified position:
            childrenPos = QPointF(pos)
            if not item.autoPositioningMode() and item.parentNode() is not None:
                itemPos = item.parentNode().posRequired() + item.deltaPos()
                item.moveTo(itemPos.x(), itemPos.y())
                childrenPos = itemPos
            else:
                item.moveTo(itemPos.x(), itemPos.y())
                item.calculateDeltaPos()

            # Calculate next item position:
            if self.__type == GroupType.VerticalGroup:
                if item.childrenGroup().isVisible():
                    moveX = childrenPos.x() + self.itemsWidth() * 0.5 + self.groupInterval \
                        + item.childrenGroup().itemsWidth() * 0.5
                    item.childrenGroup().moveTo(moveX, childrenPos.y())
                pos.setY(pos.y() + item.height() * 0.5)  # + self.itemInterval)
            else:
                if item.childrenGroup().isVisible():
                    moveY = childrenPos.y() + self.itemsHeight() * 0.5 \
                        + self.groupInterval + item.childrenGroup().itemsHeight() * 0.5
                    item.childrenGroup().moveTo(childrenPos.x(), moveY)
                pos.setX(pos.x() + item.width() * 0.5)  # + self.itemInterval)

            if nextItem is not None:
                if self.__type == GroupType.VerticalGroup:
                    pos.setY(pos.y() + self.itemInterval + nextItem.height() * 0.5)
                else:
                    pos.setX(pos.x() + self.itemInterval + nextItem.width() * 0.5)

            item = nextItem

    def update(self):
        if not self.isVisible():
            return
        pos = QPointF()
        n = 0
        item = self.__firstVisible()
        while item is not None:
            n += 1
            pos += item.pos()
            item = self.__nextVisible()
        pos /= float(n)
        self.moveTo(pos.x(), pos.y())

    def fullUpdate(self):
        p = self.__parentItem
        while p is not None and p.parentNode() is not None:
            p = p.parentNode()
        if p is not None:
            p.itemGroup().calcMargins()
            p.itemGroup().moveTo(p.posRequired().x(), p.posRequired().y())
        else:
            self.calcMargins()
            item = self.__firstVisible()
            if item is not None:
                self.moveTo(item.posRequired().x(), item.posRequired().y())

    def addItem(self, item, before=999999):
        if item not in self.__items:
            if before >= len(self.__items):
                self.__items.append(item)
            else:
                self.__items.insert(before, item)
            if item.itemGroup() != self:
                item.setItemGroup(self)
                item.setAutoPositioningMode(True, DisplayRegime.Horizontal)
                item.setAutoPositioningMode(True, DisplayRegime.Vertical)
            if item.isVisible() and len(self.__items) > 1:
                self.fullUpdate()

    def removeItem(self, item):
        if item in self.__items:
            wasVisible = item.isVisible()
            self.__items.remove(item)
            if item.itemGroup() == self:
                item.setItemGroup(None)
            if wasVisible and len(self.__items) > 0:
                self.fullUpdate()

    def moveItemBack(self, item):
        if item in self.__items:
            i = self.__items.index(item)
            if i > 0:
                prevItem = self.__items[i - 1]
                self.__items[i - 1] = item
                self.__items[i] = prevItem
                if item.isVisible() and prevItem.isVisible():
                    self.fullUpdate()

    def moveItemForward(self, item):
        if item in self.__items:
            i = self.__items.index(item)
            if i < (len(self.__items) - 1):
                nextItem = self.__items[i + 1]
                self.__items[i + 1] = item
                self.__items[i] = nextItem
                if item.isVisible() and nextItem.isVisible():
                    self.fullUpdate()

#######################################################################################################################
#######################################################################################################################
