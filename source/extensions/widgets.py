# coding=utf-8
# -----------------
# file      : widgets.py
# date      : 2014/10/19
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

__author__ = 'Victor Zarubkin'
__copyright__ = 'Copyright (C) 2014  Victor Zarubkin'
__credits__ = ['Victor Zarubkin']
__license__ = ['GPLv3']
__version__ = '1.3.0'  # this is last application version when this script file was changed
__email__ = 'victor.zarubkin@gmail.com'
############################################################################

from PySide import QtCore
from PySide.QtGui import *
from language import globalLanguage, trStr

#######################################################################################################################
#######################################################################################################################


class scrollProxy(object):
    def __init__(self, widget):
        self.__widget = widget
        self.__widgetType = type(widget)
        self.__widget.focusInEvent = self.focusInEvent
        self.__widget.focusOutEvent = self.focusOutEvent

    def focusOutEvent(self, *args, **kwargs):
        # print('debug: %s focus OUT' & self.__widgetType.__name__)
        self.__widget.verticalScrollBar().setProperty('parentFocus', False)
        self.__widget.horizontalScrollBar().setProperty('parentFocus', False)
        self.__widget.verticalScrollBar().setStyle(QApplication.style())
        self.__widget.horizontalScrollBar().setStyle(QApplication.style())
        self.__widgetType.focusOutEvent(self.__widget, *args, **kwargs)

    def focusInEvent(self, *args, **kwargs):
        # print('debug: %s focus IN' & self.__widgetType.__name__)
        self.__widget.verticalScrollBar().setProperty('parentFocus', True)
        self.__widget.horizontalScrollBar().setProperty('parentFocus', True)
        self.__widget.verticalScrollBar().setStyle(QApplication.style())
        self.__widget.horizontalScrollBar().setStyle(QApplication.style())
        self.__widgetType.focusOutEvent(self.__widget, *args, **kwargs)


class comboBoxScrollProxy(object):
    def __init__(self, widget):
        self.__widget = widget
        self.__widgetType = type(widget)
        self.__widget.showPopup = self.showPopup
        self.__widget.hidePopup = self.hidePopup

    def hidePopup(self, *args, **kwargs):
        # print('debug: %s focus OUT' & self.__widgetType.__name__)
        self.__widget.view().verticalScrollBar().setProperty('parentFocus', False)
        self.__widget.view().horizontalScrollBar().setProperty('parentFocus', False)
        self.__widget.view().verticalScrollBar().setStyle(QApplication.style())
        self.__widget.view().horizontalScrollBar().setStyle(QApplication.style())
        self.__widgetType.hidePopup(self.__widget, *args, **kwargs)

    def showPopup(self, *args, **kwargs):
        # print('debug: %s focus IN' & self.__widgetType.__name__)
        self.__widget.view().verticalScrollBar().setProperty('parentFocus', True)
        self.__widget.view().horizontalScrollBar().setProperty('parentFocus', True)
        self.__widget.view().verticalScrollBar().setStyle(QApplication.style())
        self.__widget.view().horizontalScrollBar().setStyle(QApplication.style())
        self.__widgetType.showPopup(self.__widget, *args, **kwargs)

#######################################################################################################################


class trLabel(QLabel):
    def __init__(self, text, parent=None):
        isTr = isinstance(text, trStr)
        if isTr:
            txt = text.text()
        else:
            txt = text
        QLabel.__init__(self, txt, parent)
        if isTr:
            self._text = text
        else:
            self._text = trStr(text, text)
        self._tooltip = trStr('', '')
        globalLanguage.languageChanged.connect(self._onLanguageChange)

    def setText(self, text):
        if isinstance(text, trStr):
            self._text = text
            QLabel.setText(self, self._text.text())
        else:
            self._text = trStr(text, text)
            QLabel.setText(self, text)

    def setToolTip(self, text):
        if isinstance(text, trStr):
            self._tooltip = text
            QLabel.setToolTip(self, self._tooltip.text())
        else:
            self._tooltip = trStr(text, text)
            QLabel.setToolTip(self, text)

    @QtCore.Slot(str)
    def _onLanguageChange(self, _):
        QLabel.setText(self, self._text.text())
        QLabel.setToolTip(self, self._tooltip.text())

