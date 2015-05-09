# coding=utf-8
# -----------------
# file      : proj.py
# date      : 2012/12/15
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

""" Script file with definition of Project class.

Project is a storage that keeps all created tree nodes ('TreeNodes' object), all available tree node collections
(list of 'NodeLibrary' objects), tree lookup table ('BehaviorTree' object), an "alphabet" ('Aplhabet' object) that
defines xml files format, paths to xml files, and so on.
"""

from __future__ import unicode_literals

__author__ = 'Victor Zarubkin'
__copyright__ = 'Copyright (C) 2012  Victor Zarubkin'
__credits__ = ['Victor Zarubkin']
__license__ = ['GPLv3']
__version__ = '1.3.0'  # this is last application version when this script file was changed
__email__ = 'victor.zarubkin@gmail.com'
############################################################################

import datetime
from time import sleep

from PySide.QtGui import *

from treenode import BehaviorTree, TreeNodeDesc, TreeNodes
from .history import History

from . import liparser
from . import treeparser
from auxtypes import *
import globals

from language import trStr

#######################################################################################################################
#######################################################################################################################


class Project(object):
    def __init__(self):
        self.modified = False
        self.name = ''
        self.path = ''
        self.lib_paths = []
        self.tree_paths = []
        self.alphabet = None
        self.shapelib = None
        self.libraries = {}
        self.trees = BehaviorTree()
        self.nodes = TreeNodes()
        self.top_level_trees = []
        self.__lib_parser = liparser.LibParser()
        self.__tree_parser = treeparser.TreeParser()
        self.__history = History(self)

        globals.librarySignals.excludeLibrary.connect(self.excludeLibrary)

        globals.librarySignals.removeNode.connect(self.__onRemoveNode)
        globals.librarySignals.renameNode.connect(self.__onRenameNode)
        globals.librarySignals.changeCreator.connect(self.__onChangeCreatorNode)

        globals.librarySignals.renameAttribute.connect(self.__onRenameAttrNode)
        globals.librarySignals.changeAttribute.connect(self.__onChangeAttributeNode)
        globals.librarySignals.addAttribute.connect(self.__onAddAttributeNode)
        globals.librarySignals.deleteAttribute.connect(self.__onDeleteAttributeNode)

        globals.librarySignals.addNewNode.connect(self.__onAddNewNodeToLibrary)
        globals.librarySignals.addNode.connect(self.__onAddNodeToLibrary)
        globals.librarySignals.changeNodeType.connect(self.__onChangeTypeNode)
        globals.librarySignals.changeNodeChildren.connect(self.__onChangeChildrenNode)
        globals.librarySignals.changeNodeDescription.connect(self.__onChangeDescriptionNode)
        globals.librarySignals.changeNodeShape.connect(self.__onShapeChangeNode)

        globals.librarySignals.renameLibrary.connect(self.__onRenameLibraryQuery)

        globals.librarySignals.renameIncomingEvent.connect(self.__onIncomingEventRenameNode)
        globals.librarySignals.renameOutgoingEvent.connect(self.__onOutgoingEventRenameNode)
        globals.librarySignals.addIncomingEvent.connect(self.__onIncomingEventAddNode)
        globals.librarySignals.addOutgoingEvent.connect(self.__onOutgoingEventAddNode)
        globals.librarySignals.deleteIncomingEvent.connect(self.__onIncomingEventDeleteNode)
        globals.librarySignals.deleteOutgoingEvent.connect(self.__onOutgoingEventDeleteNode)

    def activate(self):
        self.__history.activate()

    def deactivate(self):
        self.__history.deactivate()

    def getHistoryUndoActions(self):
        return self.__history.getUndoActions()

    def getHistoryRedoActions(self):
        return self.__history.getRedoActions()

    def gotLibrary(self, libname):
        return libname in self.libraries

    def getLibrary(self, libname):
        if libname in self.libraries:
            return self.libraries[libname]
        return None

    def addLibrary(self, filename):
        loaded_libs = self.__lib_parser.load(self.alphabet, [filename], self.libraries, self.shapelib)
        if loaded_libs:
            path = relativePath(filename, self.path)
            if path is not None:
                globals.historySignals.pushState.emit('Add new libraries from \'{0}\''.format(path))
                self.lib_paths.append(path)

                for libname in loaded_libs:
                    self.libraries[libname] = loaded_libs[libname]

                for uid in self.nodes:
                    node = self.nodes[uid]
                    if not node.isEmpty():
                        node.reparseAttributes()

                for libname in loaded_libs:
                    globals.librarySignals.libraryAdded.emit(libname)

                self.modified = True
                return True

        return False

    def excludeLibrary(self, libname):
        if libname in self.libraries:
            usedBy = self.trees.getBranchesByLibrary(libname, self.nodes)
            if usedBy:
                message = '<font color=\"red\">'
                message += trStr('Library <b>\'{0}\'</b> is used by branches:'.format(libname),
                                 'Библиотека <b>\'{0}\'</b> используется в деревьях:'.format(libname)).text()
                message += '</font>'
                for branchName in usedBy:
                    message += '<br/>- <b>{0}</b>'.format(usedBy[branchName].refname())
                message += '<br/>'
            else:
                message = ''
            message += trStr(
                '<font color=\"red\">Do You really want to exclude library <b>\'{0}\'</b> \
                    from the project?</font>'.format(libname),
                '<font color=\"red\">Вы действительно хотите исключить библиотеку <b>\'{0}\'</b> \
                    из проекта?</font>'.format(libname)).text()
            title = trStr('Excluding library', 'Исключение библиотеки').text()
            if QMessageBox.warning(None, title, message,
                                   QMessageBox.Yes | QMessageBox.No, QMessageBox.No) == QMessageBox.Yes:
                globals.historySignals.pushState.emit('Exclude library \'{0}\' from project'.format(libname))
                self.modified = True
                del self.libraries[libname]
                globals.librarySignals.libraryExcluded.emit(libname)

    def gotTree(self, fullname):
        return fullname in self.trees

    def getTree(self, fullname):
        return self.trees.get(fullname)

    def addTree(self, filename):
        trees, nodes, treesFiles = self.__tree_parser.load([filename], self)
        if treesFiles and treesFiles[0] not in self.tree_paths:
            path = treesFiles[0]
            globals.historySignals.pushState.emit('Include new trees from \'{0}\' into project'.format(path))
            self.tree_paths.append(path)
            for t in trees:
                uid = trees[t]
                bt = nodes[uid]
                if self.trees.add(bt, silent=True):
                    self.nodes.add(bt, recursive=True)
            self.modified = True
            return True
        return False

    def __onRenameNode(self, libname, oldname, newname):
        if libname in self.libraries:
            library = self.libraries[libname]
            print('INFO: Trying to rename node \'{0}\' of library \'{1}\' into \'{2}\'...'
                  .format(oldname, libname, newname))
            if newname in library:
                print('ERROR: Node \'{0}\' already exist in library \'{1}\'!'.format(newname, libname))
                return False
            if oldname not in library:
                print('WARNING: There are no node \'{0}\' in library \'{1}\'.'.format(oldname, libname))
                return False

            globals.historySignals.pushState.emit(
                'Rename \'{0}\' node to \'{1}\' in library \'{2}\''.format(oldname, newname, libname))

            node = library.list[oldname]
            del library.list[oldname]
            node.name = newname
            library.list[newname] = node
            print('OK: Node \'{0}\' of library \'{1}\' has been renamed to \'{2}\'.'.format(oldname, libname, newname))
            self.modified = True

            for uid in self.nodes:
                treeNode = self.nodes[uid]
                treeNode.rename(libname, oldname, newname, recursive=False)

            globals.librarySignals.nodeRenamed.emit(libname, oldname, newname)

    def __onRemoveNode(self, libname, nodename):
        if libname in self.libraries and nodename in self.libraries[libname]:
            usedBy = globals.project.trees.getBranchesByNode(libname, nodename, self.nodes)
            if usedBy:
                message = '<font color=\"red\">'
                message += trStr('Node <b>\'{0}\'</b> is used by branches:'.format(nodename),
                                 'Узел <b>\'{0}\'</b> используется в деревьях:'.format(nodename)).text()
                message += '</font>'
                for branchName in usedBy:
                    message += '<br/>- <b>{0}</b>'.format(usedBy[branchName].refname())
                message += '<br/>'
            else:
                message = ''
            message += trStr('<font color=\"red\">Do You really want to delete \
                             node <b>\'{0}\'</b>?</font>'.format(nodename),

                             '<font color=\"red\">Вы действительно хотите удалить \
                             узел <b>\'{0}\'</b>?</font>'.format(nodename))\
                .text()
            title = trStr('Delete node', 'Удаление узла').text()
            if QMessageBox.warning(None, title, message,
                                   QMessageBox.Yes | QMessageBox.No, QMessageBox.No) == QMessageBox.Yes:
                globals.historySignals.pushState.emit(
                    'Delete \'{0}\' node from library \'{1}\''.format(nodename, libname))
                library = self.libraries[libname]
                print('warning: {0} {1} node \'{2}\' have been removed from \'{3}\' library!'
                      .format(library.list[nodename].nodeType, library.list[nodename].nodeClass, nodename, libname))
                nodeClass = library.list[nodename].nodeClass
                del library.list[nodename]
                self.modified = True
                globals.librarySignals.nodeRemoved.emit(libname, nodename, nodeClass)

    def __onChangeCreatorNode(self, libname, nodename, creator):
        if libname in self.libraries and nodename in self.libraries[libname]:
            if creator:
                print('OK: Creator for node \'{0}\' of library \'{1}\' is set to \'{2}\'.'
                      .format(nodename, libname, creator))
            else:
                print('OK: Creator for node \'{0}\' of library \'{1}\' was removed.'.format(nodename, libname))
            globals.historySignals.pushState.emit(
                'Change creator for node \'{0}\' in library \'{1}\''.format(nodename, libname))
            library = self.libraries[libname]
            creatorOld = library.list[nodename].creator
            library.list[nodename].setCreator(creator)
            self.modified = True
            globals.librarySignals.creatorChanged.emit(libname, nodename, creatorOld, creator)

    def __onRenameAttrNode(self, libname, nodename, oldname, newname, full):
        if libname in self.libraries and nodename in self.libraries[libname]:
            globals.historySignals.pushState.emit(
                'Rename attribute for node \'{0}\' in library \'{1}\''.format(nodename, libname))
            success, attrname = self.libraries[libname].list[nodename].renameAttribute(oldname, newname, full)
            if success:
                self.modified = True

                for uid in self.nodes:
                    treeNode = self.nodes[uid]
                    treeNode.renameAttribute(libname, nodename, oldname, attrname, recursive=False)

                globals.librarySignals.attribueRenamed.emit(libname, nodename, oldname, attrname)
            else:
                globals.historySignals.popState.emit()

    def __onChangeAttributeNode(self, libname, nodename, attributeName, attributeDesc):
        if libname in self.libraries and nodename in self.libraries[libname]:
            node = self.libraries[libname].list[nodename]
            old_attr = node[attributeName]
            globals.historySignals.pushState.emit(
                'Modify attribute for node \'{0}\' in library \'{1}\''.format(nodename, libname))
            if old_attr is not None and node.replaceAttribute(attributeName, attributeDesc):
                self.modified = True

                for uid in self.nodes:
                    treeNode = self.nodes[uid]
                    treeNode.validateAttribute(libname, nodename, attributeName, old_attr, recursive=False)

                globals.librarySignals.attribueChanged.emit(libname, nodename, attributeName, old_attr)
            else:
                globals.historySignals.popState.emit()

    def __onAddAttributeNode(self, libname, nodename, attributeName, attributeDesc):
        if libname in self.libraries and nodename in self.libraries[libname]:
            node = self.libraries[libname].list[nodename]
            globals.historySignals.pushState.emit(
                'Add new attribute for node \'{0}\' in library \'{1}\''.format(nodename, libname))
            if node.addAttribute(attributeDesc):
                self.modified = True

                for uid in self.nodes:
                    treeNode = self.nodes[uid]
                    treeNode.addAttribute(libname, nodename, attributeName, recursive=False)

                globals.librarySignals.attribueAdded.emit(libname, nodename, attributeName)
            else:
                globals.historySignals.popState.emit()

    def __onDeleteAttributeNode(self, libname, nodename, attributeName):
        if libname in self.libraries and nodename in self.libraries[libname]:
            node = self.libraries[libname].list[nodename]
            globals.historySignals.pushState.emit(
                'Delete attribute for node \'{0}\' in library \'{1}\''.format(nodename, libname))
            if node.deleteAttribute(attributeName):
                self.modified = True

                for uid in self.nodes:
                    treeNode = self.nodes[uid]
                    treeNode.deleteAttribute(libname, nodename, attributeName, recursive=False)

                globals.librarySignals.attribueDeleted.emit(libname, nodename, attributeName)
            else:
                globals.historySignals.popState.emit()

    def __onAddNewNodeToLibrary(self, libname, nodeClass, nodeType):
        if libname in self.libraries:
            print('debug: adding new {0} {1} node into {2} library ...'.format(nodeType, nodeClass, libname))
            node_class = globals.project.alphabet[nodeClass]
            if node_class is None:
                print('error: Can\'t create new node for unknown class \'{0}\'!'.format(nodeClass))
                return
            node_type = node_class[nodeType]
            if node_type is None:
                print('error: Can\'t create new node for unknown type \'{0}\' of class \'{1}\'!'
                      .format(nodeType, nodeClass))
                return
            if node_type.isLink():
                print('error: Can\'t create new node for type \'{0}\' of class \'{1}\'! Type \'{0}\' is link!'
                      .format(nodeType, nodeClass))
                return
            nodename = 'NewNode_{0}'.format(datetime.datetime.now().time())
            library = self.libraries[libname]
            while nodename in library:
                sleep(0.01)
                nodename = 'NewNode_{0}'.format(datetime.datetime.now().time())
            newNode = TreeNodeDesc(nodename, nodeClass, nodeType, libname, False)
            newNode.description = 'New node created by user.'
            newNode.shape = globals.project.shapelib.defaultShape()
            color = node_class.defaultState().colorEnabled
            newNode.icon = newNode.shape.icon(color)
            for c in node_type.children:
                child = node_type.children[c]
                if child.obligatory():
                    newNode.childClasses.append(c)

            globals.historySignals.pushState.emit(
                'Add new node \'{0}\' into library \'{1}\''.format(nodename, libname))

            library.list[nodename] = newNode
            print('ok: added new {0} {1} node \'{2}\' into {3} library'.format(nodeType, nodeClass, nodename, libname))
            self.modified = True

            globals.librarySignals.nodeAdded.emit(libname, nodename)

    def __onAddNodeToLibrary(self, libname, node):
        if libname in self.libraries:
            print('debug: adding {0} {1} \'{2}\' node into library \'{3}\' ...'
                  .format(node.nodeType, node.nodeClass, node.name, libname))
            if not node.name:
                print('error: Can\'t add node without name!')
                return
            node_class = globals.project.alphabet[node.nodeClass]
            if node_class is None:
                print('error: Can\'t add node of unknown class \'{0}\'!'.format(node.nodeClass))
                return
            node_type = node_class[node.nodeType]
            if node_type is None:
                print('error: Can\'t add node of unknown type \'{0}\' of class \'{1}\'!'
                      .format(node.nodeType, node.nodeClass))
                return
            if node_type.isLink():
                print('error: Can\'t add node for type \'{0}\' of class \'{1}\'! Type \'{0}\' is link!'
                      .format(node.nodeType, node.nodeClass))
                return

            library = self.libraries[libname]
            if node.name in library:
                nodename = '{0}_{1}'.format(node.name, datetime.datetime.now().time())
                while nodename in library:
                    sleep(0.01)
                    nodename = '{0}_{1}'.format(node.name, datetime.datetime.now().time())
            else:
                nodename = node.name

            node.setName(nodename)
            node.setLibrary(libname)

            globals.historySignals.pushState.emit('Add node \'{0}\' into library \'{1}\''.format(nodename, libname))

            library.list[nodename] = node
            print('ok: added {0} {1} node \'{2}\' into {3} library'
                  .format(node.nodeType, node.nodeClass, nodename, libname))
            self.modified = True

            globals.librarySignals.nodeAdded.emit(libname, nodename)

    def __onRenameLibraryQuery(self, oldName, newName):
        if oldName in self.libraries:
            print('info: Renaming library \'{0}\' to \'{1}\' ...'.format(oldName, newName))

            if newName in self.libraries:
                print('warning: Library with name \'{0}\' already exist! Library \'{1}\' will not be renamed.'
                      .format(newName, oldName))
                print('')
                return

            lib = self.libraries[oldName]
            lib.libname = newName

            for nodeName in lib.list:
                lib.list[nodeName].setLibrary(newName)

            for node in self.nodes:
                if node.libname == oldName:
                    node.setLibName(newName)

            self.libraries[newName] = lib
            del self.libraries[oldName]

            print('ok: Library \'{0}\' renamed to \'{1}\''.format(oldName, newName))
            print('')

            globals.librarySignals.libraryRenamed.emit(oldName, newName)

    def __onChangeTypeNode(self, libname, nodename, typeName):
        if libname in self.libraries and nodename in self.libraries[libname] \
                and self.libraries[libname].list[nodename].nodeType != typeName:
            library = self.libraries[libname]
            node = library.list[nodename]
            print('debug: changing type for {0} {1} node \'{2}\' of library \'{3}\'...'
                  .format(node.nodeType, node.nodeClass, nodename, libname))
            node_class = globals.project.alphabet[node.nodeClass]
            if node_class is None:
                print('error: CRITICAL ERROR: Can\'t find class \'{0}\''.format(node.nodeClass))
                return
            node_type = node_class[typeName]
            if node_type is None:
                print('error: Can\'t change type for node \'{0}\' from \'{1}\' to \'{2}\' \
                        because it is not sub type for \'{3}\' class'
                      .format(nodename, node.nodeType, typeName, node.nodeClass))
                return
            if node_type.isLink():
                print('error: Can\'t change type for node \'{0}\' from \'{1}\' to \'{2}\' because it is link-type.'
                      .format(nodename, node.nodeType, typeName))
                return

            globals.historySignals.pushState.emit(
                'Change type for node \'{0}\' in library \'{1}\''.format(nodename, libname))

            typeOld, node.nodeType = node.nodeType, typeName
            remove_list = []
            for c in node.childClasses:
                if c not in node_type:
                    remove_list.append(c)
            for r in remove_list:
                node.childClasses.remove(r)
            for c in node_type.children:
                if c not in node.childClasses:
                    child = node_type.children[c]
                    if child.obligatory():
                        node.childClasses.append(c)
            print('ok: type of {0}::{1} node was changed from \'{2}\' to \'{3}\''
                  .format(libname, nodename, typeOld, typeName))

            self.modified = True

            for uid in self.nodes:
                treeNode = self.nodes[uid]
                treeNode.changeType(libname, nodename, typeName, recursive=False)

            globals.librarySignals.nodeTypeChanged.emit(libname, nodename, typeOld, typeName)

    def __onChangeChildrenNode(self, libname, nodename, childrenList):
        if libname in self.libraries and nodename in self.libraries[libname]:
            node = self.libraries[libname].list[nodename]
            node_class = globals.project.alphabet[node.nodeClass]
            node_type = node_class[node.nodeType]
            accepted_children = []
            for cls_name in childrenList:
                if cls_name in node_type.children:
                    child = node_type.children[cls_name]
                    if child.used():
                        accepted_children.append(cls_name)
            for cls_name in node_type.children:
                child = node_type.children[cls_name]
                if child.used() and child.obligatory() and cls_name not in accepted_children:
                    # we have to use an obligatory classes
                    accepted_children.append(cls_name)

            globals.historySignals.pushState.emit(
                'Change possible child types for node \'{0}\' in library \'{1}\''.format(nodename, libname))

            node.childClasses = accepted_children
            self.modified = True

            globals.librarySignals.nodeChildrenChanged.emit(libname, nodename)

    def __onChangeDescriptionNode(self, libname, nodename, description):
        if libname in self.libraries and nodename in self.libraries[libname]:
            globals.historySignals.pushState.emit(
                'Change description for node \'{0}\' in library \'{1}\''.format(nodename, libname))
            self.libraries[libname].list[nodename].description = description
            self.modified = True
            globals.librarySignals.nodeDescriptionChanged.emit(libname, nodename, description)

    def __onShapeChangeNode(self, libname, nodename, shapename):
        if libname in self.libraries and nodename in self.libraries[libname]:
            if self.shapelib is not None and shapename in self.shapelib:
                globals.historySignals.pushState.emit(
                    'Change shape for node \'{0}\' in library \'{1}\''.format(nodename, libname))
                node = self.libraries[libname].list[nodename]
                node.shape = self.shapelib[shapename]
                color = globals.project.alphabet[node.nodeClass].defaultState().colorEnabled
                node.icon = node.shape.icon(color)
                self.modified = True
                globals.librarySignals.nodeShapeChanged.emit(libname, nodename, shapename)

    def __onIncomingEventRenameNode(self, libname, nodename, oldname, newname):
        if libname in self.libraries and nodename in self.libraries[libname]:
            node = self.libraries[libname].list[nodename]
            if oldname in node.incomingEvents:
                index = node.incomingEvents.index(oldname)
                if index >= 0:
                    globals.historySignals.pushState.emit('Change incoming event name for \
                        node \'{0}\' in library \'{1}\''.format(nodename, libname))
                    node.incomingEvents[index] = newname
                    self.modified = True

    def __onOutgoingEventRenameNode(self, libname, nodename, oldname, newname):
        if libname in self.libraries and nodename in self.libraries[libname]:
            node = self.libraries[libname].list[nodename]
            if oldname in node.outgoingEvents:
                index = node.outgoingEvents.index(oldname)
                if index >= 0:
                    globals.historySignals.pushState.emit('Change outgoing event name for \
                        node \'{0}\' in library \'{1}\''.format(nodename, libname))
                    node.outgoingEvents[index] = newname
                    self.modified = True

    def __onIncomingEventAddNode(self, libname, nodename, eventName):
        if libname in self.libraries and nodename in self.libraries[libname]:
            node = self.libraries[libname].list[nodename]
            if eventName not in node.incomingEvents:
                globals.historySignals.pushState.emit(
                    'Add new incoming event for node \'{0}\' in library \'{1}\''.format(nodename, libname))
                node.incomingEvents.append(eventName)
                self.modified = True
                globals.librarySignals.nodeEventsCountChanged.emit(libname, nodename)

    def __onOutgoingEventAddNode(self, libname, nodename, eventName):
        if libname in self.libraries and nodename in self.libraries[libname]:
            node = self.libraries[libname].list[nodename]
            if eventName not in node.outgoingEvents:
                globals.historySignals.pushState.emit(
                    'Add new outgoing event for node \'{0}\' in library \'{1}\''.format(nodename, libname))
                node.outgoingEvents.append(eventName)
                self.modified = True
                globals.librarySignals.nodeEventsCountChanged.emit(libname, nodename)

    def __onIncomingEventDeleteNode(self, libname, nodename, eventName):
        if libname in self.libraries and nodename in self.libraries[libname]:
            node = self.libraries[libname].list[nodename]
            if eventName in node.incomingEvents:
                index = node.incomingEvents.index(eventName)
                if index >= 0:
                    globals.historySignals.pushState.emit(
                        'Remove incoming event for node \'{0}\' in library \'{1}\''.format(nodename, libname))
                    node.incomingEvents.pop(index)
                    self.modified = True
                    globals.librarySignals.nodeEventsCountChanged.emit(libname, nodename)

    def __onOutgoingEventDeleteNode(self, libname, nodename, eventName):
        if libname in self.libraries and nodename in self.libraries[libname]:
            node = self.libraries[libname].list[nodename]
            if eventName in node.outgoingEvents:
                index = node.outgoingEvents.index(eventName)
                if index >= 0:
                    globals.historySignals.pushState.emit(
                        'Remove outgoing event for node \'{0}\' in library \'{1}\''.format(nodename, libname))
                    node.outgoingEvents.pop(index)
                    self.modified = True
                    globals.librarySignals.nodeEventsCountChanged.emit(libname, nodename)

########################################################################################################################
########################################################################################################################
