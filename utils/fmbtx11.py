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

        self.libX11.XOpenDisplay.restype   = ctypes.c_void_p
        self.libX11.XDefaultScreen.restype = ctypes.c_int

        self.X_True = ctypes.c_int(1)
        self.X_False = ctypes.c_int(0)
        self.X_CurrentTime = ctypes.c_ulong(0)
        self.NULL = ctypes.c_char_p(0)
        self.display = self.libX11.XOpenDisplay(self.NULL)
        self.current_screen = self.libX11.XDefaultScreen(self.display)

    def __del__(self):
        self.libX11.XCloseDisplay(self.display)

    def _thingToKeycode(self, key):
        keysym = self.libX11.XStringToKeysym(key)
        if keysym == 0:
            return None
        return self.libX11.XKeysymToKeycode(self.display, keysym)

    def sendTap(self, x, y):
        self.libXtst.XTestFakeMotionEvent(self.display, self.current_screen, int(x), int(y), self.X_CurrentTime)
        self.libXtst.XTestFakeButtonEvent(self.display, 1, self.X_True, self.X_CurrentTime)
        self.libXtst.XTestFakeButtonEvent(self.display, 1, self.X_False, self.X_CurrentTime)
        self.libX11.XFlush(self.display)
        return True

    def sendPress(self, key):
        keycode = self._thingToKeycode(key)
        if keycode == None: return False
        self.libXtst.XTestFakeKeyEvent(self.display, keycode, self.X_True, self.X_CurrentTime)
        self.libXtst.XTestFakeKeyEvent(self.display, keycode, self.X_False, self.X_CurrentTime)
        self.libX11.XFlush(self.display)
	return True

    def sendKeyDown(self, key):
        keycode = self._thingToKeycode(key)
        if keycode == None: return False
        self.libXtst.XTestFakeKeyEvent(self.display, keycode, self.X_True, self.X_CurrentTime)
        self.libX11.XFlush(self.display)
        return True

    def sendKeyUp(self, key):
        keycode = self._thingToKeycode(key)
        if keycode == None: return False
        self.libXtst.XTestFakeKeyEvent(self.display, keycode, self.X_False, self.X_CurrentTime)
        self.libX11.XFlush(self.display)
        return True

    def sendTouchMove(self, x, y):
        self.libXtst.XTestFakeMotionEvent(self.display, self.current_screen, int(x), int(y), self.X_CurrentTime)
        self.libX11.XFlush(self.display)
        return True

    def sendTouchDown(self, x, y):
        self.libXtst.XTestFakeMotionEvent(self.display, self.current_screen, int(x), int(y), self.X_CurrentTime)
        self.libXtst.XTestFakeButtonEvent(self.display, 1, self.X_True, self.X_CurrentTime)
        self.libX11.XFlush(self.display)
        return True

    def sendTouchUp(self, x, y):
        self.libXtst.XTestFakeMotionEvent(self.display, self.current_screen, int(x), int(y), self.X_CurrentTime)
        self.libXtst.XTestFakeButtonEvent(self.display, 1, self.X_False, self.X_CurrentTime)
        self.libX11.XFlush(self.display)
        return True

    def sendType(self, string):
        for character in string:
            self.sendPress(character)
        return True

    def sendTap(self, x, y):
        self.libXtst.XTestFakeMotionEvent(self.display, self.current_screen, int(x), int(y), self.X_CurrentTime)
        self.libXtst.XTestFakeButtonEvent(self.display, 1, self.X_True, self.X_CurrentTime)
        self.libXtst.XTestFakeButtonEvent(self.display, 1, self.X_False, self.X_CurrentTime)
        self.libX11.XFlush(self.display)
        return True

    def recvScreenshot(self, filename):
        # This is a hack to get this stack quickly testable,
        # let's replace this with Xlib/libMagick functions, too...
        import commands
        commands.getstatusoutput("xwd -root -out '%s.xwd'" % (filename,))
        commands.getstatusoutput("convert '%s.xwd' '%s'" % (filename, filename))
        return True
