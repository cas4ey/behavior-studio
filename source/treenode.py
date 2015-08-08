# coding=utf-8
# -----------------
# file      : treenode.py
# date      : 2012/09/22
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

""" Script file containing data structures used by the application.

The list of classes:
TreeNodeDesc, NodeLibrary, NodeAttrDesc, NodeAttr, TreeNode, BehaviorTree, TreeNodes,
and some other small auxiliary data structures.

TreeNodeDesc is a descriptor of behavior tree node. It contains information such as
name, node-class, node-type, library name, description, list of attributes descriptors (NodeAttrDesc objects).

NodeLibrary is a collection of 'TreeNodeDesc' objects (like in Visio - general nodes, diagram nodes and so on).

NodeAttrDesc is a descriptor of the attribute. It contains name, type, conversion methods (from it's type into string
and back).

NodeAttr is the attribute instance, it holds the name of attribute (to make it possible to search for it's
descriptor inside TreeNodeDesc's list of attributes) and it's value.

TreeNode is the tree node instance, it holds the name, library name, node-class name, node-type name, unique identifier,
tree name it belongs to, xml file path (in which this tree must be saved), list of attributes (NodeAttr objects),
children nodes and some other information.

BehaviorTree is a lookup table (in fact it is a pair of dicts) that stores TreeNode's unique identifiers available by
string name (it's a name of a tree, not the name of concrete TreeNode or it's descriptor).

TreeNodes is a storage of all created 'TreeNode' objects, each of which can be found by it's unique identifier.
"""

from __future__ import unicode_literals

__author__ = 'Victor Zarubkin'
__copyright__ = 'Copyright (C) 2012  Victor Zarubkin'
__credits__ = ['Victor Zarubkin']
__license__ = ['GPLv3']
__version__ = '1.3.0'  # this is last application version when this script file was changed
__email__ = 'victor.zarubkin@gmail.com'
############################################################################

import copy

from PySide.QtCore import QPointF, Signal as QtSignal, Slot as QtSlot, QObject
from treeview.dispregime import DisplayRegime

from uuid import uuid1
from zlib import crc32
from random import randrange

from compat_2to3 import *
import globals

#######################################################################################################################
#######################################################################################################################

_signed_int4_max = 2**31
_unsigned_int4_max = 2**32 - 1


def _randomInt():
    return randrange(_unsigned_int4_max)


def _crc32_py3(val):
    return crc32(bytes(val, 'utf-8'))


def _crc32_py2(val):
    return crc32(val) + _signed_int4_max


if isPython2:
    _crc32 = _crc32_py2
elif isPython3:
    _crc32 = _crc32_py3
else:
    _crc32 = None
    print('warning: Incompatible python version! Must be Python 2.x or Python 3.x!')
    print('')


def _createUid():
    return _crc32(str(uuid1(clock_seq=_randomInt())))

#######################################################################################################################


class NodeLibrary(object):
    # Constructor
    def __init__(self, name):
        self.libname = name
        self.libpath = ''
        self.list = {}

    # operator 'in':
    def __contains__(self, item):
        return item in self.list

    # operator '[]':
    def __getitem__(self, item):
        return self.list.get(item)

    # operator 'len()'
    def __len__(self):
        return len(self.list)

    # Returns True if nodes list is empty
    def empty(self):
        return not self.list

    # Set library path
    def setPath(self, path):
        self.libpath = path

    # Returns library path
    def path(self):
        return self.libpath

    # Returns library name
    def name(self):
        return self.libname

    def insert(self, node, name=''):
        the_name = name
        if not the_name:
            the_name = node.name
        if the_name not in self.list:
            node.name = the_name
            self.list[the_name] = node

    def remove(self, nodename):
        if nodename in self.list:
            del self.list[nodename]

    def getAll(self, nodeClass, nodeType=''):
        nodes = dict()
        for n in self.list:
            node = self.list[n]
            if n not in nodes and node.nodeClass == nodeClass:
                if not nodeType or node.nodeType == nodeType:
                    nodes[n] = node
        return nodes

    def countOf(self, nodeClass, nodeType=''):
        return len(self.getAll(nodeClass, nodeType))

    def deepcopy(self):
        lib = NodeLibrary(copy.deepcopy(self.libname))
        lib.setPath(copy.deepcopy(self.libpath))
        for n in self.list:
            lib.list[n] = self.list[n].deepcopy()
        return lib

#######################################################################################################################
#######################################################################################################################


class TreeNodeDesc(object):
    # Constructor
    def __init__(self, name, classname, typename, libname, debugByDefault=False):
        self.creator = ''  # имя класса, по которому будет создан новый инстанс узла при загрузке дерева на стороне C
        self.name = name
        self.libname = libname
        self.nodeClass = classname  # self.__avail_class[0]
        self.nodeType = typename  # self.__avail_types[0]
        self.childClasses = []
        self.description = ''
        self.icon = None
        self.shape = None
        self.debugByDefault = debugByDefault
        self.incomingEvents = []
        self.outgoingEvents = []
        self.__attributes = {}

    def setLibrary(self, libname):
        """
        Задать имя библиотеки, в которой хранится данный узел.

        На стороне C - это имя библиотеки, в которой описана реализация данного узла.
        """
        self.libname = libname

    def setName(self, name):
        """
        Задать имя узла.

        На стороне C - это строковый идентификатор, по которому можно создать новый инстанс
        класса-реализации данного узла.

        См. также setCreator
        """
        self.name = name

    def setCreator(self, creatorName):
        """
        Задать имя класса, по которому будет создан новый инстанс узла при загрузке дерева на стороне C.

        Если не задано, то инстанс создается по имени узла self.name.
        """
        self.creator = creatorName

    def __contains__(self, item):
        """
        operator 'in'
        """
        return item in self.__attributes

    def __getitem__(self, item):
        """
        operator '[]'
        """
        return self.__attributes.get(item)

    def addAttribute(self, attr):
        if attr.fullname not in self.__attributes:
            self.__attributes[attr.fullname] = attr
            return True
        return False

    def deleteAttribute(self, attrName):
        if attrName in self.__attributes:
            del self.__attributes[attrName]
            return True
        return False

    def attributes(self):
        return self.__attributes

    def getAttributesCopy(self):
        attrs = {}
        for a in self.__attributes:
            attrs[a] = self.__attributes[a].deepcopy()
        return attrs

    def setAttributes(self, attrs):
        self.__attributes = attrs

    def renameAttribute(self, oldname, newname, full):
        if oldname not in self.__attributes:
            return False, ''
        attr = self.__attributes[oldname]
        if full:
            if newname in self.__attributes:
                return False, ''
        else:
            fullname = attr.getFullName(newname)
            if fullname in self.__attributes:
                return False, ''
        if attr.rename(newname, full):
            del self.__attributes[oldname]
            self.__attributes[attr.fullname] = attr
            return True, attr.fullname
        return False, ''

    def replaceAttribute(self, attributeName, newAttribute):
        if attributeName not in self.__attributes:
            return False
        self.__attributes[attributeName] = newAttribute
        return True

    def deepcopy(self):
        nodeCopy = TreeNodeDesc(copy.deepcopy(self.name), copy.deepcopy(self.nodeClass), copy.deepcopy(self.nodeType),
                                copy.deepcopy(self.libname), bool(self.debugByDefault))
        nodeCopy.setCreator(copy.deepcopy(self.creator))
        nodeCopy.childClasses = copy.deepcopy(self.childClasses)
        nodeCopy.description = copy.deepcopy(self.description)
        nodeCopy.icon = self.icon
        nodeCopy.shape = self.shape
        nodeCopy.incomingEvents = copy.deepcopy(self.incomingEvents)
        nodeCopy.outgoingEvents = copy.deepcopy(self.outgoingEvents)
        nodeCopy.setAttributes(self.getAttributesCopy())
        return nodeCopy

#######################################################################################################################
#######################################################################################################################


def str2bool(s):
    if not s:
        return False
    sl = s.lower()
    if sl in ('false', '0', 'no'):
        return False
    if sl in ('true', 'yes'):
        return True
    l = len(sl)
    if l > 1 and sl[0:1] == '0x':
        try:
            if long(sl, 16) == 0:
                return False
            return True
        except ValueError:
            print(u'error: can\'t convert \'{0}\' to long, return 0'.format(s))
            return False
    if '.' in s or 'e' in sl:
        try:
            if long(float(sl)) == 0:
                return False
            return True
        except ValueError:
            print(u'error: can\'t convert \'{0}\' to float, return 0'.format(s))
            return False
    return True


def bool2str(val):
    if val:
        return u'1'
    return u'0'


