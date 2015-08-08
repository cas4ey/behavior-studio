# coding=utf-8
# -----------------
# file      : alphabet.py
# date      : 2013/02/16
# author    : Victor Zarubkin
# contact   : victor.zarubkin@gmail.com
# copyright : Copyright (C) 2013  Victor Zarubkin
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
__copyright__ = 'Copyright (C) 2013  Victor Zarubkin'
__credits__ = ['Victor Zarubkin']
__license__ = ['GPLv3']
__version__ = '1.3.0'  # this is last application version when this script file was changed
__email__ = 'victor.zarubkin@gmail.com'
############################################################################

import os

from xml.dom.minidom import parse

from PySide.QtCore import Qt
from PySide.QtGui import QColor

from auxtypes import processString
from compat_2to3 import dict_items

import globals

#######################################################################################################################

_versionWithSingleHeader = (1, 0)
_versionWithDifferentHeaders = (1, 2, 4)

#######################################################################################################################
#######################################################################################################################


class _Colorizer:
    __colorTable = {
        'red': Qt.red,
        'darkRed': Qt.darkRed,
        'green': Qt.green,
        'darkGreen': Qt.darkGreen,
        'blue': Qt.blue,
        'darkBlue': Qt.darkBlue,
        'black': Qt.black,
        'darkGray': Qt.darkGray,
        'gray': Qt.gray,
        'lightGray': Qt.lightGray,
        'white': Qt.white,
        'yellow': Qt.yellow,
        'darkYellow': Qt.darkYellow,
        'cyan': Qt.cyan,
        'darkCyan': Qt.darkCyan,
        'magenta': Qt.magenta,
        'darkMagenta': Qt.darkMagenta,
        'orange': QColor(255, 127, 0)
    }

    def __init__(self):
        pass

    @staticmethod
    def fromStr(name, a=255):
        if name in _Colorizer.__colorTable:
            c = QColor(_Colorizer.__colorTable[name])
        else:
            c = QColor(Qt.transparent)
        c.setAlpha(a)
        return c

    @staticmethod
    def fromRgb(r, g, b, a=255):
        return QColor(r, g, b, a)

    @staticmethod
    def fromQcolor(qtColor, a=255):
        c = QColor(qtColor)
        c.setAlpha(a)
        return c

#######################################################################################################################
#######################################################################################################################


class AlphabetChild(object):
    def __init__(self, elem, minCount=0, maxCount=1):
        self.element = elem
        self.min = max(0, minCount)
        self.max = max(0, maxCount)
        if self.min > self.max:
            self.min, self.max = self.max, self.min

    def obligatory(self):
        return self.min > 0

    def multiple(self):
        return self.max > 1

    def used(self):
        return self.max > 0

#######################################################################################################################


class AttributesElement(object):
    def __init__(self, tag, obligatory):
        self.tag = tag
        self.obligatory = obligatory

#######################################################################################################################


class StateElement(object):
    def __init__(self, value, name, colorEnabled, colorDisabled):
        self.value = value
        self.name = name

        if colorEnabled is None:
            if colorDisabled is None:
                ce = _Colorizer.fromQcolor(Qt.blue, 32)
            else:
                ce = QColor(colorDisabled)
        else:
            ce = colorEnabled

        if colorDisabled is None:
            if colorEnabled is None:
                cd = _Colorizer.fromQcolor(Qt.blue, 12)
            else:
                cd = QColor(colorEnabled)
        else:
            cd = colorDisabled

        self.colorEnabled = ce
        self.colorDisabled = cd

#######################################################################################################################


