# coding=utf-8
# -----------------
# file      : auxtypes.py
# date      : 2012/09/29
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

""" This script file contains several auxiliary functions that simplifies unix/win32 files paths manipulation. """

__author__ = 'Victor Zarubkin'
__copyright__ = 'Copyright (C) 2012  Victor Zarubkin'
__credits__ = ['Victor Zarubkin']
__license__ = ['GPLv3']
__version__ = '1.1.0'  # this is last application version when this script file was changed
__email__ = 'victor.zarubkin@gmail.com'
############################################################################

import os

########################################################################################################################
########################################################################################################################


def processString(string):
    strings = string.split('\\n')
    if len(strings) > 1:
        strings2 = []
        for s in strings:
            strings2.append(' '.join(s.split()))
        string = '\n'.join(strings2)
    return string


def toUnixPath(path):
    return path.replace('\\', '/')
    # sub = path.split('\\')
    # if len(sub) < 2:
    #     return path
    # return '/'.join(sub)


def relativePath(path, source):
    if path is None or not path:
        return None
    if os.path.isabs(path):
        if not os.path.exists(path):
            return None
        dir_path = source
        if os.path.isfile(source):
            dir_path = os.path.dirname(source)
        return toUnixPath(os.path.relpath(path, dir_path))
    return toUnixPath(path)


def absPath(relative_path, source, getDir=False):
    path = relativePath(relative_path, source)  # getting relative path
    if path is None or not path:
        return None
    source_dir = source
    if os.path.isfile(source):
        source_dir = os.path.dirname(source)
    full_path = os.path.join(source_dir, path)  # getting full path
    if getDir is True and not os.path.isdir(full_path):
        full_path = os.path.dirname(full_path)
    full_path = os.path.normpath(full_path)
    if not os.path.exists(full_path):
        return None
    return toUnixPath(full_path)


def joinPath(dirName, fileName):
    return '/'.join([dirName, fileName])

########################################################################################################################
########################################################################################################################