def bool2str2(val):
    if val:
        return u'True'
    return u'False'

#######################################################################################################################


def int2hex(val):
    if val < 0:
        return u'-0x%x' % abs(val)
    return u'0x%x' % val


def uint2hex(val):
    return u'0x%x' % val


def int2hex8(val):
    if val < 0:
        return u'-0x%08x' % abs(val)
    return u'0x%08x' % val


def uint2hex8(val):
    return u'0x%08x' % val


def int2hex16(val):
    if val < 0:
        return u'-0x%016x' % abs(val)
    return u'0x%016x' % val


def uint2hex16(val):
    return u'0x%016x' % val

#######################################################################################################################


def str2int(val):
    if not val:
        return 0
    if 'x' in val:
        try:
            return int(val, 16)
        except ValueError:
            print(u'error: can\'t convert \'{0}\' to int, return 0'.format(val))
            return 0
    if '.' in val or 'e' in val:
        try:
            return int(float(val))
        except ValueError:
            print(u'error: can\'t convert \'{0}\' to float, return 0'.format(val))
            return 0
    try:
        return int(val)
    except ValueError:
        print(u'error: can\'t convert \'{0}\' to int, return 0'.format(val))
        return 0

#######################################################################################################################


def str2long(val):
    if not val:
        return long(0)
    if 'x' in val:
        try:
            return long(val, 16)
        except ValueError:
            print(u'error: can\'t convert \'{0}\' to long, return 0'.format(val))
            return long(0)
    if '.' in val or 'e' in val:
        try:
            return long(float(val))
        except ValueError:
            print(u'error: can\'t convert \'{0}\' to float, return 0'.format(val))
            return long(0)
    try:
        return long(val)
    except ValueError:
        print(u'error: can\'t convert \'{0}\' to long, return 0'.format(val))
        return long(0)

#######################################################################################################################


def str2float(val):
    if not val:
        return 0.0
    if 'x' in val:
        try:
            return float(long(val, 16))
        except ValueError:
            print(u'error: can\'t convert \'{0}\' to long, return 0'.format(val))
            return 0.0
    try:
        return float(val)
    except ValueError:
        print(u'error: can\'t convert \'{0}\' to float, return 0.0'.format(val))
        return 0.0

#######################################################################################################################


def one2one(val):
    return val


#######################################################################################################################
#######################################################################################################################


class AttrTypeData:
    BOOL = 'bool'
    INT = 'int'
    EXT = 'ext'
    CINT64 = 'int64'
    LONG = 'long'
    REAL = 'real'
    STR = 'str'

#######################################################################################################################


class _TypeInfoEntry(object):
    def __init__(self, classType, name, conv, rev1, rev2, default, enums, hints, minValue, maxValue):
        self.classType = classType
        self.name = name
        self.converter = conv
        self.revConverter1 = rev1
        self.revConverter2 = rev2
        self.default = default
        self.enums = enums
        self.hints = hints
        self.minValue = minValue
        self.maxValue = maxValue

#######################################################################################################################


def _hint(text):
    return text, '', text, True

#######################################################################################################################

DEFAULT_TYPE = 'string'
DEFAULT_CLASS_TYPE = AttrTypeData.STR

TYPE_INFO = {
    'bool': _TypeInfoEntry(AttrTypeData.BOOL, 'bool', str2bool, bool2str, bool2str2, False, [True, False],
                           {'0': _hint('False'), '1': _hint('True')}, None, None),
    'char': _TypeInfoEntry(AttrTypeData.INT, 'char', str2int, unicode, unicode, int(0), [], {},
                           int(-0x80), int(0x7f)),
    'uchar': _TypeInfoEntry(AttrTypeData.INT, 'uchar', str2int, unicode, unicode, int(0), [], {},
                            int(0), int(0xff)),
    'short': _TypeInfoEntry(AttrTypeData.INT, 'short', str2int, unicode, unicode, int(0), [], {},
                            int(-0x8000), int(0x7fff)),
    'ushort': _TypeInfoEntry(AttrTypeData.INT, 'ushort', str2int, unicode, unicode, int(0), [], {},
                             int(0), int(0xffff)),
    'int': _TypeInfoEntry(AttrTypeData.INT, 'int', str2int, unicode, unicode, int(0), [], {},
                          int(-0x80000000), int(0x7fffffff)),
    'uint': _TypeInfoEntry(AttrTypeData.EXT, 'uint', str2long, unicode, unicode, long(0), [], {},
                           long(0), long(0xffffffff)),
    'int64': _TypeInfoEntry(AttrTypeData.LONG, 'int64', str2long, unicode, unicode, long(0), [], {},
                            long(-0x8000000000000000), long(0x7fffffffffffffff)),
    'uint64': _TypeInfoEntry(AttrTypeData.CINT64, 'uint64', str2long, uint2hex16, uint2hex16, long(0), [],
                             {}, long(0), long(0xffffffffffffffff)),
    'long': _TypeInfoEntry(AttrTypeData.LONG, 'long', str2long, unicode, unicode, long(0), [], {}, None, None),
    'float': _TypeInfoEntry(AttrTypeData.REAL, 'float', str2float, unicode, unicode, float(0.0), [], {}, None, None),
    'double': _TypeInfoEntry(AttrTypeData.REAL, 'double', str2float, unicode, unicode, float(0.0), [], {}, None, None),
    'string': _TypeInfoEntry(AttrTypeData.STR, 'string', unicode, one2one, one2one, u'', [], {}, None, None),
    'text': _TypeInfoEntry(AttrTypeData.STR, 'text', unicode, one2one, one2one, u'', [], {}, None, None)
}

TYPE_INFO_ALIAS = {
    'bool': 'bool',
    'boolean': 'bool',

    'char': 'char',
    'character': 'char',
    'int8': 'char',
    'int-8': 'char',
    'int 8': 'char',
    'byte': 'char',

    'uchar': 'uchar',
    'unsigned char': 'uchar',
    'unsigned character': 'uchar',
    'uint8': 'uchar',
    'unsigned int8': 'uchar',
    'uint-8': 'uchar',
    'unsigned int-8': 'uchar',
    'uint 8': 'uchar',
    'unsigned int 8': 'uchar',
    'unsigned byte': 'uchar',
    'ubyte': 'uchar',

    'short': 'short',
    'int16': 'short',
    'int-16': 'short',
    'int 16': 'short',

    'ushort': 'ushort',
    'unsigned short': 'ushort',
    'uint16': 'ushort',
    'unsigned int16': 'ushort',
    'uint-16': 'ushort',
    'unsigned int-16': 'ushort',
    'uint 16': 'ushort',
    'unsigned int 16': 'ushort',

    'int': 'int',
    'int32': 'int',
    'int-32': 'int',
    'int 32': 'int',

    'uint': 'uint',
    'unsigned int': 'uint',
    'uint32': 'uint',
    'unsigned int32': 'uint',
    'uint-32': 'uint',
    'unsigned int-32': 'uint',
    'uint 32': 'uint',
    'unsigned int 32': 'uint',

    'int64': 'int64',
    'int-64': 'int64',
    'int 64': 'int64',

    'uint64': 'uint64',
    'unsigned int64': 'uint64',
    'uint-64': 'uint64',
    'unsigned int-64': 'uint64',
    'uint 64': 'uint64',
    'unsigned int 64': 'uint64',

    'long': 'long',
    'pylong': 'long',
    'py long': 'long',
    'python long': 'long',

    'float': 'float',
    'real': 'float',

    'double': 'double',
    'double float': 'double',
    'double real': 'double',
    'dreal': 'double',
    'dfloat': 'double',

    'string': 'string',
    'text': 'text'
}

ATTRIBUTE_TYPES = tuple(sorted(TYPE_INFO.keys()))

#######################################################################################################################
#######################################################################################################################


