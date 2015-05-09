# coding=utf-8
# -----------------
# file      : globals.py
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

""" Script file with global Behavior Studio variables. """

__author__ = 'Victor Zarubkin'
__copyright__ = 'Copyright (C) 2012  Victor Zarubkin'
__credits__ = ['Victor Zarubkin']
__license__ = ['GPLv3']
__version__ = '1.3.0'  # this is last application version when this script file was changed
__email__ = 'victor.zarubkin@gmail.com'
############################################################################

from PySide.QtCore import Signal as QtSignal, QObject
from language import trStr
from treenode import Uid, TreeNodeDesc

########################################################################################################################
########################################################################################################################


def versionToInt(versionTuple):
    """ Converts version tuple to single integer value.

    Output integer value will look like 122 (if version is (1, 2, 2)).

    :param versionTuple: A tuple containing version (for example, (1, 2, 2))
    :return: An integer representation of version
    """

    return int(''.join([str(digit) for digit in versionTuple]))


def versionToStr(versionTuple):
    """ Converts version tuple to string.

    Output string will be formatted like '1.2.2' (if version is (1, 2, 2)).

    :param versionTuple: A tuple containing version (for example, (1, 2, 2))
    :return: Text representation of version
    """

    return '.'.join([str(digit) for digit in versionTuple])


def versionFromStr(versionString):
    """ Converts string to version tuple.

    Splits version numbers by '.' character, converts them into integer values
    and combine them all together into a tuple.

    :param versionString: String containing version (for example, '1.2.2')
    :return: Version tuple (something like (1, 2, 2))
    """

    return tuple([int(digit) for digit in versionString.split('.')])

########################################################################################################################

version = versionFromStr(__version__)  # Current application version (It is a tuple. Example: (1, 2, 1))
strVersion = str(__version__)  # Current application version string (example: '1.2.1')
intVersion = versionToInt(version)  # Current application version digits packed into single integer (example: 121)

# Recent versions list to be able to read previous versions application settings from system register (using QSettings)
_previousVersions = [
    (1, 2, 6),
    (1, 2, 5),
    (1, 2, 4),
    (1, 2, 3)
]
intPreviousVersions = [versionToInt(ver) for ver in _previousVersions]

scaleMax = 450.0  # Maximum scaling factor for graphics scene (Initial value is 100.0)
scaleMin = 3.0  # Minimum scaling factor for graphics scene (Initial value is 100.0)

pressedKeys = []  # Current global pressed keys (Example: [Qt.Key_Ctrl, Qt.Key_C])

applicationConfigFile = [u'../config/config.xml', u'../../../data/behavior/editor/config.xml']
applicationIconsPath = u''

recentProjectsFile = u'recent_projects.txt'
recentProjects = []
maxRecentProjects = int(10)

historyEnabled = True
maxBehaviorTreeHistory = int(20)

explicitConfig = False
showLogo = True

itemsAnimation = True
itemsShadow = True
connectorsHighlight = False
connectorsBold = True

linksEditable = False

displayConstantaCopyright = False

saveLibraries = False
editLibraries = False

debugMode = False  # Debug mode. If 'True' then there will be lots of debug messages in the 'Output' dock window

''' Global clipboard used to copy/paste trees and tree-nodes '''
clipboard = {
    'tree-node': None,
    'node-desc': None
}

project = None  # Current tree project

autosaveEnabled = False  # Is auto saving enabled
autosaveTime = 45.0  # Interval in seconds for auto-saving project and libs

''' Background images paths for graphics scene '''
backgrounds = [
    '../background.png',
    '../background1.png',
    '../background2.png',
    '../background3.png',
]

''' Current background image index for graphics scene.

If < 0 or > len(backgrounds)-1 then no background will be displayed. '''
background = 1

########################################################################################################################


class _OptionsSignals(QObject):
    shadowsChanged = QtSignal(bool)
    connectorHighlightingChanged = QtSignal(bool)
    connectorsBoldChanged = QtSignal(bool)
    backgroundChanged = QtSignal(int)


optionsSignals = _OptionsSignals()  # signals used to notify about global options change

########################################################################################################################


