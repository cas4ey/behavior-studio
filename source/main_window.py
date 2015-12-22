# coding=utf-8
# -----------------
# file      : main_window.py
# date      : 2012/09/15
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

""" Script file with definition of MainWindow class.

This is the main window of the editor.
"""

__author__ = 'Victor Zarubkin'
__copyright__ = 'Copyright (C) 2012  Victor Zarubkin'
__credits__ = ['Victor Zarubkin']
__license__ = ['GPLv3']
__version__ = '1.3.0'  # this is last application version when this script file was changed
__email__ = 'victor.zarubkin@gmail.com'
############################################################################

import sys
import os
import socket

from inspect import currentframe, getframeinfo
from datetime import datetime
from time import sleep
from xml.dom.minidom import parse

from PySide import QtCore
from PySide.QtCore import *
from PySide.QtGui import *

from extensions.widgets import trAction, trMenuWithTooltip
from extensions.help_widget import HelpWidget
from libtree import lltree, llinfo
from treelist import tltree, tlinfo
from output_log import OutputDock
from project import parser, liparser, treeparser
from treeview import tab
from treenode import NodeLibrary, BehaviorTree, TreeNodes
from treeview.connector import ConnectorType
from auxtypes import toUnixPath, absPath, joinPath
from language import Language, globalLanguage, trStr
from remote_debugger.debugger_server import DebugServer
from remote_debugger.debugger_widget import StateDebugDock

import globals

########################################################################################################################

host = socket.gethostname().lower()
startYear = 2012
lastYear = 2015

########################################################################################################################
########################################################################################################################


def _bool2attr(flag):
    if flag:
        return trStr('yes', u'да').text()
    return trStr('no', u'нет').text()


def _bool2attr2(flag):
    if flag:
        return trStr('on', u'вкл').text()
    return trStr('off', u'выкл').text()

########################################################################################################################
########################################################################################################################


class AppArgs(object):
    def __init__(self, _argv):
        self.argv = _argv
        self.current_file = str(_argv[0])
        self.options_error = False
        self.config_file = globals.applicationConfigFile
        self.config_file_default = True
        self.debug = False

        self.project_for_opening = ""

########################################################################################################################
########################################################################################################################


class ProjectAction(trAction):
    def __init__(self, wnd, filepath, titleEng, titleRus, parent=None):
        trAction.__init__(self, trStr(titleEng, titleRus), parent)
        self.__wnd = wnd
        self.__file = filepath
        self.triggered.connect(self.__onTrigger)

    @QtCore.Slot()
    def __onTrigger(self):
        self.__wnd.openProject(self.__file)


class ConfigAction(trAction):
    def __init__(self, getter, setter, title, parent=None):
        trAction.__init__(self, title, parent)
        self.setCheckable(True)
        self.__getter = getter
        self.__setter = setter
        self.setChecked(self.__getter())
        self.toggled.connect(self.__onToggle)

    @QtCore.Slot(bool)
    def __onToggle(self, checked):
        self.__setter(checked)


class ExtendedCheckableAction(trAction):
    changed = QtCore.Signal(trAction)  # Signal emits on action trigger and sends \'self\' as signal parameter

    def __init__(self, text='', parent=None):
        trAction.__init__(self, text, parent)
        self.setCheckable(True)
        self.triggered.connect(self.__onTrigger)

    @QtCore.Slot()
    def __onTrigger(self):
        self.changed.emit(self)

########################################################################################################################
########################################################################################################################


def yearsStr():
    year = datetime.now().year
    if year < lastYear:
        return u'{0}-{1}'.format(startYear, lastYear)
    return u'{0}-{1}'.format(startYear, year)


def _printColors():
        print('--------------------------------------------------------------')
        print(trStr('Colors legend:', u'Цвета сообщений:').text())
        print(trStr(u'error: █ Error messages', u'error: █ Ошибки').text())
        print(trStr(u'warning: █ Warning messages', u'warning: █ Предупреждения').text())
        print(trStr(u'info: █ Information messages', u'info: █ Информационные сообщения').text())
        print(trStr(u'ok: █ Success messages', u'ok: █ Сообщения об успешном завершении операций').text())
        dbg, globals.debugMode = globals.debugMode, True
        print(trStr(u'debug: █ Debug information', u'debug: █ Отладочная информация').text())
        globals.debugMode = dbg
        print(trStr(u'█ Other messages', u'█ Другие сообщения').text())
        print('--------------------------------------------------------------')
        print('')

########################################################################################################################
########################################################################################################################


