# coding=utf-8
# -----------------
# file      : liparser.py
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

import os
from xml.dom.minidom import parse
from lxml import etree

from auxtypes import processString, toUnixPath

import treenode

import globals

#######################################################################################################################
#######################################################################################################################


class LibParser(object):
    def __init__(self):
        self.__outer = dict()
        self.__shapeLib = None
        self.__alphabet = None

    def load(self, alphabet, files, libs=None, shapes=None):
        libraries = dict()
        if alphabet is not None or alphabet.numElems('', True) > 0:
            self.__alphabet = alphabet
            self.__shapeLib = shapes
            if libs is not None:
                self.__outer = libs

            if isinstance(files, list):
                self.__loadLibraries(libraries, files, '../')
            elif isinstance(files, str) or isinstance(files, str):
                self.__loadLibrary(libraries, files)

            self.__outer = dict()
            self.__shapeLib = None
            self.__alphabet = None
        return libraries

    def save(self, alphabet, libraries):
        print('')
        print('info: Saving all node libraries...')
        if alphabet is None:
            print('error: alphabet is None!')
            print('')
            return
        self.__alphabet = alphabet
        libsByFile = dict()
        for libname in libraries:
            lib = libraries[libname]
            if lib.path() not in libsByFile:
                libsByFile[lib.path()] = [lib]
            else:
                libsByFile[lib.path()].append(lib)
        for f in libsByFile:
            self.__saveLibraryFile(f, libsByFile[f])
        self.__alphabet = None
        print('')

    def __loadLibraries(self, libraries, files, caller=None):
        num_loaded = 0
        for filename in files:
            if os.path.isabs(filename):
                num_loaded += self.__loadLibrary(libraries, filename)
            else:
                if caller is None:
                    abspath = os.path.abspath(filename)
                    num_loaded += self.__loadLibrary(libraries, abspath)
                else:
                    caller_dir = os.path.dirname(caller)
                    f = [caller_dir, filename]
                    realpath = '/'.join(f)
                    num_loaded += self.__loadLibrary(libraries, realpath)
        print('')
        return num_loaded

    def __loadLibrary(self, libraries, filename):
        if not filename:
            return 0

        print('info: Parsing \"{0}\" ...'.format(filename))
        dom = parse(filename)
        data = dom.getElementsByTagName(self.__alphabet.headerLibrary)

        if not data:
            data = dom.getElementsByTagName('libraries')
            if not data:
                print('error: Wrong library file! It has no tags \'{0}\' and \'libraries\'.'
                      .format(self.__alphabet.headerLibrary))
                print('')
                return 0

        filename = toUnixPath(os.path.normpath(os.path.abspath(filename)))
        libs = data[0].getElementsByTagName('library')
        libs.extend(data[0].getElementsByTagName('Library'))
        outerlibs = data[0].getElementsByTagName('include')
        num_loaded = 0

        # Loading libraries:
        for lib in libs:
            library = self.__parseLib(libraries, lib)
            if library is not None:
                library.setPath(filename)
                libraries[library.libname] = library
                num_loaded += 1

        # Reading external files:
        if outerlibs:
            libpaths = []
            for outer in outerlibs:
                libpaths.append(outer.getAttribute('path'))
            num_loaded += self.__loadLibraries(libraries, libpaths, filename)

        if num_loaded == 0:
            print('WARNING: No libraries found!')
            print('')

        return num_loaded

    def __parseLib(self, libraries, lib):
        if lib.hasAttribute('name'):
            libname = lib.getAttribute('name')
        elif lib.hasAttribute('Name'):
            libname = lib.getAttribute('Name')
        else:
            libname = ''

        if not libname:
            print('error: each library must have attribute \"name\"!')
            return None

        if libname in libraries or libname in self.__outer:
            print('warning: Library \"{0}\" is already exists!'.format(libname))
            return None

        newLib = treenode.NodeLibrary(libname)

        nodes = lib.getElementsByTagName('node')
        nodes.extend(lib.getElementsByTagName('Node'))
        if not nodes:
            print('warning: Library \"{0}\" is empty!'.format(libname))
            return newLib

        loadres = False
        for node in nodes:
            if self.__parseNode(newLib, node) is True:
                loadres = True

        if loadres is True:
            print('ok: Library \"{0}\" is loaded!'.format(libname))
        else:
            print('error: Failed to load nodes for library \"{0}\".'.format(libname))
            print('warning: Library \"{0}\" is empty!'.format(libname))

        return newLib

    def __parseNode(self, lib, node):
        nodeClass = ''
        if node.hasAttribute('class'):
            nodeClass = node.getAttribute('class')
        elif node.hasAttribute('Class'):
            nodeClass = node.getAttribute('Class')

        if nodeClass not in self.__alphabet:
            print('error: there are no class \"{0}\" in current alphabet!'.format(nodeClass))
            return False

        cls = self.__alphabet[nodeClass]

        nodeType = ''
        if node.hasAttribute('type'):
            nodeType = node.getAttribute('type')
        elif node.hasAttribute('Type'):
            nodeType = node.getAttribute('Type')

        subType = cls.get(nodeType)
        if subType is None:
            print('error: class \"{0}\" have no type \"{1}\".'.format(cls.name, nodeType))
            return False

        if node.hasAttribute('name'):
            name = node.getAttribute('name')
        elif node.hasAttribute('Name'):
            name = node.getAttribute('Name')
        else:
            name = ''

        if not name:
            print('error: each node must have name!')
            return False
        if name in lib:
            print('warning: node with name \"{0}\" is already exists.'.format(name))
            return False

        if cls.debuggable:
            if node.hasAttribute('debugDefault'):
                dbg = node.getAttribute('debugDefault').lower()
            elif node.hasAttribute('DebugDefault'):
                dbg = node.getAttribute('DebugDefault').lower()
            else:
                dbg = 'no'
            if dbg in ('yes', '1', 'true'):
                defaultDebugState = True
            else:
                defaultDebugState = False
        else:
            defaultDebugState = False

        newNode = treenode.TreeNodeDesc(name, nodeClass, nodeType, lib.libname, defaultDebugState)

        if node.hasAttribute('creator'):
            newNode.creator = node.getAttribute('creator')

        children = node.getElementsByTagName('children')
        children.extend(node.getElementsByTagName('Children'))
        for child in children:
            if child.hasAttribute('class'):
                ch_cls = child.getAttribute('class')
            elif child.hasAttribute('Class'):
                ch_cls = child.getAttribute('Class')
            else:
                ch_cls = ''
            if ch_cls not in self.__alphabet or ch_cls in newNode.childClasses:
                continue
            if child.hasAttribute('use'):
                useStr = child.getAttribute('use').lower()
            elif child.hasAttribute('Use'):
                useStr = child.getAttribute('Use').lower()
            else:
                useStr = 'no'
            if useStr in ('yes', '1', 'true'):
                newNode.childClasses.append(ch_cls)
        newNode.childClasses.sort()

        # Loading node description:---------
        if node.getElementsByTagName('description'):
            descrTag = node.getElementsByTagName('description')[0]
        elif node.getElementsByTagName('Description'):
            descrTag = node.getElementsByTagName('Description')[0]
        else:
            descrTag = None
        if descrTag is not None:
            if descrTag.hasAttribute('text'):
                descr = descrTag.getAttribute('text')
            elif descrTag.hasAttribute('Text'):
                descr = descrTag.getAttribute('Text')
            else:
                descr = ''
            if descr:
                newNode.description = processString(descr)

        # Loading node shape:---------
        if self.__shapeLib is not None:
            shapeName = ''
            if node.getElementsByTagName('shape'):
                shapeTag = node.getElementsByTagName('shape')[0]
            elif node.getElementsByTagName('Shape'):
                shapeTag = node.getElementsByTagName('Shape')[0]
            else:
                shapeTag = None
            if shapeTag is not None:
                if shapeTag.hasAttribute('name'):
                    shapeName = shapeTag.getAttribute('name')
                elif shapeTag.hasAttribute('Name'):
                    shapeName = shapeTag.getAttribute('Name')
            if shapeName in self.__shapeLib:
                newNode.shape = self.__shapeLib[shapeName]
                color = cls.defaultState().colorEnabled
                newNode.icon = newNode.shape.icon(color)

        # Loading node attributes:-------
        attrs = node.getElementsByTagName('attribute')
        attrs.extend(node.getElementsByTagName('Attribute'))
        for attr in attrs:
            newAttr = self.__parseAttr(newNode, attr, False)
            if newAttr is not None:
                newNode.addAttribute(newAttr)

        attrs = node.getElementsByTagName('array')
        attrs.extend(node.getElementsByTagName('Array'))
        for attr in attrs:
            newAttr = self.__parseAttr(newNode, attr, True)
            if newAttr is not None:
                newNode.addAttribute(newAttr)

        attrs = node.getElementsByTagName('dynamic_attribute')
        for attr in attrs:
            newAttr = self.__parseDynamicAttr(newNode, attr, False)
            if newAttr is not None:
                newNode.addAttribute(newAttr)

        attrs = node.getElementsByTagName('dynamic_array')
        for attr in attrs:
            newAttr = self.__parseDynamicAttr(newNode, attr, True)
            if newAttr is not None:
                newNode.addAttribute(newAttr)

        # Loading events:-------------------
        eventsElems = node.getElementsByTagName('events')
        for eventElem in eventsElems:
            incomingEvents = eventElem.getElementsByTagName('incoming')
            outgoingEvents = eventElem.getElementsByTagName('outgoing')
            for ev in incomingEvents:
                if ev.hasAttribute('name'):
                    evname = ev.getAttribute('name')
                    if not evname:
                        print('warning: node with name \"{0}\" has events without name!'.format(name))
                    if evname not in newNode.incomingEvents:
                        newNode.incomingEvents.append(evname)
                else:
                    print('warning: node with name \"{0}\" has events without name!'.format(name))
            for ev in outgoingEvents:
                if ev.hasAttribute('name'):
                    evname = ev.getAttribute('name')
                    if not evname:
                        print('warning: node with name \"{0}\" has events without name!'.format(name))
                    if evname not in newNode.outgoingEvents:
                        newNode.outgoingEvents.append(evname)
                else:
                    print('warning: node with name \"{0}\" has events without name!'.format(name))

        # Saving node:-------------------
        lib.insert(newNode)

        return True

    def __parseAttr(self, node, attr, isArray, externalName=None, externalDescription=None):
        """ Parse xml-node 'attribute' or 'array' """

        if externalName is not None and externalName:
            name = externalName
        elif attr.hasAttribute('name'):
            name = attr.getAttribute('name')
        elif attr.hasAttribute('Name'):
            name = attr.getAttribute('Name')
        else:
            name = ''

        strings = name.split('/')
        if not strings:
            print('error: Wrong attribute name \"{0}\" for node \"{1}\". It must contain at least one character. \
                Attribute will not be loaded!'.format(name, node.name))
            return None

        if not strings[-1]:
            print('error: Wrong attribute name \"{0}\" (full name is \"{1}\") for node \"{2}\". \
                It must contain at least one character. Attribute will not be loaded!'
                  .format(strings[-1], name, node.name))
            return None

        if attr.hasAttribute('type'):
            atype = attr.getAttribute('type').lower()
        elif attr.hasAttribute('Type'):
            atype = attr.getAttribute('Type').lower()
        else:
            atype = ''

        if atype not in treenode.TYPE_INFO_ALIAS:
            print('error: Attribute type \"{0}\" is not allowed! Attribute \"{1}\" for node \"{2}\" \
                will not be loaded!'.format(atype, name, node.name))
            return None

        atype = treenode.TYPE_INFO_ALIAS[atype]

        if attr.hasAttribute('description'):
            desc = attr.getAttribute('description')
            desc = processString(desc)
        elif attr.hasAttribute('Description'):
            desc = attr.getAttribute('Description')
            desc = processString(desc)
        elif externalDescription is not None:
            desc = externalDescription
        else:
            desc = ''

        newAttr = treenode.NodeAttrDesc(name, atype, isArray)
        newAttr.description = desc

        if newAttr.typeName() != atype:
            print('warning: Attribute type \"{0}\" changed to \"{1}\"! See attribute \"{2}\" in node \"{3}\"'
                  .format(atype, newAttr.typeName(), name, node.name))

        if not newAttr.subtags and isArray:
            print('error: There are no sub-tags for array \"{0}\" in node \"{1}\"! (Require at least 1 sub-tag) \
                Attribute \"{0}\" will not be loaded!'.format(name, node.name))
            return None

        if attr.hasAttribute('default'):
            defaultValue = attr.getAttribute('default')
        elif attr.hasAttribute('Default'):
            defaultValue = attr.getAttribute('Default')
        else:
            defaultValue = ''

        if attr.hasAttribute('available'):
            vals = attr.getAttribute('available')
        elif attr.hasAttribute('Available'):
            vals = attr.getAttribute('Available')
        else:
            vals = ''

        if vals:
            vals = vals.split(';')
            availableValues = []
            for v in vals:
                if not v:
                    continue
                if '|' in v:
                    value_and_text = v.split('|', 1)
                    if len(value_and_text) > 1:
                        text = value_and_text[1]
                        if '|' in text:
                            text_and_hint = text.split('|', 1)
                            text = text_and_hint[0]
                            hint = text_and_hint[1]
                        else:
                            hint = ''
                        availableValues.append((value_and_text[0], text, hint))
                    else:
                        availableValues.append((value_and_text[0], '', ''))
                else:
                    availableValues.append((v, '', ''))
            newAttr.setAvailableValuesByText(availableValues)

        if not newAttr.availableValues():
            if attr.hasAttribute('min'):
                minValue = attr.getAttribute('min')
            elif attr.hasAttribute('Min'):
                minValue = attr.getAttribute('Min')
            else:
                minValue = None
            if minValue is not None:
                newAttr.setMin(minValue)

            if attr.hasAttribute('max'):
                maxValue = attr.getAttribute('max')
            elif attr.hasAttribute('Max'):
                maxValue = attr.getAttribute('Max')
            else:
                maxValue = None
            if maxValue is not None:
                newAttr.setMax(maxValue)

        if defaultValue:
            newAttr.setDefaultValue(defaultValue)

        return newAttr

    def __parseDynamicAttr(self, node, attr, isArray):
        """
        Parse xml-node 'dynamic_attribute' or 'dynamic_array'
        """

        if attr.hasAttribute('name'):
            name = attr.getAttribute('name')
        elif attr.hasAttribute('Name'):
            name = attr.getAttribute('Name')
        else:
            name = ''

        strings = name.split('/')
        if not strings:
            print('error: Dynamic attribute wrong name \"{0}\" for node \"{1}\". It must contain \
                at least one character. Dynamic attribute will not be loaded!'.format(name, node.name))
            return None

        if not strings[-1]:
            print('error: Dynamic attribute wrong name \"{0}\" (full name is \"{1}\") for node \"{2}\". \
                    It must contain at least one character. Dynamic attribute will not be loaded!'
                  .format(strings[-1], name, node.name))
            return None

        if attr.hasAttribute('depend_on'):
            control = attr.getAttribute('depend_on')
        else:
            control = ''

        if not control:
            print('error: Dynamic attribute \"{0}\" for node \"{1}\" have no dependency. \
                    Please, fill xml-attribute \"depend_on\". Dynamic attribute will not be loaded!'
                  .format(name, node.name))
            return None

        if control not in node:
            print('error: No dependent attribute \"{0}\" in node \"{1}\" for dynamic attribute \"{2}\". \
                  Dynamic attribute will not be loaded!'.format(control, node.name, name))
            return None

        dependentAttr = node[control]
        default = dependentAttr.value2str(dependentAttr.defaultValue())
        print('debug: Default key for dynamic attribute \'{0}\' of node \'{1}\' will be \'{2}\''
              .format(name, node.name, default))

        if attr.hasAttribute('description'):
            desc = attr.getAttribute('description')
            desc = processString(desc)
        elif attr.hasAttribute('Description'):
            desc = attr.getAttribute('Description')
            desc = processString(desc)
        else:
            desc = ''

        newDynamicAttr = treenode.DynamicAttrDesc(name, desc, isArray, control, default)

        if not newDynamicAttr.subtags and isArray:
            print('error: There are not sub-tags for dynamic attribute array \"{0}\" for node \"{1}\". \
                    Arrays require at least 1 sub-tag! Dynamic attribute will not be loaded!'
                  .format(name, node.name))
            return None

        units = attr.getElementsByTagName('unit')
        for unit in units:
            newAttr = self.__parseAttr(node, unit, isArray, name, desc)
            if newAttr is not None:
                if unit.hasAttribute('keys'):
                    key = unit.getAttribute('keys')
                    keys = key.split(';')
                    while len(keys) > 1 and not keys[-1]:
                        keys.pop()
                    if not keys:
                        keys.append('')
                else:
                    keys = ['']
                newDynamicAttr.addAttribute(newAttr, keys)

        if newDynamicAttr.empty():
            print('error: There are no units for dynamic attribute \"{0}\" of node \"{1}\"! \
                    Dynamic attribute \"{0}\" will not be loaded!'.format(name, node.name))
            return None

        newDynamicAttr.correctDefault()

        return newDynamicAttr

    def __saveLibraryFile(self, filePath, libs):
        if not libs:
            return

        # add main xml tag inside document
        root = etree.Element(self.__alphabet.headerLibrary)
        root.set('version', globals.strVersion)

        separator = ' ==========================================================' \
                    '============================================================ '

        if libs:
            for lib in sorted(libs, key=lambda x: x.name()):
                root.append(etree.Comment(separator))
                self.__saveLibrary(root, lib)
            root.append(etree.Comment(separator))

        # saving xml document to file
        f = open(filePath, 'wb')
        f.write(etree.tostring(root, encoding='utf-8', pretty_print=True, xml_declaration=True, with_comments=True))
        # f.write(doc.toprettyxml('\t', '\n', 'utf-8'))
        f.close()

        print('ok: Library file \'{0}\' is saved!'.format(filePath))

    def __saveLibrary(self, root, library):
        lib = etree.SubElement(root, 'library')
        lib.set('name', library.name())

        separator = ' *************************************************' \
                    '******************************************************** '

        count = 0
        # saving "top" classes first (those who can be used as top nodes in behavior tree)
        for isTop in (True, False):
            all_classes = self.__alphabet.getClasses(top=isTop)
            for cls in sorted(all_classes):
                nodes = library.getAll(cls)
                if nodes:
                    count += 1
                    lib.append(etree.Comment(separator))
                    lib.append(etree.Comment(' {0}S '.format(cls.upper())))
                    for n in sorted(nodes.keys()):
                        self.__saveNode(lib, nodes[n])
                        lib.append(etree.Comment(''))

        if count > 0:
            lib.append(etree.Comment(separator))

    def __saveNode(self, lib, treeNode):
        node = etree.SubElement(lib, 'node')

        node.set('class', treeNode.nodeClass)
        node.set('type', treeNode.nodeType)
        node.set('name', treeNode.name)

        if treeNode.creator:
            node.set('creator', treeNode.creator)

        if treeNode.debugByDefault:
            node.set('debugDefault', 'yes')

        # save 'children' tag
        # saving "top" classes first (those who can be used as top nodes in behavior tree)
        for isTop in (True, False):
            all_classes = self.__alphabet.getClasses(top=isTop)
            for cls in sorted(all_classes):
                child = etree.SubElement(node, 'children')
                child.set('class', cls)
                if cls in treeNode.childClasses:
                    child.set('use', 'yes')
                else:
                    child.set('use', 'no')

        # save 'description' tag
        description = etree.SubElement(node, 'description')
        description.set('text', treeNode.description.replace('\n', ' \\n '))

        # save 'shape' tag
        shape = etree.SubElement(node, 'shape')
        if treeNode.shape is not None:
            shape.set('name', treeNode.shape.name())
        else:
            shape.set('name', '')

        # save 'icon' tag (deprecated)
        # if treeNode.icon:
        # 	icon = etree.SubElement(node, u'icon')
        # 	icon.set(u'path', treeNode.icon)

        # save events
        events = etree.SubElement(node, 'events')
        if treeNode.incomingEvents:
            for eventName in treeNode.incomingEvents:
                ev = etree.SubElement(events, 'incoming')
                ev.set('name', eventName)
        if treeNode.outgoingEvents:
            for eventName in treeNode.outgoingEvents:
                ev = etree.SubElement(events, 'outgoing')
                ev.set('name', eventName)

        attributes = treeNode.attributes()

        # build lists of attributes by type
        regularAttributes = []
        arrayAttributes = []
        dynamicAttributes = []
        dynamicArrayAttributes = []

        # use sorted by name attributes - this prevents from libs difference on every application launch
        for a in sorted(attributes.keys()):
            attribute = attributes[a]
            if not attribute.isDynamic():
                if not attribute.isArray():
                    regularAttributes.append(a)
                else:
                    arrayAttributes.append(a)
            else:
                if not attribute.isArray():
                    dynamicAttributes.append(a)
                else:
                    dynamicArrayAttributes.append(a)

        # save regular attributes
        for a in regularAttributes:
            attribute = attributes[a]
            attr = etree.SubElement(node, 'attribute')
            self.__saveAttribute(attr, attribute)

        # save regular arrays of attributes
        for a in arrayAttributes:
            attribute = attributes[a]
            attr = etree.SubElement(node, 'array')
            self.__saveAttribute(attr, attribute)

        # save dynamic attributes
        for a in dynamicAttributes:
            attribute = attributes[a]
            attr = etree.SubElement(node, 'dynamic_attribute')
            self.__saveAttributeDynamic(attr, attribute)

        # save arrays of dynamic attributes
        for a in dynamicArrayAttributes:
            attribute = attributes[a]
            attr = etree.SubElement(node, 'dynamic_array')
            self.__saveAttributeDynamic(attr, attribute)

    def __saveAttribute(self, attr, attribute):
        attr.set('type', attribute.typeName())
        attr.set('name', attribute.name(True))
        self.__saveAttributeData(attr, attribute, False)
        attr.set('description', attribute.description.replace('\n', ' \\n '))

    def __saveAttributeData(self, attr, attribute, saveType=True):
        if saveType:
            attr.set('type', attribute.typeName())

        typedata = attribute.typeInfo()

        if typedata is None:
            saveDefault = True
            saveMin = (attribute.minValue() is not None)
            saveMax = (attribute.maxValue() is not None)
        else:
            saveDefault = (attribute.defaultValue() != typedata.default)
            if attribute.minValue() is not None \
                    and (typedata.minValue is None or attribute.minValue() != typedata.minValue):
                saveMin = True
            else:
                saveMin = False
            if attribute.maxValue() is not None \
                    and (typedata.maxValue is None or attribute.maxValue() != typedata.maxValue):
                saveMax = True
            else:
                saveMax = False

        if saveDefault:
            attr.set('default', attribute.value2str2(attribute.defaultValue()))
        if saveMin:
            attr.set('min', attribute.value2str2(attribute.minValue()))
        if saveMax:
            attr.set('max', attribute.value2str2(attribute.maxValue()))

        avail = attribute.availableValuesXml()
        if avail:
            attr.set('available', avail)

    def __saveAttributeDynamic(self, attr, attribute):
        attr.set('name', attribute.fullname)
        attr.set('depend_on', attribute.controlAttribute)
        attr.set('description', attribute.description.replace('\n', ' \\n '))

        keysByUnit = {}
        units = attribute.units()
        for key in units:
            if not key:
                continue
            unit = units[key]
            if unit not in keysByUnit:
                keysByUnit[unit] = [key]
            else:
                keysByUnit[unit].append(key)

        # sort keys alphabetically - this prevents from libs difference on every application launch
        for unit in keysByUnit:
            keysByUnit[unit].sort()

        # save units in alphabetical order too - this prevents from libs difference on every application launch
        sorted_attributes = sorted(keysByUnit.keys(), key=lambda x: x.typeName())
        for unit_attribute in sorted_attributes:
            u = etree.SubElement(attr, 'unit')
            keys = ';'.join(keysByUnit[unit_attribute])
            u.set('keys', keys)
            self.__saveAttributeData(u, unit_attribute)

#######################################################################################################################
#######################################################################################################################