class CodeGeneratorMethod(object):
    def __init__(self, checked, force, ret, iface, name, modifier, args, impl='', initSection=''):
        self.defaultChecked = force or checked
        self.force = force
        self.returnType = ret
        self.name = name
        self.modifier = modifier
        self.interface = iface
        self.args = args
        self.overrideModifier = ''
        self.implementation = impl
        self.initSection = initSection
        self.index = int(-1)

    def fullname(self):
        return '{0}::{1}'.format(self.interface, self.name)

    def declarationHpp(self, args):
        if len(self.modifier) > 0:
            return '{0} {1}({2}) {3}'.format(self.returnType, self.name, args, self.modifier)
        return '{0} {1}({2})'.format(self.returnType, self.name, args)

    def declarationCpp(self, classname, args):
        if len(self.modifier) > 0:
            return '{0} {1}::{2}({3}) {4}'.format(self.returnType, classname, self.name, args, self.modifier)
        return '{0} {1}::{2}({3})'.format(self.returnType, classname, self.name, args)

#######################################################################################################################


class CodeGeneratorVariable(object):
    def __init__(self, typeName, name):
        self.typeName = typeName
        self.name = name

#######################################################################################################################


class CodeGeneratorData(object):
    scopes = ['public', 'protected', 'private']

    def __init__(self):
        self.namespace = ''
        self.includes = []
        self.interfaces = []
        self.baseClasses = {}
        self.appendix = {}
        self.methods = {}
        self.variables = {}

#######################################################################################################################


class ClassElement(object):
    """
    ClassElement is class of tree node.
    In terms of behavior tree: a Task is one class, a Condition is another class.
    (Leaf Task, Decorator Task and Composite Task are TYPES, not classes)
    """

    def __init__(self, alphabet, name, tag, libTag, top=False, attributesTag='', attrsObligatory=False):
        self.alphabet = alphabet
        self.name = name
        self.tag = tag
        self.lib = libTag
        self.top = top
        self.attributes = AttributesElement(attributesTag, attrsObligatory)
        self.linkTag = ''
        self.infoTag = ''
        self.debuggable = False
        self.invertible = False
        self.types = dict()
        self.states = dict()
        self.defaultStateKey = 0
        self.codegenData = None

    # operator 'in':
    def __contains__(self, item):
        """ Standard operator 'in'. Checks if certain type is subtype of this class.
        Parameter 'item' is a name of required type.
        See also function 'got'. """
        return item in self.types

    # operator '[]':
    def __getitem__(self, item):
        """ Standard operator '[]'. Returns a reference to type specified by it's name.
        Parameter 'item' is a name of required type.
        See also function 'get'. """
        return self.types.get(item, None)

    # operator 'len()'
    def __len__(self):
        """ Standard operator 'len'. Returns size of types list. """
        return len(self.types)

    def __iter__(self):
        return self.types.__iter__()

    def add(self, newType):
        """ Adds new type to the list of available types.
        Parameter newType is reference to new element. """
        if newType.name not in self.types:
            newType.classname = self.name
            self.types[newType.name] = newType

    def get(self, typeName):
        """ Returns a reference to specified type.
        Parameter typeName is a name of required type. """
        return self.types.get(typeName, None)

    def getFirstType(self, link=False):
        for t in self.types:
            if not self.types[t].isLink() or link:
                return self.types[t]
        return None

    def getTypeNames(self, link=False):
        if link:
            return list(self.types.keys())
        names = []
        for t in self.types:
            if not self.types[t].isLink():
                names.append(t)
        return names

    def getLinkTypes(self):
        """ Returns a list of subtypes that are links. """
        links = dict()
        for t in self.types:
            if self.types[t].isLink():
                links[t] = self.types[t]
        return links

    def isLinkable(self):
        """ Returns True if you can remember and use link to this class.
        Otherwise returns False. """
        return bool(self.linkTag)

    def defaultState(self):
        return self.states[self.defaultStateKey]

#######################################################################################################################


