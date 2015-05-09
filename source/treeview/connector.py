# coding=utf-8
# -----------------
# file      : connector.py
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

from __future__ import unicode_literals

__author__ = 'Victor Zarubkin'
__copyright__ = 'Copyright (C) 2012  Victor Zarubkin'
__credits__ = ['Victor Zarubkin']
__license__ = ['GPLv3']
__version__ = '1.3.0'  # this is last application version when this script file was changed
__email__ = 'victor.zarubkin@gmail.com'
############################################################################

from math import sin, cos, acos, pi

from PySide import QtCore
from PySide.QtGui import *
from PySide.QtCore import *

from .dispregime import DisplayRegime
from .colors import DiagramColor

import globals

#######################################################################################################################
#######################################################################################################################


class ConnectorType(object):
    Curve = 1
    Line = 2
    Polyline = 3
    __available = (Curve, Line, Polyline)

    convTab = {
        'Curved': Curve,
        'curved': Curve,
        'Curve': Curve,
        'curve': Curve,
        'Line': Line,
        'line': Line,
        'Polyline': Polyline,
        'polyline': Polyline,
        'Poly': Polyline,
        'poly': Polyline
    }

    def __init__(self, ctype=Polyline):
        self.__type = ConnectorType.Polyline
        if type(ctype) is ConnectorType:
            self.__type = ctype.val
        elif ctype in self.__available:
            self.__type = ctype

    @property
    def val(self):
        return self.__type

    @val.setter
    def val(self, value):
        if type(value) is ConnectorType:
            self.__type = value.val
        elif value in self.__available:
            self.__type = value

    def __eq__(self, other):
        if type(other) is ConnectorType:
            return self.__type == other.val
        return self.__type == other

    def __ne__(self, other):
        return not self.__eq__(other)


def _createHighlight(color):
    effect = QGraphicsDropShadowEffect()
    effect.setColor(color)
    effect.setOffset(0, 0)
    effect.setBlurRadius(15)
    return effect


