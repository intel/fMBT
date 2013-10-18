# fMBT, free Model Based Testing tool
# Copyright (c) 2013, Intel Corporation.
#
# This program is free software; you can redistribute it and/or modify it
# under the terms and conditions of the GNU Lesser General Public License,
# version 2.1, as published by the Free Software Foundation.
#
# This program is distributed in the hope it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for
# more details.
#
# You should have received a copy of the GNU Lesser General Public License along with
# this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin St - Fifth Floor, Boston, MA 02110-1301 USA.

"""
This is library implements fMBT GUITestInterface for VNC.
"""

import fmbt
import fmbtgti

import twisted.python.log
import vncdotool.client
import vncdotool.api


def _adapterLog(msg):
    fmbt.adapterlog("fmbtvnc %s" % (msg,))


class Screen(fmbtgti.GUITestInterface):
    def __init__(self, host, port=5900):
        fmbtgti.GUITestInterface.__init__(self)
        self.setConnection(VNCConnection(host, port))

    def init(self):
        self._conn.init()


class VNCConnection(fmbtgti.GUITestConnection):
    def __init__(self, host, port=5900):
        fmbtgti.GUITestConnection.__init__(self)
        self._host = host
        self._port = port
        self.first_shot = True
        observer = twisted.python.log.PythonLoggingObserver()
        observer.start()
        factory = vncdotool.client.VNCDoToolFactory()
        self.client = vncdotool.api.ThreadedVNCClientProxy(factory)
        if self.client.connect(self._host, self._port) == None:
            raise VNCConnectionError('Cannot connect to VNC host "%s" port "%s"' % (self._host, self._port))

    def init(self):
        return True

    def close(self):
        self.client.close()

    def sendPress(self, key):
        self.client.keyPress(key)

    def sendKeyDown(self,key):
        self.client.keyDown(key)

    def sendKeyUp(self,key):
        self.client.keyUp(key)

    def sendTouchDown(self, x, y):
        self.client.mouseMove(x,y)
        self.client.mouseDown(1)

    def sendTouchUp(self, x, y):
        self.client.mouseMove(x,y)
        self.client.mouseUp(1)

    def sendTap(self,x,y):
        self.client.mouseMove(x,y)
        self.client.mousePress(1)

    def sendTouchMove(self, x, y):
        self.client.mouseMove(x,y)

    def sendType(self, text):
        for key in text:
            self.client.keyPress(key)

    def recvScreenshot(self, filename):
        if self.first_shot:
            self.client.captureScreen(filename)
            self.first_shot = False
        self.client.captureScreen(filename)
        return True

    def target(self):
        return "VNC-" + self._host + "-" + str(self._port)

class FMBTVNCError(Exception): pass
class VNCConnectionError(Exception): pass
