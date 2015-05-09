# coding=utf-8
# -----------------
# file      : shapelib.py
# date      : 2013/03/17
# author    : Victor Zarubkin
# contact   : victor.zarubkin@gmail.com
# copyright : Copyright (C) 2013  Victor Zarubkin
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
__copyright__ = 'Copyright (C) 2013  Victor Zarubkin'
__credits__ = ['Victor Zarubkin']
__license__ = ['GPLv3']
__version__ = '1.3.0'  # this is last application version when this script file was changed
__email__ = 'victor.zarubkin@gmail.com'
############################################################################

import os
from xml.dom.minidom import parse

from PySide.QtCore import *
from PySide.QtGui import *
from PySide.QtSvg import QSvgRenderer

from auxtypes import toUnixPath, relativePath, absPath

############################################################################

_defaultScale = 0.75

#######################################################################################################################
#######################################################################################################################


class PPRenderer(object):
    def __init__(self, path, scale=_defaultScale):
        self.__isInit = False
        self.__viewbox = QRect()
        self.__viewboxF = QRectF()
        self.__path = QPainterPath()
        self.__path.setFillRule(Qt.WindingFill)
        self.__scale = scale
        self.__parse(path)

    def isInit(self):
        return bool(self.__isInit)

    def viewBox(self):
        return self.__viewbox

    def viewBoxF(self):
        return self.__viewboxF

    def render(self, painter, vbox=None):
        if self.__isInit:
            painter.drawPath(self.__path)

    def icon(self, color):
        if self.__isInit:
            # create QIcon:
            pixmap = QPixmap(self.__path.boundingRect().size().toSize())
            pixmap.fill(Qt.transparent)
            pen = QPen(Qt.black, 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            if color is None:
                br = QBrush(QColor(255, 128, 32, 224))
            else:
                br = QBrush(color)
            painter = QPainter(pixmap)
            painter.setPen(pen)
            painter.setBrush(br)
            painter.translate(-self.__path.boundingRect().topLeft())
            painter.drawPath(self.__path)
            painter.end()
            return QIcon(pixmap)
        return None

    def setPainterPath(self, painterPath, scale=None):
        self.__path = painterPath
        if scale is not None:
            self.__scale = scale
        self.__isInit = True
        self.__viewboxF = self.__path.boundingRect()
        self.__viewbox = QRect(QPoint(self.__viewboxF.top(), self.__viewboxF.left()),
                               QPoint(self.__viewboxF.bottom(), self.__viewboxF.right()))

    def __parse(self, thisFile):
        painterPath = QPainterPath()
        painterPath.setFillRule(Qt.WindingFill)
        if os.path.exists(thisFile):
            dom = parse(thisFile)
            dataAll = dom.getElementsByTagName('painter_path')
            if dataAll:
                data = dataAll[0]
                subroutines = data.getElementsByTagName('draw')
                if subroutines:
                    minX = 99999.0
                    maxX = -99999.0
                    minY = 99999.0
                    maxY = -99999.0
                    for sub in subroutines:
                        if sub.hasAttribute('call') and sub.hasAttribute('x') and sub.hasAttribute('y'):
                            method = sub.getAttribute('call')
                            x = float(sub.getAttribute('x')) * self.__scale
                            y = float(sub.getAttribute('y')) * self.__scale
                            maxX = max(maxX, x)
                            minX = min(minX, x)
                            maxY = max(maxY, y)
                            minY = min(minY, y)
                            if method == 'addText':
                                if sub.hasAttribute('size'):
                                    fontSize = int(float(sub.getAttribute('size')) * self.__scale)
                                else:
                                    fontSize = 20
                                text = sub.getAttribute('text')
                                font = QFont('CourierNew', fontSize)
                                fontRect = QFontMetrics(font).boundingRect(text)
                                painterPath.addText(QPointF(x, y) - QPointF(fontRect.center()), font, text)
                            elif method == 'addEllipse':
                                w = float(sub.getAttribute('w')) * self.__scale
                                h = float(sub.getAttribute('h')) * self.__scale
                                maxX = max(maxX, x + w)
                                maxY = max(maxY, y + h)
                                eval("painterPath.{0}".format(method))(x, y, w, h)
                            else:
                                eval("painterPath.{0}".format(method))(x, y)
                            self.__isInit = True
                    if self.__isInit:
                        self.__viewbox = QRect(QPoint(int(minX), int(minY)), QPoint(int(maxX), int(maxY)))
                        self.__viewboxF = QRectF(QPointF(minX, minY), QPointF(maxX, maxY))
        self.__path = painterPath


class VecShape(object):
    vertical = 1
    horizontal = 2

    def __init__(self, name, signPath='', scale=_defaultScale):
        self.__scale = scale
        self.__name = name

        if signPath:
            substrings = signPath.split('.')
            last = len(substrings) - 1
            if substrings[last] == 'pp' or substrings[last] == 'PP':
                self.__sign = PPRenderer(signPath, scale)
            else:
                self.__sign = QSvgRenderer(signPath)
        else:
            self.__sign = PPRenderer('', scale)
            path = QPainterPath()
            path.moveTo(-16.0 * scale, -16.0 * scale)
            path.lineTo(16.0 * scale, -16.0 * scale)
            path.lineTo(16.0 * scale, 16.0 * scale)
            path.lineTo(-16.0 * scale, 16.0 * scale)
            path.lineTo(-16.0 * scale, -16.0 * scale)
            self.__sign.setPainterPath(path)

        self.verticalBoundPoints = []
        self.horizontalBoundPoints = []
        self.__textPoint = QPointF()

    def name(self):
        return self.__name

    def addPoint(self, boundPoint=QPointF(), shapeType=vertical):
        if shapeType == VecShape.vertical:
            self.verticalBoundPoints.append(boundPoint * self.__scale)
            if boundPoint.y() > self.__textPoint.y():
                self.__textPoint.setY(boundPoint.y())
        else:
            self.horizontalBoundPoints.append(boundPoint)

    def textPoint(self, pos, textW):
        return QPointF(pos.x() + self.__textPoint.x() - textW * 0.5,
                       pos.y() + self.__textPoint.y() - 5.0 / self.__scale)

    def connectors(self, height, viewType=vertical):
        if viewType == VecShape.vertical:
            points = []
            for p in self.verticalBoundPoints:
                h = 0.0
                if p.y() > 0.0:
                    h = height * 0.9  # *self.scale
                point = QPointF(p.x(), p.y() + h)
                points.append(point)
            return points
        return self.horizontalBoundPoints

    def boundingRect(self, width, height, ex=False):
        if ex:
            return QRectF(QPointF(-width * 0.5, -height * 0.5), QPointF(width * 0.5, height * 0.5))
        W = 0.5 * (max(width, self.__sign.viewBoxF().width()))
        H = 0.5 * self.__sign.viewBoxF().height()
        return QRectF(QPointF(-W, -H), QPointF(W, H + height * 0.5))

    def shape(self, width, height, ex=False):
        path = QPainterPath()
        # path.addRect(QRectF(-self.__sign.viewBoxF().width()*0.5, -self.
        #              __sign.viewBoxF().height()*0.5, self.__sign.viewBoxF().width(), self.__sign.viewBoxF().height()))
        path.addRect(QRectF(self.__sign.viewBoxF()))
        return path

    def paint(self, painter):
        # viewBox = QRectF(QPointF(-self.__sign.viewBoxF().width()*0.5, -self.__sign.viewBoxF().height()*0.5),
        #                  QSizeF(self.__sign.viewBoxF().width(), self.__sign.viewBoxF().height()))
        self.__sign.render(painter, QRectF(self.__sign.viewBoxF()))

    def paintBackground(self, painter):
        if isinstance(self.__sign, PPRenderer):
            self.__sign.render(painter)

    def icon(self, color):
        if isinstance(self.__sign, PPRenderer):
            return self.__sign.icon(color)
        return None

#######################################################################################################################
#######################################################################################################################


def defaultShape():
    defaultShp = VecShape('default')
    defaultShp.addPoint(QPointF(-16.0, 0.0), VecShape.horizontal)
    defaultShp.addPoint(QPointF(16.0, 0.0), VecShape.horizontal)
    defaultShp.addPoint(QPointF(0.0, -16.0), VecShape.vertical)
    defaultShp.addPoint(QPointF(0.0, 16.0), VecShape.vertical)
    return defaultShp


class ShapeLib(object):
    def __init__(self, inputFile=''):
        self.path = ''
        self.resdir = ''
        self.shapes = dict()
        self.shapes['default'] = defaultShape()
        if inputFile:
            self.init(inputFile)

    # operator 'in':
    def __contains__(self, item):
        return item in self.shapes

    # operator '[]':
    def __getitem__(self, item):
        if item in self.shapes:
            return self.shapes[item]
        return None

    def defaultShape(self):
        return self.shapes['default']

    def init(self, shapesFile):
        global _defaultScale
        print('INFO: loading shapes from \"{0}\"'.format(shapesFile))

        if os.path.exists(shapesFile):
            dom = parse(shapesFile)
            data = dom.getElementsByTagName('ShapeData')

            if data:
                resourceOk = False

                resdir = ''
                shapePath = ''
                if data[0].hasAttribute('path'):
                    path = absPath(data[0].getAttribute('path'), shapesFile, True)
                    if path is not None and path:
                        resdir = path
                        shapePath = '/'.join([resdir, 'square.pp'])
                        if os.path.exists(shapePath):
                            resourceOk = True

                if resourceOk:
                    self.shapes.clear()

                    self.shapes['default'] = VecShape('default', shapePath, _defaultScale)
                    self.shapes['default'].addPoint(QPointF(-16.0, 0.0), VecShape.horizontal)
                    self.shapes['default'].addPoint(QPointF(16.0, 0.0), VecShape.horizontal)
                    self.shapes['default'].addPoint(QPointF(0.0, -16.0), VecShape.vertical)
                    self.shapes['default'].addPoint(QPointF(0.0, 16.0), VecShape.vertical)

                    shapes = data[0].getElementsByTagName('VecShape')  # data[0].getElementsByTagName('Shape')
                    for shape in shapes:
                        # self.readPolyShape(shape)
                        self.readVecShape(shape, resdir)

                    res = len(self.shapes) > 1
                    if res:
                        self.path = shapesFile
                        self.resdir = resdir

                    return res
                print('ERROR: Resource dir for shapes file \"{0}\" is broken!'.format(shapesFile))
                print('')
            else:
                print('ERROR: Shapes file has no header \"ShapeData\"!')
                print('')
        else:
            print('ERROR: shapes file \"{0}\" does not exist!'.format(shapesFile))
            print('')
        return False

    def readVecShape(self, shape, resdir):
        if not shape.hasAttribute('Name') or not shape.hasAttribute('Sign'):
            return

        shapeName = shape.getAttribute('Name')
        if not shapeName or shapeName in self.shapes:
            return

        signFile = shape.getAttribute('Sign')
        signPath = '/'.join([resdir, signFile])
        if not os.path.exists(signPath):
            return

        scale = 1.0
        if shape.hasAttribute('Scale'):
            scale = float(shape.getAttribute('Scale'))

        self.shapes[shapeName] = VecShape(shapeName, signPath, scale)

        bounds = shape.getElementsByTagName('ConnectorPoints')
        for bound in bounds:
            horizPoint = QPointF()
            if bound.hasAttribute('hor_x'):
                horizPoint.setX(float(bound.getAttribute('hor_x')))
            if bound.hasAttribute('hor_y'):
                horizPoint.setY(float(bound.getAttribute('hor_y')))

            vertiPoint = QPointF()
            if bound.hasAttribute('vert_x'):
                vertiPoint.setX(float(bound.getAttribute('vert_x')))
            if bound.hasAttribute('vert_y'):
                vertiPoint.setY(float(bound.getAttribute('vert_y')))

            self.shapes[shapeName].addPoint(horizPoint, VecShape.horizontal)
            self.shapes[shapeName].addPoint(vertiPoint, VecShape.vertical)

#######################################################################################################################
#######################################################################################################################
