# coding=utf-8
# -----------------
# file      : debugger_server.py
# date      : 2014/11/15
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

from compat_2to3 import *

from PySide import QtCore
from PySide.QtGui import *
from PySide.QtCore import *
import select
import socket
import threading

if isPython2:
    import Queue as queue
else:
    import queue

import sys
import zlib

import globals
from remote_debugger import debugger_globals

#######################################################################################################################

_packetHeader = '[pkt]'
_idMarker = '[id]'
_timeMarker = '[t]'
_messageMarker = '[m]'
_treeStateMarker = '[ts]'

_packetHeaderLen = len(_packetHeader)
_treeStateMarkerLen = len(_treeStateMarker)
_timeMarkerLen = len(_timeMarker)
_idMarkerLen = len(_idMarker)

_portionSize = 32  # clients receive buffer size in bytes
_refreshRate = 40  # how often handle clients connections and receive data, milliseconds

#######################################################################################################################


class DebugMessage(object):
    def __init__(self, text):
        self._text = text
        self._type = str

    def _setType(self, messageType):
        self._type = messageType

    def type(self):
        return self._type

    def text(self):
        return self._text

#######################################################################################################################


class TreeDebugMessage(DebugMessage):
    def __init__(self, text):
        DebugMessage.__init__(self, text)
        self._setType(TreeDebugMessage)
        self._uid = 0
        self._state = 0
        self._message = ''
        self._valid = False

        texts = text.split(',')
        num = len(texts)
        if 1 < num < 4:
            # try to read node uid
            try:
                self._uid = int(texts[0])
                validUid = True
            except ValueError:
                validUid = False

            # try to read node state
            try:
                self._state = int(texts[1])
                validState = True
            except ValueError:
                validState = False

            # read debug message
            if num > 2:
                self._message = texts[2]

            self._valid = validUid and validState

    def valid(self):
        return self._valid

    def uid(self):
        return self._uid

    def state(self):
        return self._state

    def message(self):
        return self._message

#######################################################################################################################