class _LibrarySignals(QObject):
    renameNode = QtSignal(str, str, str)  # (library name, node current name, node new name)
    nodeRenamed = QtSignal(str, str, str)  # (library name, node old name, node new name)

    removeNode = QtSignal(str, str)  # (library name, node name)
    nodeRemoved = QtSignal(str, str, str)  # (library name, node name, node class)

    addNewNode = QtSignal(str, str, str)  # (library name, new node class name, new node type name)
    addNode = QtSignal(str, TreeNodeDesc)  # (library name, node desctiptor)
    nodeAdded = QtSignal(str, str)  # (library name, new node name)

    changeNodeType = QtSignal(str, str, str)  # (library name, node name, new type name)
    nodeTypeChanged = QtSignal(str, str, str, str)  # (library name, node name, old type name, new type name)

    changeNodeChildren = QtSignal(str, str, list)  # (library name, node name, list of available child classes)
    nodeChildrenChanged = QtSignal(str, str)  # (library name, node name)

    changeNodeDescription = QtSignal(str, str, str)  # (library name, node name, new description)
    nodeDescriptionChanged = QtSignal(str, str, str)  # (library name, node name, new description)

    changeNodeShape = QtSignal(str, str, str)  # (library name, node name, shape name)
    nodeShapeChanged = QtSignal(str, str, str)  # (library name, node name, shape name)

    changeCreator = QtSignal(str, str, str)  # (library name, node name, creator new name)
    creatorChanged = QtSignal(str, str, str, str)  # (library name, node name, creator old name, creator new name)

    renameAttribute = QtSignal(str, str, str, str, bool)  # (library name, node name, attribute old name, attribute new name, flag of that new name is full (includes path) )
    attribueRenamed = QtSignal(str, str, str, str)  # (library name, node name, attribute old full name (include path), attribute new full name)

    changeAttribute = QtSignal(str, str, str, object)  # (library name, node name, attribute full name (include path), attribute descriptor)
    attribueChanged = QtSignal(str, str, str, object)  # (library name, node name, attribute full name (include path), previous attribute descriptor)

    addAttribute = QtSignal(str, str, str, object)  # (library name, node name, attribute full name (include path), attribute descriptor)
    attribueAdded = QtSignal(str, str, str)  # (library name, node name, attribute full name (include path))

    deleteAttribute = QtSignal(str, str, str)  # (library name, node name, attribute full name (include path))
    attribueDeleted = QtSignal(str, str, str)  # (library name, node name, attribute full name (include path))

    renameIncomingEvent = QtSignal(str, str, str, str)  # (library name, node name, old event name, new event name)
    renameOutgoingEvent = QtSignal(str, str, str, str)  # (library name, node name, old event name, new event name)

    deleteIncomingEvent = QtSignal(str, str, str)  # (library name, node name, event name)
    deleteOutgoingEvent = QtSignal(str, str, str)  # (library name, node name, event name)

    addIncomingEvent = QtSignal(str, str, str)  # (library name, node name, event name)
    addOutgoingEvent = QtSignal(str, str, str)  # (library name, node name, event name)

    nodeEventsCountChanged = QtSignal(str, str)  # (library name, node name)

    excludeLibrary = QtSignal(str)  # (library name)
    libraryExcluded = QtSignal(str)  # (library name)
    libraryAdded = QtSignal(str)  # (library name)

    renameLibrary = QtSignal(str, str)  # (old library name, new library name)
    libraryRenamed = QtSignal(str, str)  # (old library name, new library name)

    editPermissionChanged = QtSignal(bool)  # (edit library permission flag (True or False))


librarySignals = _LibrarySignals()  # signals emited by NodeLibrary (see treenode.py)

########################################################################################################################


class _BehaviorTreeSignals(QObject):
    treeDeleted = QtSignal(str)
    treeRenamed = QtSignal(str, str)
    treeOpened = QtSignal(str, str)
    treeClosed = QtSignal(str, str)
    treeRootChanged = QtSignal(str, str, Uid, Uid)  # first arg - file path, second arg - short tree name, third arg - old root Uid, fourth arg - new root Uid
    nodeDisconnected = QtSignal(Uid, Uid)  # first argument - uid of node, second argument - uid of parent node
    nodeConnected = QtSignal(Uid, Uid)  # first argument - uid of node, second argument - uid of parent node


behaviorTreeSignals = _BehaviorTreeSignals()  # signals emited by BehaviorTree (see treenode.py)

########################################################################################################################


class _TreeListSignals(QObject):
    doubleClicked = QtSignal(str)  # mouse has double clicked on a tree in the tree list window

    branchGrabbed = QtSignal(str)  # tree has been grabbed by mouse in the tree list window
    branchReleased = QtSignal(int, int)  # tree released by mouse in the tree list window
    branchMove = QtSignal(int, int)  # mouse with grabbed tree has moved to new position

    openExistingTreeFile = QtSignal()  # tree-list context menu event - user want to add existing tree into project
    createNewTreeFile = QtSignal()  # tree-list context menu event - user want to add new tree into project


treeListSignals = _TreeListSignals()  # signals emited by the tree list window (TL_Tree in tltree.py)

########################################################################################################################


class _NodeLibraryListSignals(QObject):
    nodeGrabbed = QtSignal(str, str)  # node grabbed by mouse in the library list window
    nodeReleased = QtSignal(int, int)  # node released by mouse in the library list window
    grabMove = QtSignal(int, int)  # mouse with grabbed node has moved to new position

    libSelected = QtSignal(str)  # library selected in the library list window
    nodeSelected = QtSignal(str, str)  # node selected in the library list window
    notSelected = QtSignal()  # selection cancelled in the library list window

    openExistingLibraryFile = QtSignal()  # library list context menu event - user want to add existing library into project
    createNewLibraryFile = QtSignal()  # library list context menu event - user want to add new library into project


nodeListSignals = _NodeLibraryListSignals()  # signals emited by the library list window (LL_Tree in lltree.py)

########################################################################################################################


