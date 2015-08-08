# coding=utf-8
# -----------------
# file      : treeparser.py
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
from xml.dom.minidom import parse, Document

from auxtypes import processString, toUnixPath

import treenode
from treeview.dispregime import DisplayRegime
from PySide.QtCore import QPointF

import globals


def fullTreeName(path, name):
    return '{0}/{1}'.format(path, name)


_versionWithUids = (1, 2)  # first Behavior Studio version with nodes' uids

#######################################################################################################################
#######################################################################################################################


class TreeParser(object):
    __debug_str = ('debug', 'Debug', 'DEBUG')

    def __init__(self):
        pass

    def load(self, files, project):
        bt = treenode.BehaviorTree()
        nodes = treenode.TreeNodes()

        if project is None or project.alphabet is None:
            return bt, nodes, []

        if isinstance(files, list):
            n, treesFiles = self.__loadTrees(project, bt, nodes, files, '../')
        elif isinstance(files, str) or isinstance(files, str):
            n, treesFiles = self.__loadTree(project, bt, nodes, files)
        else:
            treesFiles = []

        return bt, nodes, treesFiles

    def save(self, alphabet, trees, nodes, files):
        res = False
        for filename in files:
            res = self.__saveFile(alphabet, trees, nodes, filename) or res
        return res

    # Check if specified tree exists in specified file
    def check(self, filename, treename):
        if not filename:
            return False

        if not os.path.exists(filename):
            return False

        print('info: Parsing \"{0}\" ...'.format(filename))
        dom = parse(filename)
        data = dom.getElementsByTagName('BehaviorTree')

        if not data:
            return False

        nodes = data[0].getElementsByTagName('Node')

        if not nodes:
            return False

        for node in nodes:
            ref = node.getAttribute('BranchName')
            if ref is not None and ref == treename:
                return True

        return False

    # Load several trees
    # files - list of xml-files
    # caller - path to main xml-file (initiator of this load)
    def __loadTrees(self, project, bt, nodes, files, caller=None):
        num_loaded = 0
        goodFiles = []
        for filename in files:
            if os.path.isabs(filename):
                #print 'INFO: absolute path is given for file \"{0}\"'.format(filename)
                res = self.__loadTree(project, bt, nodes, filename)
                num_loaded += res[0]
                if res[1]:
                    goodFiles.append(res[1][0])
            else:
                print('INFO: path to file \"{0}\" is relative! Searching for absolute path ...'.format(filename))
                if caller is None:
                    abspath = os.path.abspath(filename)
                    print('INFO: trying to load from current script dir... path is \"{0}\"'.format(abspath))
                    res = self.__loadTree(project, bt, nodes, abspath)
                    num_loaded += res[0]
                    if res[1]:
                        goodFiles.append(res[1][0])
                else:
                    realpath = '/'.join([os.path.dirname(caller), filename])
                    print('INFO: abs path found: \"{0}\"'.format(realpath))
                    res = self.__loadTree(project, bt, nodes, realpath)
                    num_loaded += res[0]
                    if res[1]:
                        goodFiles.append(res[1][0])

        return num_loaded, goodFiles

    # Load tree from xml-file
    def __loadTree(self, project, bt, nodes, filename):
        global _versionWithUids

        if not filename:
            return 0, []

        filename = toUnixPath(os.path.normpath(filename))

        print('info: Parsing \"{0}\" ...'.format(filename))
        dom = parse(filename)
        data = dom.getElementsByTagName(project.alphabet.headerTree)

        if not data:
            print('error: Wrong tree file!')
            print('')
            return 0, []

        mainNode = data[0]

        if mainNode.hasAttribute('Version'):
            versionText = mainNode.getAttribute('Version')
        elif mainNode.hasAttribute('version'):
            versionText = mainNode.getAttribute('version')
        else:
            versionText = ''

        if not versionText or '.' not in versionText:
            version = tuple(_versionWithUids)
            versionText = globals.versionToStr(version)
            print('info: File has no version. Default it to {0}'.format(versionText))
        else:
            version = globals.versionFromStr(versionText)
            print('info: File version is {0}'.format(versionText))

        # trying to read diagram file with saved diagram items positions:
        fname, _ = os.path.splitext(filename)
        diagram_file = fname + '.dgm'
        if os.path.exists(diagram_file):
            diagramData = parse(diagram_file).getElementsByTagName(project.alphabet.headerTree)
            if not diagramData:
                mainDiagramNode = None
            else:
                mainDiagramNode = diagramData[0]
        else:
            mainDiagramNode = None

        # getting all tags for main classes:
        xmlNodes = dict()
        topClasses = project.alphabet.getClasses(True)
        for t in topClasses:
            cls = project.alphabet.getClass(t)
            xml_nodes = mainNode.getElementsByTagName(cls.tag)
            if xml_nodes and cls.tag not in xmlNodes:
                if mainDiagramNode is not None:
                    diagramNodes = mainDiagramNode.getElementsByTagName(cls.tag)
                else:
                    diagramNodes = None
                xmlNodes[cls.tag] = [cls.name, xml_nodes, diagramNodes]
            # nodes = data[0].getElementsByTagName('Node')

        num_loaded = 0

        if not xmlNodes:  # not nodes:
            print('warning: Tree \"{0}\" is empty!'.format(filename))
            return 0, [filename]

        for tag in xmlNodes:
            cls = project.alphabet.getClass(xmlNodes[tag][0])
            xml_nodes = xmlNodes[tag][1]
            diagNodes = xmlNodes[tag][2]
            i = 0
            for xml_node in xml_nodes:
                if xml_node.parentNode is mainNode:
                    if diagNodes is not None and i < len(diagNodes) and diagNodes[i].parentNode is mainDiagramNode:
                        diagramNode = diagNodes[i]
                    else:
                        diagramNode = None
                    newNode = self.__parseNode(version, project, bt, nodes, filename, cls, xml_node, None, diagramNode)
                    if newNode is not None:
                        num_loaded += 1
                i += 1

        if num_loaded < 1:
            print('warning: no trees were loaded!')

        print('ok: Parsing complete.')
        print('')

        return num_loaded, [filename]

    # Loading node
    def __parseNode(self, version, project, bt, nodes, currFile, cls, node, parent, diagramNode):
        global _versionWithUids

        if node.hasAttribute('Name'):
            name = node.getAttribute('Name')
        else:
            name = ''

        if not name:
            print('ERROR: Each node requires tag \"Name\"!')
            return None

        if node.hasAttribute('Type'):
            nodeType = node.getAttribute('Type')
        else:
            nodeType = ''

        if not nodeType:
            print('ERROR: Each node requires tag \"Type\"!')
            return None

        strings = nodeType.split(' ')
        nodeType = strings[-1]

        if nodeType not in cls:
            print('error: Type \"{0}\" is not specified for class \"{1}\".'.format(nodeType, cls.name))
            return None

        # read diagram info:
        diagramInfo, diagramUid = self.__readDiagramInfo(diagramNode)

        isInverse = False
        if '!' in name or '~' in name:
            isInverse = True
            name = name.replace('!', '')
            name = name.replace('~', '')
            name = name.strip()

        # Checking for debug usage:
        isDebug = False
        if len(strings) > 1 and cls.debuggable and strings[0] in self.__debug_str:
            isDebug = True

        # Checking for single-block:
        isSingleBlock = False
        if node.hasAttribute('singleBlock'):
            sb = node.getAttribute('singleBlock').lower()
            if sb not in ('0', 'no', 'false'):
                isSingleBlock = True

        # Getting uid for node:
        if node.hasAttribute('uid'):
            u = node.getAttribute('uid')
            if u:
                uid = int(u)
            else:
                uid = None
        else:
            uid = None

        subType = cls.get(nodeType)

        if subType.isLink():
            isSingleBlock = False
            target = ''
            if node.hasAttribute(subType.targetTag()):
                target = node.getAttribute(subType.targetTag())
            if not target:
                print('error: All links must have target! (tag <{0}> is missing)'.format(subType.targetTag()))
                return None

            filename = ''
            if node.hasAttribute('File'):
                filename = node.getAttribute('File')
                if not os.path.isabs(filename):
                    realpath = '/'.join([os.path.dirname(currFile), filename])
                    filename = os.path.normpath(os.path.abspath(realpath))
                filename = toUnixPath(filename)
                if not os.path.exists(filename):
                    filename = ''
            if not filename:
                filename = currFile

            branchRef = fullTreeName(filename, target)
            if branchRef in bt or branchRef in project.trees:
                newNode = treenode.TreeNode(project, node, cls.name, nodeType, isDebug, uid)
                newNode.target = branchRef
                newNode.setPath(currFile)
                if diagramUid == newNode.uid() or version < _versionWithUids:
                    newNode.diagramInfo = diagramInfo

                if newNode.uid() in nodes:
                    print('error: Node with uid \"{0}\" already exist in current file!'.format(newNode.uid()))
                    return None

                if newNode.uid() in project.nodes:
                    print('error: Node with uid \"{0}\" already exist in current project!'.format(newNode.uid()))
                    return None

                nodes.add(newNode, False)
                return newNode

            print('error: Link to \"{0}\" is not found neither in file \"{1}\" nor in current project!'
                  .format(target, filename))
            return None

        elif not subType.singleblockEnabled:
            isSingleBlock = False

        if node.hasAttribute(cls.lib):
            libname = node.getAttribute(cls.lib)
        else:
            libname = ''

        if not libname:
            print('error: Each \"{0}\" node requires tag \"{1}\"!'.format(cls.name, cls.lib))
            return None

        newNode = treenode.TreeNode(project, node, cls.name, nodeType, isDebug, uid)

        if newNode.uid() in nodes:
            print('error: Node with uid \"{0}\" already exist in current file!'.format(newNode.uid()))
            return None

        if newNode.uid() in project.nodes:
            print('error: Node with uid \"{0}\" already exist in current project!'.format(newNode.uid()))
            return None

        nodes.add(newNode, False)

        newNode.setSingleblock(isSingleBlock)
        newNode.setLibName(libname)
        newNode.setNodeName(name)
        newNode.setPath(currFile)
        if diagramUid == newNode.uid() or version < _versionWithUids:
            newNode.diagramInfo = diagramInfo
        if isInverse:
            newNode.setInverse(isInverse)

        # Read branch name:--------------------------------------------------------------
        if cls.top:
            if node.hasAttribute(cls.linkTag):
                ref = node.getAttribute(cls.linkTag)
            else:
                ref = ''

            if ref:
                branchRef = fullTreeName(currFile, ref)
                if branchRef in bt:
                    print('error: Branch with name \"{0}\" already exist in current file! See node with uid=\"{1}\"'
                          .format(ref, newNode.uid()))
                    nodes.remove(newNode, False)
                    return None
                if branchRef in project.trees:
                    print('error: Branch with name \"{0}\" already exist in current project! See node with uid=\"{1}\"'
                          .format(ref, newNode.uid()))
                    nodes.remove(newNode, False)
                    return None
                newNode.setRefName(ref)
            elif parent is None:
                print('error: Root nodes requires link tag \"{0}\"! Wrong node is \"{1}\" with uid=\"{2}\".'
                      .format(cls.linkTag, name, newNode.uid()))
                nodes.remove(newNode, False)
                return None

        # Loading node settings:----------------------------------------------------
        newNode.setParent(parent)
        newNode.reparseAttributes(True)

        # Load child nodes:---------------------------------------------------------
        for chldCls in subType.children:
            childParams = subType.children[chldCls]
            childClass = project.alphabet.getClass(chldCls)
            if childClass is None:
                continue
            if childParams.max < 1:
                continue  # no children of this class must be provided
            children = node.getElementsByTagName(childClass.tag)
            if diagramNode is not None:
                diagramChildren = diagramNode.getElementsByTagName(childClass.tag)
            else:
                diagramChildren = None
            loaded = 0
            j = 0
            for child in children:
                if child.parentNode is node:
                    if diagramChildren is not None and j < len(diagramChildren) \
                            and diagramChildren[j].parentNode is diagramNode:
                        childDiagramNode = diagramChildren[j]
                    else:
                        childDiagramNode = None
                    childNode = self.__parseNode(version, project, bt, nodes, currFile, childClass, child, newNode, childDiagramNode)
                    if childNode is not None:
                        loaded += 1
                        newNode.addChild(childNode, silent=True)
                        if loaded >= childParams.max:
                            break
                j += 1
            if loaded < childParams.min:
                print('warning: Node \"{0}\" with uid=\"{1}\" doesn\'t have enough \"{2}\"-children. \
                        Real count=\"{3}\", but must be \"{4}\".'
                      .format(name, newNode.uid(), childClass.name, loaded, childParams.min))

        # Save branch:--------------------------------------------------------------
        if cls.top and newNode.refname():
            if not bt.add(branch=newNode, silent=True):
                print('error: can\'t add node \"{0}\" with uid=\"{1}\" into trees list with branch name \"{2}\"'
                      .format(name, newNode.uid(), newNode.refname()))
                nodes.remove(newNode, False)
                return None

        return newNode

    def __readDiagramInfo(self, diagramNode):
        dinfo = treenode.DiagramInfo()
        # read diagram info:
        if diagramNode is None:
            return dinfo, -1

        if diagramNode.hasAttribute('uid'):
            uid = int(diagramNode.getAttribute('uid'))
        else:
            uid = -1

        if diagramNode.hasAttribute('expanded'):
            val = diagramNode.getAttribute('expanded').lower()
            if val in ('yes', '1', 'true'):
                dinfo.expanded = True
            else:
                dinfo.expanded = False

        if diagramNode.hasAttribute('hAuto'):
            val = diagramNode.getAttribute('hAuto').lower()
            if val in ('yes', '1', 'true'):
                dinfo.autopositioning[DisplayRegime.Horizontal].autopos = True
            else:
                dinfo.autopositioning[DisplayRegime.Horizontal].autopos = False

        if diagramNode.hasAttribute('vAuto'):
            val = diagramNode.getAttribute('vAuto').lower()
            if val in ('yes', '1', 'true'):
                dinfo.autopositioning[DisplayRegime.Vertical].autopos = True
            else:
                dinfo.autopositioning[DisplayRegime.Vertical].autopos = False

        hShift = QPointF()
        if diagramNode.hasAttribute('hx'):
            hShift.setX(float(diagramNode.getAttribute('hx')))
        if diagramNode.hasAttribute('hy'):
            hShift.setY(float(diagramNode.getAttribute('hy')))
        dinfo.autopositioning[DisplayRegime.Horizontal].shift = hShift

        vShift = QPointF()
        if diagramNode.hasAttribute('vx'):
            vShift.setX(float(diagramNode.getAttribute('vx')))
        if diagramNode.hasAttribute('vy'):
            vShift.setY(float(diagramNode.getAttribute('vy')))
        dinfo.autopositioning[DisplayRegime.Vertical].shift = vShift

        if diagramNode.hasAttribute('sceneX'):
            dinfo.scenePos.setX(float(diagramNode.getAttribute('sceneX')))
        if diagramNode.hasAttribute('sceneY'):
            dinfo.scenePos.setY(float(diagramNode.getAttribute('sceneY')))

        return dinfo, uid

    ##################################################################
    ##################################################################

    def __saveFile(self, projectAlphabet, projectTrees, projectNodes, filename):
        # main xml document
        doc = Document()
        diagramDoc = Document()

        # add main xml tag inside document
        main = doc.createElement(projectAlphabet.headerTree)
        main.setAttribute('version', globals.strVersion)
        doc.appendChild(main)

        diagramMain = diagramDoc.createElement(projectAlphabet.headerTree)
        diagramMain.setAttribute('version', globals.strVersion)
        diagramDoc.appendChild(diagramMain)

        treelist = projectTrees.getBranchesByFile(filename, projectNodes)
        external_files = []
        sorted_names = []
        for t in treelist:
            sorted_names.append(t)
            external_files.extend(self.__getExternals(treelist[t], filename))

        # save external files
        for f in external_files:
            curr = doc.createElement('Include')
            main.appendChild(curr)
            curr.setAttribute('file', f)

        # save nodes information
        for infotag in projectAlphabet.infos:
            nodes = projectTrees.getUsedNodes(projectNodes, filename, True, infotag)
            nodes.sort(key=lambda x: x.name)
            for n in nodes:
                if not n.incomingEvents and not n.outgoingEvents:
                    continue
                nodeCls = projectAlphabet[n.nodeClass]
                if nodeCls is None:
                    continue
                info = doc.createElement(infotag)
                main.appendChild(info)
                info.setAttribute('Name', n.name)
                info.setAttribute(nodeCls.lib, n.libname)
                events = doc.createElement('events')
                info.appendChild(events)
                for ev in n.incomingEvents:
                    eventElem = doc.createElement('incoming')
                    events.appendChild(eventElem)
                    eventElem.setAttribute('name', ev)
                for ev in n.outgoingEvents:
                    eventElem = doc.createElement('outgoing')
                    events.appendChild(eventElem)
                    eventElem.setAttribute('name', ev)

        sorted_names.sort()
        done_list = {}
        num = 0
        num_trees = len(treelist)
        while len(done_list) < num_trees and num < num_trees:
            for t in sorted_names:
                if t in done_list:
                    continue
                dependsOn = projectTrees.getDependantsOf(t, projectNodes)
                dependsOnCurrent = []
                for d in dependsOn:
                    uid = projectTrees.get(d)
                    br = projectNodes[uid]
                    if br is not None and br.path() == filename and d not in done_list:
                        dependsOnCurrent.append(d)
                if dependsOnCurrent:
                    # this branch depends on some other branch that have not been added to xml yet
                    continue
                done_list[t] = self.__saveNode(filename, doc, main, treelist[t], diagramDoc, diagramMain)
            num += 1

        # saving xml document to file
        tree_file = open(filename, 'wb')
        tree_file.write(doc.toprettyxml('\t', '\n', 'utf-8'))
        tree_file.close()

        # saving diagram xml document
        fname, _ = os.path.splitext(filename)
        diagram_filename = fname + '.dgm'
        diagram_file = open(diagram_filename, 'wb')
        diagram_file.write(diagramDoc.toprettyxml('\t', '\n', 'utf-8'))
        diagram_file.close()

        return True

    def __getExternals(self, treeNode, filename):
        external_files = []
        nodeType = treeNode.type()

        if nodeType.isLink():
            if nodeType.linkTargetTag:
                strings = treeNode.target.split('/')
                if len(strings) > 1:
                    strings.pop()
                    targetFile = '/'.join(strings)
                    if targetFile != filename:
                        external_files.append(toUnixPath(os.path.relpath(targetFile, os.path.dirname(filename))))
            return external_files

        if treeNode.nodeDesc() is not None:
            for c in treeNode.allChildren():
                if c in treeNode.nodeDesc().childClasses and c in nodeType:
                    children = treeNode.children(c)
                    for child in children:
                        external_files.extend(self.__getExternals(child, filename))

        return external_files

    def __saveNode(self, filename, xml, parentXmlNode, treeNode, diagramXml, parentDiagramXmlNode):
        nodeCls = treeNode.cls()

        # add new Node to xml
        curr = xml.createElement(nodeCls.tag)
        parentXmlNode.appendChild(curr)

        diagramCurr = diagramXml.createElement(nodeCls.tag)
        parentDiagramXmlNode.appendChild(diagramCurr)

        # save reference
        if treeNode.refname() and nodeCls.linkTag:
            curr.setAttribute(nodeCls.linkTag, treeNode.refname())

        # save type
        nodeType = treeNode.type()
        typename = ''
        if nodeCls.debuggable and treeNode.debug is True:
            typename += 'debug '
        typename += nodeType.name
        curr.setAttribute('Type', typename)

        # save unique id
        curr.setAttribute('uid', str(treeNode.uid()))

        if nodeType.isLink():
            # save reference target
            if nodeType.linkTargetTag:
                strings = treeNode.target.split('/')
                if len(strings) > 1:
                    targetRef = strings[-1]
                    curr.setAttribute(nodeType.linkTargetTag, targetRef)
                    strings.pop()
                    targetFile = '/'.join(strings)
                    if targetFile != filename:
                        tfile = toUnixPath(os.path.relpath(targetFile, os.path.dirname(filename)))
                        curr.setAttribute('File', tfile)
            # save diagram data
            self.__saveDigramData(treeNode.uid(), treeNode.diagramInfo, diagramCurr)
            return curr
        elif nodeType.singleblockEnabled and treeNode.singleBlock():
            curr.setAttribute('singleBlock', '1')

        # save node name
        nodename = ''
        if treeNode.isInverse():
            nodename += '!'
        nodename += treeNode.nodeName
        curr.setAttribute('Name', nodename)

        desc = treeNode.nodeDesc()
        if desc is not None and desc.creator:
            # save creator
            creatorName = ''
            if treeNode.isInverse():
                creatorName += '!'
            creator_name = desc.creator
            creator_lib = ''
            for symbol in ('/', '|'):
                if symbol in desc.creator:
                    creator_parts = desc.creator.split(symbol)
                    creator_lib = creator_parts[0]
                    creator_name = creator_parts[-1]
                    if creator_lib == creator_name:
                        creator_lib = ''
                    break
            creatorName += creator_name
            curr.setAttribute('Creator', creatorName)
            if creator_lib:
                curr.setAttribute('CreatorLib', creator_lib)

        # save library
        curr.setAttribute(nodeCls.lib, treeNode.libname)

        # save attributes
        if nodeCls.attributes.tag:
            settings = xml.createElement(nodeCls.attributes.tag)
            curr.appendChild(settings)
            tags = dict()
            for attrName in treeNode.attributes():
                attr = treeNode.attributes()[attrName]
                attrDesc = attr.attrDesc()
                if attrDesc is None:
                    treename = treeNode.root().refname()
                    print('warning: Node \'{0}\' of tree \'{1}\' has no attribute \'{2}\'. \
                        This attribute will not be saved.'.format(treeNode.nodeName, treename, attrName))
                    continue
                if attrDesc.isArray():
                    strVals = attr.valueToStr()
                    if not strVals or not attrDesc.subtags:
                        continue
                    elem = settings
                    last = len(attrDesc.subtags) - 1
                    for i in range(last):
                        sub = attrDesc.subtags[i]
                        if sub in tags:
                            elem = tags[sub][0]
                            continue
                        newElem = xml.createElement(sub)
                        tags[sub] = [newElem]
                        elem.appendChild(newElem)
                        elem = newElem
                    lastSub = attrDesc.subtags[last]
                    i = 0
                    for value in strVals:
                        n = i + 1
                        if lastSub in tags:
                            if len(tags[lastSub]) < n:
                                newElem = xml.createElement(lastSub)
                                tags[lastSub].append(newElem)
                                elem.appendChild(newElem)
                                curElem = newElem
                            else:
                                curElem = tags[lastSub][i]
                        else:
                            newElem = xml.createElement(lastSub)
                            tags[lastSub] = [newElem]
                            elem.appendChild(newElem)
                            curElem = newElem
                        curElem.setAttribute(attrDesc.attrname, value)
                        i += 1
                else:
                    elem = settings
                    for sub in attrDesc.subtags:
                        if sub in tags:
                            elem = tags[sub][0]
                            continue
                        newElem = xml.createElement(sub)
                        tags[sub] = [newElem]
                        elem.appendChild(newElem)
                        elem = newElem
                    value = attr.valueToStr()
                    elem.setAttribute(attrDesc.attrname, value)

        # save diagram data
        self.__saveDigramData(treeNode.uid(), treeNode.diagramInfo, diagramCurr)

        # save children
        if treeNode.nodeDesc() is not None:
            ccc = []
            for c in treeNode.allChildren():
                if c in treeNode.nodeDesc().childClasses and c in nodeType:
                    ccc.append(c)
            ccc.sort()
            for c in ccc:
                children = treeNode.children(c)
                max_children = nodeType.child(c).max
                num_children = 0
                for child in children:
                    if self.__saveNode(filename, xml, curr, child, diagramXml, diagramCurr) is not None:
                        num_children += 1
                        if num_children >= max_children:
                            break

        return curr

    def __saveDigramData(self, uid, diagramInfo, diagramNode):
        diagramNode.setAttribute('uid', str(uid))

        if diagramInfo.expanded:
            val = '1'
        else:
            val = '0'
        diagramNode.setAttribute('expanded', val)

        if diagramInfo.autopositioning[DisplayRegime.Horizontal].autopos:
            val = '1'
        else:
            val = '0'
        diagramNode.setAttribute('hAuto', val)

        if diagramInfo.autopositioning[DisplayRegime.Vertical].autopos:
            val = '1'
        else:
            val = '0'
        diagramNode.setAttribute('vAuto', val)

        diagramNode.setAttribute('hx', str(diagramInfo.autopositioning[DisplayRegime.Horizontal].shift.x()))
        diagramNode.setAttribute('hy', str(diagramInfo.autopositioning[DisplayRegime.Horizontal].shift.y()))

        diagramNode.setAttribute('vx', str(diagramInfo.autopositioning[DisplayRegime.Vertical].shift.x()))
        diagramNode.setAttribute('vy', str(diagramInfo.autopositioning[DisplayRegime.Vertical].shift.y()))

        diagramNode.setAttribute('sceneX', str(diagramInfo.scenePos.x()))
        diagramNode.setAttribute('sceneY', str(diagramInfo.scenePos.y()))

#######################################################################################################################
#######################################################################################################################

