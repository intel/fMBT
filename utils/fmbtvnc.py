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
import gtkvnc

def _adapterLog(msg):
    fmbt.adapterlog("fmbtvnc %s" % (msg,))

class VNC(fmbtgti.GUITestInterface):
    def __init__(self, host, port=5900):
        fmbtgti.GUITestInterface.__init__(self)
        self.setConnection(VncdeviceConnection(Host=host, Port=port))

class VncdeviceConnection(fmbtgti.GUITestConnection):
    def __init__(self, Host, Port=5900):
#        fmbtgti.GUITestInterface.__init__(self)
        self.dpy = gtkvnc.Display()
        self.HOST = Host
        self.PORT = Port
        print Host + ":" + str(Port)
        print self.dpy.open_host(Host, str(Port))
        print self.dpy.is_open()
        print self.dpy.get_height()
        print self.dpy.get_width()

    def close(self):
        fmbtgti.GUITestInterface.close(self)        
        self.dpy.close()

    def sendPress(self, keyName):
        self.dpy.send_key([keyName])

    def sendTap(self,x,y):
        self.dpy.send_pointer(x=x,y=y,button_mask=1)

    def recvScreenshot(self, filename):
        print self.dpy.is_open()
        print self.dpy.get_height()
        print self.dpy.get_width()
        pix=self.dpy.get_pixbuf()
        pix.save(filename=filename,type=filename.split(".")[-1])

    def target(self):
        return "VNC " + self.HOST + ":" + str(self.PORT)