class NodeAttrDesc(object):
    __default_type_name = 'int'

    def __init__(self, name, valtype='', isArray=False):
        global TYPE_INFO
        self.fullname = name
        parts = name.split(u'/')
        self.attrname = parts.pop()
        self.subtags = list(filter(bool, parts))
        self.__typedata = TYPE_INFO[self.__default_type_name]
        self.__defaultValue = self.__typedata.default
        self.__enums = copy.deepcopy(self.__typedata.enums)
        self.__hints = copy.deepcopy(self.__typedata.hints)
        self.__minValue = self.__typedata.minValue
        self.__maxValue = self.__typedata.maxValue
        self.__isArray = isArray
        if valtype:
            self.setType(valtype, isArray)
        self.description = u''

    def typeInfo(self):
        return self.__typedata

    def typeName(self):
        return str(self.__typedata.name)

    def typeClass(self):
        return str(self.__typedata.classType)

    def name(self, full=False):
        if full:
            return self.fullname
        return self.attrname

    def fullName(self):
        return self.fullname

    def isDynamic(self):
        return False

    def deepcopy(self):
        theCopy = NodeAttrDesc(copy.deepcopy(self.fullname), self.typeName(), bool(self.__isArray))
        theCopy.description = copy.deepcopy(self.description)
        theCopy.setAvailableValues(self.__enums, self.__hints)
        theCopy.setMinActual(copy.deepcopy(self.__minValue))
        theCopy.setMaxActual(copy.deepcopy(self.__maxValue))
        theCopy.setActualDefaultValue(copy.deepcopy(self.__defaultValue))
        return theCopy

    def path(self):
        return '/'.join(self.subtags)

    def rename(self, name, full):
        if not name:
            return False
        if full:
            if self.fullname == name:
                return False
            self.fullname = name
            parts = name.split('/')
            self.attrname = parts[-1]
            parts.pop()
            self.subtags = list(filter(bool, parts))
        else:
            if self.attrname == name:
                return False
            self.attrname = name
            self.fullname = self.getFullName(name)
        return True

    def getFullName(self, attrname):
        path = self.path()
        if path:
            return '{0}/{1}'.format(path, attrname)
        return attrname

    def setType(self, valtype, isArray=False):
        global TYPE_INFO, TYPE_INFO_ALIAS
        if valtype not in TYPE_INFO_ALIAS:
            return False
        valtype = TYPE_INFO_ALIAS[valtype]
        self.__isArray = isArray
        if self.__typedata.name != valtype:
            self.__typedata = TYPE_INFO[valtype]
            self.__minValue = self.__typedata.minValue
            self.__maxValue = self.__typedata.maxValue
            self.__defaultValue = self.__typedata.default
            self.__enums = copy.deepcopy(self.__typedata.enums)
            self.__hints = copy.deepcopy(self.__typedata.hints)
        return True

    def isArray(self):
        return self.__isArray

    def setArray(self, isArrayFlag):
        self.__isArray = bool(isArrayFlag)

    def defaultValue(self):
        return self.__defaultValue

    def availableValuesXml(self):
        """	Returns text string for writing it into xml-file """
        values = []
        if self.__typedata.classType != AttrTypeData.BOOL:
            # custom type
            for v in self.__enums:
                val = self.value2str2(v)
                if v in self.__hints:
                    _, hint, displayText, isDefault = self.__hints[v]
                    if not isDefault:
                        val += u'|{0}'.format(displayText)
                        if hint:
                            val += u'|{0}'.format(hint)
                values.append(val)
        else:
            # type is bool
            for v in self.__hints:
                _, hint, displayText, isDefault = self.__hints[v]
                if not isDefault:
                    strVal = self.value2str2(v)
                    val = u'{0}|{1}'.format(strVal, displayText)
                    if hint:
                        val += u'|{0}'.format(hint)
                    values.append(val)
        return u';'.join(values)

    def availableValues(self):
        return self.__enums

    def valueHint(self, value):
        if value not in self.__hints:
            strValue2 = self.value2str2(value)
            return False, strValue2, u'', strValue2, True
        displayText, hint, userText, isDefault = self.__hints[value]
        return True, displayText, hint, userText, isDefault

    def setHint(self, value, hint):
        if value in self.__enums:
            if value not in self.__hints:
                userText = editorText = self.value2str2(value)
            else:
                editorText, _, userText, _ = self.__hints[value]
            self.__hints[value] = (editorText, hint, userText, False)
            return True
        return False

    def setText(self, value, displayText):
        if value in self.__enums:
            if value not in self.__hints:
                hint = ''
            else:
                _, hint, _, _ = self.__hints[value]
            strValue2 = self.value2str2(value)
            if displayText:
                editorText = u'{0} [{1}]'.format(displayText, strValue2)
            else:
                editorText = strValue2
            self.__hints[value] = (editorText, hint, displayText, False)
            return True
        return False

    def appendAvailableValueText(self, text, displayText='', hint=''):
        val = self.str2value(text)
        if val not in self.__enums:
            self.__enums.append(val)
            strValue2 = self.value2str2(val)
            if displayText:
                editorText = u'{0} [{1}]'.format(displayText, strValue2)
                self.__hints[val] = (editorText, hint, displayText, False)
            else:
                self.__hints[val] = (strValue2, hint, strValue2, not hint)
            return True
        elif displayText:
            strValue2 = self.value2str2(val)
            editorText = u'{0} [{1}]'.format(displayText, strValue2)
            self.__hints[val] = (editorText, hint, displayText, False)
            return True
        return False

    def appendAvailableValue(self, val, displayText='', hint=''):
        if val not in self.__enums:
            self.__enums.append(val)
            strValue2 = self.value2str2(val)
            if displayText:
                editorText = u'{0} [{1}]'.format(displayText, strValue2)
                self.__hints[val] = (editorText, hint, displayText, False)
            else:
                self.__hints[val] = (strValue2, hint, strValue2, not hint)
            return True
        return False

    def changeAvailableValue(self, oldOne, newOne):
        if oldOne != newOne and oldOne in self.__enums and newOne not in self.__enums and oldOne not in self.__typedata.enums:
            index = self.__enums.index(oldOne)
            self.__enums[index] = newOne
            if oldOne in self.__hints:
                self.__hints[newOne] = self.__hints[oldOne]
                del self.__hints[oldOne]
            else:
                strValue2 = self.value2str2(newOne)
                self.__hints[newOne] = (strValue2, '', strValue2, True)
            return True
        return False

    def removeAvailableValue(self, value):
        if value not in self.__enums or value in self.__typedata.enums:
            return False
        self.__enums.remove(value)
        if value is self.__hints:
            del self.__hints[value]
        if value == self.__defaultValue:
            self.setActualDefaultValue(value)
        return True

    def clearAvailableValues(self):
        self.__enums = copy.deepcopy(self.__typedata.enums)
        self.__hints = copy.deepcopy(self.__typedata.hints)

    def setAvailableValuesByText(self, textVals):
        self.clearAvailableValues()
        for val, text, hint in textVals:
            self.appendAvailableValueText(val, text, hint)

    def setAvailableValues(self, vals, texts):
        self.__enums = copy.deepcopy(vals)
        self.__hints = copy.deepcopy(texts)

    def minValue(self):
        return self.__minValue

    def setMin(self, text):
        if text is None or not text:
            self.__minValue = self.__typedata.minValue
        else:
            val = self.str2value(text)
            if self.__typedata.minValue is not None:
                correctVal = max(val, self.__typedata.minValue)
            else:
                correctVal = val
            if self.__typedata.maxValue is not None:
                val = correctVal
                correctVal = min(val, self.__typedata.maxValue)
            self.__minValue = correctVal

    def setMinActual(self, val):
        self.__minValue = val

    def maxValue(self):
        return self.__maxValue

    def setMax(self, text):
        if text is None or not text:
            self.__maxValue = self.__typedata.maxValue
        else:
            val = self.str2value(text)
            if self.__typedata.minValue is not None:
                correctVal = max(val, self.__typedata.minValue)
            else:
                correctVal = val
            if self.__typedata.maxValue is not None:
                val = correctVal
                correctVal = min(val, self.__typedata.maxValue)
            self.__maxValue = correctVal

    def setMaxActual(self, val):
        self.__maxValue = val

    def setDefaultValue(self, text):
        if text is not None:
            return self.setActualDefaultValue(self.str2value(text))
        return self.setActualDefaultValue(None)

    def setActualDefaultValue(self, val):
        if self.isAvailableValue(val):
            self.__defaultValue = val
            return True
        if self.__enums:
            self.__defaultValue = copy.deepcopy(self.__enums[0])
            return True
        if self.__minValue is not None:
            self.__defaultValue = copy.deepcopy(self.__minValue)
            return True
        if self.__maxValue is not None:
            self.__defaultValue = copy.deepcopy(self.__maxValue)
            return True
        self.__defaultValue = copy.deepcopy(self.__typedata.default)
        return False

    def isAvailableValue(self, val):
        if val is None:
            return False
        if self.__enums:
            return val in self.__enums
        if self.__typedata.enums:
            return val in self.__typedata.enums
        if self.__minValue is not None:
            if val < self.__minValue:
                return False
        if self.__maxValue is not None:
            if val > self.__maxValue:
                return False
        return True

    def validate(self, val):
        if self.__enums:
            if val in self.__enums:
                return val
            return self.__defaultValue
        if self.__typedata.enums:
            if val in self.__typedata.enums:
                return val
            return self.__defaultValue
        if self.__minValue is not None:
            if val < self.__minValue:
                return self.__minValue
        if self.__maxValue is not None:
            if val > self.__maxValue:
                return self.__maxValue
        return val

    def value2str(self, val):
        if val is None:
            return u''
        if isinstance(val, list):
            return list(map(self.__typedata.revConverter1, val))
        return self.__typedata.revConverter1(val)

    def value2str2(self, val):
        if val is None:
            return ''
        if isinstance(val, list):
            return list(map(self.__typedata.revConverter2, val))
        return self.__typedata.revConverter2(val)

    def str2value(self, text):
        if isinstance(text, list):
            return list(map(self.__typedata.converter, text))
        return self.__typedata.converter(text)

    def update(self, attributes, currentKey):
        """
        update method for supporting DynamicAttrDesc interface.
        """
        return False, currentKey

    def default(self):
        """
        default method for supporting DynamicAttrDesc interface.
        """
        return self

    def defaultKey(self):
        """
        defaultKey method for supporting DynamicAttrDesc interface.
        """
        return ''

    def get(self, key):
        """
        operator '[]' for supporting DynamicAttrDesc interface.
        """
        return self