class _HistorySignals(QObject):
    pushState = QtSignal(str)
    popState = QtSignal()

    undoRedoChange = QtSignal()

    undo = QtSignal()
    undoMade = QtSignal()

    redo = QtSignal()
    redoMade = QtSignal()


historySignals = _HistorySignals()  # signals used to control history

########################################################################################################################


class _GeneralSignals(QObject):
    preSave = QtSignal()  # signal automatically emitted just before project will be saved
    sceneItemPos = QtSignal(bool, float, float)


generalSignals = _GeneralSignals()

########################################################################################################################


def getDebugMode():
    global debugMode
    return debugMode


def setDebugMode(val):
    global debugMode
    if not val:
        print(trStr('debug: DEBUG MODE is \'OFF\'', u'debug: РЕЖИМ ОТЛАДКИ \'ВЫКЛ\'').text())
        print('')
    debugMode = val
    if val:
        print(trStr('debug: DEBUG MODE is \'ON\'', u'debug: РЕЖИМ ОТЛАДКИ \'ВКЛ\'').text())
        print('')

########################################################################################################################


def getAnimation():
    global itemsAnimation
    return itemsAnimation


def setAnimation(val):
    global itemsAnimation
    itemsAnimation = val
    if val:
        print(trStr('info: Animation is \'ON\'', u'info: Анимация \'ВКЛ\'').text())
    else:
        print(trStr('info: Animation is \'OFF\'', u'info: Анимация \'ВЫКЛ\'').text())
    print('')

########################################################################################################################


def getDropShadow():
    global itemsShadow
    return itemsShadow


def setDropShadow(val):
    global itemsShadow
    global optionsSignals
    itemsShadow = val
    if val:
        print(trStr('info: Drop shadows is \'ON\'', u'info: Тени \'ВКЛ\'').text())
    else:
        print(trStr('info: Drop shadows is \'OFF\'', u'info: Тени \'ВЫКЛ\'').text())
    print('')
    optionsSignals.shadowsChanged.emit(bool(itemsShadow))

########################################################################################################################


def getConnectorsHighlight():
    global connectorsHighlight
    return connectorsHighlight


def setConnectorsHighlight(val):
    global connectorsHighlight
    global optionsSignals
    connectorsHighlight = val
    if val:
        print(trStr('info: Active connector highlighting is \'ON\'',
                    u'info: Подсвечивание активных соединительных линий \'ВКЛ\'').text())
    else:
        print(trStr('info: Active connector highlighting is \'OFF\'',
                    u'info: Подсвечивание активных соединительных линий \'ВЫКЛ\'').text())
    print('')
    optionsSignals.connectorHighlightingChanged.emit(bool(connectorsHighlight))

########################################################################################################################


def getConnectorsBold():
    global connectorsBold
    return connectorsBold


def setConnectorsBold(val):
    global connectorsBold
    global optionsSignals
    connectorsBold = val
    if val:
        print(trStr('info: Bold active connectors is \'ON\'',
                    u'info: Выделение жирным активных соединительных линий \'ВКЛ\'').text())
    else:
        print(trStr('info: Bold active connectors is \'OFF\'',
                    u'info: Выделение жирным активных соединительных линий \'ВЫКЛ\'').text())
    print('')
    optionsSignals.connectorsBoldChanged.emit(bool(connectorsBold))

########################################################################################################################


def getLibsSave():
    global saveLibraries
    return saveLibraries


def setLibsSave(val):
    global saveLibraries
    saveLibraries = val
    if val:
        print(trStr('info: Saving libraries is \'ON\'', u'info: Сохранение библиотек \'ВКЛ\'').text())
    else:
        print(trStr('info: Saving libraries is \'OFF\'', u'info: Сохранение библиотек \'ВЫКЛ\'').text())
    print('')


########################################################################################################################


def getLibsEdit():
    global editLibraries
    return editLibraries


def setLibsEdit(val):
    global editLibraries
    editLibraries = val
    if val:
        print(trStr('info: Editing node libraries is \'ON\'', u'info: Редактирование библиотек \'ВКЛ\'').text())
    else:
        print(trStr('info: Editing node libraries is \'OFF\'', u'info: Редактирование библиотек \'ВЫКЛ\'').text())
    print('')
    librarySignals.editPermissionChanged.emit(editLibraries)

########################################################################################################################


def getShowLogo():
    global showLogo
    return showLogo


def setShowLogo(val):
    global showLogo
    showLogo = val

########################################################################################################################


def getAutosaveEnabled():
    global autosaveEnabled
    return autosaveEnabled


def setAutosaveEnabled(val):
    global autosaveEnabled
    global autosaveTime
    autosaveEnabled = val
    if val:
        print(trStr('info: Auto saving is \'ON\'. Auto save interval is {0} seconds'.format(autosaveTime),
                    u'info: Автосохранение \'ВКЛ\'. Интервал автосохранения {0} секунд'.format(autosaveTime)).text())
    else:
        print(trStr('info: Auto saving is \'OFF\'', u'info: Автосохранение \'ВЫКЛ\'').text())
    print('')

########################################################################################################################
########################################################################################################################

