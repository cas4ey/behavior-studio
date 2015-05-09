# coding=utf-8
# -----------------
# file      : help_widget.py
# date      : 2014/11/01
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

from PySide import QtCore
from PySide.QtGui import *
from PySide.QtCore import *

from extensions.widgets import *

from language import globalLanguage, trStr

from auxtypes import joinPath

import globals

#######################################################################################################################
#######################################################################################################################


class _HelpItem(QTreeWidgetItem):
    def __init__(self, *args, **kwargs):
        QTreeWidgetItem.__init__(self, *args, **kwargs)
        self._contents = trStr('', '')
        self._text = trStr('', '')
        self._index = -1
        globalLanguage.languageChanged.connect(self._onLanguageChange)

    def setIndex(self, index):
        self._index = index

    def index(self):
        return self._index

    def setText(self, column, text):
        self._text = text
        QTreeWidgetItem.setText(self, 0, self._text.text())

    def setContents(self, contents):
        self._contents = contents

    def setContentsEng(self, contents):
        self._contents.setEng(contents)

    def setContentsRus(self, contents):
        self._contents.setRus(contents)

    def contents(self):
        return self._contents.text()

    @QtCore.Slot(str)
    def _onLanguageChange(self, language):
        QTreeWidgetItem.setText(self, 0, self._text.text())