class TypeElement(object):
    """
    TypeElement is type of tree node of certain class.
    In terms of behavior tree: Leaf Task, Decorator Task, Composite Task are different types
    of Task class nodes.
    (Task is class, Decorator is type)
    """

    def __init__(self, alphabet, classname, name):
        self.singleblockEnabled = False
        self.alphabet = alphabet  # reference to current tree alphabet
        self.classname = classname  # parent class name (a string)
        self.name = name  # type name (a string)
        self.linkTargetTag = ''  # a name of xml tag to read and write link. Link is a text name of a subtree, it is used for references.
        self.__isCopy = False  # indicates that using this reference will create a copy of branch
        self.children = dict()  # a list of available child nodes (this is list of class names)

    # operator 'in':
    def __contains__(self, item):
        """ Standard operator 'in'. Checks if nodes of certain class may be children of this type.
        Parameter 'item' is a name of required class. """
        return item in self.children

    # operator '[]':
    def __getitem__(self, item):
        """ Standard operator '[]'. Returns a reference to class specified by it's name.
        Parameter 'item' is a name of required class. """
        return self.children.get(item, None)

    # operator 'len()'
    def __len__(self):
        """ Standard operator 'len'. Returns size of children list. """
        return len(self.children)

    def isLink(self):
        return bool(self.linkTargetTag)

    def __iter__(self):
        return self.children.__iter__()

    def setCopyLink(self, val):
        if self.isLink():
            self.__isCopy = val

    def isCopyLink(self):
        return self.isLink() and self.__isCopy

    def targetTag(self):
        return self.linkTargetTag

    def cls(self):
        return self.alphabet[self.classname]

    def child(self, classname):
        return self.children.get(classname, None)

    def get(self, item):
        return self.children.get(item, None)

    def addChild(self, classname, minCount, maxCount):
        if classname not in self.children:
            self.children[classname] = AlphabetChild(classname, minCount, maxCount)

#######################################################################################################################
#######################################################################################################################