#######################################################################################################################
#######################################################################################################################


class DynamicAttrDesc(object):
    def __init__(self, name, description, isArray, controlAttributeName, defaultKey=''):
        self.__isArray = isArray
        self.__defaultKey = defaultKey
        self.description = description
        self.controlAttribute = controlAttributeName
        self.fullname = name
        parts = name.split(u'/')
        self.attrname = parts.pop()
        self.subtags = list(filter(bool, parts))
        self.__attributes = dict()
        self.__typesTip = u''

    def name(self, full=False):
        if full:
            return self.fullname
        return self.attrname

    def fullName(self):
        return self.fullname

    def empty(self):
        return not self.__attributes

    def units(self):
        return self.__attributes

    def get(self, key):
        """ operator '[]' """
        return self.__attributes.get(key)

    def isDynamic(self):
        return True

    def isArray(self):
        return self.__isArray

    def setArray(self, isArrayFlag):
        self.__isArray = bool(isArrayFlag)

    def deepcopy(self):
        theCopy = DynamicAttrDesc(copy.copy(self.fullname), copy.copy(self.description),\
                                  bool(self.__isArray), copy.copy(self.controlAttribute),\
                                  copy.copy(self.__defaultKey))
        attrs = dict()
        for a in self.__attributes:
            attrs[a] = self.__attributes[a].deepcopy()
        theCopy.__setAttributes(attrs)
        theCopy.__setTypesTip(copy.copy(self.__typesTip))
        return theCopy

    def path(self):
        return '/'.join(self.subtags)

    def rename(self, name, full):
        if not name:
            return False
        if full:
            if self.fullname == name:
                return False
            self.fullname = name
            parts = name.split(u'/')
            self.attrname = parts.pop()
            self.subtags = list(filter(bool, parts))
        else:
            if self.attrname == name:
                return False
            self.attrname = name
            self.fullname = self.getFullName(name)
        return True

    def getFullName(self, attrname):
        path = self.path()
        if path:
            return '{0}/{1}'.format(path, attrname)
        return attrname

    def typesTip(self):
        return self.__typesTip

    def default(self):
        return self.__attributes[self.__defaultKey]

    def defaultKey(self):
        return self.__defaultKey

    def addAttribute(self, attr, keys):
        if self.__isArray == attr.isArray():
            if isinstance(keys, list):
                for key in keys:
                    self.__attributes[key] = attr
            else:
                self.__attributes[keys] = attr
            return True
        return False

    def correctDefault(self):
        if not self.__attributes:
            return
        if self.__defaultKey not in self.__attributes:
            self.__defaultKey = ''
            if '' not in self.__attributes:
                if isPython2:
                    self.__attributes[''] = self.__attributes.itervalues().next()
                else:
                    self.__attributes[''] = next(iter(list(self.__attributes.values())))
            self.__updateTypesTip()
            return
        elif '' not in self.__attributes:
            self.__attributes[''] = self.__attributes[self.__defaultKey]
        self.__updateTypesTip()

    def __updateTypesTip(self):
        self.__typesTip = u'possible types:'
        if '' in self.__attributes:
            self.__typesTip += u'\ndefault - \'{0}\''.format(self.__attributes[''].typeName())
        for a in self.__attributes:
            if a:
                self.__typesTip += u'\n\'{0}\' when var \'{1}\' == \'{2}\''.format(self.__attributes[a].typeName(), \
                                                                                   self.controlAttribute, a)

    def __setAttributes(self, attrs):
        self.__attributes = attrs

    def __setTypesTip(self, tip):
        self.__typesTip = tip

    def update(self, attributes, currentKey):
        if self.controlAttribute in attributes:
            text = attributes[self.controlAttribute].value2strAlternate()
            if text != currentKey:
                if text in self.__attributes:
                    return True, text
                return False, text
        return False, currentKey

#######################################################################################################################
#######################################################################################################################


