# coding=utf-8
# -----------------
# file      : tree_node_pattern_gen.py
# date      : 2014/08/16
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

""" Script describing pattern code generator - TreeNodePatternGenerator class.

This class can generate C++ source files ('cpp' and 'h') with template
"""

from __future__ import unicode_literals

__author__ = 'Victor Zarubkin'
__copyright__ = 'Copyright (C) 2014  Victor Zarubkin'
__credits__ = ['Victor Zarubkin']
__license__ = ['GPLv3']
__version__ = '1.3.0'  # this is last application version when this script file was changed
__email__ = 'victor.zarubkin@gmail.com'
############################################################################

import os
import re
from datetime import datetime
from language import trStr

from PySide.QtCore import *
from PySide.QtGui import *

#######################################################################################################################

now = datetime.now()

tab = '    '


def currentDate():
    if now.month < 10:
        m = '0{0}'.format(now.month)
    else:
        m = '{0}'.format(now.month)
    if now.day < 10:
        d = '0{0}'.format(now.day)
    else:
        d = '{0}'.format(now.day)
    return '{0}/{1}/{2}'.format(now.year, m, d)

#######################################################################################################################
#######################################################################################################################


class TreeNodePatternGenerator(object):
    __hdrBegin = '/************************************************************************\n'
    __hdrFilename = '* file name         : '
    __hdrSeparator = '* ----------------- : \n'
    __hdrDatetime = '* creation time     : {0}\n'.format(currentDate())
    __hdrCopyright = '* copyright         : (c) {0} LLC Constanta-Design\n'.format(now.year)
    __hdrAuthor = '* author            : '
    __hdrDescription = '* description       : '
    __hdrBlankline = '*                   : '
    __hdrChangelog = '* change log        : * '
    __hdrEnd = '************************************************************************/\n\n'

    __codeGlobalSeparator = '\n{0}\n{0}\n\n'.format('////////////////////////////////////////////////////////////'
                                                     '////////////////////////////////////////////////////////////'
                                                     '/////////////////////////////')
    __codeLocalSeparator = '\n////////////////////////////////////////////////////////////////////////////////////' \
                           '/////////////////////////////////////////////\n\n'

    def __init__(self):
        pass

    def generate(self, methods, author, nodeDescriptor, codegenData, headerfile=True, cppfile=True):
        if nodeDescriptor.name.isupper() or nodeDescriptor.name.islower():
            if '_' not in nodeDescriptor.name:
                nameparts = [nodeDescriptor.name]
            else:
                nameparts = nodeDescriptor.name.split('_')
        else:
            nameparts = [a for a in re.split(r'([A-Z][a-z]*)', nodeDescriptor.name.replace('_', '')) if a]

        filename = ''
        i = 0
        for n in nameparts:
            filename += n.lower()
            if i < len(nameparts) - 1:
                filename += '_'
            i += 1

        taskname = ''.join([a for a in nameparts if len(a) > 1])

        classnames = dict()
        for i in codegenData.interfaces:
            classnames[i] = taskname + codegenData.appendix[i]

        if headerfile:
            self.__generateHdr(methods, cppfile, author, nodeDescriptor, codegenData, classnames, nameparts, filename)

        if cppfile:
            self.__generateCpp(methods, author, nodeDescriptor, codegenData, classnames, filename)

    def __generateHdr(self, methods, onlyDeclarations, author, nodeDescriptor, codegenData, classnames, nameparts,
                      filename):
        fname = filename + '.h'

        descriptionStrings = nodeDescriptor.description.split('\n')

        header = self.__hdrBegin + self.__hdrFilename + fname + '\n' + self.__hdrSeparator + \
            self.__hdrDatetime + self.__hdrCopyright + self.__hdrAuthor + author + '\n' + \
            self.__hdrSeparator + self.__hdrDescription

        i = 0
        for d in descriptionStrings:
            header += d + '\n'
            if i < len(descriptionStrings) - 1:
                header += self.__hdrBlankline
            i += 1

        header += self.__hdrSeparator + self.__hdrChangelog + '\n' + self.__hdrEnd

        if not os.path.exists('./generated_files/'):
            os.makedirs('./generated_files/')
        f = open('./generated_files/{0}'.format(fname), 'w')

        # header
        f.write(header.encode('utf8'))

        # ifndef/define macro
        defineMacro = '__'
        for n in nameparts:
            defineMacro += n.upper() + '_'
        defineMacro += '__H__'

        # ifndef/define zone
        f.write('#ifndef {0}\n#define {0}\n\n'.format(defineMacro))

        # includes
        for incl in codegenData.includes:
            f.write('#include \"{0}\"\n'.format(incl))

        f.write(self.__codeGlobalSeparator)

        # namespace
        if codegenData.namespace:
            f.write('namespace {0}\n'.format(codegenData.namespace) + '{\n' + self.__codeLocalSeparator)

        # forward declarations
        for i in classnames:
            f.write('class {0};\n'.format(classnames[i]))

        # class declarations------------------------------------
        for i in codegenData.interfaces:
            classname = classnames[i]

            f.write(self.__codeLocalSeparator)

            # class declaration
            if i in codegenData.baseClasses:
                f.write('class {0} : public {1}\n'.format(classname, codegenData.baseClasses[i]) + '{\n')
            else:
                f.write('class {0} : public {1}\n'.format(classname, i) + '{\n')

            if i in codegenData.variables and codegenData.variables[i]:
                for var in codegenData.variables[i]:
                    f.write(tab + '{0} {1};\n'.format(var.typeName, var.name))
                f.write('\n')

            f.write('public:\n\n')

            # ISOUnknown stuff
            f.write('{0}DECLARE_QUERYMAP2({1}, {2}, ISOUnknown);\n\n'.format(tab, classname, i))

            # constructor
            for scope in codegenData.scopes:
                for m in codegenData.methods[i][scope]:
                    if m.name == '@ctor':
                        # args
                        args = m.args
                        if args:
                            for j in codegenData.interfaces:
                                args = args.replace('@class-{0}'.format(j), classnames[j])
                        # declaration
                        f.write(tab + '{0}({1})'.format(classname, args))
                        # implementation
                        if onlyDeclarations:
                            f.write(';\n')
                        else:
                            if m.initSection:
                                initStrings = m.initSection.split('\n')
                                symbolPrefix = ': '
                                for s in initStrings:
                                    s = s.strip()
                                    if len(s) > 0:
                                        f.write('\n' + tab + tab + symbolPrefix + s)
                                        symbolPrefix = ', '
                            elif i in codegenData.baseClasses:
                                f.write(' : {0}()'.format(codegenData.baseClasses[i]))
                            f.write('\n' + tab + '{\n')
                            if m.implementation:
                                implStrings = m.implementation.split('\n')
                                for s in implStrings:
                                    s = s.strip()
                                    if s:
                                        f.write(tab + tab + s + '\n')
                            f.write(tab + '}\n')
                        f.write('\n')
                        break

            # destructor
            f.write(tab + 'virtual ~{0}()'.format(classname))
            if onlyDeclarations:
                f.write(';\n')
            else:
                f.write('\n' + tab + '{\n' + tab + '}\n')

            current_scope = 'public'

            # methods:
            for scope in codegenData.scopes:
                if not codegenData.methods[i][scope]:
                    continue

                if scope != current_scope:
                    f.write('\n{0}:\n'.format(scope))
                    current_scope = scope

                for m in codegenData.methods[i][scope]:
                    if m.index not in methods[i][scope] or not methods[i][scope][m.index]:
                        continue  # do not generate this method
                    if m.name == '@ctor':
                        continue  # constructor has been already generated
                    # args
                    args = m.args
                    if args:
                        for j in codegenData.interfaces:
                            args = args.replace('@class-{0}'.format(j), classnames[j])
                    # declaration
                    f.write('\n' + tab + m.declarationHpp(args))
                    # implementation
                    if onlyDeclarations:
                        f.write(';\n')
                    else:
                        f.write('\n' + tab + '{\n')
                        impl = m.implementation
                        if impl:
                            for j in codegenData.interfaces:
                                impl = impl.replace('@class-{0}'.format(j), classnames[j])
                            lines = impl.split('\n')
                            for line in lines:
                                line = line.replace('\\t', tab)
                                f.write(tab + tab + line + '\n')
                        f.write(tab + '}\n')

            # end of class
            f.write('\n}; // END class ' + classname + '.\n')

        # end namespace
        if codegenData.namespace:
            f.write(self.__codeLocalSeparator)
            f.write('} ' + '// END namespace {0}.\n'.format(codegenData.namespace))

        # file ending
        f.write(self.__codeGlobalSeparator)
        f.write('#endif // {0}\n'.format(defineMacro))

        f.close()

        print('OK: Successfully created file  {0}'.format(os.path.abspath('./generated_files/{0}'.format(fname))))

    def __generateCpp(self, methods, author, nodeDescriptor, codegenData, classnames, filename):
        fname = filename + '.cpp'

        header = self.__hdrBegin + self.__hdrFilename + fname + '\n' + self.__hdrSeparator + \
            self.__hdrDatetime + self.__hdrCopyright + self.__hdrAuthor + author + '\n' + \
            self.__hdrSeparator + self.__hdrDescription

        header += 'Файл содержит реализацию методов классов '
        cnt = int(0)
        for i in classnames:
            if cnt > 0:
                header += ', '
            header += classnames[i]
            cnt += int(1)
        header += '.\n'

        header += self.__hdrSeparator + self.__hdrChangelog + '\n' + self.__hdrEnd

        if not os.path.exists('./generated_files/'):
            os.makedirs('./generated_files/')
        f = open('./generated_files/{0}'.format(fname), 'w')

        # header
        f.write(header.encode('utf8'))

        # includes
        f.write('#include \"{0}.h\"\n'.format(filename))

        f.write(self.__codeGlobalSeparator)

        # namespace
        if len(codegenData.namespace) > 0:
            f.write('namespace {0}\n'.format(codegenData.namespace) + '{\n' + self.__codeLocalSeparator)

        # class implementation------------------------------------
        cnt = int(0)
        for i in codegenData.interfaces:
            classname = classnames[i]

            if cnt > 0:
                f.write(self.__codeLocalSeparator)

            # constructor
            for scope in codegenData.scopes:
                for m in codegenData.methods[i][scope]:
                    if m.name == '@ctor':
                        # args
                        args = m.args
                        if args:
                            for j in codegenData.interfaces:
                                args = args.replace('@class-{0}'.format(j), classnames[j])
                        # declaration
                        f.write('{0}::{0}({1})'.format(classname, args))
                        # implementation
                        if m.initSection:
                            initStrings = m.initSection.split('\n')
                            symbolPrefix = ': '
                            for s in initStrings:
                                s = s.strip()
                                if s:
                                    f.write('\n' + tab + symbolPrefix + s)
                                    symbolPrefix = ', '
                        elif i in codegenData.baseClasses:
                            f.write('\n' + tab + ': {0}()'.format(codegenData.baseClasses[i]))
                        f.write('\n{\n')
                        if m.implementation:
                            implStrings = m.implementation.split('\n')
                            for s in implStrings:
                                s = s.strip()
                                if s:
                                    f.write(tab + s + '\n')
                        f.write('}\n\n')
                        break

            # destructor
            f.write('{0}::~{0}()\n'.format(classname) + '{\n}\n')

            # methods:
            for scope in codegenData.scopes:
                for m in codegenData.methods[i][scope]:
                    if m.index not in methods[i][scope] or not methods[i][scope][m.index]:
                        continue  # do not generate this method
                    if m.name == '@ctor':
                        continue  # constructor has been already generated
                    f.write(self.__codeLocalSeparator)
                    # args
                    args = m.args
                    if args:
                        for j in codegenData.interfaces:
                            args = args.replace('@class-{0}'.format(j), classnames[j])
                    # declaration
                    f.write(m.declarationCpp(classname, args))
                    # implementation
                    f.write('\n{\n')
                    impl = m.implementation
                    if impl:
                        for j in codegenData.interfaces:
                            impl = impl.replace('@class-{0}'.format(j), classnames[j])
                        lines = impl.split('\n')
                        for line in lines:
                            line = line.replace('\\t', tab)
                            f.write(tab + line + '\n')
                    f.write('}\n')

            cnt += int(1)

        # end namespace
        if codegenData.namespace:
            f.write(self.__codeLocalSeparator)
            f.write('} ' + '// END namespace {0}.\n'.format(codegenData.namespace))

        # file ending
        f.write(self.__codeGlobalSeparator)

        f.close()

        print('OK: Successfully created file  {0}'.format(os.path.abspath('./generated_files/{0}'.format(fname))))

