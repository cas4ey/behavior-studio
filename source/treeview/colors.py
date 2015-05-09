# coding=utf-8
# -----------------
# file      : colors.py
# date      : 2014/09/20
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

__author__ = 'Victor Zarubkin'
__copyright__ = 'Copyright (C) 2014  Victor Zarubkin'
__credits__ = ['Victor Zarubkin']
__license__ = ['GPLv3']
__version__ = '1.2.6'  # this is last application version when this script file was changed
__email__ = 'victor.zarubkin@gmail.com'
############################################################################

from PySide.QtGui import QColor
from PySide.QtCore import Qt

#######################################################################################################################
#######################################################################################################################


def QcolorA(color, alpha):
    col = QColor(color)
    col.setAlpha(alpha)
    return col


class DiagramColor(object):
    red = QColor(255, 48, 48, 224)
    orange = QColor(220, 161, 0, 224)
    lightorange = QColor(244, 204, 32, 224)
    yellow = QColor(224, 255, 32, 224)
    green = QColor(48, 224, 48, 224)
    darkgreen = QColor(48, 176, 48, 224)
    greengray = QColor(128, 192, 128, 225)
    lightgray = QColor(204, 204, 204, 224)
    white = QColor(255, 255, 255, 224)
    bluegray = QColor(96, 148, 255, 244)

    debugColor = red  # this is color of '!' sign of item's debug indicator
    rootColor = red  # this is color of root item text indicator
    selectedColor = orange  # this is color of connection lines from selected item to it's children
    eventsColor = green  # this is color of event triangles
    defaultTextColor = lightgray  # this is color of text under items
    defaultRefColor = bluegray  # this is color of reference text items
    defaultLineColor = Qt.black  # this is color of lines drawed within item sign

    connectionLineColor = QColor(0, 0, 0, 204)  # this color is used for connector line with arrow when connecting or disconnecting items
    conectionBackgroundColor = QColor(255, 128, 64, 164)  # this color is used for items under connector line with arrow

#######################################################################################################################
#######################################################################################################################