class NodeAttr(object):
    def __init__(self, attrname, nodename, libname, project, key=None):
        self.__project = project
        self.__nodename = nodename
        self.__libname = libname
        self.__name = attrname
        self.__dynamicKey = ''
        if key is None:
            desc = self.nodeDesc()
            if desc is not None:
                self.__dynamicKey = desc[self.__name].defaultKey()
        else:
            self.__dynamicKey = key
        self.__value = self.__defVal()
        globals.librarySignals.nodeRenamed.connect(self.__onNodeRename)

    def deepcopy(self):
        theCopy = NodeAttr(copy.copy(self.__name), copy.copy(self.__nodename),\
                           copy.copy(self.__libname), self.__project, copy.copy(self.__dynamicKey))
        theCopy.setActualValueNoCheck(copy.deepcopy(self.__value))
        return theCopy

    def setName(self, name):
        self.__name = name

    def __onNodeRename(self, libname, oldname, newname):
        if self.__libname == libname and self.__nodename == oldname:
            self.__nodename = newname

    def isArray(self):
        desc = self.nodeDesc()
        if desc is not None:
            return desc[self.__name].isArray()
        return False

    def attrDesc(self):
        desc = self.nodeDesc()
        if desc is not None:
            d = desc[self.__name]
            if d is not None:
                return d.get(self.__dynamicKey)
        return None

    def attrDescActual(self):
        desc = self.nodeDesc()
        if desc is not None:
            return desc[self.__name]
        return None

    def attrname(self):
        desc = self.attrDesc()
        if desc is not None:
            return desc.attrname
        return ''

    def nodeDesc(self):
        if self.__project is not None and self.__libname in self.__project.libraries and \
                self.__nodename in self.__project.libraries[self.__libname]:
            return self.__project.libraries[self.__libname][self.__nodename]
        return None

    def setKey(self, key):
        self.__dynamicKey = key

    def dynamicKey(self):
        return self.__dynamicKey

    def setValue(self, text):
        desc = self.attrDesc()
        if desc is None:
            return False
        if isinstance(text, list):
            if desc.isArray():
                return self.__setActualValueArray(desc.str2value(text), desc)
            return self.__setActualValue(desc.str2value(text[0]), desc)
        else:
            if desc.isArray():
                return self.__setActualValueArray([desc.str2value(text)], desc)
            return self.__setActualValue(desc.str2value(text), desc)

    def setValueAtIndex(self, text, index):
        return self.setValueAt(text, index)

    def setValueAt(self, text, index):
        desc = self.attrDesc()
        if desc is None or not desc.isArray() or index < 0:
            return False
        if isinstance(text, list):
            return False
        if text is None:
            return self.__eraseAt(index)
        return self.__setActualValueAt(desc.str2value(text), desc, index)

    def insertValueAt(self, text, index):
        desc = self.attrDesc()
        if desc is None or not desc.isArray() or index < 0:
            return False
        if isinstance(text, list):
            return False
        if text is None:
            return self.__insertActualValueAt(desc.defaultValue(), desc, index)
        return self.__insertActualValueAt(desc.str2value(text), desc, index)

    def appendValue(self, text):
        desc = self.attrDesc()
        if desc is None or not desc.isArray():
            return False
        if text is None:
            return self.__appendActualValue(desc.defaultValue(), desc)
        if isinstance(text, list):
            return self.__appendActualValueArray(desc.str2value(text), desc)
        return self.__appendActualValue(desc.str2value(text), desc)

    def setActualValue(self, val):
        desc = self.attrDesc()
        if desc is None:
            return False
        if isinstance(val, list):
            if desc.isArray():
                return self.__setActualValueArray(val, desc)
            return self.__setActualValue(val[0], desc)
        else:
            if desc.isArray():
                return self.__setActualValueArray([val], desc)
            return self.__setActualValue(val, desc)

    def setActualValueAtIndex(self, val, index):
        return self.setActualValueAt(val, index)

    def setActualValueAt(self, val, index):
        desc = self.attrDesc()
        if desc is None or not desc.isArray() or index < 0:
            return False
        if isinstance(val, list):
            return False
        if val is None:
            return self.__eraseAt(index)
        return self.__setActualValueAt(val, desc, index)

    def insertActualValueAt(self, val, index):
        desc = self.attrDesc()
        if desc is None or not desc.isArray() or index < 0:
            return False
        if isinstance(val, list):
            return False
        if val is None:
            return self.__insertActualValueAt(desc.defaultValue(), desc, index)
        return self.__insertActualValueAt(val, desc, index)

    def appendActualValue(self, val):
        desc = self.attrDesc()
        if desc is None or not desc.isArray():
            return False
        if val is None:
            return self.__appendActualValue(desc.defaultValue(), desc)
        if isinstance(val, list):
            return self.__appendActualValueArray(val, desc)
        return self.__appendActualValue(val, desc)

    def __eraseAt(self, index):
        if index < len(self.__value):
            self.__value.pop(index)
        else:
            self.__value.pop()
        return True

    def setActualValueNoCheck(self, val):
        self.__value = val

    def __setActualValue(self, val, desc):
        if not desc.isAvailableValue(val):
            return False
        self.__value = val
        return True

    def __setActualValueAt(self, val, desc, index):
        if not desc.isAvailableValue(val) or index >= len(self.__value):
            return False
        self.__value[index] = val
        return True

    def __insertActualValueAt(self, val, desc, index):
        if not desc.isAvailableValue(val):
            return False
        if index < len(self.__value):
            self.__value.insert(index, val)
        else:
            self.__value.append(val)
        return True

    def __appendActualValue(self, val, desc):
        if not desc.isAvailableValue(val):
            return False
        self.__value.append(val)
        return True

    def __setActualValueArray(self, valarray, desc):
        self.__value = []
        if not valarray:
            return False
        for v in valarray:
            if desc.isAvailableValue(v):
                self.__value.append(v)
        return bool(self.__value)

    def __appendActualValueArray(self, valarray, desc):
        if not valarray:
            return False
        n = 0
        for v in valarray:
            if desc.isAvailableValue(v):
                self.__value.append(v)
                n += 1
        return n > 0

    def reset(self):
        self.__value = self.__defVal()

    def value(self):
        return self.__value

    def valueToStr(self):
        desc = self.attrDesc()
        if desc is None:
            return u''
        return desc.value2str(self.__value)

    def value2strAlternate(self):
        desc = self.attrDesc()
        if desc is None:
            return u''
        return desc.value2str2(self.__value)

    def __defVal(self):
        desc = self.attrDesc()
        if desc is None:
            return int(0)
        if desc.isArray():
            return []
        return desc.defaultValue()

    def update(self, otherAttributes):
        desc = self.nodeDesc()
        if desc is None:
            return
        d = desc[self.__name]
        if d is None:
            return
        old = d.get(self.__dynamicKey)
        updated, key = d.update(otherAttributes, self.__dynamicKey)
        if updated:
            if key != self.__dynamicKey:
                self.__dynamicKey = key
                if old is not None:
                    curr = d.get(key)
                    if d.isArray():
                        vals = self.__value
                        self.__value = []
                        for v in vals:
                            text = old.value2str(v)
                            val = curr.validate(curr.str2value(text))
                            self.__value.append(val)
                    else:
                        text = old.value2str(self.__value)
                        self.__value = curr.validate(curr.str2value(text))
        elif key != self.__dynamicKey:
            self.__dynamicKey = key

#######################################################################################################################
#######################################################################################################################


class AutoposData(object):
    def __init__(self):
        self.autopos = True  # flag of automatic calculating "shift"
        self.shift = QPointF()  # shift relative to parent node on visual diagram


class DiagramInfo(object):
    def __init__(self):
        self.expanded = True  # flag of need to expand children nodes on visual diagram
        self.autopositioning = {DisplayRegime.Horizontal: AutoposData(), DisplayRegime.Vertical: AutoposData()}
        self.scenePos = QPointF()

    def deepcopy(self):
        theCopy = DiagramInfo()
        theCopy.expanded = bool(self.expanded)
        theCopy.autopositioning[DisplayRegime.Horizontal].autopos = bool(self.autopositioning[DisplayRegime.Horizontal].autopos)
        theCopy.autopositioning[DisplayRegime.Horizontal].shift = QPointF(self.autopositioning[DisplayRegime.Horizontal].shift)
        theCopy.autopositioning[DisplayRegime.Vertical].autopos = bool(self.autopositioning[DisplayRegime.Vertical].autopos)
        theCopy.autopositioning[DisplayRegime.Vertical].shift = QPointF(self.autopositioning[DisplayRegime.Vertical].shift)
        theCopy.scenePos = QPointF(self.scenePos)
        return theCopy


class Uid(object):
    def __init__(self, value):
        self.value = value


