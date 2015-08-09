# coding=utf-8
# -----------------
# file      : diagram.py
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

from os import path
from math import fabs
from inspect import currentframe, getframeinfo

from PySide import QtCore
from PySide.QtGui import *
from PySide.QtCore import *
from extensions.widgets import scrollProxy

from treenode import *
from .itemgroup import ItemGroup, DEFAULT_INTERVAL, DEFAULT_GROUP_INTERVAL
from .polyitem import PolyItem
from .connector import ConnectorArrow, ConnectorType
from .dispregime import DisplayRegime, GroupType, AlignType
from treelist.tlinfo import TaskInfoWidget
from language import trStr
from auxtypes import joinPath

import globals

#######################################################################################################################
#######################################################################################################################


class TreeGraphicsScene(QGraphicsScene):
    regimeChanged = QtCore.Signal(int)
    intervalChanged = QtCore.Signal(int, int)

    connectorWidthScaleF = QtCore.Signal(float)
    connectorTypeChanged = QtCore.Signal(int)
    connectorTypeChangeFinish = QtCore.Signal()

    beginMoveItemInList = QtCore.Signal()
    endMoveItemInList = QtCore.Signal()

    dragItemStart = QtCore.Signal()
    dragItemEnd = QtCore.Signal()

    connectItemsStart = QtCore.Signal()
    connectItemsEnd = QtCore.Signal()

    selectedItemChange = QtCore.Signal(QGraphicsPolygonItem)

    queryTab = QtCore.Signal(str)

    grabApply = QtCore.Signal(bool)

    scalingTime = 10
    scalingStep = 10.0

    _size = 1500.0
    _emptySize = 100.0

    def __init__(self, project, branchname, displayMode, refresh, parent=None):
        QGraphicsScene.__init__(self, parent)
        self.__flushing = False
        self.__focused = False
        self.parentView = parent

        self.updateCounter = int(0)
        self.__removedItems = []
        self.polyItems = []
        self.polyItemsByUid = dict()
        if displayMode:
            self.regime = DisplayRegime.Horizontal
        else:
            self.regime = DisplayRegime.Vertical
        self.alignmentType = (AlignType.CenterV | AlignType.CenterH)
        self.dragMode = False
        self.itemsDragEnabled = False

        self.project = project
        self.branchname = branchname

        if project is not None:
            uid = self.project.trees.get(self.branchname)
            self.rootNode = self.project.nodes.get(uid)
        else:
            self.rootNode = None
        self.rootItem = None
        self.disconnectedItems = []
        self.topItem = None

        self.scale = 100.0
        self.itemInterval = DEFAULT_INTERVAL
        self.groupInterval = DEFAULT_GROUP_INTERVAL
        self.connectorWidthF = 1.0

        self.verifying = False
        self.justifyItems = False
        self.maxWidth = 0
        self.widestItem = None

        self.connectorMode = False
        self.connectorArrow = None
        self.connectorType = ConnectorType(ConnectorType.Polyline)

        halfSize = TreeGraphicsScene._size if project is not None else TreeGraphicsScene._emptySize
        self.topLeft = QPointF(-halfSize, -halfSize)
        self.bottomRight = QPointF(halfSize, halfSize)
        self.setSceneRect(QRectF(self.topLeft, self.bottomRight))

        self.clickedButton = None
        self.clickPos = QPoint()
        self.clickScenePos = QPointF()
        self.timer = QTime()
        self.dragItem = None
        self.selected = None
        self.clickedItem = None

        self.grabbing = False
        self.grabItem = None

        self.underCursor = None
        self.__shadow = None
        self.underCursorWidget = None
        self.underCursorWidgetScale = 1.0
        self.scalingTimer = QTimer()
        self.scalingTimer.timeout.connect(self.rescaleUnderCursorWidget)

        self.__removerTimer = QTimer()
        self.__removerTimer.setSingleShot(True)
        self.__removerTimer.timeout.connect(self.__onRemoveItemsTimeout)

        self.mousePos = QPointF()

        if self.rootNode is not None:
            # отключение анимации при обновлении окна
            animation, globals.itemsAnimation = bool(globals.itemsAnimation), False

            self.fillItemsChildrenTree(self.rootNode)
            self.rootItem.setRoot(True)
            self.topItem = self.rootItem
            self.disconnectedItems.append(self.rootItem)
            if self.rootNode.diagramInfo.scenePos.manhattanLength() > 0.005:
                needCenteringScene = True
                self.rootItem.moveTo(self.rootNode.diagramInfo.scenePos.x(),
                                     self.rootNode.diagramInfo.scenePos.y(), True)
            elif self.regime == DisplayRegime.Vertical:
                needCenteringScene = False
                self.rootItem.moveRequired(0, -150, True, True)  # refresh)
            else:
                needCenteringScene = False
                self.rootItem.moveRequired(-150, 0, True, True)  # refresh)
            if self.justifyItems:
                self.rootItem.recalcBoundaries(True)
            self.rootItem.itemGroup().fullUpdate()
            self.updateSceneRect()
            # if not refresh:
            if globals.itemsAnimation:
                timeWait = 1000
                QTimer().singleShot(timeWait, self.update)
            else:
                timeWait = 0
                self.update()
            if needCenteringScene:
                QTimer().singleShot(timeWait + 40, self.__centerOnRoot)
            globals.itemsAnimation = animation

            self.__updateTimer = QTimer()
            self.__updateTimer.setSingleShot(True)
            self.__updateTimer.timeout.connect(self.update)

            self.__updateRectTimer = QTimer()
            self.__updateRectTimer.setSingleShot(True)
            self.__updateRectTimer.timeout.connect(self.updateSceneRect)

            globals.behaviorTreeSignals.nodeDisconnected.connect(self.__onTreeNodeDisconnect)
            globals.behaviorTreeSignals.nodeConnected.connect(self.__onTreeNodeConnect)
            globals.behaviorTreeSignals.treeRootChanged.connect(self.__onTreeRootChange)

    @QtCore.Slot(Uid, Uid)
    def __onTreeNodeDisconnect(self, nodeUid, parentUid):
        if not self.__focused and parentUid.value in self.polyItemsByUid:
            # отключение анимации при обновлении окна
            animation, globals.itemsAnimation = bool(globals.itemsAnimation), False

            items = self.polyItemsByUid[parentUid.value]
            for item in items:
                item.verifyChildren()
                item.itemGroup().update()
            self.scheduleUpdate()
            globals.itemsAnimation = animation

    @QtCore.Slot(Uid, Uid)
    def __onTreeNodeConnect(self, nodeUid, parentUid):
        if not self.__focused and parentUid.value in self.polyItemsByUid:
            # отключение анимации при обновлении окна
            animation, globals.itemsAnimation = bool(globals.itemsAnimation), False

            items = self.polyItemsByUid[parentUid.value]
            for item in items:
                item.verifyChildren()
                item.itemGroup().update()
            self.scheduleUpdate()
            globals.itemsAnimation = animation

    @QtCore.Slot()
    def __centerOnRoot(self):
        if self.regime == DisplayRegime.Vertical:
            shift = QPointF(0.0, 150.0)
        else:
            shift = QPointF(150.0, 0.0)
        self.parentView.centerOn(self.rootItem.posRequired() + shift)

    @QtCore.Slot()
    def __onRemoveItemsTimeout(self):
        if self.__removedItems:
            QGraphicsScene.removeItem(self, self.__removedItems.pop())
            if self.__removedItems:
                self.__removerTimer.start(40)

    def scheduleUpdate(self):
        if not self.__updateTimer.isActive():
            self.__updateTimer.start(10)

    def scheduleUpdateSceneRect(self):
        if not self.__updateRectTimer.isActive():
            self.__updateRectTimer.start(10)

    def flush(self):
        self.__flushing = True
        self.queryTab.disconnect()
        if self.rootItem in self.disconnectedItems:
            self.disconnectedItems.remove(self.rootItem)
        for item in self.disconnectedItems:
            item.removeFromScene()
        if self.rootItem is not None:
            self.rootItem.removeFromScene()
            self.rootItem = None
        # if self.__removedItems:
        #     for item in self.__removedItems:
        #         QGraphicsScene.removeItem(self, item)
        self.__removedItems = []
        self.rootNode = None
        self.selected = None
        self.widestItem = None
        self.topItem = None
        self.grabItem = None
        self.dragItem = None
        self.underCursor = None
        self.clickedItem = None
        self.underCursorWidget = None
        if self.connectorArrow is not None:
            self.removeItem(self.connectorArrow)
            self.connectorArrow = None
        self.clear()
        self.polyItemsByUid.clear()
        if self.polyItems is not None:
            del self.polyItems[:]
            del self.polyItems
            self.polyItems = None
        if self.scalingTimer is not None:
            self.scalingTimer.stop()
            del self.scalingTimer
            self.scalingTimer = None
        if self.timer is not None:
            del self.timer
            self.timer = None
        self.project = None
        self.__shadow = None
        self.branchname = ''
        self.__flushing = False

    def isFocused(self):
        return bool(self.__focused)

    def setFocused(self, f):
        self.__focused = bool(f)

    @QtCore.Slot()
    def rescaleUnderCursorWidget(self):
        if self.underCursorWidget is not None and self.underCursorWidgetScale < 100.0:
            self.underCursorWidgetScale = min(100.0, self.underCursorWidgetScale + TreeGraphicsScene.scalingStep)
            self.underCursorWidget.setScale(self.underCursorWidgetScale / self.scale)
        else:
            self.scalingTimer.stop()

    def justifyMode(self):
        return self.justifyItems

    def itemsWidth(self):
        return self.maxWidth

    def alignment(self):
        return self.alignmentType

    def alignLeft(self):
        self.alignmentType &= ~(AlignType.Right | AlignType.CenterH)
        self.alignmentType |= AlignType.Left
        if self.regime == DisplayRegime.Vertical:
            for item in self.disconnectedItems:
                item.itemGroup().fullUpdate()
            self.updateSceneRect()
            self.update()

    def alignRight(self):
        self.alignmentType &= ~(AlignType.Left | AlignType.CenterH)
        self.alignmentType |= AlignType.Right
        if self.regime == DisplayRegime.Vertical:
            for item in self.disconnectedItems:
                item.itemGroup().fullUpdate()
            self.updateSceneRect()
            self.update()

    def alignTop(self):
        self.alignmentType &= ~(AlignType.Bottom | AlignType.CenterV)
        self.alignmentType |= AlignType.Top
        if self.regime == DisplayRegime.Horizontal:
            for item in self.disconnectedItems:
                item.itemGroup().fullUpdate()
            self.updateSceneRect()
            self.update()

    def alignBottom(self):
        self.alignmentType &= ~(AlignType.Top | AlignType.CenterV)
        self.alignmentType |= AlignType.Bottom
        if self.regime == DisplayRegime.Horizontal:
            for item in self.disconnectedItems:
                item.itemGroup().fullUpdate()
            self.updateSceneRect()
            self.update()

    def alignCenterHor(self):
        self.alignmentType &= ~(AlignType.Left | AlignType.Right)
        self.alignmentType |= AlignType.CenterH
        if self.regime == DisplayRegime.Horizontal:
            for item in self.disconnectedItems:
                item.itemGroup().fullUpdate()
            self.updateSceneRect()
            self.update()

    def alignCenterVer(self):
        self.alignmentType &= ~(AlignType.Top | AlignType.Bottom)
        self.alignmentType |= AlignType.CenterV
        if self.regime == DisplayRegime.Horizontal:
            for item in self.disconnectedItems:
                item.itemGroup().fullUpdate()
            self.updateSceneRect()
            self.update()

    def __changeRootItem(self, newRoot):
        if newRoot == self.rootItem or self.__flushing:
            return False

        globals.historySignals.pushState.emit(u'Change root for branch \'{0}\''.format(self.rootNode.refname()))

        # do something with old root
        self.rootItem.setRoot(False)
        oldRootNode = self.rootNode
        self.project.trees.addDisconnectedNodes(self.branchname, oldRootNode.uid())

        # make new root
        newRoot.setRoot(True)
        newRoot.node.setRefName(self.rootNode.refname())
        self.rootItem = newRoot
        self.rootNode.setRefName('')
        self.rootNode = newRoot.node
        if newRoot != self.topItem:
            self.topItem = newRoot

        self.project.trees.removeDisconnectedNodes(self.branchname, self.rootNode.uid())
        self.project.trees.add(branch=self.rootNode, force=True, silent=True)

        if self.rootNode.uid() not in self.project.nodes:
            print(u'warning: New root node {0} \'{1}\' is not in project\'s nodes list! Adding it into list.'
                  .format(self.rootNode.uid(), self.rootNode.nodeName))
            print('debug: See diagram.py : {0}'.format(getframeinfo(currentframe()).lineno))
            self.project.nodes.add(self.rootNode, recursive=False)

        globals.behaviorTreeSignals.treeRootChanged\
            .emit(self.rootNode.path(), self.rootNode.refname(), Uid(oldRootNode.uid()), Uid(self.rootNode.uid()))

        return True

    @QtCore.Slot(str, str, Uid, Uid)
    def __onTreeRootChange(self, filePath, shortTreeName, oldRootUid, newRootUid):
        if not self.__focused:
            newRoot = self.project.nodes.get(newRootUid.value)
            if newRoot is not None:
                treeName = newRoot.fullRefName()
                verificationList = []
                for uid in self.polyItemsByUid:
                    items = self.polyItemsByUid[uid]
                    for item in items:
                        if item.node is not None:
                            nodeType = item.node.type()
                            if nodeType is not None and nodeType.isLink():
                                if item.node.target == treeName:
                                    verificationList.append(item)
                for item in verificationList:
                    item.verifyChildren()
                    item.itemGroup().update()

    @QtCore.Slot(float)
    def onScaleChange(self, scale):
        self.scale = scale
        # print u'debug: scale is {0}'.format(scale)
        if self.scale < 100.0:
            self.connectorWidthScaleF.emit(100.0 / self.scale)
        else:
            self.connectorWidthScaleF.emit(1.0)
        if self.underCursorWidget is not None:
            self.underCursorWidget.setScale(self.underCursorWidgetScale / self.scale)

    @QtCore.Slot(int)
    def setConnectorType(self, connectorType):
        self.connectorType.val = connectorType
        self.connectorTypeChanged.emit(connectorType)
        self.update()
        self.connectorTypeChangeFinish.emit()

    def fillItemsChildrenTree(self, currentNode, parentItem=None, before=999999):
        text = 'Unknown'
        ref = ''
        editable = True
        if parentItem is not None:
            if globals.linksEditable:
                editable = parentItem.editable()
            else:
                editable = parentItem.editable() and not parentItem.node.type().isLink()

        movable = True
        if parentItem is not None:
            if globals.linksEditable:
                movable = parentItem.editable() and parentItem.draggable()
            else:
                movable = parentItem.editable() and parentItem.draggable() and not parentItem.node.type().isLink()

        if currentNode.type().isLink():
            text = currentNode.type().name
            texts = currentNode.target.split('/')
            ref = texts[-1]
            newItem = self.createNewPolyItem(currentNode, movable, editable)
            newItem.setText(text, ref)
            if parentItem is not None:
                newItem.setPos(parentItem.pos().x(), parentItem.pos().y(), True)

            if parentItem is None:
                self.rootItem = newItem
                self.rootItem.setItemGroup(ItemGroup(self, None, self.itemInterval, self.groupInterval))
                self.regimeChanged.connect(self.rootItem.itemGroup().onRegimeChange)
                self.intervalChanged.connect(self.rootItem.itemGroup().setInterval)
            else:
                parentItem.addChild(newItem, before)

            uid = self.project.trees.get(currentNode.target)
            found = self.project.nodes.get(uid)
            if found is not None:
                self.fillItemsChildrenTree(found, newItem)
            # newItem.expandCollapseToggle()
            if currentNode.diagramInfo.expanded:
                newItem.expand()
            else:
                newItem.collapse()
            # look to self.createNewPolyItem - newItem.expandClicked.connect is called there!!!
            # newItem.expandClicked.connect(self.__onItemExpand)
        else:
            desc = currentNode.nodeDesc()
            if desc is not None:
                text = currentNode.nodeDesc().name
            # ref = node.refname()

            newItem = self.createNewPolyItem(currentNode, movable, editable)
            newItem.setText(text, ref)

            if parentItem is None:
                self.rootItem = newItem
                self.rootItem.setItemGroup(ItemGroup(self, None, self.itemInterval, self.groupInterval))
                self.regimeChanged.connect(self.rootItem.itemGroup().onRegimeChange)
                self.intervalChanged.connect(self.rootItem.itemGroup().setInterval)
            else:
                newItem.setPos(parentItem.pos().x(), parentItem.pos().y(), True)
                parentItem.addChild(newItem, before)

            ccc = []
            for cls in currentNode.allChildren():
                ccc.append(cls)
            ccc.sort()
            for cls in ccc:  # currentNode.allChildren():
                if cls not in desc.childClasses or cls not in currentNode.type():
                    continue
                children = currentNode.children(cls)
                max_children = currentNode.type().child(cls).max
                num_children = 0
                for child in children:
                    self.fillItemsChildrenTree(child, newItem)
                    num_children += 1
                    if num_children >= max_children:
                        break

            if currentNode.diagramInfo.expanded:
                newItem.expand()
            else:
                newItem.collapse()

    def setDisplayMode(self, mode):
        changeMade = False
        if mode:
            if self.regime == DisplayRegime.Vertical:
                self.regime = DisplayRegime.Horizontal
                self.regimeChanged.emit(DisplayRegime.Horizontal)
                changeMade = True
        else:
            if self.regime == DisplayRegime.Horizontal:
                self.regime = DisplayRegime.Vertical
                self.regimeChanged.emit(DisplayRegime.Vertical)
                changeMade = True
        if changeMade:
            animation = globals.itemsAnimation
            if not self.__focused:
                globals.itemsAnimation = False
            for item in self.disconnectedItems:
                item.itemGroup().fullUpdate()
            self.updateSceneRect()
            self.update()
            globals.itemsAnimation = animation

    def setDragMode(self, mode):
        self.dragMode = mode

    def setItemsDragMode(self, mode):
        self.itemsDragEnabled = mode

    def setJustifyMode(self, mode):
        if mode != self.justifyItems:
            self.justifyItems = mode
            if self.justifyItems:
                self.findWidest([])
            for item in self.disconnectedItems:
                item.recalcBoundaries(True)
                item.itemGroup().fullUpdate()
            self.updateSceneRect()
            self.update()

    def select(self, item):
        if item == self.selected:
            return

        self.selected = item

        items = self.selectedItems()
        for i in items:
            i.setSelected(False)
            i.clearFocus()
        self.clearSelection()

        if self.selected is not None:
            self.selected.setSelected(True)
            self.selected.setFocus()

        self.setFocusItem(self.selected)
        self.selectedItemChange.emit(self.selected)

    def setConnectorMode(self, mode):
        self.connectorMode = mode

    def __showConnectorArrow(self, item, pos):
        if self.connectorArrow is None:
            self.connectorArrow = ConnectorArrow(self, pos, pos)
            self.addItem(self.connectorArrow)
        else:
            self.connectorArrow.setStartEnd(pos, pos)
            self.connectorArrow.show()
        self.regimeChanged.connect(self.connectorArrow.onRegimeChange)
        self.connectorArrow.setStartItem(item)
        self.connectorArrow.setEndItem(item)
        self.connectItemsStart.emit()

    def __hideConnectorArrow(self, finishMethodName):
        if self.connectorArrow is not None and self.connectorArrow.isVisible():
            # self.regimeChanged.disconnect(self.connectorArrow.onRegimeChange)
            if finishMethodName is not None and finishMethodName:
                eval('self.connectorArrow.{0}()'.format(finishMethodName))
            # self.connectorArrow.hide()
            self.connectItemsEnd.emit()
            self.removeItem(self.connectorArrow)
            self.connectorArrow = None
            return True
        return False

    def contextMenuEvent(self, event):
        scenePos = self.parentView.mapToScene(self.parentView.mapFromGlobal(QCursor.pos()))
        if self.polyItemUnderCursor(scenePos) is None:
            menu = QMenu()

            actions = []

            action = QAction(trStr('Paste', u'Вставить').text(), None)
            action.setIcon(QIcon('/'.join([globals.applicationIconsPath, 'paste3.png'])))
            action.triggered.connect(self.paste)

            if globals.clipboard['tree-node'] is None or self.grabbing:
                action.setEnabled(False)

            menu.addAction(action)
            actions.append(action)

            menu.exec_(QCursor.pos())
        else:
            QGraphicsScene.contextMenuEvent(self, event)

    def paste(self):
        if globals.clipboard['tree-node'] is not None and not self.grabbing:
            scenePos = self.parentView.mapToScene(self.parentView.mapFromGlobal(QCursor.pos()))
            self.addCopyOfNode(globals.clipboard['tree-node'], scenePos.x(), scenePos.y())

    def keyPressEvent(self, event):
        k = event.key()
        if k == Qt.Key_Alt:
            oldItem = self.underCursor
            self.underCursor = self.polyItemUnderCursor(self.mousePos)
            self.toggleNodeInfoWidget(self.underCursor, oldItem, True)
        elif k == Qt.Key_Shift:
            if self.clickedButton == Qt.LeftButton and self.dragItem is None and self.clickedItem is not None:
                inItemPos = self.clickScenePos - self.clickedItem.pos()
                if self.clickedItem.boundingRect().contains(inItemPos):
                    self.dragItem = self.clickedItem
                    self.beginMoveItemInList.emit()
        elif k == Qt.Key_Control:
            if self.clickedButton == Qt.LeftButton and self.clickedItem is not None and self.clickedItem.draggable() and \
                    not self.clickedItem.isMoving():
                self.__showConnectorArrow(self.clickedItem, self.clickScenePos)
        elif k == Qt.Key_Escape:
            # cancel item parent change
            self.__hideConnectorArrow('cancel')
        QGraphicsScene.keyPressEvent(self, event)

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key_Shift:
            if self.dragItem is not None:
                self.dragItem = None
                self.endMoveItemInList.emit()
        elif event.key() == Qt.Key_Control:
            # cancel item parent change
            self.__hideConnectorArrow('cancel')
            if Qt.Key_C in globals.pressedKeys:
                if self.selected is not None and self.selected.node is not None and not self.selected.node.type().isLink() and not self.grabbing:
                    globals.clipboard['tree-node'] = self.selected.node.deepcopy(False, True)
                elif globals.clipboard['tree-node'] is not None:
                    del globals.clipboard['tree-node']
                    globals.clipboard['tree-node'] = None
            elif Qt.Key_V in globals.pressedKeys:
                self.paste()
        elif event.key() == Qt.Key_Alt:
            # close node info widget
            if self.underCursorWidget is not None:
                QGraphicsScene.removeItem(self, self.underCursorWidget)
                self.underCursorWidget = None
                self.scalingTimer.stop()
        elif event.key() == Qt.Key_Delete:
            # remove current selected item
            if self.selected is not None:
                # if self.selected.node is not None:
                #    if self.selected.node.type().isLink():
                #        texts = self.selected.node.target.split('/')
                #        message = u'Remove link {0} to \"{1}\"'.format(self.selected.node.nodeType,
                #                                                       texts[len(texts)-1])
                #    elif self.selected.node.refname():
                #        message = u'Remove branch \"{0}\"'.format(self.selected.node.refname())
                #    else:
                #        message = u'Remove branch {0} {1}'.format(self.selected.node.nodeType,
                #                                                  self.selected.node.nodeClass)
                #    globals.historySignals.pushState(message)
                self.selected.removeFromScene(True)
        elif event.key() == Qt.Key_C:
            done = False
            if Qt.Key_Control in globals.pressedKeys and self.selected is not None and not self.grabbing:
                if self.selected.node is not None and not self.selected.node.type().isLink():
                    globals.clipboard['tree-node'] = self.selected.node.deepcopy(False, True)
                    done = True
            if not done and globals.clipboard['tree-node'] is not None:
                del globals.clipboard['tree-node']
                globals.clipboard['tree-node'] = None
        elif event.key() == Qt.Key_V and globals.clipboard['tree-node'] is not None and not self.grabbing:
            scenePos = self.parentView.mapToScene(self.parentView.mapFromGlobal(QCursor.pos()))
            self.addCopyOfNode(globals.clipboard['tree-node'], scenePos.x(), scenePos.y())
        QGraphicsScene.keyReleaseEvent(self, event)

    def itemUnderCursor(self, cursorPos, itemType):
        underCursor = self.items(cursorPos, Qt.ContainsItemShape, Qt.AscendingOrder)
        # underCursor = self.items(cursorPos, Qt.IntersectsItemBoundingRect, Qt.AscendingOrder)
        clickedItem = None
        for item in underCursor:
            if isinstance(item, itemType):
                clickedItem = item
                break
        return clickedItem

    def polyItemUnderCursor(self, cursorPos):
        underCursor = self.items(cursorPos, Qt.ContainsItemShape, Qt.AscendingOrder)
        clickedItem = None
        for item in underCursor:
            if item in self.polyItems:
                clickedItem = item
                break
        return clickedItem

    def mousePressEvent(self, event):
        self.clickedButton = event.button()
        self.clickPos = event.screenPos()
        self.clickScenePos = event.scenePos()
        self.timer.start()

        self.clickedItem = self.itemUnderCursor(self.clickScenePos, PolyItem)

        if self.dragItem is not None:
            self.dragItem = None
            self.endMoveItemInList.emit()

        if self.clickedButton == Qt.LeftButton:
            if (self.connectorMode or Qt.Key_Control in globals.pressedKeys) and self.clickedItem is not None and self.clickedItem.draggable():
                self.__showConnectorArrow(self.clickedItem, self.clickScenePos)
            elif self.dragMode or Qt.Key_Shift in globals.pressedKeys:
                # drag item inside item group (change item's priority)
                if self.clickedItem is not None:
                    inItemPos = self.clickScenePos - self.clickedItem.pos()
                    if self.clickedItem.boundingRect().contains(inItemPos):
                        self.dragItem = self.clickedItem
                        self.beginMoveItemInList.emit()
            elif self.selected is not None and self.clickedItem is not None and self.clickedItem == self.selected:
                # drag item to another position on scene
                self.dragItemStart.emit()
                self.selected.dragToAnotherPos(True)
                QGraphicsScene.mousePressEvent(self, event)

        if self.clickedButton == Qt.MidButton:
            if self.clickedItem is not None:
                self.clickedItem.expandCollapseToggle()

    def mouseReleaseEvent(self, event):
        if self.dragItem is not None:
            self.dragItem = None
            self.endMoveItemInList.emit()

        if not self.__hideConnectorArrow('finish'):
            if self.selected is not None and self.selected.isMoving():
                self.selected.dragToAnotherPos(False)
                self.dragItemEnd.emit()
                self.topItem = self.__findTopItem([])
                if self.__changeRootItem(self.topItem):
                    self.update()

            if self.clickedButton == Qt.LeftButton:
                dt = self.timer.elapsed()
                delta = QLineF(QPointF(self.clickPos.x(), self.clickPos.y()),
                               QPointF(event.screenPos().x(), event.screenPos().y()))
                if dt < 300 and delta.length() < 6 and self.clickedItem is not None:
                    self.select(self.clickedItem)  # self.itemUnderCursor(event.scenePos(), PolyItem))

        self.clickedItem = None
        self.clickedButton = None
        QGraphicsScene.mouseReleaseEvent(self, event)

    def mouseMoveEvent(self, event):
        self.mousePos = event.scenePos()
        oldItem = self.underCursor
        self.underCursor = self.polyItemUnderCursor(self.mousePos)
        self.toggleNodeInfoWidget(self.underCursor, oldItem, False)

        if self.underCursor is not oldItem:
            if self.underCursor is None:
                globals.generalSignals.sceneItemPos.emit(False, 0.0, 0.0)
            else:
                globals.generalSignals.sceneItemPos.emit(True, self.underCursor.pos().x(), self.underCursor.pos().y())

        if self.connectorArrow is not None and self.connectorArrow.isVisible():
            self.connectorArrow.setEnd(self.mousePos)
            self.connectorArrow.setEndItem(self.underCursor)
            # self.update()
        elif self.dragItem is not None:
            delta = self.mousePos - self.clickScenePos
            if self.regime == DisplayRegime.Horizontal:
                if fabs(delta.y()) > self.dragItem.boundingRect().height():
                    if delta.y() < 0:
                        key = Qt.Key_Up
                    else:
                        key = Qt.Key_Down
                    self.dragItem.keyPressEvent(QKeyEvent(QEvent.KeyPress, key, Qt.ShiftModifier))
                    self.clickScenePos = self.mousePos
                    if self.selected is None or self.selected != self.dragItem:
                        self.select(self.dragItem)
            elif fabs(delta.x()) > self.dragItem.boundingRect().width():
                if delta.x() < 0:
                    key = Qt.Key_Left
                else:
                    key = Qt.Key_Right
                self.dragItem.keyPressEvent(QKeyEvent(QEvent.KeyPress, key, Qt.ShiftModifier))
                self.clickScenePos = self.mousePos
                if self.selected is None or self.selected != self.dragItem:
                    self.select(self.dragItem)
        QGraphicsScene.mouseMoveEvent(self, event)

    def toggleNodeInfoWidget(self, itemUnderCursor, oldItem, force=False):
        if force or itemUnderCursor is None or oldItem is None or itemUnderCursor != oldItem \
                or self.underCursorWidget is None:
            if self.underCursorWidget is not None:
                QGraphicsScene.removeItem(self, self.underCursorWidget)
                self.underCursorWidget = None
                self.__shadow = None
                self.scalingTimer.stop()
            if itemUnderCursor is not None and itemUnderCursor.node is not None \
                    and (force or (Qt.Key_Alt in globals.pressedKeys)):
                widget = TaskInfoWidget(self.project, itemUnderCursor.node)  # , False, None, Qt.Popup))
                widget.showOnlyAttributes()
                self.underCursorWidget = QGraphicsProxyWidget()
                self.underCursorWidget.setWidget(widget)
                if globals.itemsShadow:
                    self.__shadow = QGraphicsDropShadowEffect()
                    self.__shadow.setColor(QColor(0, 0, 0, 128))
                    self.__shadow.setOffset(-8, 8)
                    self.__shadow.setBlurRadius(8)
                    self.underCursorWidget.setGraphicsEffect(self.__shadow)
                self.addItem(self.underCursorWidget)
                self.underCursorWidget.setPos(self.mousePos)
                self.underCursorWidget.setZValue(1000.0)
                self.underCursorWidgetScale = 1.0
                self.underCursorWidget.setScale(self.underCursorWidgetScale / self.scale)
                # self.update()
                self.scalingTimer.start(TreeGraphicsScene.scalingTime)

    def selectItem(self, item):
        if item != self.selected:
            if self.dragItem is not None:
                self.dragItem = None
                self.endMoveItemInList.emit()
            self.selected = item
            items = self.selectedItems()
            for i in items:
                i.setSelected(False)
                i.clearFocus()
            self.clearSelection()
            if self.selected is not None:
                self.selected.setSelected(True)
                self.selected.setFocus()
            self.setFocusItem(self.selected)
            self.selectedItemChange.emit(self.selected)

    def createNewPolyItem(self, treenode, draggable=True, editable=True):
        newItem = PolyItem(self, treenode, draggable, editable)
        newItem.widthChanged.connect(self.itemWidthChanged)
        newItem.childMoved.connect(self.onItemMove)
        newItem.expandClicked.connect(self.__onItemExpand)
        newItem.doubleClicked.connect(self.__onItemDoubleClick)
        newItem.parentChanged.connect(self.__onItemParentChange)
        self.addItem(newItem)
        self.polyItems.append(newItem)
        if treenode.uid() not in self.polyItemsByUid:
            self.polyItemsByUid[treenode.uid()] = [newItem]
        else:
            self.polyItemsByUid[treenode.uid()].append(newItem)
        return newItem

    def addNewRandomItem(self, parentItem, nodeClass, nodeType=''):
        if parentItem is None:
            return None

        editable = parentItem.editable()
        draggable = editable

        newTreeNode = TreeNode(self.project, None, nodeClass, nodeType, False, None)
        newTreeNode.setPath(self.rootItem.node.path())
        if not nodeType:
            self.project.nodes.add(newTreeNode)
            parentItem.node.addChild(newTreeNode)

            newItem = self.createNewPolyItem(newTreeNode, draggable, editable)
            newItem.setText('Unknown', '')

            parentItem.addChild(newItem)

            return newItem

        desc = self.__findNodeDesc(newTreeNode.nodeClass, newTreeNode.nodeType)
        if desc is not None or newTreeNode.type().isLink():
            text = newTreeNode.nodeType
            if desc is not None:
                newTreeNode.setLibName(desc.libname)
                newTreeNode.setNodeName(desc.name)
                newTreeNode.setDebugMode(desc.debugByDefault)
                newTreeNode.reparseAttributes()  # чтобы заполнить атрибуты значениями по умолчанию
                text = desc.name

            self.project.nodes.add(newTreeNode)
            parentItem.node.addChild(newTreeNode)

            newItem = self.createNewPolyItem(newTreeNode, draggable, editable)
            newItem.setText(text, '')

            parentItem.addChild(newItem)

            return newItem

        return None

    def addNewItemForExistingNode(self, parentItem, treeNode, before=999999):
        if parentItem is not None:
            self.fillItemsChildrenTree(treeNode, parentItem, before)
            return True
        return False

    def addCopyOfNode(self, node, x, y):
        nodeCopy = self.project.nodes.createCopy(node, False, True)
        self.project.trees.addDisconnectedNodes(self.branchname, nodeCopy.uid())
        item = self.createNewPolyItem(nodeCopy)
        self.disconnectedItems.append(item)
        text = node.nodeType
        desc = node.nodeDesc()
        if desc is not None:
            text = desc.name
        item.setText(text, '')
        item.setItemGroup(ItemGroup(self, None, self.itemInterval, self.groupInterval))
        self.regimeChanged.connect(item.itemGroup().onRegimeChange)
        self.intervalChanged.connect(item.itemGroup().setInterval)
        item.setPos(x, y, True)
        item.verify(True, True)
        self.topItem = self.__findTopItem([])
        if self.__changeRootItem(self.topItem):
            self.update()

    def addNewAbstractItem(self, isLink, nCls, nType, nLib, nName):
        newTreeNode = self.project.nodes.create(self.project, None, nCls, nType, False, None)
        newTreeNode.setPath(self.rootItem.node.path())
        if not isLink:
            newTreeNode.setLibName(nLib)
            newTreeNode.setNodeName(nName)
        else:
            newTreeNode.target = nName

        text = newTreeNode.nodeType
        if not isLink:
            desc = newTreeNode.nodeDesc()
            if desc is None:
                text = nName
            else:
                text = desc.name
                newTreeNode.setDebugMode(desc.debugByDefault)
                newTreeNode.reparseAttributes()  # чтобы заполнить атрибуты значениями по умолчанию

        newItem = self.createNewPolyItem(newTreeNode, True, True)
        self.disconnectedItems.append(newItem)
        newItem.setText(text, '')

        newItem.setItemGroup(ItemGroup(self, None, self.itemInterval, self.groupInterval))
        self.regimeChanged.connect(newItem.itemGroup().onRegimeChange)
        self.intervalChanged.connect(newItem.itemGroup().setInterval)

        self.project.trees.addDisconnectedNodes(self.branchname, newTreeNode.uid())

        return newItem

    def removeItem(self, item):
        isPolyItem = item in self.polyItems
        if isPolyItem:
            # if item.textItem is not None:
            #     QGraphicsScene.removeItem(self, item.textItem)

            if item == self.selected:
                if self.dragItem is not None:
                    self.dragItem = None
                    self.endMoveItemInList.emit()
                self.selected = None
                self.selectedItemChange.emit(None)

            if item == self.widestItem and not self.__flushing:
                self.findWidest([item])
                verify = True
            else:
                verify = False

            if not self.__flushing:
                if item == self.topItem:
                    self.topItem = self.__findTopItem([item])
                if item == self.rootItem and self.topItem is not None:
                    self.__changeRootItem(self.topItem)

            if item in self.disconnectedItems:
                self.disconnectedItems.remove(item)

            bruteforce = True
            if item.node is not None:
                item_node_uid = item.node.uid()
                if item_node_uid in self.polyItemsByUid:
                    bruteforce = False
                    if item in self.polyItemsByUid[item_node_uid]:
                        self.polyItemsByUid[item_node_uid].remove(item)
                        if not self.polyItemsByUid[item_node_uid]:
                            del self.polyItemsByUid[item_node_uid]
            if bruteforce:
                for uid in self.polyItemsByUid:
                    if item in self.polyItemsByUid[uid]:
                        self.polyItemsByUid[uid].remove(item)
                        if not self.polyItemsByUid[uid]:
                            del self.polyItemsByUid[uid]
                        break

            self.polyItems.remove(item)
            item.flush()
        else:
            verify = False

        # QGraphicsScene.removeItem(self, item)
        item.setVisible(False)
        self.__removedItems.append(item)
        # self.__removerTimer.start(40)

        if verify and self.justifyItems and not self.verifying:
            self.rootItem.recalcBoundaries(True)
            self.rootItem.itemGroup().fullUpdate()
            self.updateSceneRect()
            self.update()

    def updateItems(self, full):
        for item in self.disconnectedItems:
            self.verifying = True
            item.verify(full, True)
            self.verifying = False
            if self.justifyItems:
                item.recalcBoundaries(True)
            item.itemGroup().fullUpdate()
        self.updateSceneRect()
        self.update()

    @QtCore.Slot(QGraphicsPolygonItem, float)
    def itemWidthChanged(self, item, width):
        if self.widestItem is None or width > self.maxWidth:
            self.widestItem = item
            self.maxWidth = width

    def findWidest(self, excludes):
        """ Finds widest PolyItem.
        Parameter excludes is a list of excluded items. ([item1, item2, item3])
        """

        self.maxWidth = 0
        self.widestItem = None
        for item in self.polyItems:
            if item in excludes:
                continue
            itemW = item.boundingRect().width()
            if itemW > self.maxWidth:
                self.widestItem = item
                self.maxWidth = itemW

    def __findTopItem(self, excludes):
        """ Finds top PolyItem.

        Parameter excludes is a list of excluded items. ([item1, item2, item3])
        'Top' means item with minimal y coordinate for vertical display type
        and item with minimal x coordinate for horizontal display type.
        """

        def isLess1(item1, item2):
            return item1.posRequired().y() < item2.posRequired().y()

        def isLess2(item1, item2):
            return item1.posRequired().x() < item2.posRequired().x()

        if self.regime == DisplayRegime.Vertical:
            isLess = isLess1
        else:
            isLess = isLess2

        if self.topItem in excludes:
            topItem = None
        else:
            topItem = self.topItem

        for item in self.disconnectedItems:
            if not item.isVisible() or item.node is None or item in excludes:
                continue
            nodeCls = item.node.cls()
            if nodeCls is None or not nodeCls.top:
                continue
            if topItem is None:
                topItem = item
                continue
            if isLess(item, topItem):
                topItem = item

        return topItem

    @QtCore.Slot()
    def updateSceneRect(self):
        left = self.topLeft.x()
        top = self.topLeft.y()
        right = self.bottomRight.x()
        bottom = self.bottomRight.y()
        for item in self.polyItems:
            pos = item.posRequired()
            if pos.x() < left:
                left = pos.x()
            if pos.x() > right:
                right = pos.x()
            if pos.y() < top:
                top = pos.y()
            if pos.y() > bottom:
                bottom = pos.y()

        topLeft = self.topLeft
        bottomRight = self.bottomRight
        if left < topLeft.x():
            topLeft.setX(left - self.maxWidth * 0.7)
        if right > bottomRight.x():
            bottomRight.setX(right + self.maxWidth * 0.7)
        if top < topLeft.y():
            topLeft.setY(top - self.maxWidth * 0.25)
        if bottom > bottomRight.y():
            bottomRight.setY(bottom + self.maxWidth * 0.25)

        self.setSceneRect(QRectF(topLeft, bottomRight))

    @QtCore.Slot()
    def __onItemExpand(self):
        if self.updateCounter == 0:
            self.updateSceneRect()
            if globals.itemsAnimation:
                self.updateCounter += int(1)
                QTimer().singleShot(40, self.__delayedUpdate)
            else:
                self.update()

    @QtCore.Slot(QGraphicsPolygonItem)
    def __onItemDoubleClick(self, item):
        if item in self.polyItems and item.node is not None:
            node = item.node.root()
            if node.refname():
                self.queryTab.emit(node.fullRefName())

    @QtCore.Slot(QGraphicsPolygonItem)
    def __onItemParentChange(self, item):
        if item.parentNode() is None:
            if item not in self.disconnectedItems:
                self.disconnectedItems.append(item)
        elif item in self.disconnectedItems:
            self.disconnectedItems.remove(item)

    @QtCore.Slot()
    def __delayedUpdate(self):
        for item in self.disconnectedItems:
            item.itemGroup().fullUpdate()
        self.updateCounter = int(0)
        self.update()

    @QtCore.Slot()
    def __resetCounter(self):
        self.updateCounter = int(0)

    def update(self):
        self.updateCounter += int(1)
        if self.updateCounter == 1:
            QGraphicsScene.update(self)
            QTimer().singleShot(40, self.__resetCounter)
        # print 'INFO: Scene updated {0} times!'.format(self.updateCounter)

    def onItemMove(self, parentItem, item):
        """ item sends this signal when it's child has been moved in children list (child's priority changed)
        this signal IS NOT SENT when item change it's position on scene!
        """
        pass

    @QtCore.Slot(str, str)
    def onNodeGrab(self, libname, nodename):
        if self.project is None or libname not in self.project.libraries:
            self.grabApply.emit(False)
            return

        lib = self.project.libraries[libname]
        if nodename not in lib:
            self.grabApply.emit(False)
            return

        nodeDesc = lib[nodename]

        self.grabbing = False
        self.grabItem = self.addNewAbstractItem(False, nodeDesc.nodeClass, nodeDesc.nodeType, libname, nodename)
        if self.grabItem is None:
            self.grabApply.emit(False)
            return

        self.grabbing = True
        self.grabItem.hide()
        self.grabApply.emit(True)

    @QtCore.Slot(str)
    def onBranchGrab(self, treename):
        if self.project is None or treename not in self.project.trees:
            self.grabApply.emit(False)
            return

        # при первом проходе пытаемся выбрать ссылку, которая не копирует ветвь
        # при втором - любую ссылку
        selectedClass = None
        selectedType = None
        for i in range(2):
            for classname in self.project.alphabet.getClasses(True):
                fin = False
                cls = self.project.alphabet.getClass(classname)
                for tpname in cls.getLinkTypes():
                    t = cls.types[tpname]
                    if i > 0 or not t.isCopyLink():
                        selectedType = t
                        fin = True
                        break
                if fin:
                    selectedClass = cls
                    break
            if selectedClass is not None and selectedType is not None:
                break

        self.grabbing = False
        self.grabItem = self.addNewAbstractItem(True, selectedClass.name, selectedType.name, '', treename)
        if self.grabItem is None:
            self.grabApply.emit(False)
            return

        self.grabbing = True
        self.grabItem.hide()
        self.grabApply.emit(True)

    @QtCore.Slot(float, float)
    def onGrabRelease(self, x, y):
        if self.grabbing:
            self.grabItem.setPos(x, y, True)
            self.grabItem.verify(True, True)
            self.grabbing = False
            self.select(self.grabItem)
            self.grabItem = None
            self.topItem = self.__findTopItem([])
            if self.__changeRootItem(self.topItem):
                self.update()

    @QtCore.Slot()
    def onGrabCancel(self):
        if self.grabbing:
            self.grabbing = False
            self.project.trees.removeDisconnectedNodes(self.branchname, self.grabItem.node.uid())
            self.project.nodes.remove(self.grabItem.node)
            self.removeItem(self.grabItem)
            self.grabItem = None

    @QtCore.Slot(float, float)
    def onGrabMove(self, x, y):
        if self.grabbing:
            if not self.grabItem.isVisible():
                self.grabItem.show()
            self.grabItem.setPos(x, y, True)

    def __findNodeDesc(self, nodeClass, nodeType):
        nodeDesc = None
        for libname in self.project.libraries:
            lib = self.project.libraries[libname]
            nodes = lib.getAll(nodeClass, nodeType)
            for n in nodes:
                nodeDesc = nodes[n]
                break
            if nodeDesc is not None:
                break
        return nodeDesc

