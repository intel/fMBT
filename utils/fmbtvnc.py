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
This is library implements fMBT GUITestInterface for Windows.

"""

import fmbt
import fmbtgti

import threading
import Queue
import logging

from twisted.internet import reactor
from twisted.internet.defer import maybeDeferred
from twisted.python.log import PythonLoggingObserver
from twisted.python.failure import Failure

from vncdotool import command
from vncdotool.client import VNCDoToolFactory, VNCDoToolClient


class ThreadedVNCClientProxy(object):

    def __init__(self, factory):
        self.factory = factory
        self.queue = Queue.Queue()

    def connect(self, host, port=5900):
        reactor.callWhenRunning(reactor.connectTCP, host, port, self.factory)

    def start(self):
        self.thread = threading.Thread(target=reactor.run, name='Twisted',
                                       kwargs={'installSignalHandlers': False})
        self.thread.daemon = True
        self.thread.start()

        return self.thread

    def join(self):
        def _stop(result):
            reactor.stop()

        reactor.callFromThread(self.factory.deferred.addBoth, _stop)
        self.thread.join()

    def __getattr__(self, attr):
        method = getattr(VNCDoToolClient, attr)

        def _releaser(result):
            self.queue.put(result)
            return result

        def _callback(protocol, *args, **kwargs):
            d = maybeDeferred(method, protocol, *args, **kwargs)
            d.addBoth(_releaser)
            return d

        def proxy_call(*args, **kwargs):
            reactor.callFromThread(self.factory.deferred.addCallback,
                                   _callback, *args, **kwargs)
            result = self.queue.get()
            if isinstance(result, Failure):
                raise VNCDoThreadError(result)

        return proxy_call


def _adapterLog(msg):
    fmbt.adapterlog("fmbtvnc %s" % (msg,))

class VNC(fmbtgti.GUITestInterface):
    def __init__(self, host, port=5900):
        fmbtgti.GUITestInterface.__init__(self)
        self.setConnection(VncdeviceConnection(Host=host, Port=port))

    def init(self):
        self._conn.init()
    

class VncdeviceConnection(fmbtgti.GUITestConnection):
    def __init__(self, Host, Port=5900):
#        fmbtgti.GUITestInterface.__init__(self)
        self.HOST = Host
        self.PORT = Port
        self.first_shot = True
        observer = PythonLoggingObserver()
        observer.start()
        factory = VNCDoToolFactory()
        self.client = ThreadedVNCClientProxy(factory)
        self.client.connect(self.HOST,self.PORT)
        self.client.start()

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
        print "tap %i %i" % (x,y)
        self.client.mouseMove(x,y)
        self.client.mousePress(1)

    def sendTouchMove(self, x, y):
        self.client.mouseMove(x,y)

    def recvScreenshot(self, filename):
        if self.first_shot:
            self.client.captureScreen(filename)
            self.first_shot = False
        self.client.captureScreen(filename)
        return True

    def target(self):
        return "VNC-" + self.HOST + ":" + str(self.PORT)