class MainWindow(QMainWindow):
    treeViewModeChange = QtCore.Signal(bool)
    treeDragModeChange = QtCore.Signal(bool)
    treeJustifyModeChange = QtCore.Signal(bool)
    treeConnectorModeChange = QtCore.Signal(bool)
    connectorTypeChanged = QtCore.Signal(int)

    def __init__(self, args, parent=None):
        QMainWindow.__init__(self, parent)
        self.setObjectName('MainWindow')

        global host
        years = startYear  # yearsStr()

        self._connectorType = ConnectorType(ConnectorType.Polyline)

        self.setMinimumSize(800, 600)
        self.resize(1280, 800)

        self._dockOutput = OutputDock(trStr('Output', u'Вывод'))
        self._dockOutput.setObjectName('output')
        self._dockOutput.setAllowedAreas(Qt.AllDockWidgetAreas)
        sys.stdout = self._dockOutput

        self._dockDebugger = StateDebugDock(trStr('Remote debugger', u'Дистанционный отладчик'))
        self._dockDebugger.setObjectName('debugger')
        self._dockDebugger.setAllowedAreas(Qt.AllDockWidgetAreas)

        # display log colors legend
        _printColors()

        # read configuration file
        configData = self.__readConfig(args)
        if len(configData) > 1 and configData[1] is not None:
            self._connectorType.val = configData[1]

        # print welcome message and set window title
        print('ok: Welcome to Behavior Studio {0}!'.format(globals.strVersion))
        if globals.displayConstantaCopyright:
            windowTitle = 'Behavior Studio {0} | created by Victor Zarubkin, {1}'
            print('ok: created by Victor Zarubkin, {0}'.format(years))
            print('ok: mailto: victor.zarubkin@gmail.com')
            print('ok: LLC Constanta-Design, http://www.cdezign.ru/')
        else:
            windowTitle = 'Behavior Studio {0} | Copyright (C) 2012-2015  Victor Zarubkin'
            print('ok: Copyright (C) 2012-2015  Victor Zarubkin')
            print('ok: mailto: victor.zarubkin@gmail.com')
            print('ok: BehaviorStudio is distributed under terms of the GNU General Public License v3.')
            print('ok: A copy of the GNU General Public License can be found in file COPYING.')
        print('--------------------------------------------------------------')
        print('Studio output:')
        print('')

        self.setWindowTitle(windowTitle.format(globals.strVersion, years))

        # inform if there is an error in program launch options
        if args.options_error:
            print('warning: start options error!')
            print('warning: you have entered:')
            args_list = []
            for a in args.argv:
                args_list.append(str(a))
            print(u'warning: {0}'.format(' '.join(args_list)))
            print('info: available options:')
            print('info: * -h, --help - see this hint')
            print('info: * -c, --config, --config-file - set start configuration file')
            print(u'info: example: {0} -c config.xml'.format(args.current_file))
            print('')

        # print current configuration
        if len(configData) < 2 or configData[2] is None:
            print('error: config file have not been loaded!')
            print('')
        else:
            if args.config_file_default:
                conf_message = 'warning: configuration loaded from default file:'
            else:
                conf_message = 'ok: configuration loaded from file:'
            print('{0} {1}'.format(conf_message, configData[2]))
            print('')
            print(trStr('ok: application configuration:', u'ok: конфигурация приложения:').text())
            print(trStr('default language is \'english\'', u'язык интерфейса по-умолчанию - \'русский\'').text())
            print(trStr('animation = \'{0}\'', u'анимация = \'{0}\'').text().format(_bool2attr2(globals.itemsAnimation)))
            print(trStr('shadows = \'{0}\'', u'тени = \'{0}\'').text().format(_bool2attr2(globals.itemsShadow)))
            print(trStr('connectors highlight = \'{0}\'', u'подсвет соед. линий = \'{0}\'').text()
                  .format(_bool2attr2(globals.connectorsHighlight)))
            print(trStr('bold connectors = \'{0}\'', u'выделение жирным соед. линий = \'{0}\'').text()
                  .format(_bool2attr2(globals.connectorsBold)))
            print(trStr('links edit permission = \'{0}\'', u'редактируемые ссылки = \'{0}\'').text()
                  .format(_bool2attr(globals.linksEditable)))
            print(trStr('save tree files = \'yes\'', u'сохранять файлы с деревьями = \'да\'').text())
            print(trStr('save library files = \'{0}\'', u'сохранять файлы библиотек = \'{0}\'').text()
                  .format(_bool2attr(globals.saveLibraries)))
            if not globals.saveLibraries:
                print(trStr('info: libraries would not be saved. Set attribute \'saveLibs\' to \'yes\' in '
                            'Your config file to enable libraries saving.',
                            u'info: библиотеки узлов не будут сохраняться. Установите атрибут \'saveLibs\' в \'yes\' '
                            u'в конфигурационном файле, чтобы включить сохранение библиотек.').text())
            print(trStr('node libraries edit permission = \'{0}\'', u'редактируемые библиотеки = \'{0}\'').text()
                  .format(_bool2attr(globals.editLibraries)))
            if not globals.editLibraries:
                print(trStr('info: to be able to edit libraries and nodes, set attribute \'editLibs\' to \'yes\' '
                            'in Your config file.',
                            u'info: чтобы включить возможность редактирования библиотек, установите '
                            u'атрибут \'editLibs\' в \'yes\' в конфигурационном файле.').text())
            if globals.autosaveEnabled:
                print(trStr('auto saving = \'yes\'; auto saving interval = \'{0}\' sec'.format(globals.autosaveTime),
                            u'автоматическое сохранение = \'вкл\'; интервал сохранения = \'{0}\' сек'
                            .format(globals.autosaveTime)).text())
            else:
                print(trStr('auto saving = \'no\'', u'автоматическое сохранение = \'выкл\'').text())
            print(trStr('ok: end application configuration.', u'ok: конец конфигурации приложения.').text())
            print('')

        self._launchArgs = args

        # set window icon
        # globalLanguage.changeLanguage(configData[0])
        self.setWindowIcon(QIcon(joinPath(globals.applicationIconsPath, 'tree17.png')))

        # read recent projects file
        self.__readRecentProjects()

        self._menuRecentProjects = trMenuWithTooltip(trStr('Recent projects', u'Последние проекты'))
        self._menuRecentProjects.setEnabled(False)

        # ACTIONS: ---------------------------------------------
        self._actionOpenLibrary = trAction(trStr('&Load library...', u'Загрузить &библиотеку...'))
        self._actionOpenLibrary.setIcon(QIcon(joinPath(globals.applicationIconsPath, 'book_add.png')))
        self._actionOpenLibrary.setToolTip(trStr('Add existing library into project',
                                                 u'Добавить файл с библиотекой узлов в проект'))
        self._actionCreateLibrary = trAction(trStr('&Create library...', u'&Создать библиотеку...'))
        self._actionCreateLibrary.setIcon(QIcon(joinPath(globals.applicationIconsPath, 'book_add.png')))
        self._actionCreateLibrary.setToolTip(trStr('Create new library file\nand add it into project',
                                                   u'Создать пустой файл с библиотекой\nузлов и добавить его в проект'))
        self._actionOpenTree = trAction(trStr('Open existing &tree file...', u'Открыть файл с &деревом...'))
        self._actionOpenTree.setToolTip(trStr('Open existing tree file and\ninclude it into project',
                                        u'Открыть существующий файл с деревом\nи добавить его в проект'))
        self._actionOpenTree.setIcon(QIcon(joinPath(globals.applicationIconsPath, 'chart_add2.png')))
        self._actionCreateTree = trAction(trStr('Create &new tree file...', u'Создать &файл с деревом...'))
        self._actionCreateTree.setToolTip(trStr('Create new tree file and\ninclude it into project',
                                                u'Создать новый файл с деревом\nи добавить его в проект'))
        self._actionCreateTree.setIcon(QIcon(joinPath(globals.applicationIconsPath, 'chart_add.png')))
        self._actionOpenProject_menu = trAction(trStr('&Open project...', u'Открыть &проект...'))
        self._actionOpenProject_menu.setIcon(QIcon(joinPath(globals.applicationIconsPath, 'folder_page.png')))
        self._actionSaveProject_menu = trAction(trStr('&Save all', u'&Сохранить все'))
        self._actionSaveProject_menu.setIcon(QIcon(joinPath(globals.applicationIconsPath, 'save.png')))
        self._actionSaveProject_menu.setEnabled(False)
        self._actionReadAlphabet = trAction(trStr('Read &alphabet...', u'Открыть файл &алфавита...'))
        self._actionExit = trAction(trStr('&Exit', u'&Выход'))
        self._actionExit.setIcon(QIcon(joinPath(globals.applicationIconsPath, 'door.png')))

        self._optionsActionAnimation = ConfigAction(globals.getAnimation, globals.setAnimation,
                                                    trStr('Animaton', u'Анимация'))
        self._optionsActionSaveLibraries = ConfigAction(globals.getLibsSave, globals.setLibsSave,
                                                        trStr('Save libraries', u'Сохранение библиотек'))
        self._optionsActionEditLibraries = ConfigAction(globals.getLibsEdit, globals.setLibsEdit,
                                                        trStr('Edit libraries', u'Редактирование библиотек'))
        self._optionsActionDebug = ConfigAction(globals.getDebugMode, globals.setDebugMode,
                                                trStr('Debug mode', u'Режим отладки'))
        self._optionsActionLogo = ConfigAction(globals.getShowLogo, globals.setShowLogo,
                                               trStr('Show logo on startup', u'Показывать логотип при старте'))
        self._optionsActionShadows = ConfigAction(globals.getDropShadow, globals.setDropShadow,
                                                  trStr('Shadows', u'Тени'))
        self._optionsActionHighlightConnectors = ConfigAction(
            globals.getConnectorsHighlight, globals.setConnectorsHighlight,
            trStr('Connectors highlight', u'Подсвет соед. линий')
        )
        self._optionsActionBoldConnectors = ConfigAction(
            globals.getConnectorsBold, globals.setConnectorsBold,
            trStr('Bold connectors', u'Выделение жирным соед. линий')
        )
        self._optionsActionAutosave = ConfigAction(globals.getAutosaveEnabled, globals.setAutosaveEnabled,
                                                   trStr('Autosave', u'Автосохранение'))

        self._actionDisableBackground = trAction(trStr('None', u'Отсутствует'))
        self._actionDisableBackground.setCheckable(True)
        self._actionDisableBackground.setToolTip(trStr('Do not draw background', u'Не рисовать фон'))

        self._actionsBackgroundImage = []

        i = 1
        for _ in globals.backgrounds:
            action = ExtendedCheckableAction(trStr('Background {0}'.format(i), u'Фон {0}'.format(i)))
            action.setToolTip(trStr('Draw {0} background image'.format(i),
                                    u'Рисовать {0}е фоновое изображение'.format(i)))
            self._actionsBackgroundImage.append(action)
            i += 1

        self._optionsActionAnimation.setToolTip(trStr('Animation for items\non graphics scene',
                                                      u'Анимация для объектов на\nграфической области'))
        self._optionsActionShadows.setToolTip(trStr('Drop shadows by items\non graphics scene',
                                                    u'Тени для объектов на\nграфической области'))
        self._optionsActionHighlightConnectors.setToolTip(
            trStr('Highlight effect for connectors\nof selected items',
                  u'Эффект подсвечивания для соединительных\nлиний активных объектов на графической области')
        )
        self._optionsActionBoldConnectors.setToolTip(
            trStr('Bold connectors of selected items',
                  u'Выделять жирным соединительные линии\nактивных объектов на графической области')
        )
        self._optionsActionSaveLibraries.setToolTip(
            trStr('Enable saving node libraries\nwhen saving project',
                  u'Разрешить сохранение библиотек\nузлов при сохранении проекта')
        )
        self._optionsActionEditLibraries.setToolTip(trStr('Enable node libraries editing',
                                                          u'Разрешить редактирование библиотек узлов'))
        self._optionsActionDebug.setToolTip(trStr('Turn on/off debug mode',
                                                  u'Вкл/выкл режим отладки'))
        self._optionsActionAutosave.setToolTip(trStr('Enable auto saving for project and libraries',
                                                     u'Разрешить автоматическое сохранение проекта и библиотек узлов'))

        self._helpActionColorsLegend = trAction(trStr('Output window legend', u'Памятка для окна вывода'))
        self._helpActionColorsLegend.triggered.connect(_printColors)

        self._helpActionAbout = trAction(trStr('About', u'О программе'))
        self._helpActionAbout.triggered.connect(self.__showAbout)

        self._helpActionAboutQt = trAction(trStr('About Qt', u'Версия Qt'))
        self._helpActionAboutQt.triggered.connect(self.__showAboutQt)

        self._helpWindow = None
        self._helpActionHelp = trAction(trStr('Help', u'Справка'))
        self._helpActionHelp.setIcon(QIcon(joinPath(globals.applicationIconsPath, 'help.png')))
        self._helpActionHelp.triggered.connect(self.__showHelp)

        self._viewActionLanguageEnglish = trAction(trStr('&English', u'&Английский'))
        self._viewActionLanguageEnglish.setToolTip(trStr(u'Английский', 'English'))
        self._viewActionLanguageEnglish.setCheckable(True)
        self._viewActionLanguageRussian = trAction(trStr('&Russian', u'&Русский'))
        self._viewActionLanguageRussian.setToolTip(trStr(u'Русский', 'Russian'))
        self._viewActionLanguageRussian.setCheckable(True)

        self._viewActionConnectorCurved = trAction(trStr('&Curved', u'&Гладкие кривые'))
        self._viewActionConnectorCurved.setCheckable(True)
        self._viewActionConnectorLine = trAction(trStr('&Line', u'&Прямые'))
        self._viewActionConnectorLine.setCheckable(True)
        self._viewActionConnectorPolyline = trAction(trStr('&Polyline', u'&Ломаные линии'))
        self._viewActionConnectorPolyline.setCheckable(True)
        if self._connectorType == ConnectorType.Curve:
            self._viewActionConnectorCurved.setChecked(True)
        elif self._connectorType == ConnectorType.Line:
            self._viewActionConnectorLine.setChecked(True)
        elif self._connectorType == ConnectorType.Polyline:
            self._viewActionConnectorPolyline.setChecked(True)
        self._viewActionConnectorCurved.triggered.connect(self.__onConnectorCurvedTrigger)
        self._viewActionConnectorLine.triggered.connect(self.__onConnectorLineTrigger)
        self._viewActionConnectorPolyline.triggered.connect(self.__onConnectorPolylineTrigger)

        self._menuLanguage = trMenuWithTooltip(trStr('&Language', u'&Язык интерфейса'))
        self._menuLanguage.setToolTip(trStr(u'Язык интерфейса', 'Language'))
        self._menuLanguage.addAction(self._viewActionLanguageEnglish)
        self._menuLanguage.addAction(self._viewActionLanguageRussian)

        self._menuConnectors = trMenuWithTooltip(trStr('&Connectors', u'Соединительные &линии'))
        self._menuConnectors.addAction(self._viewActionConnectorCurved)
        self._menuConnectors.addAction(self._viewActionConnectorLine)
        self._menuConnectors.addAction(self._viewActionConnectorPolyline)

        self._menuBackground = trMenuWithTooltip(trStr('&Background', u'&Фон'))
        self._menuBackground.addAction(self._actionDisableBackground)
        for bga in self._actionsBackgroundImage:
            self._menuBackground.addAction(bga)

        self._actionOpenLibrary.triggered.connect(self.__onLoadLibClicked)
        self._actionCreateLibrary.triggered.connect(self.__onCreateLibClicked)
        self._actionOpenTree.triggered.connect(self.__onLoadTreeClicked)
        self._actionCreateTree.triggered.connect(self.__onCreateTreeClicked)
        self._actionOpenProject_menu.triggered.connect(self.__onOpenProjectClicked)
        self._actionSaveProject_menu.triggered.connect(self.__onSaveProjectClicked)
        self._actionReadAlphabet.triggered.connect(self.__onReadAlphabetClicked)
        self._actionExit.triggered.connect(self.close)
        # ACTIONS. ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        # MENU: ---------------------------------------------
        self._menuFile = trMenuWithTooltip(trStr('&File', u'&Файл'))
        self._menuFile.addAction(self._actionOpenProject_menu)
        self._menuFile.addAction(self._actionSaveProject_menu)
        self._menuFile.addAction(self._actionReadAlphabet)
        self._menuFile.addMenu(self._menuRecentProjects)
        self._menuFile.addSeparator()
        self._menuFile.addAction(self._actionExit)

        self._menuProject = trMenuWithTooltip(trStr('&Project', u'&Проект'))
        self._menuProject.addAction(self._actionOpenTree)
        self._menuProject.addAction(self._actionCreateTree)
        self._menuProject.addSeparator()
        self._menuProject.addAction(self._actionOpenLibrary)
        self._menuProject.addAction(self._actionCreateLibrary)

        self._menuView = trMenuWithTooltip(trStr('&View', u'&Вид'))
        self._menuView.setToolTip(trStr(u'Вид', 'View'))
        self._menuView.addAction(self._optionsActionAnimation)
        self._menuView.addAction(self._optionsActionShadows)
        self._menuView.addAction(self._optionsActionHighlightConnectors)
        self._menuView.addAction(self._optionsActionBoldConnectors)
        self._menuView.addSeparator()
        self._menuView.addMenu(self._menuBackground)
        self._menuView.addSeparator()
        self._menuView.addMenu(self._menuConnectors)
        self._menuView.addSeparator()
        self._menuView.addMenu(self._menuLanguage)

        self._menuOptions = trMenuWithTooltip(trStr('&Options', u'&Настройки'))
        self._menuOptions.setToolTip(trStr(u'Настройки', 'Options'))
        self._menuOptions.addAction(self._optionsActionLogo)
        self._menuOptions.addAction(self._optionsActionAutosave)
        self._menuOptions.addAction(self._optionsActionSaveLibraries)
        self._menuOptions.addAction(self._optionsActionEditLibraries)
        self._menuOptions.addAction(self._optionsActionDebug)

        self._menuHelp = trMenuWithTooltip(trStr('&Help', u'&Помощь'))
        self._menuHelp.setToolTip(trStr(u'Помощь', 'Help'))
        self._menuHelp.addAction(self._helpActionHelp)
        self._menuHelp.addAction(self._helpActionColorsLegend)
        self._menuHelp.addSeparator()
        self._menuHelp.addAction(self._helpActionAboutQt)
        self._menuHelp.addAction(self._helpActionAbout)

        self.menuBar().addMenu(self._menuFile)
        self.menuBar().addMenu(self._menuProject)
        self.menuBar().addMenu(self._menuView)
        self.menuBar().addMenu(self._menuOptions)
        self.menuBar().addMenu(self._menuHelp)
        # MENU. ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        # DIAGRAM TOOLBAR: ---------------------------------------------------
        self._tabToolbar = QToolBar('Tree view toolbar', self)
        self._tabToolbar.setObjectName('tabToolbar')
        self._tabToolbar.setIconSize(QSize(18, 18))
        # selectMode = QAction(self.toolbar)
        # selectMode.setCheckable(True)
        # selectMode.setChecked(True)
        # selectMode.setIcon( QIcon(joinPath(globals.applicationIconsPath,'cursor.png')) )
        # self.toolbar.addAction(selectMode)
        # self.toolbar.addSeparator()

        self._actionViewHorizontal = trAction()
        self._actionViewHorizontal.setToolTip(trStr('Horizontal view', u'Горизонтальный вид'))
        self._actionViewHorizontal.setCheckable(True)
        self._actionViewHorizontal.setChecked(False)
        self._actionViewHorizontal.triggered.connect(self.__horTriggered)
        self._actionViewHorizontal.setIcon(QIcon(joinPath(globals.applicationIconsPath, 'chart_hor2.png')))

        self._actionViewVertical = trAction()
        self._actionViewVertical.setToolTip(trStr('Vertical view', u'Вертикальный вид'))
        self._actionViewVertical.setCheckable(True)
        self._actionViewVertical.setChecked(True)
        self._actionViewVertical.triggered.connect(self.__verTriggered)
        self._actionViewVertical.setIcon(QIcon(joinPath(globals.applicationIconsPath, 'chart2.png')))

        self._actionModeCursor = trAction()
        self._actionModeCursor.setToolTip(trStr('Cursor mode', u'Режим курсора'))
        self._actionModeCursor.setCheckable(True)
        self._actionModeCursor.setChecked(True)
        self._actionModeCursor.triggered.connect(self.__cursorTriggered)
        self._actionModeCursor.setIcon(QIcon(joinPath(globals.applicationIconsPath, 'cursor.png')))

        self._actionModeDrag = trAction()
        self._actionModeDrag.setToolTip(trStr('Drag mode', u'Режим перетаскивания'))
        self._actionModeDrag.setCheckable(True)
        self._actionModeDrag.setChecked(False)
        self._actionModeDrag.triggered.connect(self.__dragTriggered)
        self._actionModeDrag.setIcon(QIcon(joinPath(globals.applicationIconsPath, 'hand-icon.png')))

        self._actionModeConnectorTool = trAction()
        self._actionModeConnectorTool.setToolTip(trStr('Connector tool', u'Соединительная линия'))
        self._actionModeConnectorTool.setCheckable(True)
        self._actionModeConnectorTool.setChecked(False)
        self._actionModeConnectorTool.triggered.connect(self.__connectorTriggered)
        self._actionModeConnectorTool.setIcon(QIcon(joinPath(globals.applicationIconsPath, 'connector1.png')))

        self._actionViewJustifyWidth = trAction()
        self._actionViewJustifyWidth.setToolTip(trStr('Justify widths', u'Выравнивать ширину\nграфических элементов'))
        self._actionViewJustifyWidth.setCheckable(True)
        self._actionViewJustifyWidth.setChecked(False)
        self._actionViewJustifyWidth.toggled.connect(self.__tabJustifyTriggered)
        self._actionViewJustifyWidth.setIcon(QIcon(joinPath(globals.applicationIconsPath, 'text_align_justify.png')))

        self._tabToolbar.addAction(self._actionViewVertical)
        self._tabToolbar.addAction(self._actionViewHorizontal)
        self._tabToolbar.addSeparator()
        self._tabToolbar.addAction(self._actionModeCursor)
        self._tabToolbar.addAction(self._actionModeDrag)
        self._tabToolbar.addAction(self._actionModeConnectorTool)
        self._tabToolbar.addSeparator()
        self._tabToolbar.addAction(self._actionViewJustifyWidth)
        self._tabToolbar.addSeparator()
        # DIAGRAM TOOLBAR. ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        # PROJECT TOOLBAR: -------------------------------------------------------------
        self._projectToolbar = QToolBar('Project toolbar', self)
        self._projectToolbar.setObjectName('projectToolbar')
        self._projectToolbar.setIconSize(QSize(18, 18))

        self._actionOpenProject_tb = trAction()
        self._actionOpenProject_tb.setToolTip(trStr('Open project', u'Открыть проект'))
        self._actionOpenProject_tb.setIcon(QIcon(joinPath(globals.applicationIconsPath, 'folder_page.png')))
        self._actionOpenProject_tb.triggered.connect(self.__onOpenProjectClicked)

        self._actionSaveProject_tb = trAction()
        self._actionSaveProject_tb.setToolTip(trStr('Save all', u'Сохранить все'))
        self._actionSaveProject_tb.setIcon(QIcon(joinPath(globals.applicationIconsPath, 'save.png')))
        self._actionSaveProject_tb.setEnabled(False)
        self._actionSaveProject_tb.triggered.connect(self.__onSaveProjectClicked)

        self._actionUndo = trAction()
        self._actionUndo.setToolTip(trStr('Undo', u'Отменить действие'))
        self._actionUndo.setIcon(QIcon(joinPath(globals.applicationIconsPath, 'undo1.png')))
        self._actionUndo.setEnabled(False)
        self._actionUndo.setMenu(QMenu())
        self._actionUndo.triggered.connect(self.__onUndo)

        self._actionRedo = trAction()
        self._actionRedo.setToolTip(trStr('Redo', u'Повторить действие'))
        self._actionRedo.setIcon(QIcon(joinPath(globals.applicationIconsPath, 'redo1.png')))
        self._actionRedo.setEnabled(False)
        self._actionRedo.setMenu(QMenu())
        self._actionRedo.triggered.connect(self.__onRedo)

        self._projectToolbar.addAction(self._actionOpenProject_tb)
        self._projectToolbar.addAction(self._actionSaveProject_tb)
        self._projectToolbar.addSeparator()
        self._projectToolbar.addAction(self._actionUndo)
        self._projectToolbar.addAction(self._actionRedo)
        # PROJECT TOOLBAR. ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        self.addToolBar(Qt.TopToolBarArea, self._projectToolbar)
        self.addToolBar(Qt.TopToolBarArea, self._tabToolbar)
        # self.tabToolbar.show()

        self.setStatusBar(QStatusBar(self))
        globals.generalSignals.sceneItemPos.connect(self.__onSceneItemPos)

        self._projectParser = parser.ProjParser()
        self._lastLibraryFile = ''
        self._lastTreeFile = ''
        self._lastProjectFile = ''

        self._actionOpenProject_menu.setEnabled(True)
        self._actionOpenProject_tb.setEnabled(True)
        self._actionOpenTree.setEnabled(False)
        self._actionCreateTree.setEnabled(False)
        self._actionOpenLibrary.setEnabled(False)
        self._actionCreateLibrary.setEnabled(False)
        self._actionReadAlphabet.setEnabled(False)
        self._actionSaveProject_menu.setEnabled(False)
        self._actionSaveProject_tb.setEnabled(False)

        self._dockTreesList = tltree.TL_TreeDock(trStr('Trees list', u'Список деревьев'))
        self._dockTreesList.setObjectName('treeDock')
        self._dockTreesList.setAllowedAreas(Qt.AllDockWidgetAreas)

        self._dockNodeDescription = llinfo.InfoDock(trStr('Node description', u'Описание узла'))
        self._dockNodeDescription.setObjectName('infoDock')
        self._dockNodeDescription.setAllowedAreas(Qt.AllDockWidgetAreas)

        self._dockLibraries = lltree.LL_LibDock(trStr('Available nodes', u'Список доступных узлов'))
        self._dockLibraries.setObjectName('libDock')
        self._dockLibraries.setAllowedAreas(Qt.AllDockWidgetAreas)

        globals.nodeListSignals.libSelected.connect(self.__onLibSelected)
        globals.nodeListSignals.nodeSelected.connect(self.__onNodeSelected)

        self._tabWidget = tab.TreeTab(self._actionViewHorizontal.isChecked(),
                                      self._actionModeDrag.isChecked(),
                                      self._actionViewJustifyWidth.isChecked(),
                                      self._actionModeConnectorTool.isChecked(),
                                      self._connectorType.val,
                                      self)

        self.treeViewModeChange.connect(self._tabWidget.viewTrigger)
        self.treeDragModeChange.connect(self._tabWidget.dragModeTrigger)
        self.treeJustifyModeChange.connect(self._tabWidget.justifyModeTrigger)
        self.treeConnectorModeChange.connect(self._tabWidget.connectorToolTrigger)
        self.connectorTypeChanged.connect(self._tabWidget.onConnectorTypeChange)

        self._dockNodeAttributes = tlinfo.TaskDock(trStr('Attributes', u'Параметры'))
        self._dockNodeAttributes.setObjectName('attrDock')
        self._dockNodeAttributes.updateView.connect(self._tabWidget.updateTabsItems)
        self._dockNodeAttributes.setAllowedAreas(Qt.AllDockWidgetAreas)

        self._tabWidget.tabAdded.connect(self._dockNodeAttributes.addEmptyWidget)
        self._tabWidget.tabRemoved.connect(self._dockNodeAttributes.removeWidget)
        self._tabWidget.tabActivated.connect(self._dockNodeAttributes.setCurrent)
        self._tabWidget.itemSelected.connect(self.__onTabWidgetItemSelection)
        self._tabWidget.nothingSelected.connect(self.__onTabWidgetItemSelectionCancel)

        self._tabWidget.tabAdded.connect(self._onNewTabAdd)
        self._tabWidget.tabRemoved.connect(self._onTabDelete)

        self._centralStack = QStackedWidget()
        self._centralStack.setObjectName('centralStack')
        self._centralStack.addWidget(self._tabWidget.defaultWidget())
        self._centralStack.addWidget(self._tabWidget)
        self._centralStack.setCurrentIndex(0)

        window = QMainWindow(self)
        window.setObjectName('CentralSubWindow')
        window.setDockNestingEnabled(True)
        window.setCentralWidget(self._centralStack)
        window.setWindowFlags(Qt.Widget)
        self.setCentralWidget(window)
        # self.setCentralWidget(self.__tabWidget)

        self.addDockWidget(Qt.LeftDockWidgetArea, self._dockTreesList)
        self.addDockWidget(Qt.LeftDockWidgetArea, self._dockLibraries)
        self.addDockWidget(Qt.RightDockWidgetArea, self._dockNodeDescription)
        self.addDockWidget(Qt.RightDockWidgetArea, self._dockNodeAttributes)
        self.addDockWidget(Qt.LeftDockWidgetArea, self._dockDebugger)
        # self.addDockWidget(Qt.BottomDockWidgetArea, self.outputDock)
        window.addDockWidget(Qt.BottomDockWidgetArea, self._dockOutput)

        globalLanguage.changeLanguage(configData[0])

        # generator.test()

        self._debugServer = None
        self._debugServer = DebugServer()

        self.readSettings()

        if globalLanguage.language == Language.Russian:
            self._viewActionLanguageRussian.setChecked(True)
            self._viewActionLanguageEnglish.setChecked(False)
        else:
            self._viewActionLanguageRussian.setChecked(False)
            self._viewActionLanguageEnglish.setChecked(True)

        if globals.background < 0:
            self._actionDisableBackground.setChecked(True)
        else:
            self._actionsBackgroundImage[globals.background].setChecked(True)

        self._actionDisableBackground.triggered.connect(self.__onBackgroundDisableTrigger)
        for bga in self._actionsBackgroundImage:
            bga.changed.connect(self.__onBackgroundTrigger)

        self._viewActionLanguageEnglish.triggered.connect(self.__onLangEnglishTriggered)
        self._viewActionLanguageRussian.triggered.connect(self.__onLangRussianTriggered)

        # inform if debug mode is on
        print('debug: DEBUG MODE is \'ON\'')
        print('debug:')

        self._dockOutput.setSilent(True)
        self._optionsActionLogo.setChecked(globals.showLogo)
        self._optionsActionAnimation.setChecked(globals.itemsAnimation)
        self._optionsActionShadows.setChecked(globals.itemsShadow)
        self._optionsActionHighlightConnectors.setChecked(globals.connectorsHighlight)
        self._optionsActionBoldConnectors.setChecked(globals.connectorsBold)
        self._optionsActionSaveLibraries.setChecked(globals.saveLibraries)
        self._optionsActionEditLibraries.setChecked(globals.editLibraries)
        self._optionsActionDebug.setChecked(globals.debugMode)
        self._optionsActionAutosave.setChecked(globals.autosaveEnabled)
        self._dockOutput.setSilent(False)

        globals.setAutosaveEnabled(globals.autosaveEnabled)

        if globals.recentProjects:
            for p in globals.recentProjects:
                self._menuRecentProjects.addAction(ProjectAction(self, p, p, p, self))
            self._menuRecentProjects.setEnabled(True)

        if host != 'victor':
            self._optionsActionLogo.setVisible(False)

        # if self.debugServer is not None:
        #     self.debugServer.start()

        QTimer.singleShot(5, self._dockOutput.scrollBottom)

        globals.historySignals.undoRedoChange.connect(self.__onUndoRedoChange)
        globals.historySignals.undoMade.connect(self.__onUndoRedoChange)
        globals.historySignals.redoMade.connect(self.__onUndoRedoChange)

        globals.treeListSignals.openExistingTreeFile.connect(self.__onLoadTreeClicked)
        globals.treeListSignals.createNewTreeFile.connect(self.__onCreateTreeClicked)
        globals.nodeListSignals.openExistingLibraryFile.connect(self.__onLoadLibClicked)
        globals.nodeListSignals.createNewLibraryFile.connect(self.__onCreateLibClicked)

        self._autosaveTimerRunning = False
        self._autosaveTimer = QTimer()
        self._autosaveTimer.timeout.connect(self.__autosave)

        if args.project_for_opening:
            project_path = args.project_for_opening
            print("Open %s" % (project_path))
            self.openProject(args.project_for_opening)

    #####################################################

    def closeEvent(self, event):
        if globals.project is not None and globals.project.modified:
            title = trStr('Program quit', u'Выход из программы').text()
            message = trStr('Current project was modified.<br/>Save project before exit?', \
                            u'Текущий проект был изменен.<br/>Сохранить проект перед выходом?').text()

            msgBox = QMessageBox(QMessageBox.Question, title, message)
            yes = msgBox.addButton(trStr('Yes', u'Да').text(), QMessageBox.YesRole)
            no = msgBox.addButton(trStr('No', u'Нет').text(), QMessageBox.NoRole)
            msgBox.addButton(trStr('Cancel', u'Отмена').text(), QMessageBox.RejectRole)

            msgBox.exec_()

            result = msgBox.clickedButton()

            if result == yes:
                self.__onSaveProjectClicked()
            elif result == no:
                pass
            else:
                print('info: user cancelled closing application')
                event.setAccepted(False)
                return

        if self._debugServer is not None:
            self._debugServer.stop(True)
        self.__saveRecentProjects()

        if self._helpWindow is not None:
            self._helpWindow.close()

        self.saveSettings()

        QMainWindow.closeEvent(self, event)

    def saveSettings(self):
        settings = QSettings('Victor Zarubkin', 'Behavior Studio')
        settings.beginGroup('main')
        settings.setValue('geometry', self.saveGeometry())
        settings.setValue('windowState', self.saveState(globals.intVersion))
        settings.endGroup()

        settings.beginGroup('centralWindow')
        settings.setValue('geometry', self.centralWidget().saveGeometry())
        settings.setValue('windowState', self.centralWidget().saveState(globals.intVersion))
        settings.endGroup()

        settings.beginGroup('nodeInfo')
        settings.setValue('displayAttributes', llinfo.nodeChecks.displayAttributes)
        settings.setValue('displayDescription', llinfo.nodeChecks.displayDescription)
        settings.setValue('displayEvents', llinfo.nodeChecks.displayEvents)
        settings.setValue('displayExtended', llinfo.nodeChecks.displayExtended)
        settings.endGroup()

        settings.beginGroup('config')
        settings.setValue('connectorsType', self._connectorType.val)
        settings.setValue('animation', globals.itemsAnimation)
        settings.setValue('shadows', globals.itemsShadow)
        settings.setValue('highlightConnectors', globals.connectorsHighlight)
        settings.setValue('boldConnectors', globals.connectorsBold)
        settings.setValue('background', globals.background)
        settings.setValue('debugMode', globals.debugMode)
        settings.setValue('libraryEdit', globals.editLibraries)
        settings.setValue('librarySave', globals.saveLibraries)
        settings.setValue('language', globalLanguage.language)
        settings.setValue('autosaveEnabled', globals.autosaveEnabled)
        # settings.setValue('autosaveTime', float(globals.autosaveTime))
        settings.endGroup()

        global host
        settings.beginGroup('startup')
        if host == 'victor':
            settings.setValue('showLogo', globals.showLogo)
        else:
            settings.setValue('showLogo', True)
        settings.endGroup()

        settings.beginGroup('recentProjects')
        settings.setValue('list', globals.recentProjects)
        settings.endGroup()

    def readSettings(self):
        print('info: Trying to restore application state...')
        settings = QSettings('Victor Zarubkin', 'Behavior Studio')
        settings.beginGroup('main')
        geometry = settings.value('geometry')
        if geometry is not None:
            if self.restoreGeometry(geometry):
                print('ok: Main window geometry restored')
            else:
                print('error: Main window geometry not restored')
        else:
            print('warning: Can not find saved geometry for main window')
        state = settings.value('windowState')
        if state is not None:
            restored = self.restoreState(state, globals.intVersion)
            if not restored:
                for ver in globals.intPreviousVersions:
                    restored = self.restoreState(state, ver)
                    if restored:
                        break
            if restored:
                print('ok: Main window state restored')
            else:
                print('error: Main window state not restored')
        else:
            print('warning: Can not find saved state for main window')
        settings.endGroup()

        settings.beginGroup('centralWindow')
        geometry = settings.value('geometry')
        if geometry is not None:
            if self.centralWidget().restoreGeometry(geometry):
                print('ok: Central window geometry restored')
            else:
                print('error: Central window geometry not restored')
        else:
            print('warning: Can not find saved geometry for central window')
        state = settings.value('windowState')
        if state is not None:
            restored = self.centralWidget().restoreState(state, globals.intVersion)
            if not restored:
                for ver in globals.intPreviousVersions:
                    restored = self.centralWidget().restoreState(state, ver)
                    if restored:
                        break
            if restored:
                print('ok: Central window state restored')
            else:
                print('error: Central window state not restored')
        else:
            print('warning: Can not find saved state for central window')
        settings.endGroup()

        def toBool(qSettings, attr_name, default):
            value = qSettings.value(attr_name)
            if value is None:
                return default
            value = value.lower()
            if value not in ('true', 'false'):
                print('error: \'{0}\' value is \'{1}\', but must be \'true\' or \'false\''.format(attr_name, value))
                return default
            return value == 'true'

        def toInt(qSettings, attr_name, default):
            result_value = default
            value = qSettings.value(attr_name)
            if value is None:
                return result_value
            try:
                result_value = int(value)
            except ValueError:
                print('error: \'{0}\' value is \'{1}\' and it can not be converted to int. Default it to \'{2}\''
                      .format(attr_name, value, default))
                return default
            return result_value

        def toFloat(qSettings, attr_name, default):
            result_value = default
            value = qSettings.value(attr_name)
            if value is None:
                return result_value
            try:
                result_value = float(value)
            except ValueError:
                print('error: \'{0}\' value is \'{1}\' and it can not be converted to float. Default it to \'{2}\''
                      .format(attr_name, value, default))
                return default
            return result_value

        settings.beginGroup('nodeInfo')
        llinfo.nodeChecks.displayAttributes = toBool(settings, 'displayAttributes', llinfo.nodeChecks.displayAttributes)
        llinfo.nodeChecks.displayDescription = toBool(settings, 'displayDescription',
                                                      llinfo.nodeChecks.displayDescription)
        llinfo.nodeChecks.displayEvents = toBool(settings, 'displayEvents', llinfo.nodeChecks.displayEvents)
        llinfo.nodeChecks.displayExtended = toBool(settings, 'displayExtended', llinfo.nodeChecks.displayExtended)
        settings.endGroup()

        if not globals.explicitConfig:
            settings.beginGroup('config')
            globals.itemsAnimation = toBool(settings, 'animation', globals.itemsAnimation)
            globals.itemsShadow = toBool(settings, 'shadows', globals.itemsShadow)
            globals.connectorsHighlight = toBool(settings, 'highlightConnectors', globals.connectorsHighlight)
            globals.connectorsBold = toBool(settings, 'boldConnectors', globals.connectorsBold)
            globals.debugMode = toBool(settings, 'debugMode', globals.debugMode)
            if self._launchArgs.debug:
                globals.debugMode = True
            globals.editLibraries = toBool(settings, 'libraryEdit', globals.editLibraries)
            globals.saveLibraries = toBool(settings, 'librarySave', globals.saveLibraries)
            globals.background = min(max(toInt(settings, 'background', globals.background), -1),
                                     len(globals.backgrounds) - 1)
            # globals.autosaveTime = toFloat(settings, 'autosaveTime', globals.autosaveTime)
            globals.autosaveEnabled = toBool(settings, 'autosaveEnabled', globals.autosaveEnabled)
            if globals.autosaveEnabled:
                globals.autosaveEnabled = (globals.autosaveTime > 0.5)

            languageId = settings.value('language')
            if languageId is not None:
                globalLanguage.changeLanguage(languageId)

            connector = settings.value('connectorsType')
            if connector is not None:
                try:
                    val = int(connector)
                    if val == ConnectorType.Polyline:
                        self.__onConnectorPolylineTrigger()
                    elif val == ConnectorType.Curve:
                        self.__onConnectorCurvedTrigger()
                    elif val == ConnectorType.Line:
                        self.__onConnectorLineTrigger()
                except ValueError:
                    pass

            settings.endGroup()

            settings.beginGroup('recentProjects')
            recentList = settings.value('list')
            if recentList is not None:
                globals.recentProjects = recentList
            settings.endGroup()

        print('')

    #####################################################

    def __showAboutQt(self):
        QMessageBox.aboutQt(self)

    def __showHelp(self):
        if self._helpWindow is None:
            self._helpWindow = HelpWidget()
            self._helpWindow.closed.connect(self.__onHelpClose)
            self._helpWindow.show()
        else:
            QApplication.setActiveWindow(self._helpWindow)

    #####################################################

    @QtCore.Slot()
    def _onNewTabAdd(self):
        if self._centralStack.currentIndex() == 0:
            self._centralStack.setCurrentIndex(1)

    @QtCore.Slot()
    def _onTabDelete(self):
        if self._tabWidget.empty():
            self._centralStack.setCurrentIndex(0)

    @QtCore.Slot()
    def __onHelpClose(self):
        self._helpWindow = None

    def __showAbout(self):
        global startYear
        title = trStr('About Behavior Studio', u'О Behavior Studio').text()
        body = '<b>Behavior Studio {0}</b><br/>'.format(globals.strVersion)
        body += '<br/>'
        body += trStr('  A behavior tree editor with configurable<br/>input and output file format.',
                      u'  Редактор деревьев поведения с настраиваемым<br/>форматом входных и выходных файлов.')\
            .text()
        body += '<br/>'
        body += '<i>'
        body += '<br/><font color=\"gray\" size=\"3\">'
        if not globals.displayConstantaCopyright:
            body += trStr('Copyright &copy; 2012-2015  Victor Zarubkin', u'Copyright &copy; 2012-2015  Виктор Зарубкин')\
                .text()
            body += '<br/><a href="mailto:victor.zarubkin@gmail.com" style=\"color: CornflowerBlue\">'\
                'victor.zarubkin@gmail.com</a>'
        else:
            body += trStr('created by Victor Zarubkin, {0}', u'авторство: Виктор Зарубкин. {0}').text()\
                .format(startYear)
            body += '<br/><a href="mailto:victor.zarubkin@gmail.com" style=\"color: CornflowerBlue\">'\
                'victor.zarubkin@gmail.com</a>'
            body += '<font size=\"2\"><br/><br/>'
            body += trStr('LLC Constanta-Design', u'ООО \"Константа-Дизайн\"').text()
            body += '<br/><a href=\"http://www.cdezign.ru/\" style=\"color: CornflowerBlue\">www.cdezign.ru</a>'
        body += '</i>'
        body += '</font>'
        QMessageBox.about(self, title, body)

    def __readConfig(self, args):
        outputData = [globalLanguage.language, None, '']

        currDir = os.getcwd()  # os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))

        # Reading application config file:
        configFile = None
        data = None

        try_configs = []
        if isinstance(args.config_file, list):
            try_configs = args.config_file
        else:
            try_configs.append(args.config_file)

        okay = False
        err = False
        for conf in try_configs:
            configFile = conf
            data = None

            if not os.path.isabs(configFile):
                configFile = absPath(configFile, currDir)  # make full path from relative path
            else:
                configFile = toUnixPath(configFile)

            if configFile is None:
                err = True
                print('warning: Config file \"{0}\" does not exist!'.format(conf))
                continue

            if not os.path.exists(configFile):
                err = True
                print('warning: Config file \"{0}\" does not exist!'.format(configFile))
                continue

            dom = parse(configFile)
            data = dom.getElementsByTagName('config')
            if not data:
                err = True
                print('warning: Config file \"{0}\" is wrong formatted! It must have header \"<config>\".'
                      .format(configFile))
                continue

            okay = True
            break

        outputData[2] = configFile

        if not okay:
            print('error: Can\'t load application configuration!')
            print('')
            return outputData

        if err:
            print('')

        self.__readConfigIcons(configFile, data[0])
        outputData[0] = self.__readConfigLanguage(configFile, data[0])
        outputData[1] = self.__readConfigConnectorType(data[0])

        if data[0].hasAttribute('explicit'):
            a = data[0].getAttribute('explicit').lower()
            globals.explicitConfig = a in ('yes', 'true', '1')

        if data[0].hasAttribute('maxRecentProjects'):
            try:
                globals.maxRecentProjects = max(int(data[0].getAttribute('maxRecentProjects')), 1)
            except ValueError:
                pass

        if data[0].hasAttribute('maxBehaviorTreeHistory'):
            try:
                globals.maxBehaviorTreeHistory = max(int(data[0].getAttribute('maxBehaviorTreeHistory')), 1)
            except ValueError:
                pass

        if data[0].hasAttribute('editableLinks'):
            a = data[0].getAttribute('editableLinks').lower()
            globals.linksEditable = a not in ('no', 'false', '0')

        if data[0].hasAttribute('animation'):
            a = data[0].getAttribute('animation').lower()
            globals.itemsAnimation = a not in ('no', 'false', '0')

        if data[0].hasAttribute('shadows'):
            a = data[0].getAttribute('shadows').lower()
            globals.itemsShadow = a not in ('no', 'false', '0')

        if data[0].hasAttribute('connectorsHighlight'):
            a = data[0].getAttribute('connectorsHighlight').lower()
            globals.connectorsHighlight = a not in ('no', 'false', '0')

        if data[0].hasAttribute('connectorsBold'):
            a = data[0].getAttribute('connectorsBold').lower()
            globals.connectorsBold = a not in ('no', 'false', '0')

        if data[0].hasAttribute('cd_copyright'):
            a = data[0].getAttribute('cd_copyright').lower()
            globals.displayConstantaCopyright = a in ('yes', 'true', '1')

        if data[0].hasAttribute('saveLibs'):
            a = data[0].getAttribute('saveLibs').lower()
            globals.saveLibraries = a in ('yes', 'true', '1')

        if data[0].hasAttribute('editLibs'):
            a = data[0].getAttribute('editLibs').lower()
            globals.editLibraries = a in ('yes', 'true', '1')

        if data[0].hasAttribute('debug'):
            a = data[0].getAttribute('debug').lower()
            globals.debugMode = a in ('yes', 'true', '1')

        if args.debug:
            globals.debugMode = True

        if data[0].hasAttribute('autosaveTime'):
            try:
                globals.autosaveTime = max(float(data[0].getAttribute('autosaveTime')), 0.0)
                globals.autosaveEnabled = (globals.autosaveTime > 0.5)
            except ValueError:
                pass

        if globals.autosaveTime > 0.5 and data[0].hasAttribute('autosaveEnabled'):
            a = data[0].getAttribute('autosaveEnabled').lower()
            globals.autosaveEnabled = a in ('yes', 'true', '1')

        return outputData

    def __readConfigIcons(self, configFile, configData):
        iconsPath = ''
        if configData.hasAttribute('icons'):
            path = configData.getAttribute('icons')
            path = absPath(path, configFile, True)
            if path is None or len(path) < 1 or not os.path.exists(path):
                print('warning: icons path \"{0}\" does not exist!'.format(path))
                print('')
            else:
                iconsPath = path
        else:
            print('warning: Config file \"{0}\" have no icons path! (attribute \"<config icons=""/>\")'
                  .format(configFile))
            print('')
            return

        if not iconsPath:
            print('warning: no icons will be loaded for application!')
            print('')
            return

        globals.applicationIconsPath = iconsPath

    def __readConfigLanguage(self, configFile, configData):
        if configData.hasAttribute('language'):
            lang = configData.getAttribute('language')
            if globalLanguage.rightLanguage(lang):
                return lang
            print('warning: Config file \"{0}\" have no RIGHT language value.'.format(configFile))
            print('warning: Language \"{0}\" is not accepted value.'.format(lang))
            print('warning: Possible values are: {0}'.format(', '.join(globalLanguage.possibleValues())))
            print('')
        else:
            print('warning: Config file \"{0}\" have no language value. (attribute \"<config language=""/>\")'
                  .format(configFile))
            print('')
        return globalLanguage.language

    def __readConfigConnectorType(self, configData):
        if configData.hasAttribute('connectors'):
            ctype = configData.getAttribute('connectors')
            if ctype in ConnectorType.convTab:
                return ConnectorType.convTab[ctype]
        return None

    #####################################################

    def __readRecentProjects(self):
        if not os.path.exists(globals.recentProjectsFile):
            return
        f = open(globals.recentProjectsFile, 'r')
        for line in f:
            p = str(line.replace('\n', ''))
            if not p:
                continue
            globals.recentProjects.append(p)
            if len(globals.recentProjects) >= globals.maxRecentProjects:
                break
        f.close()

    def __saveRecentProjects(self):
        pass
        # if not globals.recentProjects:
        # 	return
        # f = open(globals.recentProjectsFile, 'w')
        # f.write('\n'.join(globals.recentProjects))
        # f.close()

    #####################################################

    def keyPressEvent(self, event):
        k = event.key()
        if k not in globals.pressedKeys:
            globals.pressedKeys.append(k)
        if k == Qt.Key_F5:
            # refresh tabs
            self._tabWidget.refreshAll()
        QMainWindow.keyPressEvent(self, event)

    def keyReleaseEvent(self, event):
        k = event.key()
        if k == Qt.Key_Z:
            if Qt.Key_Control in globals.pressedKeys:
                self.__onUndo()
        elif k == Qt.Key_Y:
            if Qt.Key_Control in globals.pressedKeys and globals.project is not None:
                self.__onRedo()
        if k in globals.pressedKeys:
            globals.pressedKeys.remove(k)
        QMainWindow.keyPressEvent(self, event)

    #####################################################

    @QtCore.Slot()
    def __onUndoRedoChange(self):
        self._actionUndo.menu().clear()
        actions = globals.project.getHistoryUndoActions()
        if actions:
            for record in reversed(actions):
                self._actionUndo.menu().addAction(record)
            self._actionUndo.setEnabled(True)
        else:
            self._actionUndo.setEnabled(False)

        self._actionRedo.menu().clear()
        actions = globals.project.getHistoryRedoActions()
        if actions:
            for record in reversed(actions):
                self._actionRedo.menu().addAction(record)
            self._actionRedo.setEnabled(True)
        else:
            self._actionRedo.setEnabled(False)

    @QtCore.Slot()
    def __onUndo(self):
        if globals.project is not None and self._actionUndo.isEnabled():
            globals.historySignals.undo.emit()

    @QtCore.Slot()
    def __onRedo(self):
        if globals.project is not None and self._actionRedo.isEnabled():
            globals.historySignals.redo.emit()

    def __onLoadLibClicked(self):
        print('info: Opening existing library file...')
        text = trStr('Open node library', u'Открыть библиотеку узлов').text()
        fname = QFileDialog.getOpenFileName(self, text, self._lastLibraryFile,
                                            'Xml Files (*.xml);;Node Lib Description (*.nld);;All Files (*.*)')

        # PySide.QFileDialog returns an array of two strings
        # First element is full path to selected file
        # Second element is given filter ("Xml lib (*.xml)" in that case)
        if not fname[0]:
            print('warning: File not selected')
            print('debug: See \'main_window.py\' : {0}'.format(getframeinfo(currentframe()).lineno))
            print('')
            return

        if globals.project is not None:
            # parse libs:
            if globals.project.addLibrary(fname[0]):
                # update lib dock tree:
                self._dockLibraries.setDatasource(globals.project.libraries, globals.project.alphabet)
                self._lastLibraryFile = fname[0]
        else:
            print('error: Project is None')
            print('debug: See \'main_window.py\' : {0}'.format(getframeinfo(currentframe()).lineno))

    def __onCreateLibClicked(self):
        if globals.project is not None:
            print('info: Creating new library file...')
            text = trStr('Create node library', u'Создать библиотеку узлов').text()
            fname = QFileDialog.getSaveFileName(self, text, '',
                                                'Xml Files (*.xml);;Node Lib Description (*.nld);;All Files (*.*)')

            # PySide.QFileDialog returns an array of two strings
            # First element is full path to selected file
            # Second element is given filter ("Xml lib (*.xml)" in that case)
            if not fname[0]:
                print('warning: File not selected')
                print('debug: See \'main_window.py\' : {0}'.format(getframeinfo(currentframe()).lineno))
                print('')
                return

            filePath = toUnixPath(fname[0])

            if filePath not in globals.project.lib_paths:
                libname = 'NewLibrary_{0}'.format(datetime.now().time())
                while libname in globals.project.libraries:
                    sleep(0.01)
                    libname = 'NewLibrary_{0}'.format(datetime.now().time())
                emptyLib = NodeLibrary(libname)
                emptyLib.setPath(filePath)
                libraryParser = liparser.LibParser()
                self._dockOutput.setSilent(True)
                libraryParser.save(globals.project.alphabet, {libname: emptyLib})
                globals.project.addLibrary(filePath)
                self._dockOutput.setSilent(False)

                # update lib dock tree:
                self._dockLibraries.setDatasource(globals.project.libraries, globals.project.alphabet)
                self._lastLibraryFile = filePath
            else:
                print(u'warning: Library file \'{0}\' already included into current project'.format(filePath))
                print('debug: See \'main_window.py\' : {0}'.format(getframeinfo(currentframe()).lineno))
                print('')

    def __onLoadTreeClicked(self):
        print('info: Opening existing tree file...')
        text = trStr('Open tree file', u'Открыть дерево').text()
        fname = QFileDialog.getOpenFileName(self, text, self._lastTreeFile,
                                            'Xml Files (*.xml);;Behavior Tree File (*.bt);;All Files (*.*)')

        # PySide.QFileDialog returns an array of two strings
        # First element is full path to selected file
        # Second element is given filter ("Xml lib (*.xml)" in that case)
        if not fname[0]:
            print('warning: File not selected')
            print('debug: See \'main_window.py\' : {0}'.format(getframeinfo(currentframe()).lineno))
            print('')
            return

        if globals.project is not None:
            # parse trees:
            if globals.project.addTree(fname[0]):
                # update tree dock tree:
                self._dockTreesList.setProject(globals.project)
                self._lastTreeFile = fname[0]
        else:
            print('error: Project is None')
            print('debug: See \'main_window.py\' : {0}'.format(getframeinfo(currentframe()).lineno))
            print('')

    def __onCreateTreeClicked(self):
        if globals.project is not None:
            print('info: Creating new tree file...')
            text = trStr('Create new tree file', u'Создать файл дерева').text()
            fname = QFileDialog.getSaveFileName(self, text, '',
                                                'Xml Files (*.xml);;Behavior Tree File (*.bt);;All Files (*.*)')

            # PySide.QFileDialog returns an array of two strings
            # First element is full path to selected file
            # Second element is given filter ("Xml lib (*.xml)" in that case)
            if not fname[0]:
                print('warning: File not selected')
                print('debug: See \'main_window.py\' : {0}'.format(getframeinfo(currentframe()).lineno))
                print('')
                return

            filePath = toUnixPath(fname[0])

            if filePath not in globals.project.tree_paths:
                treeParser = treeparser.TreeParser()
                self._dockOutput.setSilent(True)
                treeParser.save(globals.project.alphabet, BehaviorTree(), TreeNodes(), [filePath])
                globals.project.addTree(filePath)
                self._dockOutput.setSilent(False)

                # update tree dock tree:
                self._dockTreesList.setProject(globals.project)
                self._lastTreeFile = filePath
            else:
                print('warning: Tree file \'{0}\' already included into current project'.format(filePath))
                print('debug: See \'main_window.py\' : {0}'.format(getframeinfo(currentframe()).lineno))

            print('')

    def openProject(self, projectFile):
        if projectFile:
            if globals.project is not None and globals.project.modified:
                title = trStr('Open new project', u'Открытие нового проекта').text()
                message = trStr('Current project was modified.<br/>Save current project'\
                                '<br/>before opening new project?',
                                u'Текущий проект был изменен.<br/>Сохранить текущий проект'\
                                u'<br/>перед открытием нового проекта?').text()

                msgBox = QMessageBox(QMessageBox.Question, title, message)
                yes = msgBox.addButton(trStr('Yes', 'Да').text(), QMessageBox.YesRole)
                no = msgBox.addButton(trStr('No', 'Нет').text(), QMessageBox.NoRole)
                msgBox.addButton(trStr('Cancel', 'Отмена').text(), QMessageBox.RejectRole)

                msgBox.exec_()

                result = msgBox.clickedButton()

                if result == yes:
                    self.__onSaveProjectClicked()
                elif result == no:
                    pass
                else:
                    print('info: user cancelled opening new project')
                    return

            print('--------------------------------------------------------------')

            # parse proj:
            prevProject, globals.project = globals.project, None
            if prevProject is not None:
                prevProject.deactivate()

            globals.project = self._projectParser.open(projectFile)

            if globals.project is not None:
                globals.project.activate()
                self._actionUndo.menu().clear()
                self._actionUndo.setEnabled(False)

                self._actionRedo.menu().clear()
                self._actionRedo.setEnabled(False)

                self._dockNodeDescription.clear()
                self._dockNodeAttributes.clear()

                # update lib dock tree:
                self._dockLibraries.setDatasource(globals.project.libraries, globals.project.alphabet)

                # update tree dock tree:
                self._dockTreesList.setProject(globals.project)

                # set project for tab widget:
                self._centralStack.setCurrentIndex(0)
                self._tabWidget.setProject(globals.project)

                self._lastProjectFile = projectFile

                self._actionOpenTree.setEnabled(True)
                self._actionCreateTree.setEnabled(True)
                self._actionOpenLibrary.setEnabled(True)
                self._actionCreateLibrary.setEnabled(True)
                if projectFile in globals.recentProjects:
                    globals.recentProjects.remove(projectFile)
                globals.recentProjects.insert(0, projectFile)
                d = 1 + len(globals.recentProjects) - globals.maxRecentProjects
                if d > 0:
                    for i in range(d):
                        globals.recentProjects.pop()
                self._menuRecentProjects.clear()
                for p in globals.recentProjects:
                    self._menuRecentProjects.addAction(ProjectAction(self, p, p, p, self))
                self._menuRecentProjects.setEnabled(True)
                self.__saveRecentProjects()
                self._actionSaveProject_menu.setEnabled(True)
                self._actionSaveProject_tb.setEnabled(True)
                self.__startAutosaveTimer()
            else:
                if prevProject is not None:
                    prevProject.activate()
                globals.project = prevProject

    def __onOpenProjectClicked(self):
        text = trStr('Open existing project', u'Открыть проект').text()
        fname = QFileDialog.getOpenFileName(self, text, self._lastProjectFile,
                                            'Behavior Project File (*.btproj);;Xml Files (*.xml);;All Files (*.*)')

        # PySide.QFileDialog returns an array of two strings
        # First element is full path to selected file
        # Second element is given filter ("Xml lib (*.xml)" in that case)
        self.openProject(fname[0])

    def __onSaveProjectClicked(self):
        if globals.project is None:
            print('warning: Nothing to save!')
            print('info: First you have to open project at \'File\'->\'Open project...\'')
            print('info: or \'File\'->\'Recent projects\'')
            print('')
            return

        if self._projectParser.save(globals.project):
            message = u'<font color=\"YellowGreen\">project<br/>\"{0}\"<br/>saved successfully!</font>'\
                .format(globals.project.path)
            print(u'ok: project \"{0}\" have been saved successfully'.format(globals.project.path))
            print('')
            QMessageBox.information(self, 'Save project', message)
        else:
            message = u'<font color=\"red\">project<br/>\"{0}\"<br/>was not saved properly!</font>'\
                .format(globals.project.path)
            print(u'error: An error occured! Project \"{0}\" was not saved!'.format(globals.project.path))
            print('')
            QMessageBox.critical(self, 'Save project', message)

    def __autosave(self):
        if globals.project is None or not globals.project.modified:
            return
        print(trStr('info: Auto saving...', u'info: Автоматическое сохранение...').text())
        if self._projectParser.save(globals.project):
            print(trStr('ok: project \"{0}\" have been saved successfully'.format(globals.project.path),
                        u'ok: проект \"{0}\" сохранен успешно'.format(globals.project.path)).text())
            print('')
            print(trStr('ok: Auto save complete', u'ok: Автоматическое сохранение завершено').text())
        else:
            print(trStr('error: Auto save failed. For more information read output messages above.',
                        u'error: Ошибка при автоматическом сохранении. Для информации читайте сообщения выше.').text())
        print('')

    def __stopAutosaveTimer(self):
        if self._autosaveTimerRunning:
            self._autosaveTimer.stop()
            self._autosaveTimerRunning = False

    def __startAutosaveTimer(self):
        self.__stopAutosaveTimer()
        if globals.autosaveEnabled and globals.autosaveTime > 0.5:
            self._autosaveTimer.start(globals.autosaveTime * 1000.0)
            self._autosaveTimerRunning = True

    def __onReadAlphabetClicked(self):
        pass
        # if self.libraryData.isActive:
        # 	text = trStr(u'Open alphabet file', u'Открыть файл алфавита').text()
        # 	fname = QFileDialog.getOpenFileName(self,\
        # 										text, self.libraryData.lastAlphabetFile(),\
        # 										u'Xml Files (*.xml);;Alphabet File (*.abc);;All Files (*.*)')
        # 	if fname[0]:
        # 		self.libraryData.onAlphabetRead(fname[0])

    ##################################################

    def __horTriggered(self):
        self._actionViewHorizontal.setChecked(True)
        self._actionViewVertical.setChecked(False)
        self.treeViewModeChange.emit(True)

    def __verTriggered(self):
        self._actionViewHorizontal.setChecked(False)
        self._actionViewVertical.setChecked(True)
        self.treeViewModeChange.emit(False)

    def __cursorTriggered(self):
        self._actionModeConnectorTool.setChecked(False)
        self._actionModeCursor.setChecked(True)
        self._actionModeDrag.setChecked(False)
        self.treeConnectorModeChange.emit(False)
        self.treeDragModeChange.emit(False)

    def __dragTriggered(self):
        self._actionModeConnectorTool.setChecked(False)
        self._actionModeCursor.setChecked(False)
        self._actionModeDrag.setChecked(True)
        self.treeConnectorModeChange.emit(False)
        self.treeDragModeChange.emit(True)

    def __connectorTriggered(self):
        self._actionModeConnectorTool.setChecked(True)
        self._actionModeDrag.setChecked(False)
        self._actionModeCursor.setChecked(False)
        self.treeDragModeChange.emit(False)
        self.treeConnectorModeChange.emit(True)

    def __tabJustifyTriggered(self, _):
        # self.aTabWidthJustify.setChecked(c)
        self.treeJustifyModeChange.emit(self._actionViewJustifyWidth.isChecked())

    def __onLangEnglishTriggered(self):
        if globalLanguage.language != Language.English:
            self._viewActionLanguageEnglish.setChecked(True)
            self._viewActionLanguageRussian.setChecked(False)
            globalLanguage.changeLanguage(Language.English)

    def __onLangRussianTriggered(self):
        if globalLanguage.language != Language.Russian:
            self._viewActionLanguageEnglish.setChecked(False)
            self._viewActionLanguageRussian.setChecked(True)
            globalLanguage.changeLanguage(Language.Russian)

    ##############################################################
    def __onConnectorCurvedTrigger(self):
        self._viewActionConnectorCurved.setChecked(True)
        self._viewActionConnectorLine.setChecked(False)
        self._viewActionConnectorPolyline.setChecked(False)
        if self._connectorType.val != ConnectorType.Curve:
            self._connectorType.val = ConnectorType.Curve
            self.connectorTypeChanged.emit(self._connectorType.val)

    def __onConnectorLineTrigger(self):
        self._viewActionConnectorCurved.setChecked(False)
        self._viewActionConnectorLine.setChecked(True)
        self._viewActionConnectorPolyline.setChecked(False)
        if self._connectorType.val != ConnectorType.Line:
            self._connectorType.val = ConnectorType.Line
            self.connectorTypeChanged.emit(self._connectorType.val)

    def __onConnectorPolylineTrigger(self):
        self._viewActionConnectorCurved.setChecked(False)
        self._viewActionConnectorLine.setChecked(False)
        self._viewActionConnectorPolyline.setChecked(True)
        if self._connectorType.val != ConnectorType.Polyline:
            self._connectorType.val = ConnectorType.Polyline
            self.connectorTypeChanged.emit(self._connectorType.val)

    ##############################################################
    @QtCore.Slot()
    def __onBackgroundDisableTrigger(self):
        self._actionDisableBackground.setChecked(True)
        for bga in self._actionsBackgroundImage:
            bga.setChecked(False)
        print(trStr('info: Draw scene background is \'OFF\'', u'info: Фоновое изображение \'ВЫКЛ\'').text())
        globals.background = -1
        globals.optionsSignals.backgroundChanged.emit(int(globals.background))

    @QtCore.Slot(trAction)
    def __onBackgroundTrigger(self, bgAction):
        if bgAction in self._actionsBackgroundImage:
            self._actionDisableBackground.setChecked(False)
            for bga in self._actionsBackgroundImage:
                bga.setChecked(False)
            i = self._actionsBackgroundImage.index(bgAction)
            self._actionsBackgroundImage[i].setChecked(True)
            print(trStr('info: Draw scene background {0} is \'ON\''.format(i+1),
                        u'info: Фоновое изображение {0} \'ВКЛ\''.format(i+1)).text())
            globals.background = i
            globals.optionsSignals.backgroundChanged.emit(int(globals.background))
        else:
            bgAction.setChecked(False)

    ##############################################################
    @QtCore.Slot(str)
    def __onLibSelected(self, libname):
        self._dockNodeDescription.clear()
        self._dockNodeDescription.addLibraryWidget(globals.project.libraries, libname, globals.editLibraries)

    @QtCore.Slot(str, str)
    def __onNodeSelected(self, libname, nodename):
        self._dockNodeDescription.clear()
        self._dockNodeDescription.addNodeWidget(globals.project.libraries, libname, nodename, globals.editLibraries)

    def __onTabWidgetItemSelection(self, tabIndex, node, editable):
        i = self._dockNodeAttributes.currentIndex()
        self._dockNodeAttributes.setCurrent(tabIndex)
        self._dockNodeAttributes.replaceCurrentWidget(globals.project, node, editable)
        self._dockNodeAttributes.setCurrent(i)

        ok = False
        if node.libname in globals.project.libraries:
            for ln in globals.project.libraries:
                if node.nodeName in globals.project.libraries[ln]:
                    ok = True
                    break

        if ok:
            self._dockLibraries.select(node.libname, node.nodeName)
            self.__onNodeSelected(node.libname, node.nodeName)
        else:
            self._dockLibraries.select('', '')
            self._dockNodeDescription.clear()

    def __onTabWidgetItemSelectionCancel(self, tabIndex):
        i = self._dockNodeAttributes.currentIndex()
        self._dockNodeAttributes.setCurrent(tabIndex)
        self._dockNodeAttributes.replaceCurrentWidget()
        self._dockNodeAttributes.setCurrent(i)
        self._dockNodeDescription.clear()

    @QtCore.Slot(bool, float, float)
    def __onSceneItemPos(self, show, x, y):
        if show:
            self.statusBar().showMessage('item position ({0}, {1})'.format(x, y))
        else:
            self.statusBar().clearMessage()

#######################################################################################################################
#######################################################################################################################
