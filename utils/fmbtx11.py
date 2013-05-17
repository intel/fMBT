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
import ctypes

class Screen(fmbtgti.GUITestInterface):
    def __init__(self):
        fmbtgti.GUITestInterface.__init__(self)
        self.setConnection(X11Connection())

class X11Connection(fmbtgti.GUITestConnection):
    def __init__(self):
        fmbtgti.GUITestConnection.__init__(self)
        self.libX11 = ctypes.CDLL("libX11.so")
        self.libXtst = ctypes.CDLL("libXtst.so.6")
        self.X_True = ctypes.c_int(1)
        self.X_False = ctypes.c_int(0)
        self.X_CurrentTime = ctypes.c_ulong(0)
        self.NULL = ctypes.c_char_p(0)
        self.current_screen = ctypes.c_int(-1)
        self.display = ctypes.c_void_p(self.libX11.XOpenDisplay(self.NULL))

    def __del__(self):
        self.libX11.XCloseDisplay(self.display)

    def sendTap(self, x, y):
        self.libXtst.XTestFakeMotionEvent(self.display, self.current_screen, int(x), int(y), self.X_CurrentTime)
        self.libXtst.XTestFakeButtonEvent(self.display, 1, self.X_True, self.X_CurrentTime)
        self.libXtst.XTestFakeButtonEvent(self.display, 1, self.X_False, self.X_CurrentTime)
        self.libX11.XFlush(self.display)
        return True
	
    def sendPress(self, key):
        # Convert to key code
        keysim = self.libXtst.XStringToKeysym(str(key))
        keycode = self.libXtst.XKeysymToKeycode(self.display, keysim)
        self.libXtst.XTestFakeKeyEvent(self.display, keycode, self.X_True, self.X_CurrentTime)
        self.libXtst.XTestFakeKeyEvent(self.display, keycode, self.X_False, self.X_CurrentTime)
        self.libXtst.XFlush(self.display)
	return True

    def sendKeyDown(self, key):
        keysim = self.libXtst.XStringToKeysym(str(key))
        keycode = self.libXtst.XKeysymToKeycode(self.display, keysim)
        self.libXtst.XTestFakeKeyEvent(self.display, keycode, self.X_True, self.X_CurrentTime)
        self.libXtst.XFlush(self.display)
        return True

    def sendKeyUp(self, key):
        keysim = self.libXtst.XStringToKeysym(str(key))
        keycode = self.libXtst.XKeysymToKeycode(self.display, keysim)
        self.libXtst.XTestFakeKeyEvent(self.display, keycode, self.X_False, self.X_CurrentTime)
        self.libXtst.XFlush(self.display)
        return True

    def sendTouchMove(self, X, Y):
        self.libXtst.XTestFakeButtonEvent(self.display, 1, self.X_True, self.X_CurrentTime)
        self.libXtst.XTestFakeMotionEvent(self.display, self.current_screen, int(X), int(Y), self.X_CurrentTime)
        self.libXtst.XTestFakeButtonEvent(self.display, 1, self.X_False, self.X_CurrentTime)
        self.libXtst.XFlush(self.display)
        return True

    def sendTouchDown(self, X, Y):
        self.libXtst.XTestFakeMotionEvent(self.display, self.current_screen, int(X), int(Y), self.X_CurrentTime)
        self.libXtst.XTestFakeButtonEvent(self.display, 1, self.X_True, self.X_CurrentTime)
        self.libXtst.XFlush(self.display)
        return True

    def sendTouchUp(self, X, Y):
        self.libXtst.XTestFakeMotionEvent(self.display, self.current_screen, int(X), int(Y), self.X_CurrentTime)
        self.libXtst.XTestFakeButtonEvent(self.display, 1, self.X_False, self.X_CurrentTime)
        self.libXtst.XFlush(self.display)
        return True

    def sendType(self, string):
        for character in string:
            keysim = self.libXtst.XStringToKeysym(str(character))
            keycode = self.libXtst.XKeysymToKeycode(self.display, keysim)
            self.libXtst.XTestFakeKeyEvent(self.display, keycode, self.X_True, self.X_CurrentTime)
            self.libXtst.XTestFakeKeyEvent(self.display, keycode, self.X_False, self.X_CurrentTime)
            self.libXtst.XFlush(self.display)
        return True

    def sendTap(self, X, Y):
        self.libXtst.XTestFakeMotionEvent(self.display, -1, int(X), int(Y), self.X_CurrentTime)
        self.libXtst.XTestFakeButtonEvent(self.display, 1, self.X_True, self.X_CurrentTime)
        self.libXtst.XTestFakeButtonEvent(self.display, 1, self.X_False, self.X_CurrentTime)
        self.libXtst.XFlush(self.display)
        return True

    def recvScreenshot(self, filename):
        # This is a hack to get this stack quickly testable,
        # let's replace this with Xlib/libMagick functions, too...
        import commands
        commands.getstatusoutput("xwd -root -out '%s.xwd'" % (filename,))
        commands.getstatusoutput("convert '%s.xwd' '%s'" % (filename, filename))
        return True