#######################################################################################################################


class trCheckbox(QCheckBox):
    def __init__(self, text, parent=None):
        isTr = isinstance(text, trStr)
        if isTr:
            txt = text.text()
        else:
            txt = text
        QCheckBox.__init__(self, txt, parent)
        if isTr:
            self._text = text
        else:
            self._text = trStr(text, text)
        self._tooltip = trStr('', '')
        globalLanguage.languageChanged.connect(self._onLanguageChange)

    def setText(self, text):
        if isinstance(text, trStr):
            self._text = text
            QCheckBox.setText(self, self._text.text())
        else:
            self._text = trStr(text, text)
            QCheckBox.setText(self, text)

    def setToolTip(self, text):
        if isinstance(text, trStr):
            self._tooltip = text
            QCheckBox.setToolTip(self, self._tooltip.text())
        else:
            self._tooltip = trStr(text, text)
            QCheckBox.setToolTip(self, text)

    @QtCore.Slot(str)
    def _onLanguageChange(self, _):
        QCheckBox.setText(self, self._text.text())

#######################################################################################################################


class trMenu(QMenu):
    def __init__(self, text, parent=None):
        isTr = isinstance(text, trStr)
        if isTr:
            txt = text.text()
        else:
            txt = text
        QMenu.__init__(self, txt, parent)
        if isTr:
            self._title = text
        else:
            self._title = trStr(text, text)
        self._tooltip = trStr(' ', ' ')
        QMenu.setToolTip(self, ' ')
        globalLanguage.languageChanged.connect(self._onLanguageChange)

    def setTitle(self, text):
        if isinstance(text, trStr):
            self._title = text
            QMenu.setTitle(self, self._title.text())
        else:
            self._title = trStr(text, text)
            QMenu.setTitle(self, text)

    def setToolTip(self, text):
        if isinstance(text, trStr):
            self._tooltip = text
            QMenu.setToolTip(self, self._tooltip.text())
        else:
            self._tooltip = trStr(text, text)
            QMenu.setToolTip(self, text)

    @QtCore.Slot(str)
    def _onLanguageChange(self, _):
        QMenu.setTitle(self, self._title.text())
        QMenu.setToolTip(self, self._tooltip.text())


class trMenuWithTooltip(trMenu):
    def event(self, e):
        if e.type() == QtCore.QEvent.ToolTip:
            action = self.activeAction()
            if action is not None and action.toolTip().replace(' ', ''):
                QToolTip.showText(e.globalPos(), action.toolTip())
                return True
            return False
        return trMenu.event(self, e)

#######################################################################################################################


class trAction(QAction):
    def __init__(self, text='', parent=None):
        isTr = isinstance(text, trStr)
        if isTr:
            txt = text.text()
        else:
            txt = text
        QAction.__init__(self, txt, parent)
        if isTr:
            self._text = text
        else:
            self._text = trStr(text, text)
        self._tooltip = trStr(' ', ' ')  # trStr(self._text.eng().replace('&', ''), self._text.rus().replace('&', ''))
        QAction.setToolTip(self, ' ')
        globalLanguage.languageChanged.connect(self._onLanguageChange)

    def setText(self, text):
        if isinstance(text, trStr):
            self._text = text
            QAction.setText(self, self._text.text())
        else:
            self._text = trStr(text, text)
            QAction.setText(self, text)

    def setToolTip(self, text):
        if isinstance(text, trStr):
            self._tooltip = text
            QAction.setToolTip(self, self._tooltip.text())
        else:
            self._tooltip = trStr(text, text)
            QAction.setToolTip(self, text)

    @QtCore.Slot(str)
    def _onLanguageChange(self, _):
        QAction.setText(self, self._text.text())
        QAction.setToolTip(self, self._tooltip.text())

#######################################################################################################################


