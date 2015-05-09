# coding=utf-8
# -----------------
# file      : polyitem.py
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

"""

"""

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

from project.shapelib import VecShape

from compat_2to3 import *

from .itemgroup import ItemGroup
from .connector import Connector
from .textitem import TextItem, NodeTextItem
from .dispregime import DisplayRegime
from .colors import *

from language import trStr
import globals

from inspect import currentframe, getframeinfo


def createDebugTextItem():
    ti = TextItem(False, u'!')
    ti.setDefaultTextColor(DiagramColor.debugColor)
    ti.setBold(True)
    return ti


class ListAction(QAction):
    def __init__(self, scene, item, nodeClass, nodeType, text, parent=None):
        QAction.__init__(self, text, parent)
        self.triggered.connect(self.onClick)
        self.scene = scene
        self.item = item
        self.nodeClass = nodeClass
        self.nodeType = nodeType

    def onClick(self):
        self.scene.addNewRandomItem(self.item, self.nodeClass, self.nodeType)

#######################################################################################################################
#######################################################################################################################


class GlowShadowEffect(QGraphicsDropShadowEffect):
    def __init__(self, *args, **kwargs):
        QGraphicsDropShadowEffect.__init__(self, *args, **kwargs)
        self._shadow = True
        self.setOffset(-9, 9)
        self._shadowOffset = self.offset()
        self._shadowRadius = 4
        self._shadowColor = QColor(0, 0, 0, 192)
        self._glow = False
        self._glowColor = Qt.transparent
        self._glowRadius = 20

    def setShadowEnabled(self, enabled):
        self._shadow = enabled
        if self._shadow:
            self._restore()
            self.setEnabled(True)
        else:
            self._toggle()
            self.setEnabled(self._glow)

    def setGlowEnabled(self, enabled):
        self._glow = enabled
        if not self._shadow:
            self.setEnabled(enabled)

    def setGlowColor(self, color):
        self._glowColor = color
        if not self._shadow:
            self.setColor(color)

    def setGlowBlurRadius(self, radius):
        self._glowRadius = radius
        if not self._shadow:
            self.setBlurRadius(radius)

    def draw(self, painter):
        QGraphicsDropShadowEffect.draw(self, painter)
        if self._shadow and self._glow:
            self._toggle()
            QGraphicsDropShadowEffect.draw(self, painter)
            self._restore()

    def _toggle(self):
        self.setOffset(0, 0)
        self.setColor(self._glowColor)
        self.setBlurRadius(self._glowRadius)

    def _restore(self):
        self.setOffset(self._shadowOffset)
        self.setColor(self._shadowColor)
        self.setBlurRadius(self._shadowRadius)

#######################################################################################################################
#######################################################################################################################


