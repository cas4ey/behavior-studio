# coding=utf-8
# -----------------
# file      : debugger_widget.py
# date      : 2014/11/18
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

from __future__ import unicode_literals

__author__ = 'Victor Zarubkin'
__copyright__ = 'Copyright (C) 2014  Victor Zarubkin'
__credits__ = ['Victor Zarubkin']
__license__ = ['GPLv3']
__version__ = '1.3.0'  # this is last application version when this script file was changed
__email__ = 'victor.zarubkin@gmail.com'
############################################################################

from PySide import QtCore
from PySide.QtGui import *
from PySide.QtCore import *

from extensions.widgets import *

from remote_debugger import debugger_globals
from remote_debugger.debugger_mode import DebuggerMode

#######################################################################################################################
#######################################################################################################################


class StateDebugWidget(QWidget):
    def __init__(self, *args, **kwargs):
        QWidget.__init__(self, *args, **kwargs)
        self.setObjectName('stateDebuggerWidget')

        self._switcherButton = trButton(trStr('Turned off', 'Выключен'))
        self._switcherButton.setToolTip(trStr('Turn on remote debugger server', 'Включить дистанционный отладчик'))
        self._switcherButton.setCheckable(True)
        self._switcherButton.toggled.connect(self._onSwitcherButtonToggle)

        self._rbCurrentState = trRadioButton(trStr('Current state only', 'Только текущее состояние'))
        self._rbCurrentState.setChecked(True)

        self._rbMixedState = trRadioButton(trStr('Mixed states', 'Смешанный режим'))
        self._rbMixedState.setChecked(False)

        # radio buttons belongs to one group, so there is no need to connect to each button "toggled" signal,
        # it's enough to connect to one button "toggled" signal.
        self._rbCurrentState.toggled.connect(self._onRadioButtonsToggle)

        self._rbGroup = trGroupBox(trStr('Mode', 'Режим'))
        vbox = QVBoxLayout()
        vbox.addWidget(self._rbCurrentState)
        vbox.addWidget(self._rbMixedState)
        self._rbGroup.setLayout(vbox)
        self._rbGroup.setEnabled(False)

        vbox = QVBoxLayout()
        vbox.addWidget(self._switcherButton)
        vbox.addWidget(self._rbGroup)
        vbox.addStretch(1)

        self.setLayout(vbox)

    @QtCore.Slot()
    def _onSwitcherButtonToggle(self):
        turnedOn = self._switcherButton.isChecked()
        if turnedOn:
            self._switcherButton.setText(trStr('Turned on', 'Включен'))
            self._switcherButton.setToolTip(trStr('Turn off remote debugger server', 'Выключить дистанционный отладчик'))
        else:
            self._switcherButton.setText(trStr('Turned off', 'Выключен'))
            self._switcherButton.setToolTip(trStr('Turn on remote debugger server', 'Включить дистанционный отладчик'))
        self._rbGroup.setEnabled(turnedOn)
        debugger_globals.debuggerSignals.debuggerOnOff.emit(turnedOn)

    @QtCore.Slot(bool)
    def _onRadioButtonsToggle(self, checked):
        if self._rbCurrentState.isChecked():
            debugger_globals.mode = DebuggerMode.CurrentState
        elif self._rbMixedState.isChecked():
            debugger_globals.mode = DebuggerMode.MixedState
        debugger_globals.debuggerSignals.modeChanged.emit(debugger_globals.mode)

#######################################################################################################################


class StateDebugDock(trDockWidget):
    def __init__(self, title, parent=None):
        trDockWidget.__init__(self, title, parent)
        self.setWidget(StateDebugWidget())

#######################################################################################################################
#######################################################################################################################

