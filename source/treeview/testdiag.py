# coding=utf-8
# -----------------
# file      : testdiag.py
# date      : 2012/11/24
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
__version__ = '1.2.5'  # this is last application version when this script file was changed
__email__ = 'victor.zarubkin@gmail.com'
############################################################################

from PySide.QtGui import *
from PySide.QtCore import *

import math

#######################################################################################################################
#######################################################################################################################


class DiagramItem(QGraphicsPolygonItem):
    def __init__(self, parent=None, scene=None):
        super(DiagramItem, self).__init__(parent, scene)
        self.arrows = []

        self.myPolygon = QPolygonF(
            [QPointF(-100, 0), QPointF(0, 100), QPointF(100, 0), QPointF(0, -100), QPointF(-100, 0)])

        self.setPolygon(self.myPolygon)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)

    def removeConnector(self, arrow):
        if arrow in self.arrows:
            self.arrows.remove(arrow)

    def removeConnectors(self):
        for arrow in self.arrows:
            arrow.startItem.removeConnector(arrow)
            arrow.endItem.removeConnector(arrow)
            self.scene().removeItem(arrow)
        size = len(self.arrows)
        for i in range(size):
            self.arrows.pop()

    def addConnector(self, arrow):
        self.arrows.append(arrow)

    def polygon(self):
        return self.myPolygon

    def image(self):
        pixmap = QPixmap(250, 250)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setPen(QPen(Qt.black, 8))
        painter.translate(125, 125)
        painter.drawPolyline(self.myPolygon)
        return pixmap

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            for arrow in self.arrows:
                arrow.updatePosition()
        return value

#######################################################################################################################
#######################################################################################################################


class Arrow(QGraphicsLineItem):
    def __init__(self, startItem, endItem, parent=None, scene=None):
        QGraphicsLineItem.__init__(self, parent, scene)
        self.startItem = startItem
        self.endItem = endItem

        self.setFlag(QGraphicsItem.ItemIsSelectable, True)

        self.myColor = Qt.black
        self.arrowHead = QPolygonF()
        self.setPen(QPen(self.myColor, 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))

    def boundingRect(self):
        extra = (self.pen().width() + 20.0) * 0.5
        return QRectF(self.line().p1(), QSizeF(self.line().p2().x() - self.line().p1().x(),
                                               self.line().p2().y() - self.line().p1().y())).normalized()\
            .adjusted(-extra, -extra, extra, extra)

    def shape(self):
        path = QGraphicsLineItem.shape(self)
        path.addPolygon(self.arrowHead)

    def setColor(self, color):
        self.myColor = color

    def updatePosition(self):
        line = QLineF(self.mapFromItem(self.startItem, 0, 0), self.mapFromItem(self.endItem, 0, 0))
        self.setLine(line)

    def paint(self, painter, option, widget=None):
        if not self.startItem.collidesWithItem(self.endItem):
            myPen = self.pen()
            myPen.setColor(self.myColor)
            arrowSize = 20.0
            painter.setPen(myPen)
            painter.setBrush(self.myColor)

            centerLine = QLineF(self.startItem.pos(), self.endItem.pos())
            endPolygon = self.endItem.polygon()
            p1 = endPolygon.first() + self.endItem.pos()
            intersectPoint = QPointF()

            for i in range(endPolygon.count()):
                p2 = endPolygon.at(i) + self.endItem.pos()
                polyLine = QLineF(p1, p2)
                res = polyLine.intersect(centerLine)
                intersectType = res[0]
                intersectPoint = res[1]
                if intersectType == QLineF.BoundedIntersection:
                    break
                p1 = p2

            self.setLine(QLineF(intersectPoint, self.startItem.pos()))

            angle = math.acos(self.line().dx() / self.line().length())
            if self.line().dy() >= 0.0:
                angle = (math.pi * 2.0) - angle

            arrowP1 = self.line().p1() + QPointF(math.sin(angle + math.pi / 3.0) * arrowSize,
                                                 math.cos(angle + math.pi / 3.0) * arrowSize)
            arrowP2 = self.line().p1() + QPointF(math.sin(angle + math.pi - math.pi / 3.0) * arrowSize,
                                                 math.cos(angle + math.pi - math.pi / 3.0) * arrowSize)

            self.arrowHead.clear()
            self.arrowHead = QPolygonF([self.line().p1(), arrowP1, arrowP2])

            painter.drawLine(self.line())
            painter.drawPolygon(self.arrowHead)

#######################################################################################################################
#######################################################################################################################
