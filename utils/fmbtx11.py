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
This library implements fmbt GUITestInterface for X.
"""

import fmbtgti

fmbtgti._OCRPREPROCESS = [
    "",
    "-sharpen 5 -level 90%%,100%%,3.0 -sharpen 5"
    ]

import ctypes
import fmbtx11_conn

class Screen(fmbtgti.GUITestInterface):
    def __init__(self, display="", **kwargs):
        """Parameters:

          display (string, optional)
                  X display to connect to.
                  Example: display=":0". The default is "", that is,
                  the default X display in the DISPLAY environment
                  variable will be used.

          rotateScreenshot (integer, optional)
                  rotate new screenshots by rotateScreenshot degrees.
                  Example: rotateScreenshot=-90. The default is 0 (no
                  rotation).
        """
        fmbtgti.GUITestInterface.__init__(self, **kwargs)
        self.setConnection(X11Connection(display))

class X11Connection(fmbtx11_conn.Display):
    def __init__(self, display):
        fmbtx11_conn.Display.__init__(self, display)

    def target(self):
        return "X11"

    def recvScreenshot(self, filename):
        # This is a hack to get this stack quickly testable,
        # let's replace this with Xlib/libMagick functions, too...
        import commands
        commands.getstatusoutput("xwd -root -display '%s' -out '%s.xwd'" % (self._displayName, filename))
        commands.getstatusoutput("convert '%s.xwd' '%s'" % (filename, filename))
        return True

class FMBTX11Error(Exception): pass
X11ConnectionError = fmbtx11_conn.X11ConnectionError
