# coding=utf-8
# -----------------
# file      : history.py
# date      : 2014/05/25
# author    : Victor Zarubkin
# contact   : victor.zarubkin@gmail.com
# copyright : Copyright (C) 2014  Victor Zarubkin
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
__copyright__ = 'Copyright (C) 2014  Victor Zarubkin'
__credits__ = ['Victor Zarubkin']
__license__ = ['GPLv3']
__version__ = '1.3.0'  # this is last application version when this script file was changed
__email__ = 'victor.zarubkin@gmail.com'
############################################################################

import copy

from inspect import currentframe, getframeinfo

from PySide.QtCore import QObject, Slot as QtSlot, Signal as QtSignal
from PySide.QtGui import QAction

import globals

#######################################################################################################################
#######################################################################################################################


class _State(object):
    def __init__(self, message, project, index):
        self.index = index
        self.message = message
        self.modified = project.modified
        self.trees = project.trees.deepcopy()
        self.nodes = project.nodes.deepcopy(True)
        self.libraries = dict()
        for libname in project.libraries:
            self.libraries[libname] = project.libraries[libname].deepcopy()
        self.tree_paths = copy.copy(project.tree_paths)
        self.lib_paths = copy.copy(project.lib_paths)


class _StateRole(object):
    Undo = 1
    Redo = 2


class _StateAction(QAction):
    pressed = QtSignal(QAction)

    def __init__(self, state, role):
        QAction.__init__(self, '{0} {1}'.format(state.index, state.message), None)
        self.state = state
        self.role = role
        self.triggered.connect(self.__onTrigger)

    @QtSlot()
    def __onTrigger(self):
        self.pressed.emit(self)

#######################################################################################################################
#######################################################################################################################