class TreeNode(object):
    def __init__(self, project, xml_node, nodeClass, nodeType, debug, uid):
        self.singleblock = False
        self.debug = debug      # debug flag. If 'True', this TreeNode is active only in debug mode
        self.__refname = ''     # it is name of this TreeNode. 'target' field of link-TreeNode points to this name and path
        self.__path = ''        # this is full path of tree file
        self.Project = project  # reference to current project
        self.xml = xml_node     # reference to xml-node for repeat reading node attributes

        self.__attributes = dict()  # list of attributes
        self.__children = dict()    # children list by classes. It's dict({'Task':[], 'Condition':[]})
        self.__inverse = False

        self.libname = ''   # the name of target node library ('ai_behavior_general' and so on...)
        self.nodeName = ''  # 'Sequence', 'Selector', 'Repeater', 'VoidTask', 'IF', ... (it is nodes from specified library)
        self.nodeClass = nodeClass  # 'Task' or 'Condition' (or another class specified in current alphabet)
        self.nodeType = nodeType    # 'Leaf', 'Decorator', 'Composite', 'Reference', ... (each class has some sub-types)

        self.target = ''  # if current nodeType is link, then 'target' points to another node in current tree

        self.parentNode = None  # reference to parent TreeNode

        self.diagramInfo = DiagramInfo()
        # t = self.type()
        # if t is not None and t.isLink():
        #     self.diagramInfo.expanded = False

        if uid is None:
            self.__uid = _createUid()
        else:
            self.__uid = uid

    # Returns True if this node or it's children has node with name 'item'
    def __contains__(self, item):
        libname, nodename = item
        if self.libname == libname and self.nodeName == nodename:
            return True
        for cls in self.__children:
            for child in self.__children[cls]:
                if item in child:
                    return True
        return False

    def uid(self):
        return self.__uid

    def parent(self):
        """ Returns parent node of this node. """
        return self.parentNode

    def root(self):
        """ Returns a root node of current tree. """
        if self.parentNode is None:
            return self
        parent = self.parentNode
        while parent.parent() is not None:
            parent = parent.parent()
        return parent

    def setParent(self, parent):
        self.parentNode = parent

    def cls(self):
        if self.Project is not None:
            return self.Project.alphabet.getClass(self.nodeClass)
        return None

    def type(self):
        c = self.cls()
        if c is not None:
            return c.get(self.nodeType)
        return None

    def debugMode(self):
        return self.debug

    def setDebugMode(self, dbg):
        self.debug = bool(dbg)

    def singleBlock(self):
        return self.singleblock

    def setSingleblock(self, singleblock):
        self.singleblock = bool(singleblock)

    def fullRefName(self):
        if self.__refname:
            return '{0}/{1}'.format(self.__path, self.__refname)
        return ''

    def path(self):
        return self.__path

    def setPath(self, path):
        self.__path = path

    def refname(self):
        return self.__refname

    def setRefName(self, ref):
        self.__refname = ref

    def setXmlSource(self, xml_node):
        self.xml = xml_node

    def setProject(self, project):
        self.Project = project

    def setLibName(self, libname):
        self.libname = libname

    def setNodeName(self, name):
        self.nodeName = name

    def setNodeClass(self, className):
        self.nodeClass = className

    def setNodeType(self, typeName):
        self.nodeType = typeName
        t = self.type()
        if t is not None and t.isLink():
            self.diagramInfo.expanded = False

    def rename(self, libname, oldname, newname, recursive):
        if self.libname == libname and self.nodeName == oldname:
            self.nodeName = newname
        if recursive:
            for cls in self.__children:
                for child in self.__children[cls]:
                    child.rename(libname, oldname, newname, True)

    def renameAttribute(self, libname, nodename, oldname, newname, recursive):
        if self.libname == libname and nodename == self.nodeName and oldname in self.__attributes:
            attr = self.__attributes[oldname]
            del self.__attributes[oldname]
            attr.setName(newname)
            self.__attributes[newname] = attr
        if recursive:
            for cls in self.__children:
                for child in self.__children[cls]:
                    child.renameAttribute(libname, nodename, oldname, newname, True)

    def addAttribute(self, libname, nodename, attributeName, recursive):
        if libname == self.libname and nodename == self.nodeName:
            if attributeName not in self.__attributes:
                self.__attributes[attributeName] = NodeAttr(attributeName, self.nodeName, self.libname, self.Project)
        if recursive:
            for cls in self.__children:
                for child in self.__children[cls]:
                    child.addAttribute(libname, nodename, attributeName, True)

    def deleteAttribute(self, libname, nodename, attributeName, recursive):
        if libname == self.libname and nodename == self.nodeName:
            if attributeName in self.__attributes:
                del self.__attributes[attributeName]
        if recursive:
            for cls in self.__children:
                for child in self.__children[cls]:
                    child.deleteAttribute(libname, nodename, attributeName, True)

    def validateAttribute(self, libname, nodename, attributeName, attributeOldDescriptor, recursive):
        if libname == self.libname and nodename == self.nodeName:
            if attributeName in self.__attributes:
                old_value_text = attributeOldDescriptor.value2str(self.__attributes[attributeName].value())
                self.__attributes[attributeName].setValue(old_value_text)
        if recursive:
            for cls in self.__children:
                for child in self.__children[cls]:
                    child.validateAttribute(libname, nodename, attributeName, attributeOldDescriptor, True)

    def changeType(self, libname, nodename, newType, recursive):
        if self.libname == libname and self.nodeName == nodename:
            self.nodeType = newType
        if recursive:
            for cls in self.__children:
                for child in self.__children[cls]:
                    child.changeType(libname, nodename, newType, True)

    def isInverse(self):
        return bool(self.__inverse)

    def setInverse(self, inv):
        self.__inverse = bool(inv)

    def nodeDesc(self):
        desc = None
        if self.Project is not None and self.libname in self.Project.libraries:
            desc = self.Project.libraries[self.libname][self.nodeName]
        if desc is not None and desc.nodeClass == self.nodeClass and desc.nodeType == self.nodeType:
            return desc
        return None

    def isEmpty(self):
        return self.type() is None

    def attributes(self):
        return self.__attributes

    def getAttributesCopy(self):
        attr = dict()
        for a in self.__attributes:
            attr[a] = self.__attributes[a].deepcopy()
        return attr

    def setAttributes(self, attr):
        ok = False
        if attr:
            for a in attr:
                if attr[a].nodeDesc() is not None and attr[a].nodeDesc() == self.nodeDesc():
                    ok = True
                break
        if ok:
            self.__attributes.clear()
            for a in attr:
                self.__attributes[a] = attr[a].deepcopy()

    def getMessage(self):
        if self.type().isLink():
            texts = self.target.split('/')
            if not texts:
                texts = [self.target]
            return u'link {0} to \"{1}\" {2}'.format(self.nodeType, texts[-1], self.__uid)
        elif self.__refname:
            return u'branch \"{0}\" {1}'.format(self.__refname, self.__uid)
        return u'{0} {1} \"{2}\" {3}'.format(self.nodeType, self.nodeClass, self.nodeName, self.__uid)

    def addChild(self, child, before=None, silent=False):
        classname = child.cls().name
        if classname not in self.__children:
            self.__children[classname] = []
            permit = True
        elif child not in self.__children[classname]:
            permit = True
        else:
            permit = False
        if permit:
            if not silent:
                if child.parent() is None:
                    globals.historySignals.pushState.emit(u'Add child {0}'.format(child.getMessage()))
                else:
                    globals.historySignals.pushState.emit(u'Change parent for {0}'.format(child.getMessage()))
            if child.parent() is not None:
                child.parent().removeChild(child, silent=True, permanent=False)
            child.setParent(self)
            num_children = len(self.__children[classname])
            if before is None:
                before = num_children + 1
            elif before < 0:
                before = 0
            if before >= num_children:
                self.__children[classname].append(child)
            else:
                self.__children[classname].insert(before, child)
            if not silent and globals.project is not None:
                globals.project.modified = True
                globals.project.trees.removeDisconnectedNodes(None, child.uid())
                globals.behaviorTreeSignals.nodeConnected.emit(Uid(child.uid()), Uid(self.uid()))
        return permit

    def removeChild(self, child, silent=False, permanent=True):
        classname = child.cls().name
        if classname in self.__children:
            if child in self.__children[classname]:
                if not silent:
                    globals.historySignals.pushState.emit(u'Remove {0}'.format(child.getMessage()))
                child.setParent(None)
                self.__children[classname].remove(child)
                if not permanent:
                    root = self.root()
                    treeName = root.fullRefName()
                    if not treeName:
                        treeName = globals.project.trees.getDisconnectedTreeName(root.uid())
                    globals.project.trees.addDisconnectedNodes(treeName, child.uid())
                elif self.Project is not None:
                    globals.project.trees.removeDisconnectedNodes(None, child.uid())
                    # self.Project.nodes.remove(self) # !!!!!!!!!!!!!!!!!!!!
                    self.Project.nodes.remove(child)
                if not silent:
                    globals.project.modified = True
                    globals.behaviorTreeSignals.nodeDisconnected.emit(Uid(child.uid()), Uid(self.uid()))
                return True
        return False

    def children(self, classname):
        if classname in self.__children:
            return self.__children[classname]
        return []

    def indexOf(self, child):
        classname = child.cls().name
        if classname not in self.__children:
            return int(-1)
        children = self.__children[classname]
        return children.index(child)

    def swap(self, classname, i, j, silent=False):
        if i != j and i >= 0 and j >= 0 and classname in self.__children:
            children = self.__children[classname]
            num_children = len(children)
            if i < num_children and j < num_children:
                if not silent:
                    globals.historySignals.pushState.emit(u'Swap {0} WITH {1}'.format(children[i].getMessage(),
                                                                                      children[j].getMessage()))
                children[i], children[j] = children[j], children[i]
                globals.project.modified = True

    def allChildren(self):
        return self.__children

    def getUsedLibraries(self):
        libraries = []
        if self.libname:
            libraries.append(self.libname)
        for classname in self.__children:
            for child in self.__children[classname]:
                libs = child.getUsedLibraries()
                for lib in libs:
                    if lib not in libraries:
                        libraries.append(lib)
        return libraries

    def reparseAttributes(self, xml_required=False):
        self.__attributes.clear()
        desc = self.nodeDesc()
        if desc is None:
            self_type = self.type()
            if self_type is None or not self_type.isLink():
                refname = self.root().refname()
                print(u'ERROR: no description for node. Reason: {0} | Check behavior tree \"{1}\".'
                      .format(self.__reason(), refname))
                return False
            return True

        for a in desc.attributes():
            self.__attributes[a] = NodeAttr(a, desc.name, desc.libname, self.Project)

        if self.xml is None:
            for a in self.__attributes:
                self.__attributes[a].update(self.__attributes)
            if xml_required:
                print(u'ERROR: Missing xml-node for \"{0}\"'.format(self.nodeName))
            return False

        if self.type().isLink():
            return True  # no attributes for links.

        if not self.cls().attributes.tag:
            print(u'WARNING: class \"{0}\" have no attributes.'.format(self.nodeClass))
            return True

        attributesTags = self.xml.getElementsByTagName(self.cls().attributes.tag)
        if not attributesTags:
            if self.cls().attributes.obligatory:
                print(u'ERROR: Attributes tag <{0}> is missing for node \"{1}\"!'
                      .format(self.cls().attributes.tag, self.nodeName))
                return False
            print(u'WARNING: Attributes tag <{0}> is missing for node \"{1}\".'
                  .format(self.cls().attributes.tag, self.nodeName))
            return True

        settings = attributesTags[0]
        if not self.__parseSettings(settings):
            msg = u'ERROR:'
            res = False
            if not self.cls().attributes.obligatory:
                msg = u'WARNING:'
                res = True
            print(u'{0} Attributes for node \"{1}\" can not be loaded!'.format(msg, self.nodeName))
            return res

        return True

    def __parseSettings(self, settings):
        commonAttributes = []
        dynamicAttributes = []
        for atr in self.__attributes:
            attrDesc = self.__attributes[atr].attrDescActual()
            if attrDesc is not None:
                if attrDesc.isDynamic():
                    dynamicAttributes.append(atr)
                else:
                    commonAttributes.append(atr)
        for atr in commonAttributes:
            cur = settings
            attr = self.__attributes[atr]
            attrDesc = attr.attrDesc()

            if attrDesc.isArray():
                attr.reset()
                data = []
                # поиск тэгов в xml, последний тэг - это и есть массив
                for subtag in attrDesc.subtags:
                    data = cur.getElementsByTagName(subtag)
                    if not data:
                        return True  # данные не заданы
                    cur = data[0]
                for d in data:
                    if d.hasAttribute(attrDesc.attrname):
                        val = d.getAttribute(attrDesc.attrname)
                        attr.appendValue(val)
            else:
                # поиск тэгов в xml, последний тэг должен содержать необходимые атрибуты
                for subtag in attrDesc.subtags:
                    data = cur.getElementsByTagName(subtag)
                    if not data:
                        return True  # данные не заданы
                    cur = data[0]  # не массив, поэтому запоминаем только первый инстанс тэга в списке
                if cur.hasAttribute(attrDesc.attrname):
                    val = cur.getAttribute(attrDesc.attrname)
                    attr.setValue(val)

        for atr in dynamicAttributes:
            cur = settings
            attr = self.__attributes[atr]
            attr.update(self.__attributes)
            attrDesc = attr.attrDesc()
            if attrDesc is None:
                treename = self.root().refname()
                print(u'debug: Node \'{0}\' of tree \'{1}\' has no attribute \'{2}\'. \
                        This attribute\'s value will not be loaded. (special dynamic attribute condition)'
                      .format(self.nodeName, treename, atr))
                continue

            if attrDesc.isArray():
                attr.reset()
                data = []
                # поиск тэгов в xml, последний тэг - это и есть массив
                for subtag in attrDesc.subtags:
                    data = cur.getElementsByTagName(subtag)
                    if not data:
                        return True  # данные не заданы
                    cur = data[0]
                for d in data:
                    if d.hasAttribute(attrDesc.attrname):
                        val = d.getAttribute(attrDesc.attrname)
                        attr.appendValue(val)
            else:
                # поиск тэгов в xml, последний тэг должен содержать необходимые атрибуты
                for subtag in attrDesc.subtags:
                    data = cur.getElementsByTagName(subtag)
                    if not data:
                        return True  # данные не заданы
                    cur = data[0]  # не массив, поэтому запоминаем только первый инстанс тэга в списке
                if cur.hasAttribute(attrDesc.attrname):
                    val = cur.getAttribute(attrDesc.attrname)
                    attr.setValue(val)

        return True

    def __reason(self):
        if self.Project is None:
            return u'Project is missing.'
        if self.libname not in self.Project.libraries:
            return u'Library \"{0}\" is missing.'.format(self.libname)
        if self.nodeName not in self.Project.libraries[self.libname]:
            return u'Node \"{0}\" is missing from library \"{1}\".'.format(self.nodeName, self.libname)
        desc = self.Project.libraries[self.libname][self.nodeName]
        if desc.nodeClass != self.nodeClass:
            return u'Classes mismatch: current class is \"{0}\", but must be \"{1}\".'\
                .format(self.nodeClass, desc.nodeClass)
        if desc.nodeType != self.nodeType:
            return u'Types mismatch: current type is \"{0}\", but must be \"{1}\".'\
                .format(self.nodeType, desc.nodeType)
        return u'No errors found!'

    def dependsOn(self, refname):
        if self.type().isLink():
            return refname == self.target
        isDepends = False
        for c in self.__children:
            for child in self.__children[c]:
                isDepends = child.dependsOn(refname)
                if isDepends:
                    return isDepends
        return isDepends

    def deepcopy(self, _undoRedo=False, _removeRefnames=False):
        """ Make deep copy of the tree-node.
        _undoRedo - points if deepcopy method was called by undo-redo system
        _removeRefnames - points if you need to remove tree reference (TreeNode.refname)
        """

        if _undoRedo:
            uid = copy.copy(self.__uid)
            xmlnode = self.xml
        else:
            xmlnode = None
            uid = None

        theCopy = TreeNode(self.Project, xmlnode, copy.copy(self.nodeClass), copy.copy(self.nodeType), bool(self.debug), uid)
        theCopy.setSingleblock(self.singleblock)
        theCopy.setLibName(copy.copy(self.libname))
        theCopy.setNodeName(copy.copy(self.nodeName))
        theCopy.setPath(copy.copy(self.__path))
        theCopy.setRefName(copy.copy(self.__refname))
        theCopy.target = copy.copy(self.target)
        theCopy.setInverse(self.__inverse)
        theCopy.diagramInfo = self.diagramInfo.deepcopy()

        theCopy.__attributes = self.getAttributesCopy()

        for cls in self.__children:
            children = self.__children[cls]
            for child in children:
                theCopy.addChild(child.deepcopy(_undoRedo, _removeRefnames), silent=True)

        if _removeRefnames:
            theCopy.setRefName('')

        return theCopy

