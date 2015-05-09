# coding=utf-8
# -----------------
# file      : tldialog.py
# date      : 2012/11/17
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

from PySide.QtCore import *
from PySide.QtGui import *

import treenode

from language import globalLanguage, Language

#######################################################################################################################
#######################################################################################################################


class TL_CreateDialog(QDialog):
    __eng_Warnings = ['', 'enter name', 'that tree is already exist']
    __rus_Warnings = ['', 'введите имя для дерева', 'дерево с таким именем уже существует']

    def __init__(self, project, filename, parent=None):
        QDialog.__init__(self, parent)
        globalLanguage.languageChanged.connect(self.onLanguageChange)

        self.setWindowTitle('Create new behavior tree')

        self.filename = filename
        self.project = project

        enterNameLabel = QLabel('Tree name:')
        enterNameLabel.setAlignment(Qt.AlignRight)
        self.__enterNameEdit = QLineEdit()
        self.__enterNameEdit.textEdited.connect(self.onNameEditing)

        self.__OKButton = QPushButton('OK')
        self.__OKButton.setEnabled(False)

        buttonBox = QDialogButtonBox(Qt.Horizontal)
        buttonBox.addButton(self.__OKButton, QDialogButtonBox.AcceptRole)
        buttonBox.addButton(QDialogButtonBox.Cancel)
        buttonBox.rejected.connect(self.reject)
        buttonBox.accepted.connect(self.onOK)

        self.__statusBar = QStatusBar()
        self.__Warning = int(1)
        self.__statusBar.showMessage(self.warning())

        mainLayout = QGridLayout()
        mainLayout.addWidget(enterNameLabel, 0, 0)
        mainLayout.addWidget(self.__enterNameEdit, 0, 1)
        mainLayout.addWidget(buttonBox, 1, 0, 1, 2, Qt.AlignRight)
        mainLayout.setContentsMargins(5, 5, 5, 5)

        vLayout = QVBoxLayout()
        vLayout.addLayout(mainLayout)
        vLayout.addStretch(10)
        vLayout.addWidget(self.__statusBar)
        vLayout.setContentsMargins(0, 0, 0, 0)

        self.setContentsMargins(0, 0, 0, 0)
        self.setLayout(vLayout)

        # self.setMinimumWidth(540)
        # self.setMinimumHeight(self.sizeHint().height())
        # self.setMaximumHeight(self.sizeHint().height())

        self.onLanguageChange(globalLanguage.language)

    def warning(self):
        if globalLanguage.language == Language.English:
            return self.__eng_Warnings[self.__Warning]
        elif globalLanguage.language == Language.Russian:
            return self.__rus_Warnings[self.__Warning]
        return ''

    def onNameEditing(self, text):
        if text and text[-1] == ' ':
            self.__enterNameEdit.undo()
        else:
            self.__validate(text)

    def onOK(self):
        if self.__validate(self.__enterNameEdit.text()):
            classes = self.project.alphabet.getClasses(True)
            desc = None
            for c in classes:
                for l in self.project.libraries:
                    nodes = self.project.libraries[l].getAll(c)
                    if nodes:
                        for n in nodes:
                            desc = nodes[n]
                            break
                    if desc is not None:
                        break
                if desc is not None:
                    break

            if desc is not None:
                newTree = treenode.TreeNode(self.project, None, desc.nodeClass, desc.nodeType, desc.debugByDefault, None)
                newTree.libname = desc.libname
                newTree.nodeName = desc.name
                newTree.setPath(self.filename)
                newTree.setRefName(self.__enterNameEdit.text())
                newTree.reparseAttributes()
                self.parent().setTempTree(newTree)
                self.accept()
            else:
                self.reject()

    def __validate(self, name):
        fullName = self.filename + '/' + name

        if not name:
            self.__Warning = 1
        else:
            if fullName in self.project.trees:
                self.__Warning = 2
            else:
                self.__Warning = 0

        if self.__Warning > 0:
            self.__statusBar.showMessage(self.warning())
            self.__OKButton.setEnabled(False)
        else:
            self.__statusBar.clearMessage()
            self.__OKButton.setEnabled(True)

        return self.__Warning == 0

    def onLanguageChange(self, lang):
        if globalLanguage.language == Language.English:
            self.setWindowTitle('')
        elif globalLanguage.language == Language.Russian:
            self.setWindowTitle('')

#######################################################################################################################
#######################################################################################################################