class PolyItem(QGraphicsPolygonItem, QObject):
    KeyUnknown = 0
    KeyMoveBack = 1
    KeyMoveForward = 2
    KeyChangeSelection = 3
    KeyChangeChildSelect = 4
    KeyDelete = 5
    KeyManualMoving = 6
    KeyManualMode = 7

    widthChanged = QtCore.Signal(QGraphicsPolygonItem, float)
    childMoved = QtCore.Signal(QGraphicsPolygonItem, QGraphicsPolygonItem)
    expandClicked = QtCore.Signal()
    doubleClicked = QtCore.Signal(QGraphicsPolygonItem)
    hidden = QtCore.Signal(QGraphicsPolygonItem)
    showed = QtCore.Signal(QGraphicsPolygonItem)
    parentChanged = QtCore.Signal(QGraphicsPolygonItem)

    __time = 30
    __moveSpeed = 2.0 / 5.0

    def __init__(self, parentScene, nodeRef, draggable=True, editable=True, parent=None, scene=None):
        QGraphicsPolygonItem.__init__(self, parent, scene)
        QObject.__init__(self)

        self._effect = GlowShadowEffect()
        self.setGraphicsEffect(self._effect)
        self.toggleShadow(globals.itemsShadow)

        self.__positionTimer = QTimer()
        self.__positionTimer.timeout.connect(self.updatePosition)

        self.node = nodeRef
        if self.node is not None and self.node.nodeDesc() is not None:
            self.__shape = self.node.nodeDesc().shape
        else:
            self.__shape = globals.project.shapelib.defaultShape()

        if self.node is not None and self.node.uid() not in globals.project.nodes:
            print(u'warning: Node {0} \'{1}\' is not in project\'s nodes list! Adding it into list.'
                  .format(self.node.uid(), self.node.nodeName))
            print('debug: See polyitem.py : {0}'.format(getframeinfo(currentframe()).lineno))
            globals.project.nodes.add(self.node, recursive=False)

        self.__keyPressed = PolyItem.KeyUnknown
        self.__isDraggable = draggable
        self.__isEditable = editable
        self.draggingPos = False
        self.moving = False
        self.setMovable(True)

        self.__drawPath = QPainterPath()
        self.__cpoints = []

        self.lineWidth = 1
        self.lineColor = QcolorA(DiagramColor.defaultLineColor, 255)
        self.linePen = QPen(self.lineColor, self.lineWidth, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)

        self.connecting = False
        self.connectBGColor = DiagramColor.conectionBackgroundColor

        self.__debugIndicator = None
        self.__eventIndicator = None
        self.backgroundColor = QcolorA(Qt.blue, 32)
        if self.node is not None:
            if self.node.cls().debuggable and self.node.debug is True:
                self.__debugIndicator = createDebugTextItem()
                self.__debugIndicator.setParentItem(self)
            # parentScene.addItem(self.__debugIndicator)
            if not self.__isEditable:
                self.backgroundColor = self.node.cls().defaultState().colorDisabled
            else:
                self.backgroundColor = self.node.cls().defaultState().colorEnabled
            self.__validateEventIndicator()
        elif not self.__isEditable:
            self.backgroundColor = QcolorA(Qt.blue, 12)

        self.indexTextItem = None
        self.textItem = None
        self.textW = 0.0  # 42.0
        self.textH = 0.0  # 21.0
        self.__rootIndicator = None

        self.__boundingRect = self.__shape.boundingRect(self.textW, self.textH)
        self.__drawPath = self.__shape.shape(self.textW, self.textH)

        self.recalcPoints()

        self.setPen(self.linePen)

        self.__parent = None
        self.__connector = None
        self.igroup = None

        self.children = []
        self.childItemGroup = ItemGroup(parentScene, self, parentScene.itemInterval, parentScene.groupInterval)
        parentScene.regimeChanged.connect(self.childItemGroup.onRegimeChange)
        parentScene.intervalChanged.connect(self.childItemGroup.setInterval)

        self.childrenHide = False

        if self.node is not None:
            apm = self.node.diagramInfo.autopositioning[DisplayRegime.Horizontal]
            if apm.shift.manhattanLength() < 0.01:
                apm.autopos = True
            apm = self.node.diagramInfo.autopositioning[DisplayRegime.Vertical]
            if apm.shift.manhattanLength() < 0.01:
                apm.autopos = True
            if self.node.diagramInfo.scenePos.manhattanLength() > 0.005:
                QGraphicsPolygonItem.setPos(self, self.node.diagramInfo.scenePos.x(),
                                            self.node.diagramInfo.scenePos.y())

        self.setZValue(500.0)

        self.__expanding = False
        self.__collapsing = False
        self.__hiding = False
        self.__showing = False
        self.__visible = True
        self.__beginDragPos = self.pos()
        self.__posRequired = self.pos()
        self.__posHideShow = self.pos()
        self.__doneCounter = int(0)

        globals.librarySignals.nodeRenamed.connect(self.__onNodeRename)
        globals.librarySignals.nodeRemoved.connect(self.__onNodeRemove)
        globals.librarySignals.nodeTypeChanged.connect(self.__onNodeTypeChange)
        globals.librarySignals.libraryExcluded.connect(self.__onLibraryExcludeOrAdd)
        globals.librarySignals.libraryAdded.connect(self.__onLibraryExcludeOrAdd)
        globals.librarySignals.nodeEventsCountChanged.connect(self.__onNodeEventsCountChange)
        globals.librarySignals.nodeChildrenChanged.connect(self.__onNodeChildrenListChange)
        globals.librarySignals.nodeShapeChanged.connect(self.__onNodeShapeChange)
        globals.optionsSignals.shadowsChanged.connect(self.toggleShadow)
        globals.generalSignals.preSave.connect(self.__savePosition)

    @QtCore.Slot(bool)
    def toggleShadow(self, enabled):
        self._effect.setShadowEnabled(enabled)

    def setHighlight(self, enabled, color=None):
        self._effect.setGlowEnabled(enabled)
        if enabled and color is not None:
            self._effect.setGlowColor(color)

    def editable(self):
        return self.__isEditable

    def draggable(self):
        return self.__isDraggable

    def autoPositioningMode(self, displayRegime=None):
        if self.node is not None:
            if displayRegime is not None:
                return bool(self.node.diagramInfo.autopositioning[displayRegime].autopos)
            else:
                return bool(self.node.diagramInfo.autopositioning[self.scene().regime].autopos)
        else:
            return True

    def setAutoPositioningMode(self, mode, displayRegime=None):
        if self.node is not None:
            if displayRegime is not None:
                self.node.diagramInfo.autopositioning[displayRegime].autopos = bool(mode)
            else:
                self.node.diagramInfo.autopositioning[self.scene().regime].autopos = bool(mode)

    def deltaPos(self, displayRegime=None):
        if self.node is not None:
            if displayRegime is not None:
                return QPointF(self.node.diagramInfo.autopositioning[displayRegime].shift)
            else:
                return QPointF(self.node.diagramInfo.autopositioning[self.scene().regime].shift)
        return QPointF()

    def calculateDeltaPos(self):
        if self.node is None:
            return
        if self.__parent is None:
            self.node.diagramInfo.autopositioning[self.scene().regime].shift = QPointF()
        else:
            self.node.diagramInfo.autopositioning[self.scene().regime].shift = \
                self.__posRequired - self.__parent.posRequired()

    def setDeltaPos(self, deltaPos, displayRegime=None):
        if self.node is None or self.__parent is None:
            return
        if displayRegime is not None:
            self.node.diagramInfo.autopositioning[displayRegime].shift = QPointF(deltaPos)
        else:
            self.node.diagramInfo.autopositioning[self.scene().regime].shift = QPointF(deltaPos)

    def setEditable(self, editable):
        self.__isEditable = editable

    def setDragEnabled(self, drag):
        self.__isDraggable = drag

    def isRoot(self):
        return self.__rootIndicator is not None

    def dragToAnotherPos(self, drag):
        if drag != self.draggingPos:
            self.draggingPos = drag
            if not self.draggingPos:
                delta = self.pos() - self.__beginDragPos
                self.__posRequired = self.pos()
                if not self.autoPositioningMode() and self.__keyPressed == PolyItem.KeyManualMoving:
                    self.calculateDeltaPos()
                    QGraphicsPolygonItem.setPos(self, self.__beginDragPos.x(), self.__beginDragPos.y())
                    self.move(delta.x(), delta.y(), True)
                    QGraphicsPolygonItem.setPos(self, self.__posRequired.x(), self.__posRequired.y())
                else:
                    QGraphicsPolygonItem.setPos(self, self.__beginDragPos.x(), self.__beginDragPos.y())
                    if self.__parent is None:
                        self.move(delta.x(), delta.y(), True)
                    # self.updatePos() # update text and connectors positions
                    # if self.igroup is not None:
                    #    self.igroup.fullUpdate()
                    else:
                        p = self.__parent
                        while p.parentNode() is not None:
                            p = p.parentNode()
                        p.move(delta.x(), delta.y(), True)
                    QGraphicsPolygonItem.setPos(self, self.__posRequired.x(), self.__posRequired.y())
                    self.scene().scheduleUpdateSceneRect()
                # self.scene().scheduleUpdate()  # for correct connectors drawing
            self.__beginDragPos = self.pos()

    def isMoving(self):
        return self.draggingPos

    def connectionParticipate(self, connecting):
        if self.connecting != connecting:
            self.connecting = connecting
            if self.connecting:
                self.linePen.setColor(DiagramColor.connectionLineColor)
            else:
                self.linePen.setColor(self.lineColor)
            self.setPen(self.linePen)

    def setMovable(self, state):
        self.setFlag(QGraphicsItem.ItemIsMovable, state)
        self.setFlag(QGraphicsItem.ItemIsSelectable, state)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, state)
        self.setFlag(QGraphicsItem.ItemIsFocusable, state)

    def setLineWidth(self, width):
        self.lineWidth = width
        self.linePen.setWidth(width)
        self.setPen(self.linePen)

    def setLineColor(self, color, alpha=255):
        if color is None:
            self.lineColor = QColor(DiagramColor.defaultLineColor)
        else:
            self.lineColor = QcolorA(color, alpha)
        self.linePen.setColor(self.lineColor)
        self.setPen(self.linePen)

    def setBackgroundColor(self, color, alpha=32):
        self.backgroundColor = None
        if color is not None:
            self.backgroundColor = QcolorA(color, alpha)

    def hide(self, initiator=None):
        self.__showing = False
        self.__hiding = True
        self.__doneCounter = 0
        if initiator is None:
            initiator = self.__parent
        animate = globals.itemsAnimation and initiator is not None
        for child in self.children:
            if child.isVisible():
                child.hide(initiator)
                child.connector().hide()
            else:
                self.__doneCounter += 1
        if self.textItem is not None:
            self.textItem.hide()
        if self.indexTextItem is not None:
            self.indexTextItem.hide()
        if self.__debugIndicator is not None:
            self.__debugIndicator.hide()
        if self.__eventIndicator is not None:
            self.__eventIndicator.hide()
        if initiator is not None:
            self.__posHideShow = initiator.pos()
        else:
            self.__posHideShow = QPointF(self.__posRequired)
        if animate:
            self.__positionTimer.start(PolyItem.__time)
        else:
            self.__finishHide()
        # QGraphicsPolygonItem.hide(self)

    def show(self, initiator=None):
        self.setMovable(True)
        self.__showing = True
        self.__hiding = False
        self.__doneCounter = 0
        if initiator is None:
            initiator = self.__parent
        animate = initiator is not None and globals.itemsAnimation
        if animate:
            self.__setPosition(initiator.pos().x(), initiator.pos().y(), True)
        # self.__posRequired = initiator.pos()
        if not self.childrenHide:
            for child in self.children:
                if not child.isVisible():
                    child.show(initiator)
                    child.connector().show()
                else:
                    self.__doneCounter += 1
        # if self.textItem is not None:
        #    self.textItem.show()
        # if self.indexTextItem is not None:
        #    self.indexTextItem.show()
        # if self.__debugIndicator is not None:
        #    self.__debugIndicator.show()
        QGraphicsPolygonItem.show(self)
        # if animate:
        #    self.__positionTimer.start(PolyItem.__time)
        # else:
        self.__finishShow()

    def __finishHide(self):
        self.__visible = False
        self.__showing = False
        # if self.textItem is not None:
        #    self.textItem.hide()
        self.__setPosition(self.__posRequired.x(), self.__posRequired.y())
        self.setMovable(False)
        QGraphicsPolygonItem.hide(self)
        if self.__doneCounter >= len(self.children):
            self.__hiding = False
            self.hidden.emit(self)

    def __finishShow(self):
        self.__visible = True
        self.__hiding = False
        if self.textItem is not None:
            self.textItem.show()
        if self.indexTextItem is not None:
            self.indexTextItem.show()
        if self.__debugIndicator is not None:
            self.__debugIndicator.show()
        if self.__eventIndicator is not None:
            self.__eventIndicator.show()
        # if not self.childrenHide:
        #    for child in self.children:
        #        child.show()
        #        child.connector().show()
        if self.childrenHide or self.__doneCounter >= len(self.children):
            self.__showing = False
            self.showed.emit(self)

    @QtCore.Slot(QGraphicsPolygonItem)
    def __onChildHide(self, child):
        if child in self.children and (self.__hiding or self.__collapsing):
            self.__doneCounter += 1
            child.connector().hide()
            if self.__doneCounter >= len(self.children):
                if self.__hiding and not self.__visible:
                    self.__hiding = False
                    self.hidden.emit(self)
                if self.__collapsing:
                    self.linePen.setStyle(Qt.DotLine)
                    self.setPen(self.linePen)
                    self.igroup.fullUpdate()

    @QtCore.Slot(QGraphicsPolygonItem)
    def __onChildShow(self, child):
        if child in self.children and (self.__showing or self.__expanding):
            self.__doneCounter += 1
            if self.__doneCounter >= len(self.children):
                if self.__showing and self.__visible:
                    self.__showing = False
                    self.showed.emit(self)
                if self.__expanding:
                    self.igroup.fullUpdate()
                    self.expandClicked.emit()

    def setParent(self, newParent, connector=None):
        oldParent = self.__parent

        self.__parent = newParent
        if self.__connector is None or connector is None or self.__connector != connector:
            if self.__connector is not None:
                self.__connector.unbind()
                self.__connector.hide()
                self.scene().removeItem(self.__connector)
                self.__connector = None
            self.__connector = connector

        if self.__parent is None:
            self.setItemGroup(None)

        self.updateIndexText()

        if self.__parent is None and not self.isVisible():
            self.show()

        if self.__parent != oldParent:
            self.parentChanged.emit(self)

    def parentNode(self):
        return self.__parent

    def connector(self):
        return self.__connector

    def setItemGroup(self, igroup, insertBefore=999999):
        if igroup != self.igroup:
            if self.igroup is not None:
                group = self.igroup
                self.igroup = None
                group.removeItem(self)
                if group.empty():
                    del group

            self.igroup = igroup

            if self.igroup is not None:
                self.igroup.addItem(self, insertBefore)

    def itemGroup(self):
        return self.igroup

    def addChild(self, child, before=999999):
        if child in self.children:
            return

        if child.node is not None:
            if child.node.uid() in self.childrenUids():
                return
            children = self.childrenByClass(child.node.nodeClass)
        else:
            children = self.children
        num_children = len(children)

        if before >= num_children:
            if num_children < 1 or child.node is None:
                if self.children and child.node is not None and not child.node.cls().top:
                    before = 0
                else:
                    before = 999999
            else:
                i = self.children.index(children[num_children - 1])
                if 0 <= i < (len(self.children) - 1):
                    before = i + 1
                else:
                    before = 999999
        elif child.node is not None:
            i = self.children.index(children[before])
            if 0 <= i < len(self.children):
                before = i
            else:
                before = 999999

        if before >= len(self.children):
            self.children.append(child)
        else:
            self.children.insert(before, child)

        connector = Connector(self.scene(), self, child)
        self.scene().addItem(connector)
        if self.isSelected():
            connector.setColor(DiagramColor.selectedColor)
            connector.setZValue(Connector.activeZLevel)

        child.setParent(self, connector)
        child.setItemGroup(self.childItemGroup, before)

        if not self.isVisible() or self.childrenHide:
            child.hide()
            connector.hide()

        for c in self.children:
            c.updateIndexText()

        child.hidden.connect(self.__onChildHide)
        child.showed.connect(self.__onChildShow)

    def removeChild(self, child, full=False, firstCall=True):
        if child in self.children:
            # connector = child.connector()
            # self.scene().removeItem(connector)
            self.children.remove(child)
            if full and self.node is not None and child.node is not None and firstCall:
                self.node.removeChild(child.node)

            child.hidden.disconnect(self.__onChildHide)
            child.showed.disconnect(self.__onChildShow)
            child.setParent(None)

            itemGr = ItemGroup(self.scene(), None, self.scene().itemInterval, self.scene().groupInterval)
            self.scene().regimeChanged.connect(itemGr.onRegimeChange)
            self.scene().intervalChanged.connect(itemGr.setInterval)
            child.setItemGroup(itemGr)
            if not child.isVisible():
                child.show()

            for c in self.children:
                c.updateIndexText()

    def disconnectParent(self):
        if self.__parent is not None:
            parentItem = self.__parent
            parentItem.removeChild(self, full=False)
            if parentItem.node is not None and self.node is not None:
                parentItem.node.removeChild(self.node, permanent=False)
            if self.igroup is None:
                self.igroup = ItemGroup(self.scene(), None, self.scene().itemInterval, self.scene().groupInterval)
                self.scene().regimeChanged.connect(self.igroup.onRegimeChange)
                self.scene().intervalChanged.connect(self.igroup.setInterval)
                self.igroup.addItem(self)

    def indexOf(self, child):
        if child in self.children:
            return self.children.index(child)
        return -1

    def childrenList(self):
        return self.children

    def childrenUids(self):
        return [child.node.uid() for child in self.children if child.node is not None]

    def childrenByClass(self, nodeClass):
        children = []
        for child in self.children:
            if child.node is not None and child.node.nodeClass == nodeClass:
                children.append(child)
        return children

    def childrenGroup(self):
        return self.childItemGroup

    def depth(self):
        if not self.isVisible():
            return int(0)
        d = int(1)
        if self.childItemGroup is not None:
            d += self.childItemGroup.depth()
        return d

    def width(self, d=999999):
        if d < 1:
            return 0.0
        sw = self.boundingRect().width()
        if self.scene().regime == DisplayRegime.Vertical:
            if self.childItemGroup.isVisible():
                if d > 999990:
                    cw = self.childItemGroup.itemsWidth()
                else:
                    cw = self.childItemGroup.width(d - 1)
                if cw > sw:
                    return cw
        return sw

    def height(self, d=999999):
        if d < 1:
            return 0.0
        sh = self.boundingRect().height()
        if self.scene().regime == DisplayRegime.Horizontal:
            if self.childItemGroup.isVisible():
                if d > 999990:
                    ch = self.childItemGroup.itemsHeight()
                else:
                    ch = self.childItemGroup.height(d - 1)
                if ch > sh:
                    return ch
        return sh

    def childMoveBack(self, child):
        if child not in self.children:
            return

        if child.node is not None:
            sameChildren = self.childrenByClass(child.node.nodeClass)
        else:
            sameChildren = self.children

        i = sameChildren.index(child)
        if i < 1:
            return

        if child.node is not None:
            child_index = self.children.index(child)
            prev_index = self.children.index(sameChildren[i - 1])
        else:
            child_index = i
            prev_index = i - 1

        # Swap graphics items:
        prevItem = self.children[prev_index]
        self.children[prev_index] = child
        self.children[child_index] = prevItem

        # Swap TreeNode items:
        if self.node is not None and prevItem.node is not None and child.node is not None \
                and prevItem.node.nodeClass == child.node.nodeClass:
            k = self.node.indexOf(child.node)
            if k > 0:
                self.node.swap(child.node.nodeClass, k, k - 1)

        dpos1, dpos2 = child.deltaPos(DisplayRegime.Horizontal), child.deltaPos(DisplayRegime.Vertical)
        child.setDeltaPos(prevItem.deltaPos(DisplayRegime.Horizontal), DisplayRegime.Horizontal)
        child.setDeltaPos(prevItem.deltaPos(DisplayRegime.Vertical), DisplayRegime.Vertical)
        prevItem.setDeltaPos(dpos1, DisplayRegime.Horizontal)
        prevItem.setDeltaPos(dpos2, DisplayRegime.Vertical)

        mode1, mode2 = child.autoPositioningMode(DisplayRegime.Horizontal), child.autoPositioningMode(
            DisplayRegime.Vertical)
        child.setAutoPositioningMode(prevItem.autoPositioningMode(DisplayRegime.Horizontal), DisplayRegime.Horizontal)
        child.setAutoPositioningMode(prevItem.autoPositioningMode(DisplayRegime.Vertical), DisplayRegime.Vertical)
        prevItem.setAutoPositioningMode(mode1, DisplayRegime.Horizontal)
        prevItem.setAutoPositioningMode(mode2, DisplayRegime.Vertical)

        # Update graphics view:
        if child.itemGroup() is not None:
            child.itemGroup().moveItemBack(child)

        prevItem.updateIndexText()
        child.updateIndexText()

        self.childMoved.emit(self, child)

    def childMoveForward(self, child):
        if child not in self.children:
            return

        if child.node is not None:
            sameChildren = self.childrenByClass(child.node.nodeClass)
        else:
            sameChildren = self.children

        i = sameChildren.index(child)
        if i >= (len(sameChildren) - 1):
            return

        if child.node is not None:
            child_index = self.children.index(child)
            next_index = self.children.index(sameChildren[i + 1])
        else:
            child_index = i
            next_index = i + 1

        # Swap graphics items:
        nextItem = self.children[next_index]
        self.children[next_index] = child
        self.children[child_index] = nextItem

        # Swap TreeNode items:
        if self.node is not None and nextItem.node is not None and child.node is not None \
                and nextItem.node.nodeClass == child.node.nodeClass:
            k = self.node.indexOf(child.node)
            if k >= 0:
                self.node.swap(child.node.nodeClass, k, k + 1)

        dpos1, dpos2 = child.deltaPos(DisplayRegime.Horizontal), child.deltaPos(DisplayRegime.Vertical)
        child.setDeltaPos(nextItem.deltaPos(DisplayRegime.Horizontal), DisplayRegime.Horizontal)
        child.setDeltaPos(nextItem.deltaPos(DisplayRegime.Vertical), DisplayRegime.Vertical)
        nextItem.setDeltaPos(dpos1, DisplayRegime.Horizontal)
        nextItem.setDeltaPos(dpos2, DisplayRegime.Vertical)

        mode1, mode2 = child.autoPositioningMode(DisplayRegime.Horizontal), child.autoPositioningMode(
            DisplayRegime.Vertical)
        child.setAutoPositioningMode(nextItem.autoPositioningMode(DisplayRegime.Horizontal), DisplayRegime.Horizontal)
        child.setAutoPositioningMode(nextItem.autoPositioningMode(DisplayRegime.Vertical), DisplayRegime.Vertical)
        nextItem.setAutoPositioningMode(mode1, DisplayRegime.Horizontal)
        nextItem.setAutoPositioningMode(mode2, DisplayRegime.Vertical)

        # Update graphics view:
        if child.itemGroup() is not None:
            child.itemGroup().moveItemForward(child)

        nextItem.updateIndexText()
        child.updateIndexText()

        self.childMoved.emit(self, child)

    def setRoot(self, rootFlag):
        if rootFlag:
            if self.isRoot():
                return
            self.__rootIndicator = TextItem(False, u'Root', u'', self)
            self.__rootIndicator.setDefaultTextColor(DiagramColor.rootColor)
            # self.scene().addItem(self.__rootIndicator)
            self.updatePos()
        else:
            if not self.isRoot():
                return
            self.__removeChildItem(self.__rootIndicator)
            self.__rootIndicator = None

    def setText(self, text, ref=u''):
        if text is not None and self.textItem is not None:
            self.__removeChildItem(self.textItem)
            self.textItem = None

        invert_flag = False  # condition inversion flag
        if self.node is not None:
            nodeClass = self.node.cls()
            if nodeClass is not None and nodeClass.invertible and self.node.isInverse():
                invert_flag = True

        if text is not None:
            if self.textItem is None:
                self.textItem = NodeTextItem(invert_flag, text, ref, self)
            else:
                self.textItem.setText(invert_flag, text, ref)

            # self.scene().addItem(self.textItem)

            textRect = self.textItem.boundingRect()
            self.textW = textRect.width()
            self.textH = textRect.height()
        else:
            self.textW = 0.0  # 42.0
            self.textH = 0.0  # 21.0

        self.recalcBoundaries()

        if not self.isVisible() and self.textItem is not None:
            self.textItem.hide()
        elif self.igroup is not None:
            self.igroup.fullUpdate()

    def updateIndexText(self):
        i = int(-1)
        if self.node is not None and self.parentNode() is not None:
            children = self.parentNode().childrenByClass(self.node.nodeClass)
            if len(children) > 1:
                i = children.index(self)

        if i < 0:
            if self.indexTextItem is not None:
                self.indexTextItem.setParentItem(None)
                self.scene().removeItem(self.indexTextItem)
                self.indexTextItem = None
        else:
            if self.indexTextItem is not None:
                if self.indexTextItem.displayText() != str(i):
                    self.indexTextItem.setParentItem(None)
                    self.scene().removeItem(self.indexTextItem)
                    self.indexTextItem = None
            if self.indexTextItem is None:
                self.indexTextItem = NodeTextItem(False, unicode(str(i)), u'', self)
                self.indexTextItem.setSize(5)
                if self.textItem is not None:
                    self.indexTextItem.setDefaultTextColor(self.textItem.defaultTextColor())
                # self.scene().addItem(self.indexTextItem)
                self.updatePos()

    def recalcBoundaries(self, deep=False):
        self.__boundingRect = self.__shape.boundingRect(self.textW, self.textH)
        if not deep:
            self.widthChanged.emit(self, self.__boundingRect.width())

        if self.scene().justifyMode():
            self.__boundingRect = self.__shape.boundingRect(self.scene().itemsWidth(), self.textH, True)

        self.__drawPath = QPainterPath()
        if self.scene().justifyMode():
            self.__drawPath = self.__shape.shape(self.scene().itemsWidth(), self.textH, True)
        else:
            self.__drawPath = self.__shape.shape(self.textW, self.textH)

        self.recalcPoints()
        self.updatePos()

        if deep:
            for child in self.children:
                child.recalcBoundaries(True)

    def recalcPoints(self):
        self.__cpoints = []
        # left point:
        left = QPointF(self.boundingRect().left(), 0)
        self.__cpoints.append(left)
        # right point:
        right = QPointF(self.boundingRect().right(), 0)
        self.__cpoints.append(right)
        # top point:
        top = QPointF(0, self.boundingRect().top())
        self.__cpoints.append(top)
        # bottom point:
        bottom = QPointF(0, self.boundingRect().bottom())
        self.__cpoints.append(bottom)

    def __setPosition(self, x, y, force=False):
        self.moving = True
        QGraphicsPolygonItem.setPos(self, x, y)
        self.updatePos(force)
        self.moving = False

    def __move(self, dx, dy):
        self.moving = True
        QGraphicsPolygonItem.setPos(self, self.pos().x() + dx, self.pos().y() + dy)
        self.updatePos()
        self.moving = False

    def setPos(self, x, y, instant=False):
        self.__posRequired = QPointF(x, y)
        if instant or not globals.itemsAnimation:
            QGraphicsPolygonItem.setPos(self, x, y)

    def posRequired(self):
        return QPointF(self.__posRequired)

    def moveTo(self, x, y, instant=False):
        if not globals.itemsAnimation:
            instant = True
        self.moving = True
        self.setPos(x, y, instant)
        if instant:
            self.updatePos()
        else:
            self.__positionTimer.start(PolyItem.__time)
        self.moving = False

    def move(self, dx, dy, recursive=False, instant=False):
        if not globals.itemsAnimation:
            instant = True
        self.moving = True
        x = self.pos().x() + dx
        y = self.pos().y() + dy
        self.setPos(x, y, instant)
        if recursive:
            for child in self.children:
                child.move(dx, dy, True, instant)
        if instant:
            self.updatePos()
        else:
            self.__positionTimer.start(PolyItem.__time)
        self.moving = False

    def moveRequired(self, dx, dy, recursive=False, instant=False):
        if not globals.itemsAnimation:
            instant = True
        self.moving = True
        x = self.__posRequired.x() + dx
        y = self.__posRequired.y() + dy
        self.setPos(x, y, instant)
        if recursive:
            for child in self.children:
                child.moveRequired(dx, dy, True, instant)
        if instant:
            self.updatePos()
        else:
            self.__positionTimer.start(PolyItem.__time)
        self.moving = False

    def updatePos(self, force=False):
        if self.textItem is not None and (self.textItem.isVisible() or force):
            self.textItem.setPos(self.__shape.textPoint(QPointF(), self.textW))

        br = None
        if self.indexTextItem is not None and (self.indexTextItem.isVisible() or force):
            br = self.__shape.boundingRect(0, 0)
            self.indexTextItem.setPos(-br.width() * 0.5 - self.indexTextItem.boundingRect().width(),
                                      br.height() * 0.5 - self.indexTextItem.boundingRect().height() * 0.65)

        if self.__rootIndicator is not None:
            if br is None:
                br = self.__shape.boundingRect(0, 0)
            self.__rootIndicator.setPos(-self.__rootIndicator.boundingRect().width() * 0.5,
                                        -br.height() * 0.5 - self.__rootIndicator.boundingRect().height() * 0.9)

        if self.__debugIndicator is not None and (self.__debugIndicator.isVisible() or force):
            if br is None:
                br = self.__shape.boundingRect(0, 0)
            self.__debugIndicator.setPos(-self.__debugIndicator.boundingRect().width() * 0.9 - br.width() * 0.5,
                                         -br.height() * 0.5 - self.__debugIndicator.boundingRect().height() * 0.3)

        if self.__eventIndicator is not None and (self.__eventIndicator.isVisible() or force):
            if br is None:
                br = self.__shape.boundingRect(0, 0)
            self.__eventIndicator.setPos(br.width() * 0.5,
                                         -br.height() * 0.5 - self.__eventIndicator.boundingRect().height() * 0.2)

        for child in self.children:
            child.connector().updatePosition()

        if self.__connector is not None:
            self.__connector.updatePosition()

    @QtCore.Slot()
    def __savePosition(self):
        if self.node is not None:
            self.node.diagramInfo.scenePos = self.pos()

    def boundingRect(self):
        return self.__boundingRect

    def __calculateRect(self, item, topLeft, bottomRight, current_depth, max_depth):
        p = item.pos()
        bounding_rect = item.boundingRect()
        w = bounding_rect.width() * 0.5
        h = bounding_rect.height() * 0.5
        tl = QPointF(p.x() - w, p.y() - h)
        br = QPointF(p.x() + w, p.y() + h)
        if tl.x() < topLeft.x():
            topLeft.setX(tl.x())
        if br.x() > bottomRight.x():
            bottomRight.setX(br.x())
        if tl.y() < topLeft.y():
            topLeft.setY(tl.y())
        if br.y() > bottomRight.y():
            bottomRight.setY(br.y())
        if current_depth < max_depth:
            for child in item.children:
                if child.isVisible():
                    self.__calculateRect(child, topLeft, bottomRight, current_depth + 1, max_depth)

    def rect(self, d=999999):
        topLeft = QPointF(9999999.0, 9999999.0)
        bottomRight = -topLeft
        self.__calculateRect(self, topLeft, bottomRight, 1, d)
        return QRectF(topLeft, bottomRight)

    def shape(self):
        return self.__drawPath

    def connectorPoints(self):
        if self.scene().regime == DisplayRegime.Horizontal:
            return self.__shape.connectors(self.textH, VecShape.horizontal)
        return self.__shape.connectors(self.textH, VecShape.vertical)  # self.__cpoints

    @QtCore.Slot()
    def updatePosition(self):
        if self.__hiding:
            targetPos = self.__posHideShow
            # if self.__doneCounter < len(self.children):
            # 	permitMove = False
            # else:
            permitMove = True
        else:
            targetPos = self.__posRequired
            permitMove = True

        if permitMove:
            line = QLineF(self.pos(), targetPos)
            l = line.length()
            if self.__hiding:
                minLen = 2000.0 / self.scene().scale
            else:
                minLen = 330.0 / self.scene().scale
            if l < minLen:
                if self.__hiding:
                    if self.__visible:
                        self.__finishHide()
                else:
                    self.__setPosition(targetPos.x(), targetPos.y())
                    if self.__showing:
                        if not self.__visible:
                            self.__finishShow()
                self.__positionTimer.stop()
            else:
                dx = line.dx()
                dy = line.dy()
                self.__move(dx * PolyItem.__moveSpeed, dy * PolyItem.__moveSpeed)

    def paint(self, painter, option, widget):
        # painter.setClipRect(option.exposedRect)
        painter.setRenderHint(QPainter.Antialiasing)

        # draw item's shape
        self.setZValue(500.0)
        painter.setPen(self.pen())

        bgColor = self.backgroundColor
        if self.connecting:
            bgColor = self.connectBGColor

        if bgColor is not None:
            br = QBrush(bgColor)
            if self.childrenHide:
                br.setStyle(Qt.Dense4Pattern)
                mtr, flg = option.matrix.inverted()
                if flg:
                    br.setMatrix(mtr)
            painter.setBrush(br)

        # painter.drawPath(self.shape())
        self.__shape.paint(painter)

    def makeTextSelected(self, isSelected, isParent=False):
        if self.textItem is not None:
            self.textItem.makeSelected(isSelected, isParent)
        if self.indexTextItem is not None:
            self.indexTextItem.makeSelected(isSelected, isParent)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemSelectedHasChanged or change == QGraphicsItem.ItemSelectedChange:
            if self.isSelected():
                # item is selected, set children's connectors color and self text color to red
                self.setHighlight(True, DiagramColor.selectedColor)
                for child in self.children:
                    child.connector().setBold(True)
                    child.connector().setColor(DiagramColor.selectedColor)
                    child.connector().setHighlight(True, DiagramColor.selectedColor)
                    child.connector().setZValue(Connector.activeZLevel)
                if self.__connector is not None:
                    self.__connector.setBold(True)
                    self.__connector.setColor(DiagramColor.greengray)
                    self.__connector.setHighlight(True, DiagramColor.greengray)
                    self.__connector.setZValue(Connector.activeZLevel)
                if self.__parent is not None:
                    self.__parent.setHighlight(True, DiagramColor.greengray)
                    self.__parent.makeTextSelected(True, True)
                self.makeTextSelected(True)
                self.linePen.setWidth(self.lineWidth + 1)
                self.setPen(self.linePen)
                self.setFocus()  # set keyboard focus
            else:
                # item is not selected, set children's connectors color and self text color to default
                self.setHighlight(False)
                for child in self.children:
                    child.connector().setBold(False)
                    child.connector().setColor(Connector.defaultColor)
                    child.connector().setHighlight(False)
                    child.connector().setZValue(Connector.defaultZLevel)
                if self.__connector is not None:
                    self.__connector.setBold(False)
                    self.__connector.setColor(Connector.defaultColor)
                    self.__connector.setHighlight(False)
                    self.__connector.setZValue(Connector.defaultZLevel)
                if self.__parent is not None:
                    self.__parent.setHighlight(False)
                    self.__parent.makeTextSelected(False)
                self.makeTextSelected(False)
                self.linePen.setWidth(self.lineWidth)
                self.setPen(self.linePen)
                self.clearFocus()  # remove keyboard focus
            # self.scene().scheduleUpdate() # for correct connectors drawing
        elif change == QGraphicsItem.ItemPositionHasChanged or change == QGraphicsItem.ItemPositionChange:
            if not self.moving:
                self.moving = True
                self.updatePos()  # update text and connectors positions
                # self.scene().scheduleUpdate() # for correct connectors drawing
                self.moving = False
        return value

    def mouseDoubleClickEvent(self, event):
        self.doubleClicked.emit(self)
        # event.accept()

    @QtCore.Slot()
    def expandCollapseToggle(self):
        """ Toggle hide/show children """
        if self.childrenHide:
            self.expand()
        else:
            self.collapse()

    @QtCore.Slot()
    def expand(self):
        if not self.childrenHide or not self.children:
            return
        self.__doneCounter = int(0)
        self.__expanding = True
        self.__collapsing = False
        self.childrenHide = False
        if self.node is not None:
            self.node.diagramInfo.expanded = True
        if not self.isVisible():
            return
        # if we are not hidden, change children's visibility
        for child in self.children:
            child.show()
            child.connector().show()
        self.linePen.setStyle(Qt.SolidLine)
        self.setPen(self.linePen)

    @QtCore.Slot()
    def collapse(self):
        if self.childrenHide or not self.children:
            return
        self.__doneCounter = int(0)
        self.__expanding = False
        self.__collapsing = True
        self.childrenHide = True
        if self.node is not None:
            self.node.diagramInfo.expanded = False
        if not self.isVisible():
            return
        # if we are not hidden, change children's visibility
        for child in self.children:
            child.hide()
        # child.connector().hide()
        # self.linePen.setStyle(Qt.DotLine)
        # self.setPen(self.linePen)
        # self.igroup.fullUpdate()

    def recursiveExpand(self, initiator=None):
        if not self.children:
            return False
        self.childrenHide = False
        if self.node is not None:
            self.node.diagramInfo.expanded = True
        for child in self.children:
            child.show(initiator)
            child.connector().show()
            child.recursiveExpand(initiator)
        self.linePen.setStyle(Qt.SolidLine)
        self.setPen(self.linePen)
        return True

    def recursiveCollapse(self, initiator=None):
        if not self.children:
            return False
        self.childrenHide = True
        if self.node is not None:
            self.node.diagramInfo.expanded = False
        for child in self.children:
            child.hide(initiator)
            child.connector().hide()
            child.recursiveCollapse(initiator)
        self.linePen.setStyle(Qt.DotLine)
        self.setPen(self.linePen)
        return True

    @QtCore.Slot()
    def expandAll(self):
        if self.recursiveExpand(self):
            # if self.children:
            #    self.__doneCounter = int(0)
            #    self.__expanding = True
            #    self.__collapsing = False
            # else:
            self.__doneCounter = len(self.children)
            self.__expanding = False
            self.__collapsing = False
            # self.igroup.fullUpdate()
            self.expandClicked.emit()

    @QtCore.Slot()
    def collapseAll(self):
        if self.recursiveCollapse(self):
            if self.children:
                self.__doneCounter = int(0)
                self.__expanding = False
                self.__collapsing = True
            else:
                self.igroup.fullUpdate()

    def keyPressEvent(self, event):
        if self.isVisible():
            key = PolyItem.KeyUnknown
            if event.key() == Qt.Key_Delete:
                if self.__isDraggable:
                    key = PolyItem.KeyDelete
            elif event.key() == Qt.Key_Up:
                if self.scene().regime == DisplayRegime.Horizontal:
                    if event.modifiers() & Qt.ShiftModifier and self.__isDraggable:
                        key = PolyItem.KeyMoveBack
                    else:
                        key = PolyItem.KeyChangeChildSelect
                else:
                    key = PolyItem.KeyChangeSelection
            elif event.key() == Qt.Key_Down:
                if self.scene().regime == DisplayRegime.Horizontal:
                    if event.modifiers() & Qt.ShiftModifier and self.__isDraggable:
                        key = PolyItem.KeyMoveForward
                    else:
                        key = PolyItem.KeyChangeChildSelect
                else:
                    key = PolyItem.KeyChangeSelection
            elif event.key() == Qt.Key_Left:
                if self.scene().regime == DisplayRegime.Horizontal:
                    key = PolyItem.KeyChangeSelection
                elif event.modifiers() & Qt.ShiftModifier and self.__isDraggable:
                    key = PolyItem.KeyMoveBack
                else:
                    key = PolyItem.KeyChangeChildSelect
            elif event.key() == Qt.Key_Right:
                if self.scene().regime == DisplayRegime.Horizontal:
                    key = PolyItem.KeyChangeSelection
                elif event.modifiers() & Qt.ShiftModifier and self.__isDraggable:
                    key = PolyItem.KeyMoveForward
                else:
                    key = PolyItem.KeyChangeChildSelect
            elif event.key() == Qt.Key_M:
                self.setAutoPositioningMode(not self.autoPositioningMode())
                if self.igroup is not None:
                    self.igroup.fullUpdate()
            elif event.key() == Qt.Key_Space:
                key = PolyItem.KeyManualMoving
                self.setAutoPositioningMode(False)

            self.__keyPressed = key

            if key == PolyItem.KeyDelete:
                # self.removeFromScene(True)
                pass
            elif key == PolyItem.KeyMoveBack:
                if self.__parent is not None:
                    self.__parent.childMoveBack(self)
            elif key == PolyItem.KeyMoveForward:
                if self.__parent is not None:
                    self.__parent.childMoveForward(self)
            elif key == PolyItem.KeyChangeSelection:
                toParent = False
                toChildren = False
                i = 0
                if self.__parent is not None:
                    delta = self.__parent.pos() - self.pos()
                    positive = False
                    if self.scene().regime == DisplayRegime.Horizontal:
                        if delta.x() > 0:
                            positive = True
                    else:
                        if delta.y() > 0:
                            positive = True

                    if positive:
                        if event.key() == Qt.Key_Down or event.key() == Qt.Key_Right:
                            toParent = True
                    elif event.key() == Qt.Key_Up or event.key() == Qt.Key_Left:
                        toParent = True

                    if not toParent and self.children:
                        toChildren = True
                else:
                    for child in self.children:
                        if child.isVisible():
                            break
                        i += 1

                    if i < len(self.children):
                        delta = self.children[i].pos() - self.pos()
                        positive = False
                        if self.scene().regime == DisplayRegime.Horizontal:
                            if delta.x() > 0:
                                positive = True
                        else:
                            if delta.y() > 0:
                                positive = True

                        if positive:
                            if event.key() == Qt.Key_Down or event.key() == Qt.Key_Right:
                                toChildren = True
                        elif event.key() == Qt.Key_Up or event.key() == Qt.Key_Left:
                            toChildren = True

                if toParent and self.__parent.isVisible():
                    self.setSelected(False)
                    self.__parent.setSelected(True)
                elif toChildren:
                    self.setSelected(False)
                    self.children[i].setSelected(True)
            elif key == PolyItem.KeyChangeChildSelect:
                if self.__parent is not None and self.__parent.isVisible() and self.__parent.childrenList():
                    indx = self.__parent.childrenList().index(self)
                    j = -1

                    if (self.scene().regime == DisplayRegime.Horizontal and event.key() == Qt.Key_Up) \
                            or (self.scene().regime == DisplayRegime.Vertical and event.key() == Qt.Key_Left):
                        j = indx - 1
                        while j >= 0:
                            if self.__parent.childrenList()[j].isVisible():
                                break
                            j -= 1
                    elif (self.scene().regime == DisplayRegime.Horizontal and event.key() == Qt.Key_Down) \
                            or (self.scene().regime == DisplayRegime.Vertical and event.key() == Qt.Key_Right):
                        j = indx + 1
                        while j < len(self.__parent.childrenList()):
                            if self.__parent.childrenList()[j].isVisible():
                                break
                            j += 1

                    if 0 <= j < len(self.__parent.childrenList()):
                        self.setSelected(False)
                        self.__parent.childrenList()[j].setSelected(True)

        QGraphicsPolygonItem.keyPressEvent(self, event)

    def keyReleaseEvent(self, event):
        self.__keyPressed = PolyItem.KeyUnknown
        QGraphicsPolygonItem.keyReleaseEvent(self, event)

    def __validateEventIndicator(self):
        if self.node is not None:
            desc = self.node.nodeDesc()
        else:
            desc = None
        if desc is not None and (desc.incomingEvents or desc.outgoingEvents):
            text = u' '
            if desc.incomingEvents:
                text = u'◄'
            if desc.outgoingEvents:
                text += u'\n►'
            if self.__eventIndicator is None:
                self.__eventIndicator = TextItem(False, text, u'', self)
                self.__eventIndicator.setDefaultTextColor(DiagramColor.eventsColor)
            else:
                self.__eventIndicator.setText(False, text)
        elif self.__eventIndicator is not None:
            self.__removeChildItem(self.__eventIndicator)
            self.__eventIndicator = None

    def verify(self, full, deep=True):
        if self.node is not None and self.node.nodeDesc() is not None:
            self.__shape = self.node.nodeDesc().shape
        else:
            self.__shape = globals.project.shapelib.defaultShape()

        textUnknown = u'Unknown'

        refChanged = False
        if self.node is None:
            if self.textItem.displayText() != textUnknown:
                self.setText(textUnknown)
        elif self.textItem is not None:
            if self.node.type().isLink():
                text = self.node.nodeType
                texts = self.node.target.split('/')
                ref = texts[-1]
                if self.textItem.displayText() != text or self.textItem.ref != ref:
                    self.setText(text, ref)
                    refChanged = True
            elif self.node.nodeDesc() is None:
                if self.textItem.displayText() != textUnknown or self.textItem.ref:
                    self.setText(textUnknown)
            else:
                invert_flag = False  # condition inversion flag
                nodeClass = self.node.cls()
                if nodeClass is not None and nodeClass.invertible and self.node.isInverse():
                    invert_flag = True

                if invert_flag != self.textItem.inverse() or self.textItem.ref \
                        or self.textItem.displayText() != self.node.nodeDesc().name:
                    self.setText(self.node.nodeDesc().name)
        else:
            if self.node.type().isLink():
                text = self.node.nodeType
                texts = self.node.target.split('/')
                self.setText(text, texts[-1])
                refChanged = True
            elif self.node.nodeDesc() is None:
                self.setText(textUnknown)
            else:
                self.setText(self.node.nodeDesc().name)

        if full:
            if self.node.type().isLink():
                if refChanged:
                    forRemove = []
                    for child in self.children:
                        forRemove.append(child)
                    for loser in forRemove:
                        loser.removeFromScene()
                    uid = globals.project.trees.get(self.node.target)
                    found = globals.project.nodes.get(uid)
                    if found is not None:
                        self.scene().fillItemsChildrenTree(found, self)
                        self.igroup.fullUpdate()
            elif self.node.nodeDesc() is not None:
                forRemove = []
                forCreate = []
                if not self.node.type().children or not self.node.nodeDesc().childClasses:
                    for child in self.children:
                        forRemove.append(child)
                else:
                    num = dict()
                    for child in self.children:
                        if child.node is None:
                            continue
                        if child.node.nodeClass not in num:
                            num[child.node.nodeClass] = [1, [child]]
                        else:
                            num[child.node.nodeClass][0] += 1
                            num[child.node.nodeClass][1].append(child)

                    for n in num:
                        if n not in self.node.type().children or n not in self.node.nodeDesc().childClasses:
                            for child in num[n][1]:
                                forRemove.append(child)

                    for clsName in self.node.nodeDesc().childClasses:
                        if clsName not in self.node.type():
                            continue
                        max_children = self.node.type().child(clsName).max
                        num_children = 0
                        numRef = None
                        if clsName in num:
                            numRef = num[clsName]
                            num_children = numRef[0]
                        diff = num_children - max_children
                        if diff > 0:
                            # there are too many children
                            while diff > 0 and numRef[1]:
                                forRemove.append(numRef[1][-1])
                                numRef[1].pop()
                                diff -= 1
                        elif diff < 0:
                            available = []
                            for c in self.node.children(clsName):
                                found = False
                                if numRef is not None:
                                    for sec in numRef[1]:
                                        if sec.node is not None and sec.node == c:
                                            found = True
                                            break
                                if not found:
                                    available.append(c)

                            while num_children < max_children and available:
                                forCreate.append(available[0])
                                num_children += 1
                                available.pop(0)

                for loser in forRemove:
                    # self.removeChild(loser, True)
                    loser.removeFromScene()

                for lucky in forCreate:
                    self.scene().fillItemsChildrenTree(lucky, self)
                if forCreate:
                    self.igroup.fullUpdate()
        # endif full

        if self.node is not None:
            if self.node.cls().debuggable and self.node.debug is True:
                if self.__debugIndicator is None:
                    self.__debugIndicator = createDebugTextItem()
                    self.__debugIndicator.setParentItem(self)
                # self.scene().addItem(self.__debugIndicator)
                if not self.isVisible():
                    self.__debugIndicator.hide()
            else:
                if self.__debugIndicator is not None:
                    self.__removeChildItem(self.__debugIndicator)
                    self.__debugIndicator = None
            if not self.__isEditable:
                self.backgroundColor = self.node.cls().colorDisabled
            else:
                self.backgroundColor = self.node.cls().colorEnabled

        self.__validateEventIndicator()

        if deep:
            for child in self.children:
                child.verify(full, deep)

    def verifyChildren(self, deep=False):
        removeList = []
        invalidated = []

        if self.node is not None:
            isLink = self.node.type().isLink()
            all_is_ok = False
            if isLink:
                targetUid = globals.project.trees.get(self.node.target)
                if targetUid is not None:
                    newRoot = globals.project.nodes.get(targetUid)
                    if newRoot is None:
                        print(u'warning: Tree root with uid={0} not found for tree \'{1}\''
                              .format(targetUid, self.node.target))
                        print('debug: See polyitem.py : {0}'.format(getframeinfo(currentframe()).lineno))
                else:
                    newRoot = None
                for child in self.children:
                    if child.node is None:
                        removeList.append(child)
                        continue
                    if newRoot is not None and child.node.uid() == newRoot.uid():
                        all_is_ok = True  # ссылка найдена!
                        continue
                    removeList.append(child)
            else:
                newRoot = None
                for child in self.children:
                    if child.node is not None \
                            and (child.node.parent() is None or child.node.parent().uid() != self.node.uid()):
                        removeList.append(child)

            for loser in removeList:
                loser.removeFromScene(full=False)

            if not all_is_ok:
                if isLink:
                    if newRoot is None:
                        print(u'warning: Tree \'{0}\' have not root!'.format(self.node.target))
                        print('debug: See polyitem.py : {0}'.format(getframeinfo(currentframe()).lineno))
                    else:
                        invalidated.append(newRoot.uid())
                        self.scene().addNewItemForExistingNode(self, newRoot, 0)
                else:
                    polyChildren = self.childrenUids()
                    children = self.node.allChildren()
                    for c in children:
                        i = 0
                        for child in children[c]:
                            if child.uid() not in polyChildren:
                                invalidated.append(child.uid())
                                self.scene().addNewItemForExistingNode(self, child, i)
                            i += 1

        if deep:
            for child in self.children:
                if not invalidated or child.node is None or child.node.uid() not in invalidated:
                    child.verifyChildren(deep)

    def __removeChildItem(self, childItem):
        if childItem is not None:
            childItem.setParentItem(None)
            self.scene().removeItem(childItem)
        return None

    def flush(self):
        self.__positionTimer.timeout.disconnect(self.updatePosition)
        globals.librarySignals.nodeRenamed.disconnect(self.__onNodeRename)
        globals.librarySignals.nodeRemoved.disconnect(self.__onNodeRemove)
        globals.librarySignals.nodeTypeChanged.disconnect(self.__onNodeTypeChange)
        globals.librarySignals.libraryExcluded.disconnect(self.__onLibraryExcludeOrAdd)
        globals.librarySignals.libraryAdded.disconnect(self.__onLibraryExcludeOrAdd)
        globals.librarySignals.nodeEventsCountChanged.disconnect(self.__onNodeEventsCountChange)
        globals.librarySignals.nodeChildrenChanged.disconnect(self.__onNodeChildrenListChange)
        globals.librarySignals.nodeShapeChanged.disconnect(self.__onNodeShapeChange)
        globals.optionsSignals.shadowsChanged.disconnect(self.toggleShadow)
        globals.generalSignals.preSave.disconnect(self.__savePosition)
        self.widthChanged.disconnect()
        self.childMoved.disconnect()
        self.expandClicked.disconnect()
        self.doubleClicked.disconnect()
        self.parentChanged.disconnect()

    def removeFromScene(self, full=False, firstCall=True):
        forRemove = []
        for child in self.children:
            forRemove.append(child)
        for loser in forRemove:
            loser.removeFromScene(full, False)
        del self.children[:]
        if self.textItem is not None:
            self.__removeChildItem(self.textItem)
            self.textItem = None
        if self.__debugIndicator is not None:
            self.__removeChildItem(self.__debugIndicator)
            self.__debugIndicator = None
        if self.__eventIndicator is not None:
            self.__removeChildItem(self.__eventIndicator)
            self.__eventIndicator = None
        if self.indexTextItem is not None:
            self.__removeChildItem(self.indexTextItem)
            self.indexTextItem = None
        if self.__parent is not None:
            self.__parent.removeChild(self, full, firstCall)
        elif self.node is not None and self.node.parent() is not None and firstCall:
            self.node.parent().removeChild(self.node)
        self.__savePosition()
        self.node = None
        if self.igroup is not None:
            self.igroup.removeItem(self)
            if self.igroup is not None:
                del self.igroup
                self.igroup = None
        if self.childItemGroup is not None:
            del self.childItemGroup
            self.childItemGroup = None
        if self.__connector is not None:
            self.__connector.unbind()
            self.__connector.hide()
            self.scene().removeItem(self.__connector)
            self.__connector = None
        self.scene().removeItem(self)

    def contextMenuEvent(self, event):
        self.scene().selectItem(self)

        menu = QMenu()

        aExpCol = None
        aExpAll = None
        aCollAll = None
        if self.children:
            if self.childrenHide:
                text = trStr('Expand', u'Развернуть')
                handler = self.expand
            else:
                text = trStr('Collapse', u'Свернуть')
                handler = self.collapse
            aExpCol = QAction(text.text(), None)
            aExpCol.triggered.connect(handler)

            aExpAll = QAction(trStr('Expand all', u'Развернуть все').text(), None)
            aExpAll.triggered.connect(self.expandAll)

            if not self.childrenHide:
                aCollAll = QAction(trStr('Collapse all', u'Свернуть все').text(), None)
                aCollAll.triggered.connect(self.collapseAll)

        aAdds = dict()
        addZone = False
        if self.__isEditable and self.node is not None and self.node.nodeDesc() is not None:
            num = dict()
            for child in self.children:
                if child.node is None:
                    continue
                if child.node.nodeClass not in num:
                    num[child.node.nodeClass] = 1
                else:
                    num[child.node.nodeClass] += 1

            for cl in self.node.type().children:
                if cl not in self.node.nodeDesc().childClasses:
                    continue
                params = self.node.type().children[cl]
                cls = globals.project.alphabet.getClass(params.element)
                if cls is None:
                    continue

                if cls.name not in aAdds:
                    aAdds[cls.name] = []
                addTo = aAdds[cls.name]

                number = 0
                if cl in num:
                    number = num[cl]
                if number < params.max:
                    links = []
                    for t in cls.types:
                        childType = cls.types[t]
                        newAction = ListAction(self.scene(), self, cls.name, childType.name,
                                               '{0} {1}'.format(childType.name, cls.name), None)
                        newAction.setIcon(QIcon('/'.join([globals.applicationIconsPath, 'add-3.png'])))
                        if childType.isLink():
                            links.append(newAction)
                        else:
                            addTo.append(newAction)
                        addZone = True
                    for l in links:
                        addTo.append(l)

        if self.children:
            menu.addAction(aExpCol)
            menu.addAction(aExpAll)
            if aCollAll is not None:
                menu.addAction(aCollAll)
            menu.addSeparator()
        if addZone:
            counter = 0
            for clsName in aAdds:
                adds = aAdds[clsName]
                if not adds:
                    continue
                if counter > 0:
                    menu.addSeparator()
                sub_menu = QMenu(trStr(u'Add child {0}...', u'Добавить {0}...').text().format(clsName))
                menu.addMenu(sub_menu)
                for a in adds:
                    sub_menu.addAction(a)
            menu.addSeparator()

        aDelete = QAction(trStr('Delete', u'Удалить').text(), None)
        aDelete.setIcon(QIcon('/'.join([globals.applicationIconsPath, 'cancel-1.png'])))
        aDelete.triggered.connect(self.__onDeleteItemClick)

        aCopy = QAction(trStr('Copy', u'Копировать').text(), None)
        aCopy.setIcon(QIcon('/'.join([globals.applicationIconsPath, 'copy3.png'])))
        aCopy.triggered.connect(self.__onCopyItemClicked)

        menu.addAction(aCopy)
        menu.addAction(aDelete)
        menu.addSeparator()

        if self.node is None or self.node.type().isLink():
            aCopy.setEnabled(False)

        if not self.__isDraggable or self == self.scene().rootItem:
            aDelete.setEnabled(False)

        aVerifyChildren = QAction(trStr('Verify own children only', u'Валидация только своих дочерних узлов').text(),
                                  None)
        if self.node is not None:
            aVerifyChildren.triggered.connect(self.__onVerifyChildrenClicked)
        else:
            aVerifyChildren.setEnabled(False)

        aVerifyChildrenDeep = QAction(trStr('Verify all children', u'Валидация всех дочерних узлов').text(), None)
        if self.node is not None:
            aVerifyChildrenDeep.triggered.connect(self.__onDeepVerifyChildrenClicked)
        else:
            aVerifyChildrenDeep.setEnabled(False)

        menu.addAction(aVerifyChildren)
        menu.addAction(aVerifyChildrenDeep)
        menu.addSeparator()

        menu.exec_(QCursor.pos())

    @QtCore.Slot()
    def __onVerifyChildrenClicked(self):
        self.verifyChildren(False)

    @QtCore.Slot()
    def __onDeepVerifyChildrenClicked(self):
        self.verifyChildren(True)

    @QtCore.Slot()
    def __onCopyItemClicked(self):
        globals.clipboard['tree-node'] = self.node.deepcopy(False, True)

    @QtCore.Slot()
    def __onAddEmptyItemClick(self):
        self.scene().addEmptyItem(self)

    @QtCore.Slot()
    def __onAddTaskItemClick(self):
        self.scene().addTaskItem(self)

    @QtCore.Slot()
    def __onAddDecoratorItemClick(self):
        self.scene().addDecoratorTaskItem(self)

    @QtCore.Slot()
    def __onAddCompositeItemClick(self):
        self.scene().addCompositeTaskItem(self)

    @QtCore.Slot()
    def __onDeleteItemClick(self):
        if self != self.scene().rootItem:
            self.removeFromScene(True)

    @QtCore.Slot(str, str, str)
    def __onNodeRename(self, libname, oldname, newname):
        if self.textItem is not None and self.textItem.displayText() in (oldname, newname):
            self.verify(False, False)

    @QtCore.Slot(str, str, str)
    def __onNodeRemove(self, libname, nodename, nodeClass):
        if self.textItem is not None and self.textItem.displayText() == nodename:
            self.verify(False, False)

    @QtCore.Slot(str)
    def __onLibraryExcludeOrAdd(self, libname):
        if self.node is not None and self.node.libname == libname:
            self.verify(False, False)

    @QtCore.Slot(str, str, str, str)
    def __onNodeTypeChange(self, libname, nodename, typeOld, typeNew):
        if self.textItem is not None and self.textItem.displayText() == nodename:
            self.verify(True, False)

    @QtCore.Slot(str, str)
    def __onNodeChildrenListChange(self, libname, nodename):
        if self.node is not None and self.node.libname == libname and self.node.nodeName == nodename:
            self.verify(True, False)

    @QtCore.Slot(str, str, str)
    def __onNodeShapeChange(self, libname, nodename, shapeName):
        if self.node is not None:
            if self.node.libname == libname and self.node.nodeName == nodename:
                self.verify(False, False)
                self.scene().scheduleUpdate()
        elif self.textItem is not None:
            if self.textItem.displayText() == nodename:
                self.verify(False, False)
                self.scene().scheduleUpdate()

    @QtCore.Slot(str, str)
    def __onNodeEventsCountChange(self, libname, nodename):
        if self.node is not None and self.node.libname == libname and self.node.nodeName == nodename:
            self.__validateEventIndicator()
            if not self.__hiding and self.__visible and self.__eventIndicator is not None:
                br = self.__shape.boundingRect(0, 0)
                self.__eventIndicator.setPos(br.width() * 0.5,
                                             -br.height() * 0.5 - self.__eventIndicator.boundingRect().height() * 0.2)

#######################################################################################################################
#######################################################################################################################