#######################################################################################################################
#######################################################################################################################


class TreeNodes(object):
    def __init__(self):
        self.__nodes = dict()

    def __contains__(self, item):
        if item is None:
            return False
        return self.__nodes.__contains__(item)

    def __getitem__(self, item):
        if item is None:
            return None
        return self.__nodes.get(item)

    def __len__(self):
        return self.__nodes.__len__()

    def __iter__(self):
        return self.__nodes.__iter__()

    def deepcopy(self, _undoRedo):
        nodes = TreeNodes()
        for uid in self.__nodes:
            nodes.add(self.__nodes[uid].deepcopy(_undoRedo), False)
        return nodes

    def clear(self):
        self.__nodes.clear()

    def get(self, item):
        """ Returns node by it's uid. If there is no node with specified uid, returns 'None'. """
        return self.__getitem__(item)

    def add(self, node, recursive=False):
        """ Stores node's uid in list. If 'recursive' is True then also stores all node's children. """
        if globals.debugMode and node.uid() in self.__nodes:
            print(u'warning: node with uid = {0} already exist and will be replaced!'.format(node.uid()))
        self.__nodes[node.uid()] = node
        if recursive:
            classes = node.allChildren()
            for c in classes:
                children = classes[c]
                for child in children:
                    self.add(child, recursive=True)

    def remove(self, node, recursive=False):
        """ Pops node from list. If 'recursive' is True then also pops all node's children. """
        self.__nodes.pop(node.uid(), node)
        if recursive:
            classes = node.allChildren()
            for c in classes:
                children = classes[c]
                for child in children:
                    self.remove(child, recursive=True)

    def create(self, project, xml_node, nodeClass, nodeType, debug, uid):
        """ Creates new TreeNode and inserts it into the nodes list. """
        node = TreeNode(project, xml_node, nodeClass, nodeType, debug, uid)
        self.add(node)
        return node

    def createCopy(self, _originalNode, _undoRedo=False, _removeRefnames=False):
        """ Creates new TreeNode and inserts it into the nodes list. """
        node = _originalNode.deepcopy(_undoRedo, _removeRefnames)
        self.add(node, recursive=True)
        return node

#######################################################################################################################
#######################################################################################################################