class Alphabet(object):
    def __init__(self):
        self.path = ''
        self.headerTree = 'BehaviorTree'
        self.headerLibrary = 'LibData'
        self.infos = []
        self.classes = dict()
        self.version = (0, 0)

    # operator 'in':
    def __contains__(self, item):
        return item in self.classes

    # operator '[]':
    def __getitem__(self, item):
        return self.classes.get(item)

    # operator 'len()'
    def __len__(self):
        return len(self.classes)

    def __iter__(self):
        return self.classes.__iter__()

    def getClass(self, classname):
        return self.classes.get(classname, None)

    def getClasses(self, top=None):
        if top is None:
            return dict_items(self.classes.keys())
        classes = []
        for c in self.classes:
            if self.classes[c].top == top:
                classes.append(c)
        return classes

    def numClasses(self, top=None):
        return len(self.getClasses(top))

    def getType(self, classname, name):
        cls = self.getClass(classname)
        if cls is not None:
            return cls.get(name)
        return None

    def numTypes(self, classname):
        return len(self.getTypes(classname))

    def getTypes(self, classname):
        cls = self.getClass(classname)
        if cls is None:
            return dict()
        return cls.types

    def load(self, fromfile):
        global _versionWithSingleHeader, _versionWithDifferentHeaders

        print('info: Loading alphabet file \'{0}\' ...'.format(fromfile))
        if not os.path.exists(fromfile):
            print('error: Alphabet file \'{0}\' does not exist!'.format(fromfile))
            return False

        dom = parse(fromfile)
        d = dom.getElementsByTagName('alphabet')
        if not d:
            print('error: Alphabet file is wrong formatted! There are no tag <alphabet>...</alphabet>')
            return False

        data = d[0]

        if data.hasAttribute('version'):
            versionText = data.getAttribute('version')
        elif data.hasAttribute('Version'):
            versionText = data.getAttribute('Version')
        else:
            versionText = ''

        if not versionText or '.' not in versionText:
            self.version = tuple(_versionWithSingleHeader)
            versionText = globals.versionToStr(self.version)
            print('warning: Alphabet file has no version. Default it to {0}'.format(versionText))
        else:
            self.version = globals.versionFromStr(versionText)
            print('info: Alphabet file version is {0}'.format(versionText))

        if self.version >= _versionWithDifferentHeaders:
            if not data.hasAttribute('headerTree'):
                print('error: No xml attribute <alphabet ... headerTree=\"...\" ...> in alphabet file')
                return False
            header = data.getAttribute('headerTree')
            if not header:
                print('error: Xml attribute <alphabet ... headerTree=\"\" ...> is empty in alphabet file')
                return False
            self.headerTree = header
            if not data.hasAttribute('headerLibrary'):
                print('error: No xml attribute <alphabet ... headerLibrary=\"...\" ...> in alphabet file')
                return False
            header = data.getAttribute('headerLibrary')
            if not header:
                print('error: Xml attribute <alphabet ... headerLibrary=\"\" ...> is empty in alphabet file')
                return False
            self.headerLibrary = header
        else:
            if not data.hasAttribute('header'):
                print('error: No xml attribute <alphabet ... header=\"...\" ...> in alphabet file')
                return False
            header = data.getAttribute('header')
            if not header:
                print('error: Xml attribute <alphabet ... header=\"\" ...> is empty in alphabet file')
                return False
            self.headerTree = header

        res = False
        classes = data.getElementsByTagName('class')
        if not classes:
            print('error: No classes in alphabet file. There must be tags <class>...</class>.')
            return False

        self.classes.clear()
        for cls in classes:
            res = (self.__parseClass(cls) or res)

        if res:
            self.path = fromfile

        return res

    def __parseClass(self, cls):
        if cls.hasAttribute('name'):
            name = cls.getAttribute('name')
        else:
            name = ''

        if not name or name in self.classes:
            return False

        if cls.hasAttribute('tag'):
            tag = cls.getAttribute('tag')
        else:
            tag = ''

        if not tag:
            return False

        if cls.hasAttribute('libraryTag'):
            libTag = cls.getAttribute('libraryTag')
        else:
            libTag = ''

        if not libTag:
            return False

        debuggable = False
        if cls.hasAttribute('allowDebug'):
            debugMode = cls.getAttribute('allowDebug').lower()
            if debugMode in ('yes', '1', 'true'):
                debuggable = True

        invertible = False
        if cls.hasAttribute('allowInvert'):
            invMode = cls.getAttribute('allowInvert').lower()
            if invMode in ('yes', '1', 'true'):
                invertible = True

        topStr = ''
        if cls.hasAttribute('toplevel'):
            topStr = cls.getAttribute('toplevel').lower()
        top = (topStr and topStr in ('yes', '1', 'true'))

        if top and self.numClasses(True) > 0:
            print('WARNING: only ONE top-level class is allowed! Class \"{0}\" will not be loaded.'.format(name))
            return False

        states = cls.getElementsByTagName('state')
        if not states:
            print('WARNING: every class must have at least one state! Class \"{0}\" will not be loaded.'.format(name))
            return False

        atr = cls.getElementsByTagName('attributes')
        attrTag = ''
        attrsIsObligatory = False
        if atr:
            attr = atr[0]
            attrTag = ''
            if attr.hasAttribute('tag'):
                attrTag = attr.getAttribute('tag')
            if attrTag:
                if attr.hasAttribute('obligatory'):
                    ob = attr.getAttribute('obligatory').lower()
                    attrsIsObligatory = (ob and ob in ('yes', '1', 'true'))

        newClass = ClassElement(self, name, tag, libTag, top, attrTag, attrsIsObligatory)
        newClass.debuggable = debuggable
        newClass.invertible = invertible

        if cls.hasAttribute('linkTag'):
            newClass.linkTag = cls.getAttribute('linkTag')

        if cls.hasAttribute('infoTag'):
            newClass.infoTag = cls.getAttribute('infoTag')
            if newClass.infoTag and newClass.infoTag not in self.infos:
                self.infos.append(newClass.infoTag)

        # reading states:
        for s in states:
            if not s.hasAttribute('name') or not s.hasAttribute('value'):
                continue
            n = s.getAttribute('name')
            v = int(s.getAttribute('value'))
            ce = Alphabet.__parseColor(s, 'enabled')
            cd = Alphabet.__parseColor(s, 'disabled')
            if not newClass.states:
                newClass.defaultStateKey = v
            newClass.states[v] = StateElement(v, n, ce, cd)

        if not newClass.states:
            print('WARNING: every class must have at least one state! Class \"{0}\" will not be loaded.'.format(name))
            return False

        # trying to read default state name:
        default_state = cls.getElementsByTagName('default_state')
        if default_state:
            for dfs in default_state:
                if dfs.hasAttribute('name'):
                    default_state_name = dfs.getAttribute('name')
                    if default_state_name in newClass.states:
                        newClass.defaultStateKey = default_state_name
                        break

        st = newClass.defaultState()
        newClass.colorEnabled = st.colorEnabled
        newClass.colorDisabled = st.colorDisabled

        types = cls.getElementsByTagName('type')
        for typeNode in types:
            self.__parseType(newClass, typeNode)

        codeGen = cls.getElementsByTagName('codeGenerator')
        if codeGen:
            Alphabet.__parseCodeGen(newClass, codeGen[0])

        self.classes[name] = newClass

        return True

    def __parseType(self, cls, typeNode):
        if typeNode.hasAttribute('name'):
            name = typeNode.getAttribute('name')
        else:
            name = ''

        if not name or name in cls:
            return False

        target = ''
        if typeNode.hasAttribute('link'):
            l = typeNode.getAttribute('link').lower()
            if l in ('yes', '1', 'true'):
                if typeNode.hasAttribute('targetTag'):
                    target = typeNode.getAttribute('targetTag')
                if not target:
                    return False

        singleblockEnabled = False
        if typeNode.hasAttribute('allowSingleBlock'):
            sb = typeNode.getAttribute('allowSingleBlock').lower()
            if sb in ('yes', '1', 'true'):
                singleblockEnabled = True

        newType = TypeElement(self, cls.name, name)
        newType.singleblockEnabled = singleblockEnabled
        newType.linkTargetTag = target

        if newType.isLink():
            if typeNode.hasAttribute('copyTarget'):
                c = typeNode.getAttribute('copyTarget').lower()
                if c in ('yes', '1', 'true'):
                    newType.setCopyLink(True)
        else:
            children = typeNode.getElementsByTagName('children')
            for child in children:
                Alphabet.__parseChild(newType, child)

        cls.add(newType)

        return True

    @staticmethod
    def __parseChild(typeElem, xmlNode):
        clsname = ''
        if xmlNode.hasAttribute('class'):
            clsname = xmlNode.getAttribute('class')
        if not clsname:
            return False
        minimum = 0
        maximum = 1
        if xmlNode.hasAttribute('min'):
            m = xmlNode.getAttribute('min')
            if m:
                minimum = int(m)
        if xmlNode.hasAttribute('max'):
            m = xmlNode.getAttribute('max')
            if m:
                maximum = int(m)
        typeElem.addChild(clsname, minimum, maximum)
        return True

    @staticmethod
    def __parseCodeGen(cls, codeGen):
        if not codeGen.hasAttribute('interface'):
            return

        codegenData = CodeGeneratorData()

        if codeGen.hasAttribute('namespace'):
            codegenData.namespace = codeGen.getAttribute('namespace')

        codegenData.interfaces = codeGen.getAttribute('interface').split()
        if not codegenData.interfaces:
            return

        baseclasses = codeGen.getAttribute('baseclass').split()
        for bc in baseclasses:
            s = bc.split('::')
            if len(s) < 2 or s[0] not in codegenData.interfaces:
                continue
            codegenData.baseClasses[s[0]] = s[1]

        appendix = codeGen.getAttribute('appendix').split()
        for ap in appendix:
            s = ap.split('::')
            if len(s) < 2 or s[0] not in codegenData.interfaces:
                continue
            codegenData.appendix[s[0]] = s[1]

        for i in codegenData.interfaces:
            if i not in codegenData.appendix:
                return

        for i in codegenData.interfaces:
            codegenData.methods[i] = dict()
            for scope in codegenData.scopes:
                codegenData.methods[i][scope] = []

        for i in codeGen.getElementsByTagName('include'):
            if i.hasAttribute('file'):
                codegenData.includes.append(i.getAttribute('file'))

        num_methods = int(0)
        for m in codeGen.getElementsByTagName('method'):
            if not m.hasAttribute('interface') or not m.hasAttribute('name'):
                continue

            iface = m.getAttribute('interface')
            if iface not in codegenData.interfaces:
                continue

            mname = m.getAttribute('name')
            if not mname:
                continue

            if m.hasAttribute('scope'):
                scope = m.getAttribute('scope')
                if scope not in codegenData.scopes:
                    scope = 'public'
            else:
                scope = 'public'

            ret = m.getAttribute('return')
            if ret is None or not ret:
                ret = 'void'

            if m.hasAttribute('modifier'):
                modifier = m.getAttribute('modifier')
            else:
                modifier = ''

            if m.hasAttribute('override_modifier'):
                override_modifier = m.getAttribute('override_modifier')
            else:
                override_modifier = ''

            if m.hasAttribute('args'):
                args = m.getAttribute('args')
                if args:
                    args = args.replace('@ref', '&')
                    args = args.replace('@[', '<')
                    args = args.replace('@]', '>')
                    args = args.replace('^', '->')
                    args = args.replace('|', '\n')
            else:
                args = ''

            if m.hasAttribute('impl'):
                impl = m.getAttribute('impl')
                if impl:
                    impl = processString(impl)
                    impl = impl.replace('@ref', '&')
                    impl = impl.replace('@[', '<')
                    impl = impl.replace('@]', '>')
                    impl = impl.replace('^', '->')
                    impl = impl.replace('|', '\n')
            else:
                impl = ''

            if mname == '@ctor' and m.hasAttribute('init'):
                initSection = m.getAttribute('init')
                if initSection:
                    initSection = processString(initSection)
                    initSection = initSection.replace('@ref', '&')
                    initSection = initSection.replace('@[', '<')
                    initSection = initSection.replace('@]', '>')
                    initSection = initSection.replace('^', '->')
                    initSection = initSection.replace('|', '\n')
            else:
                initSection = ''

            if m.hasAttribute('force'):
                f = m.getAttribute('force').lower()
                if f not in ('no', '0', 'false'):
                    force = True
                else:
                    force = False
            else:
                force = False

            if m.hasAttribute('checked'):
                chk = m.getAttribute('checked').lower()
                if chk in ('yes', '1', 'true'):
                    checked = True
                else:
                    checked = False
            else:
                checked = True

            method = CodeGeneratorMethod(checked, force, ret, iface, mname, modifier, args, impl, initSection)
            method.overrideModifier = override_modifier
            method.index = int(len(codegenData.methods[iface][scope]))
            codegenData.methods[iface][scope].append(method)

            num_methods += int(1)

        for var in codeGen.getElementsByTagName('variable'):
            if not var.hasAttribute('interface') or not var.hasAttribute('type') or not var.hasAttribute('name'):
                continue

            iface = var.getAttribute('interface')
            if iface not in codegenData.interfaces:
                continue

            vartype = var.getAttribute('type')
            if not vartype:
                continue

            varname = var.getAttribute('name')
            if not varname:
                continue

            vartype = vartype.replace('@ref', '&')
            vartype = vartype.replace('@[', '<')
            vartype = vartype.replace('@]', '>')
            vartype = vartype.replace('^', '->')
            vartype = vartype.replace('|', '\n')

            variable = CodeGeneratorVariable(vartype, varname)
            if iface not in codegenData.variables:
                codegenData.variables[iface] = [variable]
            else:
                codegenData.variables[iface].append(variable)

        if num_methods > 0:
            cls.codegenData = codegenData

    @staticmethod
    def __parseColor(xmlNode, tagName):
        if xmlNode.hasAttribute(tagName):
            col = xmlNode.getAttribute(tagName)
            cols = col.split()
            num = len(cols)
            if num < 1:
                return None
            r, g, b, a = 0, 0, 0, 255
            r = int(cols[0])
            if num > 1:
                g = int(cols[1])
            if num > 2:
                b = int(cols[2])
            if num > 3:
                a = int(cols[3])
            return _Colorizer.fromRgb(r, g, b, a)
        return None

#######################################################################################################################
#######################################################################################################################
