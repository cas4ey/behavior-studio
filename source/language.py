# coding=utf-8
# -----------------
# file      : language.py
# date      : 2012/12/08
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

""" This script file contains definition of Language and trStr classes,
and it also contains global value of language for the application.

Language class contains possible values of languages (English and Russian at the moment),
their aliases (for example, 'english' and 'eng' for English) and current language value.
Also, it emits signal when current language value changes.

trStr class makes it possible to store text and it's translation and to get current text
(or it's translation) based on current application language value through 'text()' method.
So there is no need to write 'if language == English: ... else: ...' each time you want
to display some text.

In future I plan to replace it with QTranslator.
"""

__author__ = 'Victor Zarubkin'
__copyright__ = 'Copyright (C) 2012  Victor Zarubkin'
__credits__ = ['Victor Zarubkin']
__license__ = ['GPLv3']
__version__ = '1.3.0'  # this is last application version when this script file was changed
__email__ = 'victor.zarubkin@gmail.com'
############################################################################

from PySide import QtCore

from compat_2to3 import *

#######################################################################################################################
#######################################################################################################################


class Language(QtCore.QObject):
    English = u'english'
    Russian = u'русский'

    __languages = {
        u'english': English,
        u'eng': English,
        u'английский': English,
        u'англ': English,
        u'russian': Russian,
        u'rus': Russian,
        u'русский': Russian,
        u'рус': Russian
    }

    languageChanged = QtCore.Signal(str)  # Language change notification signal

    def __init__(self):
        QtCore.QObject.__init__(self, None)
        self.language = Language.English

    @QtCore.Slot(str)
    def changeLanguage(self, lang):
        """ Changes current language.

        Note that it also emits signal if language value would be changed.

        :param lang: Language name alias
        """
        if self.rightLanguage(lang):
            self.language = self.__languages[lang]
            self.languageChanged.emit(self.language)

    def rightLanguage(self, lang):
        """ Checks if passed language name string (alias) is available.

        :param lang: Language name alias
        :return: True if 'lang' alias present in available aliases list, False - otherwise
        """
        return lang in self.__languages

    def possibleValues(self):
        """ Returns all possible languages aliases. """
        return dict_items(self.__languages.keys())

#######################################################################################################################
#######################################################################################################################

globalLanguage = Language()  # Global application language value


class trStr(object):
    def __init__(self, eng, rus):
        self.__text = {
            Language.English: eng,
            Language.Russian: rus
        }

    def text(self):
        """ Returns text on appropriate language based on 'globalLanguage.language' value.

        :return: English or Russian translation
        """
        global globalLanguage
        return self.__text[globalLanguage.language]

    def rus(self):
        """ Returns Russian text string. """
        return self.__text[Language.Russian]

    def eng(self):
        """ Returns English text string. """
        return self.__text[Language.English]

    def setRus(self, text):
        """ Sets russian translation.

        :param text: Text in russian
        """
        self.__text[Language.Russian] = text

    def setEng(self, text):
        """ Sets english translation.

        :param text: Text in english
        """
        self.__text[Language.English] = text

    def __str__(self):
        """ Same as 'text()' method. """
        return self.text()

    def __repr__(self):
        """ Same as 'text()' method. """
        return self.text()