class History(QObject):
    def __init__(self, project):
        QObject.__init__(self)
        self._silent = False
        self._project = project
        self._undoList = []
        self._redoList = []

    def getUndoActions(self):
        return self._undoList

    def getRedoActions(self):
        return self._redoList

    def activate(self):
        """ Start receiving undo/redo signals. """
        globals.historySignals.pushState.connect(self.push)
        globals.historySignals.undo.connect(self.undo)
        globals.historySignals.redo.connect(self.redo)

    def deactivate(self):
        """ Stop this history instance from receiving undo/redo signals. """
        globals.historySignals.pushState.disconnect(self.push)
        globals.historySignals.undo.disconnect(self.undo)
        globals.historySignals.redo.disconnect(self.redo)
        self._undoList = []
        self._redoList = []

    def hasUndoRecords(self):
        return bool(self._undoList)

    def hasRedoRecords(self):
        return bool(self._redoList)

    def _setSilent(self, silent):
        self._silent = silent

    def _popUndo(self, *args, **kwargs):
        action = self._undoList.pop(*args, **kwargs)
        action.pressed.disconnect(self._onActionTriggered)
        return action

    def _popRedo(self, *args, **kwargs):
        action = self._redoList.pop(*args, **kwargs)
        action.pressed.disconnect(self._onActionTriggered)
        return action

    def _pushUndo(self, message):
        """ Save current state into undo list. """
        action = _StateAction(_State(message, self._project, len(self._undoList)), _StateRole.Undo)
        action.pressed.connect(self._onActionTriggered)
        self._undoList.append(action)
        if len(self._undoList) > globals.maxBehaviorTreeHistory:
            self._popUndo(0)

    def _pushRedo(self, message):
        """ Save current state into redo list. """
        action = _StateAction(_State(message, self._project, len(self._redoList)), _StateRole.Redo)
        action.pressed.connect(self._onActionTriggered)
        self._redoList.append(action)
        if len(self._redoList) > globals.maxBehaviorTreeHistory:
            self._popRedo(0)

    def _restore(self, state):
        self._project.trees = state.trees
        self._project.nodes = state.nodes
        self._project.libraries = state.libraries
        self._project.modified = state.modified
        self._project.tree_paths = state.tree_paths
        self._project.lib_paths = state.lib_paths

    def clear(self):
        self._undoList = []
        self._redoList = []
        if not self._silent:
            globals.historySignals.undoRedoChange.emit()

    @QtSlot(str)
    def push(self, message):
        """ Save current state into undo list.
        Automatically deactivates if current global project is not self._project.
        """
        if globals.project is not self._project:
            self.deactivate()
            print('debug: History error: invalid project')
            print('debug: See \'project/history.py\' : {0}'.format(getframeinfo(currentframe()).lineno))
            print('debug:')
        elif globals.historyEnabled:
            self._pushUndo(message)
            if not self._silent:
                globals.historySignals.undoRedoChange.emit()

    @QtSlot()
    def pop(self):
        """ Pop last saved state from history. """
        if globals.project is not self._project:
            self.deactivate()
            print('debug: History error: invalid project')
            print('debug: See \'project/history.py\' : {0}'.format(getframeinfo(currentframe()).lineno))
            print('debug:')
        elif globals.historyEnabled and self._undoList:
            self._popUndo()
            if not self._silent:
                globals.historySignals.undoRedoChange.emit()

    @QtSlot()
    def undo(self):
        """ Make undo.
        Automatically deactivates if current global project is not self._project.
        """
        if globals.project is not self._project:
            self.deactivate()
            if not self._silent:
                print('debug: History error: invalid project')
                print('debug: See \'project/history.py\' : {0}'.format(getframeinfo(currentframe()).lineno))
                print('debug:')
        elif globals.historyEnabled and self._undoList:
            # pop last state from undo list
            lastStateAction = self._popUndo()

            # save current state into redo list
            self._pushRedo(lastStateAction.state.message)

            # make an undo
            self._restore(lastStateAction.state)

            # notify all about undo
            if not self._silent:
                print('debug: Undo action \'{0}\''.format(lastStateAction.state.message))
                print('debug:')
                globals.historySignals.undoMade.emit()

    @QtSlot()
    def redo(self):
        """ Make redo.
        Automatically deactivates if current global project is not self._project.
        """
        if globals.project is not self._project:
            self.deactivate()
            if not self._silent:
                print('debug: History error: invalid project')
                print('debug: See \'project/history.py\' : {0}'.format(getframeinfo(currentframe()).lineno))
                print('debug:')
        elif globals.historyEnabled and self._redoList:
            # pop last state from redo list
            lastStateAction = self._popRedo()

            # save current state into undo list
            self._pushUndo(lastStateAction.state.message)

            # make a redo
            self._restore(lastStateAction.state)

            # notify all about redo
            if not self._silent:
                print('debug: Redo action \'{0}\''.format(lastStateAction.state.message))
                print('debug:')
                globals.historySignals.redoMade.emit()
            
    def _undoCustom(self, stateAction):
        if globals.project is not self._project:
            self.deactivate()
            if not self._silent:
                print('debug: History error: invalid project')
                print('debug: See \'project/history.py\' : {0}'.format(getframeinfo(currentframe()).lineno))
                print('debug:')
        elif globals.historyEnabled:
            if not self._silent:
                print('debug: Want to undo action \'{0}\'...'.format(stateAction.state.message))
                print('debug:')
            if stateAction in self._undoList:
                index = self._undoList.index(stateAction)
                last = len(self._undoList) - 1
                if index != last:
                    silent = bool(self._silent)
                    self._setSilent(True)
                    for i in range(last, index, -1):
                        self.undo()
                    self._setSilent(silent)
                self.undo()

    def _redoCustom(self, stateAction):
        if globals.project is not self._project:
            self.deactivate()
            if not self._silent:
                print('debug: History error: invalid project')
                print('debug: See \'project/history.py\' : {0}'.format(getframeinfo(currentframe()).lineno))
                print('debug:')
        elif globals.historyEnabled:
            if not self._silent:
                print('debug: Want to redo action \'{0}\'...'.format(stateAction.state.message))
                print('debug:')
            if stateAction in self._redoList:
                index = self._redoList.index(stateAction)
                last = len(self._redoList) - 1
                if index != last:
                    silent = bool(self._silent)
                    self._setSilent(True)
                    for i in range(last, index, -1):
                        self.redo()
                    self._setSilent(silent)
                self.redo()

    @QtSlot(QAction)
    def _onActionTriggered(self, action):
        if globals.project is not self._project:
            self.deactivate()
            if not self._silent:
                print('debug: History error: invalid project')
                print('debug: See \'project/history.py\' : {0}'.format(getframeinfo(currentframe()).lineno))
                print('debug:')
        elif globals.historyEnabled:
            if action.role == _StateRole.Undo:
                self._undoCustom(action)
            elif action.role == _StateRole.Redo:
                self._redoCustom(action)

#######################################################################################################################
#######################################################################################################################
