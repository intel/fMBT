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
This is library implements fmbtandroid.Device-like interface for
Tizen devices.

WARNING: THIS IS A PROOF-OF-CONCEPT.
"""

import fmbtgti
import commands
import os

class Device(fmbtgti.GUITestInterface):
    def __init__(self):
        fmbtgti.GUITestInterface.__init__(self)
        self.setConnection(TizenDeviceConnection())

class TizenDeviceConnection(fmbtgti.GUITestConnection):
    def recvScreenshot(self, filename):
        remoteFilename = "/tmp/fmbttizen.screenshot.xwd"
        s, o = commands.getstatusoutput("sdb shell 'xwd -root -out %s'" % (remoteFilename,))
        s, o = commands.getstatusoutput("sdb pull %s %s.xwd" % (remoteFilename, filename))
        s, o = commands.getstatusoutput("sdb shell rm %s" % (remoteFilename,))
        s, o = commands.getstatusoutput("convert %s.xwd %s" % (filename, filename))
        os.remove("%s.xwd" % (filename,))
        return True

    def sendTap(self, x, y):
        cmd = '''sdb shell "xte 'mousemove %s %s' 'mouseclick 1'"''' % (x, y)
        s, o = commands.getstatusoutput(cmd)
        return True