#######################################################################################################################
#######################################################################################################################

_viewBg = []


class TreeGraphicsView(QGraphicsView):
    scaleChange = QtCore.Signal(float)

    itemSelected = QtCore.Signal(QGraphicsView, TreeNode, bool)
    noneSelected = QtCore.Signal(QGraphicsView)

    def __init__(self, project, branchname, parent=None):
        QGraphicsView.__init__(self, parent)
        self._focusProxy = scrollProxy(self)

        self.defaultBackground = self.backgroundBrush()

        global _viewBg
        if not _viewBg:
            paths = []
            good_bgs = []
            bad_bgs = []
            i = 0
            for bg in globals.backgrounds:
                bg_path = joinPath(globals.applicationIconsPath, bg)
                paths.append(bg_path)
                if path.exists(bg_path):
                    _viewBg.append(QPixmap(bg_path))
                    good_bgs.append(i)
                else:
                    _viewBg.append(self.defaultBackground)
                    bad_bgs.append(i)
                i += 1
            if bad_bgs:
                if good_bgs:
                    for bad_bg in bad_bgs:
                        message = u'warning: Background image \'{0}\' does not exist.'.format(paths[bad_bg])
                        if globals.background in good_bgs:
                            bg_path = paths[globals.background]
                            message += u'It will be replaced with default image \'{0}\'.'.format(bg_path)
                        else:
                            bg_path = paths[good_bgs[0]]
                            message += u'It will be replaced with image \'{0}\'.'.format(bg_path)
                        _viewBg[bad_bg] = QPixmap(bg_path)
                        print(message)
                else:
                    print('warning: There are no background images exist! ' \
                          'No background will be displayed on graphics scene.')

        self.bgTransform = None
        self.__onBackgroundChange(globals.background)
        self.setCacheMode(QGraphicsView.CacheBackground)

        self.tabWidget = parent
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        # self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.setViewportUpdateMode(QGraphicsView.BoundingRectViewportUpdate)
        self.project = project
        self.branchname = branchname
        self.displayMode = DisplayRegime.Horizontal
        self.draggingMode = False
        self.justifyMode = False
        self.connectorMode = False

        self.movingItemInList = False
        self.draggingItem = False
        self.connectingItems = False
        self.grabbing = False

        self.connectorType = ConnectorType(ConnectorType.Polyline)

        self.CtrlPressed = False
        self.MousePressed = False
        self.__scrolling = False
        self.__focused = False
        self.mousePressPos = QPointF()

        self.currScale = 100.0
        self.scaleCoeff = 1.25 if project is not None else 1.0

        self.fullRefresh(True)

        QTimer().singleShot(10, lambda: self.centerOn(0, 0))

        globals.optionsSignals.backgroundChanged.connect(self.__onBackgroundChange)

    @QtCore.Slot(int)
    def __onBackgroundChange(self, backgroundType):
        if -1 < backgroundType < len(globals.backgrounds):
            global _viewBg
            if self.bgTransform:
                bg = _viewBg[backgroundType].transformed(self.bgTransform, Qt.SmoothTransformation)
            else:
                bg = QPixmap(_viewBg[backgroundType])
            self.setBackgroundBrush(bg)
        else:
            self.setBackgroundBrush(self.defaultBackground)

    # def paintEvent(self, event):
    # 	newEvent = QPaintEvent(event.region().boundingRect())
    # 	QGraphicsView.paintEvent(self, newEvent)
    # 	del newEvent

    def treename(self):
        return self.branchname

    def flush(self):
        self.draggingItem = None
        self.project = None
        self.branchname = ''
        scene = self.scene()
        if scene is not None:
            self.setScene(None)
            scene.flush()
            del scene

    def isFocused(self):
        return self.__focused

    def setFocused(self, focus):
        self.__focused = focus
        self.scene().setFocused(bool(self.__focused))

    def fullRefresh(self, onInit=False):
        if not onInit:
            self.noneSelected.emit(self)

        self.movingItemInList = False
        self.draggingItem = False
        self.connectingItems = False
        self.grabbing = False

        prevScene = self.scene()

        self.setScene(TreeGraphicsScene(self.project, self.branchname, self.displayMode, not onInit, self))
        self.scaleChange.connect(self.scene().onScaleChange)
        self.scene().selectedItemChange.connect(self.onSelectedItemChange)
        self.scene().beginMoveItemInList.connect(self.onMoveItemInListBegin)
        self.scene().endMoveItemInList.connect(self.onMoveItemInListEnd)
        self.scene().dragItemStart.connect(self.onDragItemBegin)
        self.scene().dragItemEnd.connect(self.onDragItemEnd)
        self.scene().connectItemsStart.connect(self.onConnectItemsBegin)
        self.scene().connectItemsEnd.connect(self.onConnectItemsEnd)
        self.scene().grabApply.connect(self.__onGrabApply)

        if self.tabWidget is not None:
            self.scene().queryTab.connect(self.tabWidget.tabQuery)

        if not onInit:
            self.scene().setDragMode(self.draggingMode)
            self.scene().setJustifyMode(self.justifyMode)
            self.scene().setConnectorMode(self.connectorMode)

        self.scene().setConnectorType(self.connectorType.val)

        if self.__focused:
            self.scene().setFocused(True)

        if prevScene is not None:
            prevScene.setFocused(False)
            prevScene.flush()
            del prevScene

    @QtCore.Slot()
    def refresh(self):
        self.fullRefresh()

    @QtCore.Slot()
    def onMoveItemInListBegin(self):
        self.movingItemInList = True

    @QtCore.Slot()
    def onMoveItemInListEnd(self):
        self.movingItemInList = False

    @QtCore.Slot()
    def onDragItemBegin(self):
        self.draggingItem = True
        self.MousePressed = False

    @QtCore.Slot()
    def onDragItemEnd(self):
        self.draggingItem = False

    @QtCore.Slot()
    def onConnectItemsBegin(self):
        self.connectingItems = True
        self.MousePressed = False

    @QtCore.Slot()
    def onConnectItemsEnd(self):
        self.connectingItems = False

    @QtCore.Slot(str, str)
    def onNodeGrab(self, libname, nodename):
        self.scene().onNodeGrab(libname, nodename)

    @QtCore.Slot(str)
    def onBranchGrab(self, treename):
        if treename != self.branchname:
            self.scene().onBranchGrab(treename)

    @QtCore.Slot(int, int)
    def onGrabbedRelease(self, x, y):
        if self.grabbing is False:
            return
        self.grabbing = False
        pos = self.mapToScene(self.mapFromGlobal(QPoint(x, y)))
        visibleArea = self.mapToScene(self.rect()).boundingRect()
        if visibleArea.contains(pos):
            self.scene().onGrabRelease(pos.x(), pos.y())
        else:
            self.scene().onGrabCancel()

    @QtCore.Slot(int, int)
    def onGrabbedNodeMove(self, x, y):
        if self.grabbing is False:
            return
        pos = self.mapToScene(self.mapFromGlobal(QPoint(x, y)))
        self.scene().onGrabMove(pos.x(), pos.y())

    @QtCore.Slot(bool)
    def __onGrabApply(self, grabApply):
        self.grabbing = grabApply

    def setDisplayMode(self, mode):
        self.displayMode = mode
        self.scene().setDisplayMode(mode)

    def setDragMode(self, mode):
        self.draggingMode = mode
        self.scene().setDragMode(mode)

    def setJustifyMode(self, mode):
        self.justifyMode = mode
        self.scene().setJustifyMode(mode)

    def setConnectorMode(self, mode):
        self.connectorMode = mode
        self.scene().setConnectorMode(mode)

    def setConnectorType(self, connectorType):
        prevVal = self.connectorType.val
        self.connectorType.val = connectorType
        if self.connectorType.val != prevVal:
            self.scene().setConnectorType(self.connectorType.val)

    def onSelectedItemChange(self, item):
        if item is not None and item.node is not None:
            self.itemSelected.emit(self, item.node, item.editable())
        else:
            self.noneSelected.emit(self)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Control:
            self.CtrlPressed = True
        # self.scene().setItemsDragMode(True)
        elif event.key() == Qt.Key_Plus:
            if self.CtrlPressed:
                self.scale(self.scaleCoeff, self.scaleCoeff)
                self.currScale *= self.scaleCoeff
                self.scaleChange.emit(self.currScale)
        elif event.key() == Qt.Key_Minus:
            if self.CtrlPressed:
                self.scale(1 / self.scaleCoeff, 1 / self.scaleCoeff)
                self.currScale /= self.scaleCoeff
                self.scaleChange.emit(self.currScale)
        elif event.key() == Qt.Key_F1:
            title = trStr('Graphics scene help', u'Справка для графической области').text()
            message = '<h2>'
            message += trStr('Graphics scene hot keys and hints',
                             u'Горячие клавиши и подсказки для работы с графической областью').text()
            message += '</h2><p/><h4><u>'

            message += trStr('Holding <i>Ctrl</i> button you can connect and disconnect nodes',
                             u'Удерживая <i>Ctrl</i>, можно соединять узлы').text()
            message += '</u></h4>'
            # message += u'<font color=\"cadetblue\" size=\"3\">'
            message += trStr('<p style="text-indent: 20px;">Select node, press <b>Ctrl</b>+<b>LMB</b> and move \
                             mouse cursor: you will see a red arrow. \
                             Red arrow direction points from parent node to child.</p>\
                             <p style="text-indent: 20px;">If the arrow points from empty space to node \
                             (or from node to an empty space),\
                             then this node will be diconnected from it\'s parent.</p>',

                             u'<p style="text-indent: 20px;">Выделите нужный узел, зажмите <b>Ctrl</b>+<b>ЛКМ</b> \
                             и перемещайте курсор мыши: вы увидите красную стрелку. \
                             Красная стрелка рисуется от родителя к дочернему узлу.</p>\
                             <p style="text-indent: 20px;">Если стрелка направлена к узлу из пустой \
                             области (или от узла в пустую область), то узел будет отсоединен от своего родителя.</p>')\
                .text()
            # message += u'</font>'

            message += '<h4><u>'
            message += trStr('Holding <i>Shift</i> button you can change nodes order', \
                             u'Удерживая <i>Shift</i>, можно изменять порядок узлов').text()
            message += '</u></h4>'
            # message += u'<font color=\"cadetblue\" size=\"3\">'
            message += trStr('<p style="text-indent: 20px;">Select node, press <b>Shift</b>+<b>LMB</b> \
                             and move mouse cursor until node will not change it\'s position.</p>',

                             u'<p style="text-indent: 20px;">Выделите нужный узел, зажмите <b>Shift</b>+<b>ЛКМ</b> \
                             и перемещайте курсор мыши до тех пор, пока узел не изменит свою позицию.</p>')\
                .text()
            # message += u'</font>'

            message += '<h4><u>'
            message += trStr('Holding <i>Alt</i> button you can watch node attributes',
                             u'Удерживая <i>Alt</i>, можно смотреть параметры узлов').text()
            message += '</u></h4>'
            # message += u'<font color=\"cadetblue\" size=\"3\">'
            message += trStr('<p style="text-indent: 20px;">Press <b>Alt</b> and move mouse cursor over required \
                             node on graphics scene and you will see popup window with it\'s attributes.</p>',

                             u'<p style="text-indent: 20px;">Зажмите <b>Alt</b> и переместите курсор мыши на нужный \
                             узел на графической области и появится окошко с параметрами этого узла.</p>')\
                .text()
            # message += u'</font>'

            message += '<h4><u>'
            message += trStr('There are copy/paste feature available',
                             u'Доступно копирование и вставка деревьев').text()
            message += '</u></h4>'
            # message += u'<font color=\"cadetblue\" size=\"3\">'
            message += trStr('<p style="text-indent: 20px;">Select required node and press <b>Ctrl</b>+<b>C</b> then \
                             selected node and <b>all</b> it\'s children will be copied into a clipboard.<br/>\
                             Now you can press <b>Ctrl</b>+<b>V</b> and copied tree will appear under mouse cursor.</p>\
                             <p><i><u>Hint:</u> You can copy a tree on one diagram and paste it to \
                             another diagram.</i></p>',

                             u'<p style="text-indent: 20px;">Выделите нужный узел и нажмите <b>Ctrl</b>+<b>C</b> - \
                             узел и <b>все</b> его дочерние узлы будут скопированы в буфер.<br/>\
                             Теперь вы можете нажать <b>Ctrl</b>+<b>V</b> и скопированное дерево появится \
                             под курсором мыши.</p>\
                             <p><i><u>Подсказка:</u> Дерево можно скопировать на одной диаграмме \
                             и вставить на любую другую диаграмму.</i></p>')\
                .text()
            # message += u'</font>'

            QMessageBox.information(self, title, message)

        QGraphicsView.keyPressEvent(self, event)

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key_Control:
            self.CtrlPressed = False
            self.scene().setItemsDragMode(False)
        QGraphicsView.keyReleaseEvent(self, event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and not self.MousePressed and not self.draggingItem \
                and not self.connectingItems:
            self.MousePressed = True
            self.mousePressPos = event.globalPos()
        QGraphicsView.mousePressEvent(self, event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.MousePressed = False
            if self.__scrolling:
                self.__scrolling = False
                self.verticalScrollBar().setProperty('moving', False)
                self.horizontalScrollBar().setProperty('moving', False)
                self.verticalScrollBar().setStyle(QApplication.style())
                self.horizontalScrollBar().setStyle(QApplication.style())
        QGraphicsView.mouseReleaseEvent(self, event)

    def mouseMoveEvent(self, event):
        if self.MousePressed:
            delta = event.globalPos() - self.mousePressPos
            self.mousePressPos = event.globalPos()
            delta *= self.scaleCoeff  # *self.scaleCoeff
            if not self.movingItemInList:
                self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
                self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
                if not self.__scrolling:
                    self.__scrolling = True
                    self.verticalScrollBar().setProperty('moving', True)
                    self.horizontalScrollBar().setProperty('moving', True)
                    self.verticalScrollBar().setStyle(QApplication.style())
                    self.horizontalScrollBar().setStyle(QApplication.style())
            # visibleArea = self.mapToScene(self.rect()).boundingRect()
            # centr = visibleArea.center()
        # event.accept()
        QGraphicsView.mouseMoveEvent(self, event)

    def wheelEvent(self, event):
        scaled = False
        if event.delta() > 0:
            if self.currScale < globals.scaleMax:
                self.scale(self.scaleCoeff, self.scaleCoeff)
                self.currScale *= self.scaleCoeff
                self.scaleChange.emit(self.currScale)
                scaled = True
        else:
            if self.currScale > globals.scaleMin:
                sc = 1.0 / self.scaleCoeff
                self.scale(sc, sc)
                self.currScale /= self.scaleCoeff
                self.scaleChange.emit(self.currScale)
                scaled = True
        if scaled:
            if self.currScale < 100.0:
                self.bgTransform, _ = self.transform().inverted()
            else:
                self.bgTransform = None
            if -1 < globals.background < len(globals.backgrounds):
                self.__onBackgroundChange(globals.background)

    # def drawBackground(self, painter, rect):
    #     if globals.drawBackground:
    #         painter.save()
    #         painter.setTransform(QTransform())
    #         sceneRect = self.viewport().rect()
    #         painter.setPen(Qt.NoPen)
    #         painter.setBrush(QBrush(self.backgroundPixmap))
    #         painter.drawRect(sceneRect)
    #         painter.restore()
    #     else:
    #         QGraphicsView.drawBackground(self, painter, rect)

    @QtCore.Slot(bool)
    def updateItems(self, full):
        self.scene().updateItems(full)

#######################################################################################################################
#######################################################################################################################