class Connector(QGraphicsLineItem):
    defaultZLevel = -2000.0
    activeZLevel = -1000.0
    defaultColor = DiagramColor.defaultTextColor

    def __init__(self, parentScene, startItem, endItem, parent=None, scene=None):
        QGraphicsLineItem.__init__(self, parent, scene)
        self._scene = parentScene

        self._highlighted = False
        self._highlight = _createHighlight(DiagramColor.selectedColor)
        self.setGraphicsEffect(self._highlight)
        self._highlight.setEnabled(False)

        self.lineType = ConnectorType(ConnectorType.Polyline)
        self.lineType.val = parentScene.connectorType

        self.setFlag(QGraphicsItem.ItemIsSelectable, False)
        self._bold = False
        self._explicitWidth = 1
        self._scale = 1.0
        pen = QPen(Connector.defaultColor, self._explicitWidth, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        # pen.setCosmetic(True)
        self.setPen(pen)

        self.__beginPoint = QPointF()
        self.__endPoint = QPointF()
        self.__ellipsePoint = QPointF()
        self.__drawPath = QPainterPath()

        self.startItem = None
        self.endItem = None
        self.bind(startItem, endItem)

        parentScene.connectorWidthScaleF.connect(self.setLineWidthScaleF)
        parentScene.connectorTypeChanged.connect(self.setType)

        globals.optionsSignals.connectorHighlightingChanged.connect(self.toggleHighlight)
        globals.optionsSignals.connectorsBoldChanged.connect(self.toggleBold)

        self.setZValue(Connector.defaultZLevel)

    def bind(self, start, end):
        self.unbind()
        self.startItem = start
        self.endItem = end
        self.updatePosition()

    def unbind(self):
        self.startItem = None
        self.endItem = None

    def setColor(self, color):
        pen = self.pen()
        pen.setColor(color)
        self.setPen(pen)

    def setBold(self, bold):
        self._bold = bold
        if globals.connectorsBold:
            self._explicitWidth = 2 if bold else 1
            self.setLineWidthScaleF(self._scale)

    def setHighlight(self, enabled, color=None):
        self._highlighted = enabled
        self._highlight.setEnabled(enabled and globals.connectorsHighlight)
        if enabled and color is not None:
            self._highlight.setColor(color)

    @QtCore.Slot(bool)
    def toggleHighlight(self, enabled):
        if enabled:
            self._highlight.setEnabled(self._highlighted)
        else:
            self._highlight.setEnabled(False)

    @QtCore.Slot(bool)
    def toggleBold(self, enabled):
        if self._bold:
            self._explicitWidth = 2 if enabled else 1
            self.setLineWidthScaleF(self._scale)

    @QtCore.Slot(float)
    def setLineWidthScaleF(self, scale):
        self._scale = scale
        pen = self.pen()
        if scale < 1.001:
            pen.setWidth(self._explicitWidth)
        else:
            pen.setWidthF(float(self._explicitWidth) * scale)
        self.setPen(pen)
        self.updatePosition()

    @QtCore.Slot(int)
    def setType(self, connectorType):
        self.lineType.val = connectorType
        if self.startItem is not None and self.endItem is not None:
            self.__calcPath()
            if self._highlighted and globals.connectorsHighlight:
                self._highlight.setEnabled(False)
                self._scene.connectorTypeChangeFinish.connect(self._finishTypeChange)

    @QtCore.Slot()
    def _finishTypeChange(self):
        self._highlight.setEnabled(True)
        self._scene.connectorTypeChangeFinish.disconnect(self._finishTypeChange)

    def shape(self):
        return self.__drawPath

    def paint(self, painter, option, widget):
        if self.isVisible() and not self.startItem.collidesWithItem(
                self.endItem) and self.startItem.isVisible() and self.endItem.isVisible():
            if self.lineType == ConnectorType.Curve or self.lineType == ConnectorType.Line:
                painter.setRenderHint(QPainter.Antialiasing)
            painter.setPen(self.pen())
            painter.drawPath(self.shape())
        # painter.setBrush(self.pen().color())
        # painter.drawEllipse(self.__ellipsePoint,self.pen().width()+1,self.pen().width()+1)

    def updatePosition(self):
        if self.startItem is not None and self.endItem is not None:
            line = QLineF(self.mapFromItem(self.startItem, 0, 0), self.mapFromItem(self.endItem, 0, 0))
            self.setLine(line)
            self.__specifyPoints()
            self.__calcPath()

    def __specifyPoints(self):
        if self.startItem.scene().regime == DisplayRegime.Horizontal:
            startPoints = self.startItem.connectorPoints()  # [:2]
            endPoints = self.endItem.connectorPoints()  # [:2]
        else:
            startPoints = self.startItem.connectorPoints()  # [2:]
            endPoints = self.endItem.connectorPoints()  # [2:]

        minDist = 999999.0
        for beginP in startPoints:
            for endP in endPoints:
                line = QLineF(self.mapFromItem(self.startItem, beginP), self.mapFromItem(self.endItem, endP))
                dist = line.length()
                if dist < minDist:
                    self.__beginPoint = line.p1()
                    self.__endPoint = line.p2()
                    minDist = dist

        line = QLineF(self.mapFromItem(self.endItem, 0, 0), self.__endPoint)
        direction = line.unitVector()
        self.__ellipsePoint.setX(self.__endPoint.x() + direction.dx() * (self.pen().width() + 1))
        self.__ellipsePoint.setY(self.__endPoint.y() + direction.dy() * (self.pen().width() + 1))

    def __calcPath(self):
        self.__drawPath = QPainterPath()

        if self.startItem.scene().regime == DisplayRegime.Horizontal:
            p1 = QPointF(self.__endPoint.x() * 0.5 + self.__beginPoint.x() * 0.5, self.__beginPoint.y())
            p2 = QPointF(self.__beginPoint.x() * 0.5 + self.__endPoint.x() * 0.5, self.__endPoint.y())
        else:
            p2 = QPointF(self.__endPoint.x(), self.__beginPoint.y() * 0.5 + self.__endPoint.y() * 0.5)
            p1 = QPointF(self.__beginPoint.x(), self.__endPoint.y() * 0.5 + self.__beginPoint.y() * 0.5)

        self.__drawPath.moveTo(self.__beginPoint)
        if self.lineType == ConnectorType.Curve:
            self.__drawPath.cubicTo(p1, p2, self.__endPoint)
        elif self.lineType == ConnectorType.Line:
            self.__drawPath.lineTo(self.__endPoint)
        elif self.lineType == ConnectorType.Polyline:
            self.__drawPath.lineTo(p1)
            self.__drawPath.lineTo(p2)
            self.__drawPath.lineTo(self.__endPoint)

#######################################################################################################################
#######################################################################################################################


class ConnectorArrow(QGraphicsLineItem, QObject):
    def __init__(self, parentScene, startPos, endPos, parent=None, scene=None):
        QGraphicsLineItem.__init__(self, parent, scene)
        QObject.__init__(self)

        if globals.itemsShadow:
            self.__shadow = QGraphicsDropShadowEffect()
            self.__shadow.setColor(QColor(0, 0, 0, 128))
            self.__shadow.setOffset(-8, 8)
            self.__shadow.setBlurRadius(8)
            self.setGraphicsEffect(self.__shadow)
        else:
            self.__shadow = None

        self.parentScene = parentScene
        self.setFlag(QGraphicsItem.ItemIsSelectable, False)
        self.setPen(QPen(Qt.red, 1, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        self.startItem = None
        self.endItem = None
        self.start = QPointF(startPos)
        self.end = QPointF(endPos)
        self.setLine(QLineF(self.start, self.end))
        self.setZValue(1000.0)
        self.__arrowPolygon = self.__arrow()

    def setStartItem(self, item):
        if item is None or self.startItem is None or item != self.startItem:
            if self.startItem is not None and self.endItem != self.startItem:
                self.startItem.connectionParticipate(False)
            self.startItem = item
            if self.startItem is not None:
                self.startItem.connectionParticipate(True)

    def setEndItem(self, item):
        if item is None or self.endItem is None or item != self.endItem:
            if self.endItem is not None and self.endItem != self.startItem:
                self.endItem.connectionParticipate(False)
            self.endItem = item
            if self.endItem is not None:
                self.endItem.connectionParticipate(True)

    def cancel(self):
        if self.startItem is not None:
            self.startItem.connectionParticipate(False)
        if self.endItem is not None:
            self.endItem.connectionParticipate(False)
        self.startItem = None
        self.endItem = None

    def finish(self):
        if self.endItem == self.startItem:
            self.cancel()
            return

        if self.startItem is not None:
            self.startItem.connectionParticipate(False)
        if self.endItem is not None:
            self.endItem.connectionParticipate(False)

        if self.endItem is None:
            parent = self.startItem.parentNode()
            if parent is not None and parent.node is not None:
                t = parent.node.type()
                if t is not None:
                    link = t.isLink()
                else:
                    link = False
            else:
                link = False
            if not link:
                self.startItem.disconnectParent()
            self.startItem = None
            return

        if self.parentScene.regime == DisplayRegime.Horizontal:
            if self.line().dx() > 0:
                parentItem = self.startItem
                childItem = self.endItem
            else:
                parentItem = self.endItem
                childItem = self.startItem
        elif self.line().dy() > 0:
            parentItem = self.startItem
            childItem = self.endItem
        else:
            parentItem = self.endItem
            childItem = self.startItem

        self.startItem = None
        self.endItem = None

        if parentItem is None or childItem is None:
            return

        if not parentItem.editable() or not childItem.draggable() or parentItem.node is None or childItem.node is None:
            return

        parentType = parentItem.node.type()
        if parentType.isLink():
            return

        parentDesc = parentItem.node.nodeDesc()
        if parentDesc is None:
            return

        if childItem.node.nodeClass not in parentDesc.childClasses:
            return

        childParent = childItem.parentNode()
        if childParent is not None and childParent.node is not None:
            t = childParent.node.type()
            if t is not None and t.isLink():
                return

        nodeChildren = parentItem.node.children(childItem.node.nodeClass)
        if childItem.node in nodeChildren:
            if childItem not in parentItem.childrenList():
                parentItem.addChild(childItem, nodeChildren.index(childItem.node))
        else:
            childParams = parentType.child(childItem.node.nodeClass)
            if len(nodeChildren) >= childParams.max:
                # too many children, remove one if it is not connected to parentItem
                if len(parentItem.childrenList()) == 0:
                    for node in nodeChildren:
                        if parentItem.node.removeChild(node):
                            break
                else:
                    for item in parentItem.childrenList():
                        if item.parentNode() is None and item.node is not None and item.node in nodeChildren:
                            parentItem.node.removeChild(item.node)
                            break

            if len(nodeChildren) >= childParams.max:
                return

            if childParent is not None:
                childParent.removeChild(childItem, False)

            # if childItem.node.parent() is not None:
            #     childItem.node.parent().removeChild(childItem.node)

            i = 99999
            k = 0
            myPos = childItem.pos()
            children = parentItem.childrenByClass(childItem.node.nodeClass)

            for item in children:
                itemPos = item.pos()
                if self.parentScene.regime == DisplayRegime.Vertical:
                    if itemPos.x() > myPos.x():
                        i = k
                        break
                elif self.parentScene.regime == DisplayRegime.Horizontal:
                    if itemPos.y() > myPos.y():
                        i = k
                        break
                k += 1

            parentItem.node.addChild(childItem.node, i)
            parentItem.addChild(childItem, i)

    def setStart(self, startPos):
        self.start = QPointF(startPos)
        self.setLine(QLineF(self.start, self.end))
        self.__arrowPolygon = self.__arrow()

    def setEnd(self, endPos):
        self.end = QPointF(endPos)
        self.setLine(QLineF(self.start, self.end))
        self.__arrowPolygon = self.__arrow()

    def setStartEnd(self, startPos, endPos):
        self.start = QPointF(startPos)
        self.end = QPointF(endPos)
        self.setLine(QLineF(self.start, self.end))
        self.__arrowPolygon = self.__arrow()

    @QtCore.Slot(int)
    def onRegimeChange(self, regime):
        if self.isVisible():
            self.__arrowPolygon = self.__arrow()

    def __arrow(self):
        lineLength = self.line().length()
        if lineLength < 0.001:
            return QPolygonF()

        angle = acos(self.line().dx() / lineLength)
        if self.line().dy() >= 0.0:
            angle = pi * 2.0 - angle

        arrowAngle = pi * 0.4
        arrowSize = 10.0

        origin = self.line().p2()
        k = 1.0
        if self.parentScene.regime == DisplayRegime.Horizontal:
            if self.line().dx() < 0:
                origin = self.line().p1()
                k = -1.0
        elif self.line().dy() < 0:
            origin = self.line().p1()
            k = -1.0

        arrowP1 = origin - k * QPointF(sin(angle + arrowAngle) * arrowSize,
                                       cos(angle + arrowAngle) * arrowSize)

        arrowP2 = origin - k * QPointF(sin(angle + pi - arrowAngle) * arrowSize,
                                       cos(angle + pi - arrowAngle) * arrowSize)

        return QPolygonF([origin, arrowP1, arrowP2])

    def paint(self, painter, option, widget):
        if self.isVisible():
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setPen(self.pen())
            painter.drawLine(self.line())
            painter.setBrush(self.pen().color())
            # painter.drawEllipse(self.end,self.pen().width()+1,self.pen().width()+1)
            if self.line().length() > 0.001:
                painter.drawPolygon(self.__arrowPolygon)

#######################################################################################################################
#######################################################################################################################
