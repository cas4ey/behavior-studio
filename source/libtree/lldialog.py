# coding=utf-8
# -----------------
# file      : lldialog.py
# date      : 2012/12/16
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

from __future__ import unicode_literals

__author__ = 'Victor Zarubkin'
__copyright__ = 'Copyright (C) 2012  Victor Zarubkin'
__credits__ = ['Victor Zarubkin']
__license__ = ['GPLv3']
__version__ = '1.3.0'  # this is last application version when this script file was changed
__email__ = 'victor.zarubkin@gmail.com'

from PySide.QtCore import *
from PySide.QtGui import *

from treenode import ATTRIBUTE_TYPES

#######################################################################################################################
#######################################################################################################################


class LL_CreateLibDialog(QDialog):
    __wrong_first_symbols = ['.', ':']
    __wrong_symbols = [',', ';']

    def __init__(self, parent=None):
        QDialog.__init__(self, parent)

        self.setWindowTitle('Create new node library')

        enterNameLabel = QLabel('Library name:')
        enterNameLabel.setAlignment(Qt.AlignRight)
        self.__enterNameEdit = QLineEdit()
        self.__enterNameEdit.textEdited.connect(self.onNameEditing)

        enterFileLabel = QLabel('Enter XML-file name:')
        enterFileLabel.setAlignment(Qt.AlignRight)
        self.__enterFileEdit = QLineEdit()
        self.__enterFileEdit.textEdited.connect(self.onFileEditing)
        self.__browseButton = QPushButton('Browse...')
        self.__browseButton.clicked.connect(self.onBrowseClick)

        fileLayout = QHBoxLayout()
        fileLayout.addWidget(self.__enterFileEdit)
        fileLayout.addWidget(self.__browseButton)

        self.__OKButton = QPushButton('OK')
        self.__OKButton.setEnabled(False)

        buttonBox = QDialogButtonBox(Qt.Horizontal)
        buttonBox.addButton(self.__OKButton, QDialogButtonBox.AcceptRole)
        buttonBox.addButton(QDialogButtonBox.Cancel)
        buttonBox.rejected.connect(self.reject)
        buttonBox.accepted.connect(self.onOK)

        self.__Warning = QLabel('<font color="red">enter name</font>')

        mainLayout = QGridLayout()
        mainLayout.addWidget(QLabel('.'), 0, 0, Qt.AlignRight)
        mainLayout.addWidget(self.__Warning, 0, 1, Qt.AlignLeft)
        mainLayout.addWidget(enterNameLabel, 1, 0)
        mainLayout.addWidget(enterFileLabel, 2, 0)
        mainLayout.addWidget(self.__enterNameEdit, 1, 1)
        mainLayout.addLayout(fileLayout, 2, 1)
        mainLayout.addWidget(buttonBox, 3, 0, 1, 2, Qt.AlignRight)

        self.setLayout(mainLayout)

        self.setMinimumWidth(540)
        self.setMinimumHeight(self.sizeHint().height())
        self.setMaximumHeight(self.sizeHint().height())

    def onNameEditing(self, text):
        pass

    def onFileEditing(self, text):
        pass

    def onBrowseClick(self):
        pass

    def onOK(self):
        pass

#######################################################################################################################
#######################################################################################################################


class AttrEditDialog(QDialog):
    def __init__(self, attr, parent):
        QDialog.__init__(self, parent)
        self.setWindowTitle('Edit attribute')

        self.__attr = attr

        self.__name = self.__attr.name
        self.__datatype = self.__attr.typeName()

        self.__combo = QComboBox()
        self.__combo.addItems(ATTRIBUTE_TYPES)
        if self.__datatype in ATTRIBUTE_TYPES:
            self.__combo.setCurrentIndex(ATTRIBUTE_TYPES.index(self.__datatype))

        self.__edit = QLineEdit(self.__attr.name)
        self.__edit.textEdited.connect(self.__onNameEdit)

        self.__NameErr = False
        self.__Warning = QLabel('.')
        self.__Warning.hide()

        self.__OKButton = QPushButton('OK')
        self.__OKButton.setEnabled(False)

        buttonBox = QDialogButtonBox(Qt.Horizontal)
        buttonBox.addButton(self.__OKButton, QDialogButtonBox.AcceptRole)
        buttonBox.addButton(QDialogButtonBox.Cancel)
        buttonBox.rejected.connect(self.reject)
        buttonBox.accepted.connect(self.__onOK)

        mainLayout = QGridLayout()
        mainLayout.addWidget(QLabel('.'), 0, 0, Qt.AlignRight)
        mainLayout.addWidget(self.__Warning, 0, 1, Qt.AlignLeft)
        mainLayout.addWidget(self.__combo, 1, 0)  # ,Qt.AlignRight)
        mainLayout.addWidget(self.__edit, 1, 1)
        mainLayout.addWidget(buttonBox, 2, 0, 1, 2, Qt.AlignRight)

        self.setLayout(mainLayout)

    def __onNameEdit(self, new_name):
        new_name.strip()
        self.__edit.setText(new_name)

        if not new_name:
            self.__NameErr = True
            self.__Warning.setText('<font color="red">Attr name is too short.</font>')
            self.__Warning.show()
            self.__OKButton.setEnabled(False)
        elif new_name != self.__attr.name and new_name in self.parent().attributes():
            self.__NameErr = True
            self.__Warning.setText('<font color="red">Attr name duplicate.</font>')
            self.__Warning.show()
            self.__OKButton.setEnabled(False)
        else:
            self.__NameErr = False
            self.__Warning.hide()
            self.__OKButton.setEnabled(True)

    def __onOK(self):
        if self.__NameErr is True:
            self.reject()
        else:
            self.__attr.name = self.__edit.text()
            self.__datatype = ATTRIBUTE_TYPES[self.__combo.currentIndex()]
            self.accept()


