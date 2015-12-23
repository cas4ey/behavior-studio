# coding=utf-8
# -----------------
# file      : parser.py
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
import sys
from xml.dom.minidom import parse, Document

from .proj import Project
from . import alphabet
from . import shapelib
from . import liparser
from . import treeparser

from auxtypes import processString, toUnixPath, relativePath
import globals


def absPath(path, source=''):
    if path is None or not path:
        return None
    if not os.path.exists(path):
        return None
    if os.path.isabs(path):
        return toUnixPath(path)
    return toUnixPath(os.path.abspath(path))

#######################################################################################################################
#######################################################################################################################


class _HistoryBlocker(object):
    def __init__(self):
        globals.historyEnabled = False
        print('debug: history disabled')
        print('debug: ')

    def __del__(self):
        globals.historyEnabled = True
        print('debug: history enabled')
        print('debug: ')

#######################################################################################################################


class ProjParser(object):
    def __init__(self):
        self.__lib_parser = liparser.LibParser()
        self.__tree_parser = treeparser.TreeParser()

    # Load project.
    # Creates new project and loads specified libraries and trees.
    # filename - path to project file
    def open(self, filename):
        _historyBlock = _HistoryBlocker()
        if not filename:
            print('ERROR: you must specify file path to load project!')
            return None

        if not os.path.isabs(filename):
            filename = toUnixPath(os.path.abspath(filename))  # make full path from relative path
        else:
            filename = toUnixPath(filename)

        if not os.path.exists(filename):
            print('ERROR: file \"{0}\" does not exist!'.format(filename))
            return None

        # create new project
        the_proj = Project()
        the_proj.path = filename

        # parse project file
        dom = parse(filename)
        data = dom.getElementsByTagName('btproject')

        if not data:
            print('ERROR: wrong project file! (there are no tag <btproject> in it)')
            return None

        projdata = data[0]
        proj_name = ''
        if projdata.hasAttribute('name'):
            proj_name = projdata.getAttribute('name')  # get project name
        if proj_name:
            the_proj.name = proj_name
        else:
            the_proj.name = 'unknown project'

        # Loading graphic shapes file:
        shapes = projdata.getElementsByTagName('shapelib')
        if shapes and shapes[0].hasAttribute('path'):

            plist = self.__getPathWithCommonChecking(shapes[0],the_proj)

            if len(plist) == 2:
                the_proj.shapelib = shapelib.ShapeLib()
                if not the_proj.shapelib.init(plist[1]):
                    print('ERROR: can\'t load shape library from \"{0}\".'.format(plist[1]))
                    the_proj.shapelib = None

        if the_proj.shapelib is None:
            print('ERROR: shape library is not specified for this project. (tag <shapelib path=\"\"/>)')
            return None

        print('OK: shape library has been loaded from \"{0}\"!'.format(the_proj.shapelib.path))
        print('')

        # Loading alphabet file:
        alphs = projdata.getElementsByTagName('alphabet')
        if alphs and alphs[0].hasAttribute('path'):
            plist = self.__getPathWithCommonChecking(alphs[0],the_proj)
            if len(plist) == 2:
                the_proj.alphabet = alphabet.Alphabet()
                if not the_proj.alphabet.load(plist[1]) or len(the_proj.alphabet) < 1:
                    print('ERROR: Can\'t load alphabet from \'{0}\'!'.format(plist[1]))
                    print('')
                    return None
                else:
                    print('ok: Alphabet file \'{0}\' was loaded successfully'.format(plist[1]))
                    print('')

        if the_proj.alphabet is None:
            print('ERROR: project requires alphabet file! (tag <alphabet path=\"\"/>)')
            return None

        libs = projdata.getElementsByTagName('library')
        trees = projdata.getElementsByTagName('behavior_tree')

        # Loading libraries:
        if libs:
            self.__openLibs(the_proj, libs)

        # if len(the_proj.libraries) < 1 or len(the_proj.lib_paths) < 1:
        #     print 'WARNING: the project have no libraries! No trees will be loaded.'
        #     return the_proj

        # Loading trees:
        if trees:
            self.__openTrees(the_proj, trees)

        if not the_proj.trees or not the_proj.tree_paths:
            print('WARNING: the project have no trees.')

        the_proj.modified = False

        return the_proj

    # Load node libraries.
    # the_proj - reference to project
    # libs - reference to list of xml dom-nodes with library paths
    def __openLibs(self, the_proj, libs):
        for lib in libs:
            # reading path to a library from xml:
            plist = self.__getPath(lib, the_proj.path)
            if len(plist) < 2:
                continue

            libpath = plist[1]  # target file (full path)
            if libpath in the_proj.lib_paths:
                continue  # that library have already been loaded

            # parsing specified library (ll - library list loaded from this file; ll is list of treenode.NodeLibrary):
            ll = self.__lib_parser.load(the_proj.alphabet, [libpath], the_proj.libraries, the_proj.shapelib)
            if not ll:
                continue

            # add loaded libraries to the project's library list:
            for l in ll:
                the_proj.libraries[l] = ll[l]

            # saving library path
            the_proj.lib_paths.append(libpath)

    # Load behavior trees.
    # the_proj - reference to project
    # trees - reference to list of xml dom-nodes with trees paths
    def __openTrees(self, the_proj, trees):
        for tree in trees:
            # reading path to a tree from xml:
            plist = self.__getPath(tree, the_proj.path)
            if len(plist) < 2:
                if len(plist) < 1:
                    print('WARNING: wrong path for tree...')
                else:
                    print('WARNING: file \"{0}\" does not exist.'.format(plist[0]))
                continue

            # treepath = plist[0] # target file (relative path)
            # if treepath in the_proj.tree_paths:
            #     continue # that tree have already been loaded

            temp = plist[1]  # target file (full path)

            # parsing specified tree (tr - tree list loaded from this file; tr is treenode.BehaviorTree):
            bt, nodes, treesFiles = self.__tree_parser.load([temp], the_proj)
            if treesFiles[0] in the_proj.tree_paths:  # trees.empty():
                print('warning: can not load tree from \"{0}\"'.format(temp))
                continue

            # add loaded trees to the project's tree list:
            for t in bt:
                uid = bt[t]
                node = nodes[uid]
                if the_proj.trees.add(node, silent=True):
                    the_proj.nodes.add(node, recursive=True)

            # saving tree path
            the_proj.tree_paths.append(treesFiles[0])  # treepath)

    def __getPathWithCommonChecking(self, xml_node, the_proj):
        is_common_lib = False
        if xml_node.hasAttribute('common'):
            is_common_lib = xml_node.getAttribute('common') == "True"
        if is_common_lib:
            _path = xml_node.getAttribute('path')
            if globals.loadedApplicationConfigFile:
                config_dir = os.path.dirname(globals.loadedApplicationConfigFile)
            else:
                print('ERROR: empty application config file!')
                return tuple()
            path_to_common = os.path.join(config_dir, _path)
            plist = self.__getPathStr(path_to_common, the_proj.path)
        else:
            plist = self.__getPath(xml_node, the_proj.path)

        return plist

    # Auxiliary method, reading path from xml node.
    # It returns a tuple (a list) of two paths:
    # first is relative to project's directory,
    # and second is full path
    def __getPath(self, xml_node, proj_path):
        path = xml_node.getAttribute('path')
        return self.__getPathStr(path,proj_path)

    def __getPathStr(self, _path, proj_path):
        path = relativePath(_path, proj_path)  # getting relative path
        if path is None or not path:
            return tuple()

        temp = os.path.join(os.path.dirname(proj_path), path)  # getting full path
        temp = os.path.normpath(temp)
        if not os.path.exists(temp):
            return tuple([temp])

        path = toUnixPath(path)
        temp = toUnixPath(temp)

        return tuple([path, temp])

    def save(self, project):
        if project is None:
            return False

        globals.generalSignals.preSave.emit()

        # saving trees
        self.__tree_parser.save(project.alphabet, project.trees, project.nodes, project.tree_paths)

        # saving libraries
        if globals.saveLibraries:
            self.__lib_parser.save(project.alphabet, project.libraries)
        else:
            print('info: Libraries would not be saved. Set attribute \'saveLibs\' to \'yes\' ' \
                  'in Your config file to enable libraries saving.')

        # main xml document
        doc = Document()

        # add main xml tag inside document
        main = doc.createElement('btproject')
        main.setAttribute('name', project.name)
        doc.appendChild(main)

        alphabetTag = doc.createElement('alphabet')
        alphabetTag.setAttribute('path', relativePath(project.alphabet.path, project.path))
        main.appendChild(alphabetTag)

        if project.shapelib is not None:
            if os.path.exists(project.shapelib.path):
                shp = doc.createElement('shapelib')
                path = relativePath(project.shapelib.path, project.path)
                shp.setAttribute('path', path)
                main.appendChild(shp)

        for l in project.lib_paths:
            if os.path.exists(l):
                lib = doc.createElement('library')
                path = relativePath(l, project.path)
                lib.setAttribute('path', path)
                main.appendChild(lib)

        for t in project.tree_paths:
            if os.path.exists(t):
                bt = doc.createElement('behavior_tree')
                path = relativePath(t, project.path)
                bt.setAttribute('path', path)
                main.appendChild(bt)

        # saving xml document to file
        f = open(project.path, 'w')
        if f is not None:
            f.write(doc.toprettyxml())
            f.close()

        project.modified = False

        return True

#######################################################################################################################
#######################################################################################################################
