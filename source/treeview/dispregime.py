# coding=utf-8
# -----------------
# file      : dispregime.py
# date      : 2012/10/13
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

__author__ = 'Victor Zarubkin'
__copyright__ = 'Copyright (C) 2012  Victor Zarubkin'
__credits__ = ['Victor Zarubkin']
__license__ = ['GPLv3']
__version__ = '1.2.5'  # this is last application version when this script file was changed
__email__ = 'victor.zarubkin@gmail.com'
############################################################################


class DisplayRegime(object):
    Horizontal = 0
    Vertical = 1


class GroupType(object):
    VerticalGroup = 0
    HorizontalGroup = 1


class AlignType(object):
    Top = 1
    Bottom = 2
    Left = 4
    Right = 8
    CenterH = 16
    CenterV = 32

#######################################################################################################################
