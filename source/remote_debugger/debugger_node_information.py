# coding=utf-8
# -----------------
# file      : debugger_node_information.py
# date      : 2014/11/16
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

from sortedcontainers import SortedDict as sorted_dict

#######################################################################################################################
#######################################################################################################################


class NodeDebugMessage(object):
    def __init__(self, uid, state, message=''):
        """
        *uid* is node unique identifier
        *state* is current node state
        *message* is additional user text information
        """
        self._uid = uid
        self._state = state
        self._message = message

    def uid(self):
        """ Returns unique identifier of tree node """
        return self._uid

    def state(self):
        """ Returns tree node's state """
        return self._state

    def message(self):
        """ Returns an additional user text information """
        return self._message

#######################################################################################################################


class EntityDebugInformation(object):
    def __init__(self):
        self._timeline = sorted_dict()

    def insert(self, message, time):
        self._timeline[time] = message

    def get(self, time=None):
        if not self._timeline:
            return None
        if time is None:
            return self._timeline[list(self._timeline.keys())[-1]]
        if time in self._timeline:
            return self._timeline[time]
        key_index = self._timeline.bisect_left(time) - 1
        if key_index < 0:
            return None
        return self._timeline[list(self._timeline.keys())[key_index]]

#######################################################################################################################
#######################################################################################################################

