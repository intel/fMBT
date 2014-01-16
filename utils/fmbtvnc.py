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
from twisted.internet.defer import Deferred
from twisted.internet import reactor

import vncdotool.client
import vncdotool.api

def _adapterLog(msg):
    fmbt.adapterlog("fmbtvnc %s" % (msg,))

class Screen(fmbtgti.GUITestInterface):
    def __init__(self, hostspec, port=5900, password=None, **kwargs):
        """Parameters:

          hostspec (string)
                  host and optionally display number for VNC
                  connection. Syntax: host[:display]. For example,
                  "localhost" or "10.1.2.3:4".

          port (integer, optional)
                  TCP/IP port number. This port will be used if VNC
                  display is not defined in hostspec. The default is
                  5900.

          password (string, optional)
                  VNC server password. The default is None (no
                  password).

          autoUpdate (boolean, optional)
                  If true, VNC server will be sending updated graphics
                  all the time in the background. If false, VNC server
                  will send updated graphics only on
                  refreshScreenshot(). The default is True, because it
                  works better with some VNC servers that may
                  otherwise send old graphics.

          rotateScreenshot (integer, optional)
                  rotate new screenshots by rotateScreenshot degrees.
                  Example: rotateScreenshot=-90. The default is 0 (no
                  rotation).
        """
        autoUpdate = kwargs.get("autoUpdate", True)
        fmbtgti.GUITestInterface.__init__(self, **kwargs)
        self.setConnection(VNCConnection(hostspec, port, password, autoUpdate))

    def init(self):
        self._conn.init()

class VNCConnection(fmbtgti.GUITestConnection):
    def __init__(self, hostspec, port, password, autoUpdate):
        fmbtgti.GUITestConnection.__init__(self)
        self._updatedImage = None
        if ":" in hostspec: # host:vncdisplay
            self._host, display = hostspec.split(":",1)
            try: self._port = 5900 + int(display)
            except ValueError:
                raise VNCConnectionError('Invalid VNC display "%s"' % (display,))
        else:
            self._host = hostspec
            self._port = port
        self.first_shot = True
        observer = twisted.python.log.PythonLoggingObserver()
        observer.start()
        factory = vncdotool.client.VNCDoToolFactory()
        factory.password = password
        self.client = vncdotool.api.ThreadedVNCClientProxy(factory)
        self.client.connect(self._host, self._port)
        if autoUpdate:
            reactor.callInThread(_continuousIncrementalUpdateWatch, self.client, self)
        # todo: detect failed connection and
        # raise VNCConnectionError(...)
        self.client.start()

    def init(self):
        return True

    def close(self):
        self.client.close()
        return True

    def sendPress(self, key):
        self.client.keyPress(key)
        return True

    def sendKeyDown(self,key):
        self.client.keyDown(key)
        return True

    def sendKeyUp(self,key):
        self.client.keyUp(key)
        return True

    def sendTouchDown(self, x, y, button=1):
        self.client.mouseMove(x, y)
        self.client.mouseDown(button)
        return True

    def sendTouchUp(self, x, y, button=1):
        self.client.mouseMove(x, y)
        self.client.mouseUp(button)
        return True

    def sendTap(self, x, y, button=1):
        self.client.mouseMove(x, y)
        self.client.mousePress(button)
        return True

    def sendTouchMove(self, x, y):
        self.client.mouseMove(x, y)
        return True

    def sendType(self, text):
        for key in text:
            self.client.keyPress(key)
        return True

    def recvScreenshot(self, filename):
        if self._updatedImage:
            self._updatedImage.save(filename)
        else:
            self.client.captureScreen(filename)
        return True

    def target(self):
        return "VNC-" + self._host + "-" + str(self._port)

class FMBTVNCError(Exception): pass
class VNCConnectionError(Exception): pass

def _continuousIncrementalUpdateWatch(client, conn):
    client.continuousIncrementalUpdateRequest(conn)

def _continuousIncrementalUpdateRequest(self, conn):
    self.framebufferUpdateRequest(incremental=1)
    self.deferred = Deferred()
    self.deferred.addCallback(self.continuousIncrementalUpdateSave, conn)
    return self

def _continuousIncrementalUpdateSave(self, image, conn):
    conn._updatedImage = image
    reactor.callLater(.42, self.continuousIncrementalUpdateRequest, conn)
    return self

vncdotool.client.VNCDoToolClient.continuousIncrementalUpdateRequest = \
  _continuousIncrementalUpdateRequest
vncdotool.client.VNCDoToolClient.continuousIncrementalUpdateSave = \
  _continuousIncrementalUpdateSave