# Separate thread working with client connection, receive and handle all data from client
class ClientThread(threading.Thread):
    def __init__(self, clientSocket):
        threading.Thread.__init__(self)
        self._socket = clientSocket
        self.received_data = queue.Queue()
        self.addr = queue.Queue()

    def run(self):
        """Main client thread loop.

        First, the thread accepts client connection.
        After connection is accepted, the thread will receive data from client with small portions
        (_portionSize bytes).
        After all data will be received, the thread will handle it, divide it into different packets and so on.
        """

        global _portionSize, _packetHeader, _packetHeaderLen

        # 1) Accept client connection
        client_connection, client_address = self._socket.accept()
        self.addr.put(client_address, True)

        # 2) Receive data from client
        received_data = ''
        bytes_count = 0
        while True:
            data = client_connection.recv(_portionSize)
            if data:
                received_data += data
                bytes_count += sys.getsizeof(data, 0) - sys.getsizeof(type(data)(), 0)  # real bytes count
            else:
                client_connection.close()
                break

        # 3) Divide received data into packets
        packets = []  # the packets list
        if received_data:
            received_data = zlib.decompress(received_data)
            while received_data:
                # Search for packet header...
                # 'i' is the index of first character of packet header
                i = received_data.find(_packetHeader)
                if i < 0:
                    break
                # 'k' is the index of first character of data itself (a data without packet header in it)
                k = i + _packetHeaderLen
                if k < len(received_data):
                    # If there is some data in packet after the header, try to find next packet header
                    # if it is exist (if there are several packets in client data)
                    j = received_data.find(_packetHeader, k)
                else:
                    # The packet is empty and there could not be any other packets
                    j = -1
                if j < 0:
                    # There is only one packet in client data, store it in packets list
                    packets.append(received_data[k:])
                    break
                else:
                    # There are several packets in client data.
                    # Store
                    packets.append(received_data[k:j])
                    k = j + _packetHeaderLen
                    if k < len(received_data):
                        # excluding handled packet from data
                        received_data = received_data[k:]
                    else:
                        # actually there is only one packet in client data
                        # (there are several packet headers, but the last packet is empty)
                        break

        # 4) Handle all packets and put handled data into output queue
        self.received_data.put((ClientThread._parsePackets(packets), bytes_count, client_address), True)

    @staticmethod
    def _parsePackets(packets):
        """Handle all received packets.

        A packet must contain an object id, a time mark and, at least, one message.
        Message could be a text or an information about current tree state.

        Each packet will be divided into messages and each message will be handled separately.
        """

        global _messageMarker, _treeStateMarker, _treeStateMarkerLen

        packets_by_object = dict()  # The output data. It contains all messages divided by object id

        # Handle each packet separately
        for packet in packets:
            packet_data = dict()  # an output data for one packet
            object_uid = 0  # object id
            current_time = -1.0  # packet time mark

            # Split packet into messages and handle each message separately
            messages = packet.split(_messageMarker)
            for msg in messages:
                if current_time < 0 or object_uid == 0:
                    # Try to find mandatory information: object id and time mark
                    if current_time < 0:
                        ok, current_time = ClientThread._readTime(msg)  # try to read time
                        if not ok:
                            # This information is mandatory! If there is no time mark in the packet
                            # then this packet is broken and we can't handle it
                            break
                    if object_uid == 0:
                        ok, object_uid = ClientThread._readId(msg)  # try to read object id
                        if not ok:
                            # This information is mandatory! If there is no object id in the packet
                            # then this packet is broken and we can't handle it
                            break
                else:
                    # If mandatory information has been found already then handle the message.
                    # Trying to find tree state marker
                    i = msg.find(_treeStateMarker)
                    if i < 0:
                        # Marker was not found - this message will be saved as simple text
                        common_message = DebugMessage(msg)
                        if 'cmn' in packet_data:
                            packet_data['cmn'].append(common_message)
                        else:
                            packet_data['cmn'] = [common_message]
                    else:
                        # The marker was found - this message is 'tree state' message.
                        # Remove tree state marker from message
                        k = i + _treeStateMarkerLen
                        if k < len(msg):
                            msg = msg[k:]
                        else:
                            msg = ''
                        # Handle this 'tree state' message and put it into packet data
                        state_message = TreeDebugMessage(msg)
                        if 'bt' in packet_data:
                            packet_data['bt'].append(state_message)
                        else:
                            packet_data['bt'] = [state_message]

            # If packet is not empty, then put it into the output data
            if packet_data:
                store_data = (current_time, packet_data)
                if object_uid not in packets_by_object:
                    packets_by_object[object_uid] = [store_data]
                else:
                    packets_by_object[object_uid].append(store_data)

        # Return all handled data for all objects
        return packets_by_object

    @staticmethod
    def _readTime(message):
        """Read packet time mark from a message."""

        global _timeMarker, _timeMarkerLen

        m = message
        i = m.find(_timeMarker)
        if i < 0:
            # broken packet, no time mark in packet
            return False, -1.0

        k = i + _timeMarkerLen
        if k < len(m):
            m = m[k:]
            i = m.find('[')
            if i >= 0:
                m = m[:i]
        else:
            m = ''

        if not m:
            # broken packet, no time mark in packet
            return False, -1.0

        try:
            current_time = float(m)
        except ValueError:
            # broken packet, no time mark in packet
            return False, -1.0

        return True, current_time

    @staticmethod
    def _readId(message):
        """Read object id from a message."""

        global _idMarker, _idMarkerLen

        m = message
        i = m.find(_idMarker)
        if i < 0:
            # broken packet, no id mark in packet
            return False, 0

        k = i + _idMarkerLen
        if k < len(m):
            m = m[k:]
            i = m.find('[')
            if i >= 0:
                m = m[:i]
        else:
            m = ''

        if not m:
            # broken packet, no id mark in packet
            return False, 0

        try:
            uid = int(m)
        except ValueError:
            # broken packet, no id mark in packet
            return False, 0

        return True, uid

#######################################################################################################################


# Separate thread which goal is to stop client threads
class StopperThread(threading.Thread):
    def __init__(self, threads):
        threading.Thread.__init__(self)
        self._threads = threads
        self.ready = queue.Queue()

    def run(self):
        if self._threads:
            for t in self._threads:
                t.join()
            self._threads = []
            self.ready.put(True, True)

#######################################################################################################################