class BehaviorTree(object):
    def __init__(self):
        self.__branches = dict()
        self.__disconnectedNodes = dict()

    def __contains__(self, item):
        return self.__branches.__contains__(item)

    def __getitem__(self, item):
        return self.__branches.get(item)

    def __len__(self):
        return self.__branches.__len__()

    def __iter__(self):
        return self.__branches.__iter__()

    def get(self, item):
        return self.__getitem__(item)

    def deepcopy(self):
        """ Make deep copy of all trees.
        _undoRedo - points if deepcopy method was called by undo-redo system
        """
        bt = BehaviorTree()
        bt._setBranches(self.__branches)
        bt._setDisconnectedNodes(self.__disconnectedNodes)
        return bt

    def add(self, branch, force=False, silent=False):
        """ Adds branch into the trees list.
        Also adds all it's children into the nodes list.
        force - if True, then rewrite existing tree (if tree with branch.fullRefName() already exist)
        silent - if True, then do not save project state (this is for history)
        """
        fullname = branch.fullRefName()
        if force or fullname not in self.__branches:
            if not silent:
                globals.historySignals.pushState.emit(u'Add/replace behavior tree \'{0}\''.format(branch.refname()))
            self.__branches[fullname] = branch.uid()
            self.__disconnectedNodes[fullname] = []
            if not silent and globals.project is not None:
                globals.project.modified = True
            return True
        return False

    def remove(self, fullname, silent=False):
        """ Removes a tree with name 'fullname' from trees list.
        Also removes all it's children from nodes list.
        silent - if True, then do not save project state (this is for history)
        """
        if fullname in self.__branches:
            if not silent:
                if '/' in fullname:
                    refname = fullname.split('/')[-1]
                else:
                    refname = fullname
                globals.historySignals.pushState.emit(u'Remove behavior tree \'{0}\''.format(refname))
            self.removeDisconnectedNodes(fullname, self.__branches[fullname].uid())
            del self.__branches[fullname]
            del self.__disconnectedNodes[fullname]
            if not silent:
                globals.project.modified = True
            globals.behaviorTreeSignals.treeDeleted.emit(fullname)
            return True
        return False

    def rename(self, oldname, newname, silent=False):
        """ Rename tree with name 'oldname' into 'newname'.
        silent - if True, then do not save project state (this is for history)
        """
        if oldname not in self.__branches or newname in self.__branches:
            return False

        uid = self.__branches[oldname]
        if uid not in globals.project.nodes:
            return False

        if not silent:
            globals.historySignals.pushState.emit(u'Rename behavior tree \'{0}\' to \'{1}\''.format(oldname, newname))

        branch = globals.project.nodes[uid]
        nodes = self.__disconnectedNodes[oldname]

        strings = newname.split('/')
        ref = strings.pop()
        branch.setPath('/'.join(strings))
        branch.setRefName(ref)

        self.__branches[newname] = uid
        self.__disconnectedNodes[newname] = nodes

        del self.__branches[oldname]
        del self.__disconnectedNodes[oldname]

        for b in self.__branches:
            branch_uid = self.__branches[b]
            if branch_uid in globals.project.nodes:
                self.__recursiveRename(globals.project.nodes[branch_uid], oldname, newname)

        globals.project.modified = True
        globals.behaviorTreeSignals.treeRenamed.emit(oldname, newname)

        return True

    def addDisconnectedNodes(self, fullname, nodesUids):
        if fullname in self.__disconnectedNodes:
            if not isinstance(nodesUids, list):
                uids = [nodesUids]
            else:
                uids = nodesUids
            nodes = self.__disconnectedNodes[fullname]
            for uid in uids:
                if uid not in nodes:
                    nodes.append(uid)

    def _setBranches(self, branches):
        self.__branches = dict(branches)

    def _setDisconnectedNodes(self, nodesUids):
        self.__disconnectedNodes = dict(nodesUids)

    def removeDisconnectedNodes(self, fullname, nodesUids):
        if fullname is not None:
            # search by tree with name 'fullname'
            if fullname in self.__disconnectedNodes:
                if not isinstance(nodesUids, list):
                    uids = [nodesUids]
                else:
                    uids = nodesUids
                nodes = self.__disconnectedNodes[fullname]
                for i in xrange(len(nodes)-1, -1, -1):
                    uid = nodes[i]
                    if uid in uids:
                        nodes.pop(i)
                        uids.remove(uid)
                        if not uids:
                            return
        else:
            # search by all trees if fullname is None
            if not isinstance(nodesUids, list):
                uids = [nodesUids]
            else:
                uids = nodesUids
            for k, v in dict_items(self.__disconnectedNodes.items()):
                for i in xrange(len(v) - 1, -1, -1):
                    uid = v[i]
                    if uid in uids:
                        self.__disconnectedNodes[k].pop(i)
                        uids.remove(uid)
                        if not uids:
                            return

    def getDisconnectedTreeName(self, uid):
        for k, v in dict_items(self.__disconnectedNodes.items()):
            if uid in v:
                return k
        return ''

    def disconnectedNodes(self, fullname):
        if fullname is not None and fullname:
            return self.__disconnectedNodes.get(fullname, None)
        else:
            nodes = []
            for k, v in dict_items(self.__disconnectedNodes.items()):
                nodes.extend(v)
            return nodes

    def getUsedNodes(self, projectNodes, filename='', onlyInfos=False, infotag=''):
        nodes = []
        for bt in self.__branches:
            uid = self.__branches[bt]
            if uid in projectNodes:
                node = projectNodes[uid]
                if not filename or node.path() == filename:
                    nodes = self.__getUsedNodes(node, nodes, onlyInfos, infotag)
        return nodes

    def __getUsedNodes(self, node, all_nodes, onlyInfos=False, infotag=''):
        desc = node.nodeDesc()
        cls = node.cls()
        if not onlyInfos or (cls is not None and cls.infoTag and (not infotag or cls.infoTag == infotag)):
            if desc is not None and desc not in all_nodes:
                all_nodes.append(desc)
        children = node.allChildren()
        for c in children:
            for child in children[c]:
                all_nodes = self.__getUsedNodes(child, all_nodes, onlyInfos, infotag)
        return all_nodes

    def getFilesList(self, projectNodes):
        files = []
        for t in self.__branches:
            uid = self.__branches[t]
            if uid in projectNodes:
                node = projectNodes[uid]
                if node.path() not in files and node.path():
                    files.append(node.path())
        return files

    def getBranchesByFile(self, filename, projectNodes):
        branches = dict()
        for t in self.__branches:
            uid = self.__branches[t]
            if uid in projectNodes:
                node = projectNodes[uid]
                if node.path() == filename:
                    branches[t] = node
        return branches

    def getUsedLibs(self, projectNodes):
        libraries = []
        for br in self.__branches:
            uid = self.__branches[br]
            if uid in projectNodes:
                node = projectNodes[uid]
                libs = node.getUsedLibraries()
                for lib in libs:
                    if lib not in libraries:
                        libraries.append(lib)
        return libraries

    # Returns branches who are using node with name == 'nodeName'
    def getBranchesByNode(self, libraryName, nodeName, projectNodes):
        branches = dict()
        for t in self.__branches:
            uid = self.__branches[t]
            if uid in projectNodes:
                node = projectNodes[uid]
                if (libraryName, nodeName) in node:
                    branches[t] = node
        return branches

    # Returns branches who are using library with name == 'libraryName'
    def getBranchesByLibrary(self, libraryName, projectNodes):
        branches = dict()
        for t in self.__branches:
            uid = self.__branches[t]
            if uid in projectNodes:
                node = projectNodes[uid]
                libs = node.getUsedLibraries()
                if libraryName in libs:
                    branches[t] = node
        return branches

    # Get branch dependancies
    def getDependantsOf(self, fullname, projectNodes):
        uid = self.get(fullname)
        if uid is not None and uid in projectNodes:
            return self.__getDependantsOf(projectNodes[uid])
        return []

    # Get list of branches who depends on this branch
    def whoDependsOn(self, fullname, projectNodes):
        dependands = []
        uid = self.get(fullname)
        if uid is not None and uid in projectNodes:
            for br in self.__branches:
                if br == fullname:
                    continue
                curr_uid = self.__branches[br]
                if curr_uid in projectNodes:
                    curr = projectNodes[curr_uid]
                    if curr.dependsOn(fullname):
                        dependands.append(br)
        return dependands

    def empty(self):
        return not self.__branches

    def __getDependantsOf(self, branch):
        branchType = branch.type()
        if branchType.isLink() or branch.nodeDesc() is None:
            return []

        dependsOn = []

        ccc = []
        for c in branch.allChildren():
            if c in branch.nodeDesc().childClasses and c in branchType:
                ccc.append(c)
        ccc.sort()
        for c in ccc:
            cls = branch.Project.alphabet.getClass(c)
            if cls is not None and cls.linkTag:
                max_children = branchType.child(c).max
                if max_children < 1:
                    continue
                num_children = 0
                children = branch.children(c)
                for child in children:
                    if child.type().isLink():
                        if child.target not in dependsOn:
                            dependsOn.append(child.target)
                    else:
                        childDependands = self.__getDependantsOf(child)
                        if childDependands:
                            for d in childDependands:
                                if d not in dependsOn:
                                    dependsOn.append(d)
                    num_children += 1
                    if num_children >= max_children:
                        break
        return dependsOn

    def __recursiveRename(self, branch, oldname, newname):
        for c in branch.allChildren():
            children = branch.allChildren()[c]
            for child in children:
                if child.type().isLink():
                    if child.target == oldname:
                        child.target = newname
                else:
                    self.__recursiveRename(child, oldname, newname)

#######################################################################################################################
#######################################################################################################################