class HelpWidget(QMainWindow):
    closed = QtCore.Signal()

    def __init__(self, *args, **kwargs):
        QMainWindow.__init__(self, *args, **kwargs)
        self.setObjectName('helpWindow')

        self._title = trStr('Behavior Studio Help', 'Справка Behavior Studio')
        QMainWindow.setWindowTitle(self, self._title.text())
        self.setWindowIcon(QIcon(joinPath(globals.applicationIconsPath, 'help.png')))

        # Create text window
        self.__textEdit = QTextEdit()
        self.__textEdit.setAcceptRichText(True)
        self.__textEdit.setTextInteractionFlags(Qt.TextBrowserInteraction | Qt.TextSelectableByKeyboard)
        self.__textEditFocusProxy = scrollProxy(self.__textEdit)

        # Fill table of contents
        self.__subjectHeaderLabel = trStr('Table of contents', 'Содержание')
        self.__subjectIndex = QTreeWidget()
        self.__subjectIndex.setAlternatingRowColors(True)
        self.__subjectIndex.setAnimated(True)
        self.__subjectIndex.setColumnCount(1)
        self.__subjectIndex.setHeaderLabel(self.__subjectHeaderLabel.text())
        self.__subjectFocusProxy = scrollProxy(self.__subjectIndex)

        self.__topics = []
        topItem = self.__fillContents()
        self.__subjectIndex.addTopLevelItem(topItem)

        self.__subjectIndex.currentItemChanged.connect(self.__onTopicChange)
        self.__subjectIndex.setCurrentItem(topItem)

        dock = QDockWidget()
        dock.setObjectName('helpIndex')
        dock.setAllowedAreas(Qt.LeftDockWidgetArea)
        dock.setFeatures(QDockWidget.NoDockWidgetFeatures)
        dock.setTitleBarWidget(QWidget())
        dock.setWidget(self.__subjectIndex)
        self.addDockWidget(Qt.LeftDockWidgetArea, dock)

        dock = QDockWidget()
        dock.setObjectName('helpContents')
        dock.setAllowedAreas(Qt.RightDockWidgetArea)
        dock.setFeatures(QDockWidget.NoDockWidgetFeatures)
        dock.setTitleBarWidget(QWidget())
        dock.setWidget(self.__textEdit)
        self.addDockWidget(Qt.RightDockWidgetArea, dock)

        self.setStatusBar(QStatusBar())

        globalLanguage.languageChanged.connect(self.__onLanguageChange)

        self.readSettings()

    def closeEvent(self, event):
        self.saveSettings()
        self.closed.emit()
        QMainWindow.closeEvent(self, event)

    def saveSettings(self):
        settings = QSettings('Victor Zarubkin', 'Behavior Studio')
        settings.beginGroup('help')
        settings.setValue('geometry', self.saveGeometry())
        settings.setValue('windowState', self.saveState(globals.intVersion))
        settings.setValue('subject', self.__subjectIndex.currentItem().index())
        settings.endGroup()

    def readSettings(self):
        settings = QSettings('Victor Zarubkin', 'Behavior Studio')
        settings.beginGroup('help')

        geometry = settings.value('geometry')
        if geometry is not None:
            self.restoreGeometry(geometry)

        state = settings.value('windowState')
        if state is not None:
            restored = self.restoreState(state, globals.intVersion)
            if not restored:
                for ver in globals.intPreviousVersions:
                    restored = self.restoreState(state, ver)
                    if restored:
                        break

        subject = 0
        subjectValue = settings.value('subject')
        if subjectValue is not None:
            try:
                subject = int(subjectValue)
            except ValueError:
                subject = 0

        if subject > 0:
            item = self.__topics[subject]
            self.__subjectIndex.scrollToItem(item)
            self.__subjectIndex.setCurrentItem(item)

        settings.endGroup()

    def setWindowTitle(self, text):
        if type(text) is trStr:
            self._title = text
            QMainWindow.setWindowTitle(self, self._title.text())
        else:
            self._title = trStr(text, text)
            QMainWindow.setWindowTitle(self, text)

    @QtCore.Slot(QTreeWidgetItem, QTreeWidgetItem)
    def __onTopicChange(self, current, previous):
        self.__textEdit.setHtml(current.contents())

    @QtCore.Slot(str)
    def __onLanguageChange(self, language):
        QMainWindow.setWindowTitle(self, self._title.text())
        self.__subjectIndex.setHeaderLabel(self.__subjectHeaderLabel.text())
        if self.__subjectIndex.currentItem():
            self.__textEdit.setHtml(self.__subjectIndex.currentItem().contents())
        else:
            self.__textEdit.setHtml('')

    def __fillContents(self):
        # top item
        topItem = _HelpItem()
        topItem.setIndex(len(self.__topics))
        topItem.setText(0, trStr('Behavior Studio', 'Behavior Studio'))
        self.__topics.append(topItem)

        # graphics scene topics
        item = _HelpItem()
        item.setIndex(len(self.__topics))
        item.setText(0, trStr('Working with graphics scene', 'Работа с графической областью'))
        topItem.addChild(item)
        self.__topics.append(item)

        eng = '<h1>Graphics scene</h1>Press \'<b>F1</b>\' when graphics scene is selected to ' \
              'see it\'s hot keys and hints.'
        eng += '<br/><h2>'
        eng += 'Graphics scene hot keys and hints'

        eng += '</h2><br/><h4>'
        eng += 'Holding <i>Ctrl</i> button you can connect and disconnect nodes'
        eng += '</h4>'

        eng += '<p style="text-indent: 20px;">Select node, press <b>Ctrl</b>+<b>LMB</b> and move mouse \
               cursor: you will see a red arrow. \
               Red arrow direction points from parent node to child.</p>\
               <p style="text-indent: 20px;">If the arrow points from empty space to node (or from node to an \
               empty space), then this node will be diconnected from it\'s parent.</p>'

        eng += '<br/><h4>'
        eng += 'Holding <i>Shift</i> button you can change nodes order'
        eng += '</h4>'

        eng += '<p style="text-indent: 20px;">Select node, press <b>Shift</b>+<b>LMB</b> and move mouse ' \
               'cursor until node will not change it\'s position.</p>'

        eng += '<br/><h4>'
        eng += 'Holding <i>Alt</i> button you can watch node attributes'
        eng += '</h4>'

        eng += '<p style="text-indent: 20px;">Press <b>Alt</b> and move mouse cursor over required node ' \
               'on graphics scene and you will see popup window with it\'s attributes.</p>'

        eng += '<br/><h4>'
        eng += 'There are copy/paste feature available'
        eng += '</h4>'

        eng += '<p style="text-indent: 20px;">Select required node and press <b>Ctrl</b>+<b>C</b> then \
               selected node and <b>all</b> it\'s children will be copied into a clipboard.<br/>\
               Now you can press <b>Ctrl</b>+<b>V</b> and copied tree will appear under mouse cursor.</p>\
               <p><i><u>Hint:</u> You can copy a tree on one diagram and paste it to another diagram.</i></p>'

        rus = '<h1>Графическая область редактирования</h1>Нажмите \'<b>F1</b>\', когда графическая область активна, ' \
              'чтобы увидеть список горячих клавиш и подсказки.'

        rus += '<br/><h2>'
        rus += 'Горячие клавиши и подсказки для работы с графической областью'
        rus += '</h2><br/><h4>'

        rus += 'Удерживая <i>Ctrl</i>, можно соединять узлы'
        rus += '</h4>'

        rus += '<p style="text-indent: 20px;">Выделите нужный узел, зажмите <b>Ctrl</b>+<b>ЛКМ</b> и перемещайте \
               курсор мыши: вы увидите красную стрелку. Красная стрелка рисуется от родителя к дочернему узлу.</p>\
               <p style="text-indent: 20px;">Если стрелка направлена к узлу из пустой области (или от узла \
               в пустую область), то узел будет отсоединен от своего родителя.</p>'

        rus += '<br/><h4>'
        rus += 'Удерживая <i>Shift</i>, можно изменять порядок узлов'
        rus += '</h4>'

        rus += '<p style="text-indent: 20px;">Выделите нужный узел, зажмите <b>Shift</b>+<b>ЛКМ</b> ' \
               'и перемещайте курсор мыши до тех пор, пока узел не изменит свою позицию.</p>'

        rus += '<br/><h4>'
        rus += 'Удерживая <i>Alt</i>, можно смотреть параметры узлов'
        rus += '</h4>'

        rus += '<p style="text-indent: 20px;">Зажмите <b>Alt</b> и переместите курсор мыши на нужный узел ' \
               'на графической области и появится окошко с параметрами этого узла.</p>'

        rus += '<br/><h4>'
        rus += 'Доступно копирование и вставка деревьев'
        rus += '</h4>'

        rus += '<p style="text-indent: 20px;">Выделите нужный узел и нажмите <b>Ctrl</b>+<b>C</b> - \
               узел и <b>все</b> его дочерние узлы будут скопированы в буфер.<br/>\
               Теперь вы можете нажать <b>Ctrl</b>+<b>V</b> и скопированное дерево появится под курсором мыши.</p>\
               <p><i><u>Подсказка:</u> Дерево можно скопировать на одной диаграмме и \
               вставить на любую другую диаграмму.</i></p>'

        item.setContentsEng(eng)
        item.setContentsRus(rus)

        return topItem

#######################################################################################################################
#######################################################################################################################
