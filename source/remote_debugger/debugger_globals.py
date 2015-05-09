# coding=utf-8
# -----------------
# file      : debugger_globals.py
# date      : 2014/11/23
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

"""

"""

__author__ = 'Victor Zarubkin'
__copyright__ = 'Copyright (C) 2014  Victor Zarubkin'
__credits__ = ['Victor Zarubkin']
__license__ = ['GPLv3']
__version__ = '1.2.2'  # this is last application version when this script file was changed
__email__ = 'victor.zarubkin@gmail.com'
############################################################################

from PySide.QtCore import Signal as QtSignal, QObject
from remote_debugger.debugger_mode import DebuggerMode
from remote_debugger.debugger_node_information import *

#######################################################################################################################
#######################################################################################################################

maxRecords = int(1000)  # how much debug records debugger will hold for each object
mode = DebuggerMode.CurrentState
timeMark = -1.0


class _RemoteDebuggerSignals(QObject):
    debuggerOnOff = QtSignal(bool)  # debugger has been turned on or off
    modeChanged = QtSignal(int)  # debugger mode has been changed (see DebuggerMode)
    timeSliceChanged = QtSignal(float)  # (time mark in seconds)

    def __init__(self):
        QObject.__init__(self)

debuggerSignals = _RemoteDebuggerSignals()

#######################################################################################################################
#######################################################################################################################