class trButton(QPushButton):
    def __init__(self, text, parent=None):
        isTr = isinstance(text, trStr)
        if isTr:
            txt = text.text()
        else:
            txt = text
        QPushButton.__init__(self, txt, parent)
        if isTr:
            self._text = text
        else:
            self._text = trStr(text, text)
        self._tooltip = trStr('', '')
        globalLanguage.languageChanged.connect(self._onLanguageChange)

    def setText(self, text):
        if isinstance(text, trStr):
            self._text = text
            QPushButton.setText(self, self._text.text())
        else:
            self._text = trStr(text, text)
            QPushButton.setText(self, text)

    def setToolTip(self, text):
        if isinstance(text, trStr):
            self._tooltip = text
            QPushButton.setToolTip(self, self._tooltip.text())
        else:
            self._tooltip = trStr(text, text)
            QPushButton.setToolTip(self, text)

    @QtCore.Slot(str)
    def _onLanguageChange(self, _):
        QPushButton.setText(self, self._text.text())
        QPushButton.setToolTip(self, self._tooltip.text())


class SubmitButton(trButton):
    pass

#######################################################################################################################


class trDockWidget(QDockWidget):
    def __init__(self, title, parent=None):
        isTr = isinstance(title, trStr)
        if isTr:
            txt = title.text()
        else:
            txt = title
        QDockWidget.__init__(self, txt, parent)
        if isTr:
            self._title = title
        else:
            self._title = trStr(title, title)
        globalLanguage.languageChanged.connect(self._onLanguageChange)

    def setWindowTitle(self, title):
        if isinstance(title, trStr):
            self._title = title
            QDockWidget.setWindowTitle(self, self._title.text())
        else:
            self._title = trStr(title, title)
            QDockWidget.setWindowTitle(self, title)

    @QtCore.Slot(str)
    def _onLanguageChange(self, _):
        QDockWidget.setWindowTitle(self, self._title.text())

#######################################################################################################################


class trDialog(QDialog):
    def __init__(self, *args, **kwargs):
        QDialog.__init__(self, *args, **kwargs)
        self._title = trStr('', '')
        globalLanguage.languageChanged.connect(self._onLanguageChange)

    def setWindowTitle(self, text):
        if isinstance(text, trStr):
            self._title = text
            QDialog.setWindowTitle(self, self._title.text())
        else:
            self._title = trStr(text, text)
            QDialog.setWindowTitle(self, text)

    @QtCore.Slot(str)
    def _onLanguageChange(self, _):
        QDialog.setWindowTitle(self, self._title.text())

#######################################################################################################################


class trGroupBox(QGroupBox):
    def __init__(self, title, parent=None):
        isTr = isinstance(title, trStr)
        if isTr:
            txt = title.text()
        else:
            txt = title
        QGroupBox.__init__(self, txt, parent)
        if isTr:
            self._title = title
        else:
            self._title = trStr(title, title)
        globalLanguage.languageChanged.connect(self._onLanguageChange)

    def setTitle(self, text):
        if isinstance(text, trStr):
            self._title = text
            QGroupBox.setTitle(self, self._title.text())
        else:
            self._title = trStr(text, text)
            QGroupBox.setTitle(self, text)

    @QtCore.Slot(str)
    def _onLanguageChange(self, _):
        QGroupBox.setTitle(self, self._title.text())

#######################################################################################################################


class trRadioButton(QRadioButton):
    def __init__(self, text, parent=None):
        isTr = isinstance(text, trStr)
        if isTr:
            txt = text.text()
        else:
            txt = text
        QRadioButton.__init__(self, txt, parent)
        if isTr:
            self._text = text
        else:
            self._text = trStr(text, text)
        globalLanguage.languageChanged.connect(self._onLanguageChange)

    def setText(self, text):
        if isinstance(text, trStr):
            self._text = text
            QRadioButton.setText(self, self._text.text())
        else:
            self._text = trStr(text, text)
            QRadioButton.setText(self, text)

    @QtCore.Slot(str)
    def _onLanguageChange(self, _):
        QRadioButton.setText(self, self._text.text())

#######################################################################################################################
#######################################################################################################################
