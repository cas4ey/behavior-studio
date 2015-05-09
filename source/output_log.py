# coding=utf-8
# -----------------
# file      : output_log.py
# date      : 2012/11/11
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

""" Script file with definition of ColsoleLog class and OutputDock class.

ConsoleLog is QTextEdit that stores and displays log text.
OutputDock is QDockWidget that holds ConsoleLog and redirects pintable text
from standard python output into ConsoleLog.
"""

__author__ = 'Victor Zarubkin'
__copyright__ = 'Copyright (C) 2012  Victor Zarubkin'
__credits__ = ['Victor Zarubkin']
__license__ = ['GPLv3']
__version__ = '1.3.0'  # this is last application version when this script file was changed
__email__ = 'victor.zarubkin@gmail.com'
############################################################################

import re

from PySide import QtCore
from PySide.QtCore import *
from PySide.QtGui import *

from extensions.widgets import trDockWidget, scrollProxy

from compat_2to3 import *
import globals

########################################################################################################################
########################################################################################################################


class ConsoleLog(QTextEdit):
    def __init__(self, *args, **kwargs):
        QTextEdit.__init__(self, *args, **kwargs)
        self._focusProxy = scrollProxy(self)
        self.setAcceptRichText(True)
        self.setTextInteractionFlags(Qt.TextBrowserInteraction | Qt.TextSelectableByKeyboard)
        self.__text = u'> '
        self.__fontCol = False
        self.__ignoreEndl = False

    def appendText(self, text):
        if text == '\n' and self.__ignoreEndl:
            self.__ignoreEndl = False
            return

        self.__ignoreEndl = False

        # replace symbols '<' and '>' because these are html special symbols
        text = text.replace(u'<', u'&lt;').replace(u'>', u'&gt;')

        # закрытие тэга <font>, если требуется
        if self.__fontCol and '\n' in text:
            text = u'</font>' + text
            self.__fontCol = False

        # replace '\n' with html '<br/>' and insert '> ' sub-string into the beginning of every new line
        theText = unicode(text.replace(u'\n', u'<br/>> '))
        lowerStr = theText.lower().strip()

        # messages colorizing
        if u'error:' in lowerStr[:6]:
            p = re.compile(u'error:', re.IGNORECASE)
            theText = u'<font color=\"Red\">{0}'.format(p.sub(u'', theText, 1))
            self.__fontCol = True
        elif u'warning:' in lowerStr[:9]:
            p = re.compile(u'warning:', re.IGNORECASE)
            theText = u'<font color=\"Orange\">{0}'.format(p.sub(u'', theText, 1))
            self.__fontCol = True
        elif u'info:' in lowerStr[:5]:
            p = re.compile(u'info:', re.IGNORECASE)
            theText = u'<font color=\"CadetBlue\">{0}'.format(p.sub(u'', theText, 1))
            self.__fontCol = True
        elif u'ok:' in lowerStr[:3]:
            p = re.compile(u'ok:', re.IGNORECASE)
            theText = u'<font color=\"YellowGreen\">{0}'.format(p.sub(u'', theText, 1))
            self.__fontCol = True
        elif u'debug:' in lowerStr[:6]:
            if not globals.debugMode:
                self.__ignoreEndl = True
                return
            p = re.compile(u'debug:', re.IGNORECASE)
            theText = u'<font color=\"RosyBrown\">{0}'.format(p.sub(u'', theText, 1))
            self.__fontCol = True

        # put new text into the end
        self.__text += theText

        # set new text to the QTextEdit to see changes
        self.setHtml(self.__text)

        # move scroll-bar into the end to be able to watch last message immediately
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())

########################################################################################################################
########################################################################################################################


class OutputDock(trDockWidget):
    def __init__(self, title, parent=None):
        trDockWidget.__init__(self, title, parent)
        self.__writer = self.__write
        self.__textEdit = ConsoleLog(self)
        self.setWidget(self.__textEdit)

    def setSilent(self, silent):
        """ Changes '__writer' method to be able to write text or to be idle (depends on 'silent' value).

        :param silent: Boolean value; if True, then all new text would be displayed in QTextEdit,
                        otherwise - new text will be ignored
        """
        if silent:
            self.__writer = self.__doNotWrite
        else:
            self.__writer = self.__write

    def scrollBottom(self):
        """ Scrolls QTextEdit to the last message. """
        self.__textEdit.verticalScrollBar().setValue(self.__textEdit.verticalScrollBar().maximum())

    def scrollTop(self):
        """ Scrolls QTextEdit to the top (first message). """
        self.__textEdit.verticalScrollBar().setValue(self.__textEdit.verticalScrollBar().minimum())

    @QtCore.Slot(str)
    def write(self, text):
        """ Calls another method to write input text or to do nothing.

        :param text: Input text
        """
        self.__writer(text)

    def __write(self, text):
        """ Writes text into the end of text of self QTextEdit.

        :param text: Input text that will be displayed in QTextEdit
        """
        self.__textEdit.appendText(text)

    def __doNotWrite(self, text):
        """ Does nothing.

        :param text: Input text that will be ignored
        """
        pass

    def flush(self, *args, **kwargs):
        """ This method is called on application exit maybe by QApplication, I don't know,
        But it must exist or application will crush on exit.
        """
        pass

########################################################################################################################
########################################################################################################################