class DebugServer(QObject):
    def __init__(self, port=4447):
        QObject.__init__(self, None)
        self.__sock = None
        self.__address = (socket.gethostname(), port)
        self.__launched = False
        self.__timer = QTimer()  # timer for checking new client connections
        self.__timer.timeout.connect(self.__onTimeout)
        self.__threads = []  # client threads
        self.__stoppers = []  # stopper threads
        self.__stopperTimer = QTimer()  # timer for closing client threads
        self.__stopperTimer.timeout.connect(self.__onStopperTimeout)
        debugger_globals.debuggerSignals.debuggerOnOff.connect(self._onDebuggerOnOff)

    @QtCore.Slot(bool)
    def _onDebuggerOnOff(self, on):
        if on:
            self.start()
        else:
            self.stop(False)

    @QtCore.Slot()
    def __onStopperTimeout(self):
        if self.__stoppers:
            stopped = []
            for s in self.__stoppers:
                if not s.ready.empty():
                    ready = s.ready.get_nowait()
                    if ready:
                        s.join()
                        stopped.append(s)
            for s in stopped:
                self.__stoppers.remove(s)
        if not self.__stoppers:
            self.__stopperTimer.stop()

    def start(self, port=None):
        self.stop(True)
        if port is not None and port != self.__address[1]:
            self.__address = (socket.gethostname(), port)
        self.__openSocket()

    def stop(self, wait):
        if self.__launched:
            self.__timer.stop()
            print('info: Stopping debug server on \'%s\' port %s...' % self.__address)
            self.__launched = False
            self.__sock.close()
            if self.__threads:
                if wait:
                    for c in self.__threads:
                        c.join()
                    for s in self.__stoppers:
                        s.join()
                    self.__stoppers = []
                    self.__stopperTimer.stop()
                else:
                    s = StopperThread(self.__threads)
                    s.start()
                    self.__stoppers.append(s)
                    self.__stopperTimer.start(40)
            self.__threads = []
            self.__sock = None
            print('ok: debug server stopped')
            print('')

    def __openSocket(self):
        try:
            global _refreshRate
            print('info: Starting debug server on \'%s\' port %s...' % self.__address)
            self.__sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # self.__sock.setblocking(False)
            self.__sock.bind(self.__address)
            self.__sock.listen(1)
            self.__timer.start(_refreshRate)
            self.__launched = True
            print('ok: Debug server started successfully.')
            print('ok: Debug server: use next address for client connection: \'%s\' port %s' % self.__address)
            print('')
        except socket.error as xxx_todo_changeme:
            (errorCode, message) = xxx_todo_changeme.args
            self.__launched = False
            self.__timer.stop()
            if self.__sock is not None:
                self.__sock.close()
                del self.__sock
                self.__sock = None
            lines = message.split('\n')
            print('error: Debug server: can\'t open socket:')
            for line in lines:
                print('error: Debug server: {0}'.format(line))
            print('')

    @QtCore.Slot()
    def __onTimeout(self):
        if not self.__launched:
            return

        endlist = []  # list of stopped client threads
        for c in self.__threads:
            # Check if thread just started to receive data
            if not c.addr.empty():
                client_address = c.addr.get_nowait()
                print('info: Debug server: new connection from \'%s\' port %s' % client_address)

            # Check if thread have finished client's data handling
            if c.received_data.empty():
                break

            # Receive data from thread
            packets_by_object = dict()
            bytes_count = 0
            client_address = ('none', 'none')
            while True:
                try:
                    data, bytes_received, client_address = c.received_data.get_nowait()
                    for object_uid in data:
                        if object_uid not in packets_by_object:
                            packets_by_object[object_uid] = data[object_uid]
                        else:
                            packets_by_object[object_uid].extend(data[object_uid])
                    bytes_count += bytes_received
                except queue.Empty:
                    break

            # Stop idle client thread
            c.join()
            endlist.append(c)

            # Print debug information
            if globals.debugMode:
                msg = 'debug: Debug server: received '
                if bytes_count >= 1024:
                    kbytes_count = bytes_count / 1024
                    if kbytes_count >= 1024:
                        msg += '{0} Mb from '.format(kbytes_count / 1024)
                    else:
                        msg += '{0} Kb from '.format(kbytes_count)
                else:
                    msg += '{0} Bytes from '.format(bytes_count)
                print(msg + '\'%s\' port %s' % client_address)
                for object_uid in packets_by_object:
                    for data in packets_by_object[object_uid]:
                        current_time, messages = data
                        text = 'object: {0}, time: {1}, data: '.format(object_uid, current_time)
                        for d in messages:
                            for m in messages[d]:
                                text += m.text() + '; '
                        print('debug: Debug server: received {0}'.format(text))
                print('debug: ')

            # TODO: do something with received data 'packets_by_object'

        # Remove stopped threads from client threads list
        if endlist:
            for c in endlist:
                self.__threads.remove(c)
            del endlist[:]

        # Check for new connections and start new client threads
        inputSockets, _, _ = select.select([self.__sock], [], [], 0)
        for s in inputSockets:
            c = ClientThread(s)
            c.start()
            self.__threads.append(c)

#######################################################################################################################
#######################################################################################################################