generator = TreeNodePatternGenerator()

#######################################################################################################################
#######################################################################################################################


class GlobalPatternInfo(object):
    def __init__(self):
        self.methodsChecks = {}
        self.patternAuthor = 'Enter author name'
        self.patternHpp = True
        self.patternCpp = True


patternInfo = GlobalPatternInfo()


class PatternCheckbox(QCheckBox):
    def __init__(self, state, title, userdata=None, parent=None):
        QCheckBox.__init__(self, title, parent)
        self.userdata = userdata
        self.setChecked(state)


class PatternGeneratorDialog(QDialog):
    def __init__(self, node, codegenData, parent=None):
        global patternInfo
        QDialog.__init__(self, parent)
        self.setObjectName('patternGeneratorDialog')
        self.node = node
        self.codegenData = codegenData

        for intf in codegenData.interfaces:
            if intf not in patternInfo.methodsChecks:
                patternInfo.methodsChecks[intf] = dict()
            for scope in codegenData.scopes:
                if scope not in patternInfo.methodsChecks[intf]:
                    patternInfo.methodsChecks[intf][scope] = dict()
                for m in codegenData.methods[intf][scope]:
                    if m.index not in patternInfo.methodsChecks[intf][scope]:
                        patternInfo.methodsChecks[intf][scope][m.index] = m.defaultChecked
                    elif m.force:
                        patternInfo.methodsChecks[intf][scope][m.index] = True

        self.setWindowTitle(trStr('Code generation', 'Генерация кода').text())

        authorLabel = QLabel(trStr('Author:', 'Автор:').text())
        authorLabel.setAlignment(Qt.AlignRight)

        self.__acceptButton = QPushButton(trStr('OK', 'Готово').text())
        self.__rejectButton = QPushButton(trStr('Cancel', 'Отмена').text())
        self.__hppChk = PatternCheckbox(patternInfo.patternHpp, trStr('.h file', '.h файл').text())
        self.__cppChk = PatternCheckbox(patternInfo.patternCpp, trStr('.cpp file', '.cpp файл').text())
        self.__authorEdit = QLineEdit(patternInfo.patternAuthor)

        self.__checkboxes = dict()
        for intf in codegenData.interfaces:
            self.__checkboxes[intf] = dict()
            for scope in codegenData.scopes:
                self.__checkboxes[intf][scope] = []
                for m in codegenData.methods[intf][scope]:
                    checkbox = PatternCheckbox(patternInfo.methodsChecks[intf][scope][m.index], m.fullname(), m.index)
                    if m.force:
                        checkbox.setEnabled(False)
                    self.__checkboxes[intf][scope].append(checkbox)

        buttonBox = QDialogButtonBox(Qt.Horizontal)
        buttonBox.addButton(self.__acceptButton, QDialogButtonBox.AcceptRole)
        buttonBox.addButton(self.__rejectButton, QDialogButtonBox.RejectRole)
        buttonBox.rejected.connect(self.reject)
        buttonBox.accepted.connect(self.onAccept)

        mainLayout = QGridLayout()
        mainLayout.addWidget(authorLabel, 0, 0)
        mainLayout.addWidget(self.__authorEdit, 0, 1)
        mainLayout.addWidget(self.__hppChk, 1, 0, 1, 2, Qt.AlignLeft)
        mainLayout.addWidget(self.__cppChk, 2, 0, 1, 2, Qt.AlignLeft)

        i = int(3)
        for intf in codegenData.interfaces:
            for scope in codegenData.scopes:
                for cb in self.__checkboxes[intf][scope]:
                    mainLayout.addWidget(cb, i, 0, 1, 2, Qt.AlignLeft)
                    i += int(1)

        mainLayout.addWidget(buttonBox, i, 0, 1, 2, Qt.AlignRight)
        mainLayout.setContentsMargins(5, 5, 5, 5)

        hb1 = QHBoxLayout()
        hb1.addLayout(mainLayout)
        hb1.addStretch(10)

        vb1 = QVBoxLayout()
        vb1.addLayout(hb1)
        vb1.addStretch(10)

        self.setLayout(vb1)
        self.readSettings()

        self.__hppChk.setChecked(patternInfo.patternHpp)
        self.__cppChk.setChecked(patternInfo.patternCpp)
        self.__authorEdit.setText(patternInfo.patternAuthor)

    def closeEvent(self, *args, **kwargs):
        global patternInfo
        patternInfo.patternHpp = self.__hppChk.isChecked()
        patternInfo.patternCpp = self.__cppChk.isChecked()
        patternInfo.patternAuthor = str(self.__authorEdit.text())
        self.saveSettings()
        QDialog.closeEvent(self, *args, **kwargs)

    def saveSettings(self):
        global patternInfo
        settings = QSettings('Victor Zarubkin', 'Behavior Studio')
        settings.beginGroup('patternGenerator')
        settings.setValue('geometry', self.saveGeometry())
        settings.setValue('author', patternInfo.patternAuthor)
        settings.setValue('hpp', patternInfo.patternHpp)
        settings.setValue('cpp', patternInfo.patternCpp)
        settings.endGroup()

    def readSettings(self):
        global patternInfo
        settings = QSettings('Victor Zarubkin', 'Behavior Studio')
        settings.beginGroup('patternGenerator')
        geometry = settings.value('geometry')
        if geometry is not None:
            self.restoreGeometry(geometry)

        def toBool(qSettings, attr_name, default):
            value = qSettings.value(attr_name)
            if value is None:
                return default
            value = value.lower()
            if value not in ('true', 'false'):
                print('error: \'{0}\' value is \'{1}\', but must be \'true\' or \'false\''.format(value))
                return default
            return value == 'true'

        patternInfo.patternHpp = toBool(settings, 'hpp', patternInfo.patternHpp)
        patternInfo.patternCpp = toBool(settings, 'cpp', patternInfo.patternCpp)

        authorName = settings.value('author')
        if authorName is not None:
            patternInfo.patternAuthor = authorName

        settings.endGroup()

    def onAccept(self):
        global patternInfo
        if not self.__hppChk.isChecked() and not self.__cppChk.isChecked():
            print('WARNING: Please select at least \'.h file\' or \'.cpp file\' to generate code!')
            self.reject()
            return

        patternInfo.patternHpp = self.__hppChk.isChecked()
        patternInfo.patternCpp = self.__cppChk.isChecked()
        patternInfo.patternAuthor = str(self.__authorEdit.text())

        for intf in self.codegenData.interfaces:
            for scope in self.codegenData.scopes:
                for cb in self.__checkboxes[intf][scope]:
                    patternInfo.methodsChecks[intf][scope][cb.userdata] = cb.isChecked()

        generator.generate(patternInfo.methodsChecks,
                           patternInfo.patternAuthor,
                           self.node,
                           self.codegenData,
                           bool(patternInfo.patternHpp),
                           bool(patternInfo.patternCpp)
                           )

        self.accept()

#######################################################################################################################
#######################################################################################################################