class AttrTree(QTreeWidget):
    def __init__(self, libs, attrs, parent=None):
        QTreeWidget.__init__(self, parent)
        self.setRootIsDecorated(False)
        self.setAlternatingRowColors(True)
        self.setDragEnabled(False)

        self.__libraries = libs
        self.__attributes = dict()
        for name in attrs:
            self.__attributes[name] = attrs[name].deepcopy()

        self.setHeaderLabels(['type', 'name'])
        for a in self.__attributes:
            item = QTreeWidgetItem(self)
            item.setText(0, self.__attributes[a].typeName())
            item.setText(1, self.__attributes[a].name())
            self.addTopLevelItem(item)

        self.itemDoubleClicked.connect(self.__onDoubleClicked)

    def attributes(self):
        return self.__attributes

    def addAttribute(self, attr):
        if attr.name not in self.__attributes:
            self.__attributes[attr.name] = attr
            item = QTreeWidgetItem(self)
            item.setText(0, self.__attributes[attr.name].typeName())
            item.setText(1, self.__attributes[attr.name].name())
            self.addTopLevelItem(item)

    def __onDoubleClicked(self, item, column):
        name = item.text(1)
        if self.indexOfTopLevelItem(item) >= 0 and name in self.__attributes:
            dialog = AttrEditDialog(self.__attributes[name], self)
            if dialog.exec_() == QDialog.Accepted:
                if self.__attributes[name].name not in self.__attributes:
                    temp_name = self.__attributes[name].name
                    self.__attributes[self.__attributes[name].name] = self.__attributes[name]
                    del self.__attributes[name]
                    name = temp_name
                item.setText(0, self.__attributes[name].typeName())
                item.setText(1, self.__attributes[name].name())

#######################################################################################################################
#######################################################################################################################


class LL_EditNodeDialog(QDialog):
    def __init__(self, libs, tree, libname, nodename, parent=None):
        QDialog.__init__(self, parent)
        self.setWindowTitle('Edit node')

        self.__libraries = libs
        self.__tree = tree
        self.__libname = libname
        self.__nodename = nodename
        self.__new_name = nodename

        self.__NodeNameErr = False
        self.__NameWarn = ''

        self.__attributes = dict()
        self.__attrsByRow = []

        if self.__tree is None:
            self.reject()
        elif self.__libname not in self.__libraries or self.__nodeDesc() is None:
            self.reject()
        else:
            self.__Warning = QLabel('<font color="green">Ok</font>')
            self.__Warning.hide()

            self.__EditName = QLineEdit(self.__nodename)
            self.__EditName.textEdited.connect(self.__onNameEdit)

            self.__attributes = self.__nodeDesc().getAttributesCopy()

            self.__AttrTree = AttrTree(self.__libraries, self.__nodeDesc().attributes())

            self.__attrNameValidating = False

            mainLayout = QGridLayout()
            mainLayout.addWidget(QLabel('.'), 0, 0, Qt.AlignRight)
            mainLayout.addWidget(self.__Warning, 0, 1, Qt.AlignLeft)
            mainLayout.addWidget(QLabel('Node name:'), 1, 0, Qt.AlignRight)
            mainLayout.addWidget(self.__EditName, 1, 1)
            mainLayout.addWidget(self.__AttrTree, 2, 0, 1, 2)

            self.setLayout(mainLayout)

    def __onNameEdit(self, new_name):
        new_name.strip()
        self.__EditName.setText(new_name)
        if self.__libname in self.__libraries:
            if new_name != self.__nodename and new_name in self.__libraries[self.__libname]:
                self.__NodeNameErr = True
                self.__NameWarn = '<font color="red">Node with that name is already exist.</font>'
            elif len(new_name) < 1:
                self.__NodeNameErr = True
                self.__NameWarn = '<font color="red">Too short name.</font>'
            else:
                self.__new_name = new_name
                self.__NodeNameErr = False
        else:
            self.__EditName.setText(self.__nodename)
            self.__NodeNameErr = False
        self.__WarningCheck()

    def __nodeDesc(self):
        if self.__libname in self.__libraries:
            if self.__nodename in self.__libraries[self.__libname]:
                return self.__libraries[self.__libname][self.__nodename]
        return None

    def __WarningCheck(self):
        text = ''

        if self.__NodeNameErr is True:
            if text:
                text += ' | '
            text += self.__NameWarn

        if text:
            self.__Warning.setText(text)
            self.__Warning.show()
        else:
            self.__Warning.hide()

#######################################################################################################################
#######################################################################################################################
