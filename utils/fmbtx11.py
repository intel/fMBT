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

class Screen(fmbtgti.GUITestInterface):
    def __init__(self, display=""):
        fmbtgti.GUITestInterface.__init__(self)
        self.setConnection(X11Connection(display))

class X11Connection(fmbtgti.GUITestConnection):
    def __init__(self, display):
        fmbtgti.GUITestConnection.__init__(self)
        self.libX11 = ctypes.CDLL("libX11.so.6")
        self.libXtst = ctypes.CDLL("libXtst.so.6")

        self.libX11.XOpenDisplay.restype        = ctypes.c_void_p
        self.libX11.XDefaultScreen.restype      = ctypes.c_int
        if ctypes.sizeof(ctypes.c_void_p) == 4: # 32-bit
            self.libX11.XGetKeyboardMapping.restype = ctypes.POINTER(ctypes.c_uint32)
        else: # 64-bit
            self.libX11.XGetKeyboardMapping.restype = ctypes.POINTER(ctypes.c_uint64)

        self._X_True         = ctypes.c_int(1)
        self._X_False        = ctypes.c_int(0)
        self._X_CurrentTime  = ctypes.c_ulong(0)
        self._NULL           = ctypes.c_char_p(0)
        self._NoSymbol       = 0
        if display and isinstance(display, str):
            self._display        = self.libX11.XOpenDisplay(display)
        elif not display:
            self._display        = self.libX11.XOpenDisplay(self._NULL)
        else:
            raise ValueError('Invalid display: "%s"')
        if not self._display:
            raise X11ConnectionError("Cannot connect to X11 display")
        self._current_screen = self.libX11.XDefaultScreen(self._display)

        ref                      = ctypes.byref
        self._cMinKeycode        = ctypes.c_int(0)
        self._cMaxKeycode        = ctypes.c_int(0)
        self._cKeysymsPerKeycode = ctypes.c_int(0)
        self.libX11.XDisplayKeycodes(self._display, ref(self._cMinKeycode), ref(self._cMaxKeycode))
        self._keysyms = self.libX11.XGetKeyboardMapping(
            self._display, self._cMinKeycode, (self._cMaxKeycode.value - self._cMinKeycode.value) + 1,
            ref(self._cKeysymsPerKeycode))
        self._modifierKeycodes = []
        self._shiftModifier  = self.libX11.XKeysymToKeycode(self._display, self.libX11.XStringToKeysym("Shift_L"))
        self._level3Modifier = self.libX11.XKeysymToKeycode(self._display, self.libX11.XStringToKeysym("ISO_Level3_Shift"))
        self._specialCharToXString = {
            '\n': "Return", '\\': "backslash",
            ' ': "space", '_': "underscore", '!': "exclam", '"': "quotedbl",
            '#': "numbersign", '$': "dollar", '%': "percent",
            '&': "ampersand", "'": "apostrophe",
            '(': "parenleft", ')': "parenright",
            '[': "bracketleft", ']': "bracketright",
            '{': "braceleft", '}': "braceright",
            '|': "bar", '~': "asciitilde",
            '*': "asterisk", '+': "plus", '-': "minus", '/': "slash",
            '.': "period", ',': "comma", ':': "colon", ';': "semicolon",
            '<': "less", '=': "equal", '>': "greater",
            '?': "question", '@': "at"}

    def __del__(self):
        if self._display:
            self.libX11.XCloseDisplay(self._display)

    def _typeChar(self, origChar, press=True, release=True):
        modifiers = []
        c         = self._specialCharToXString.get(origChar, origChar)
        keysym    = self.libX11.XStringToKeysym(c)
        if keysym == self._NoSymbol:
            return False
        keycode   = self.libX11.XKeysymToKeycode(self._display, keysym)

        first = (keycode - self._cMinKeycode.value) * self._cKeysymsPerKeycode.value

        for modifier_index, modifier in enumerate([self._shiftModifier, None, None, self._level3Modifier]):
            if modifier == None: continue
            try:
                if chr(self._keysyms[first + modifier_index + 1]) == origChar:
                    modifiers.append(modifier)
                    break
            except ValueError: pass

        for m in modifiers:
            self.libXtst.XTestFakeKeyEvent(self._display, m, self._X_True, self._X_CurrentTime)
            self.libX11.XFlush(self._display)

        if press:
            self.libXtst.XTestFakeKeyEvent(self._display, keycode, self._X_True, self._X_CurrentTime)
        if release:
            self.libXtst.XTestFakeKeyEvent(self._display, keycode, self._X_False, self._X_CurrentTime)
        self.libX11.XFlush(self._display)

        for m in modifiers[::-1]:
            self.libXtst.XTestFakeKeyEvent(self._display, m, self._X_False, self._X_CurrentTime)
            self.libX11.XFlush(self._display)

        return True

    def sendTap(self, x, y):
        self.libXtst.XTestFakeMotionEvent(self._display, self._current_screen, int(x), int(y), self._X_CurrentTime)
        self.libXtst.XTestFakeButtonEvent(self._display, 1, self._X_True, self._X_CurrentTime)
        self.libXtst.XTestFakeButtonEvent(self._display, 1, self._X_False, self._X_CurrentTime)
        self.libX11.XFlush(self._display)
        return True

    def sendPress(self, key):
	return self._typeChar(key, press=True, release=True)

    def sendKeyDown(self, key):
        return self._typeChar(key, press=True, release=False)

    def sendKeyUp(self, key):
        return self._typeChar(key, press=False, release=True)

    def sendTouchMove(self, x, y):
        self.libXtst.XTestFakeMotionEvent(self._display, self._current_screen, int(x), int(y), self._X_CurrentTime)
        self.libX11.XFlush(self._display)
        return True

    def sendTouchDown(self, x, y):
        self.libXtst.XTestFakeMotionEvent(self._display, self._current_screen, int(x), int(y), self._X_CurrentTime)
        self.libXtst.XTestFakeButtonEvent(self._display, 1, self._X_True, self._X_CurrentTime)
        self.libX11.XFlush(self._display)
        return True

    def sendTouchUp(self, x, y):
        self.libXtst.XTestFakeMotionEvent(self._display, self._current_screen, int(x), int(y), self._X_CurrentTime)
        self.libXtst.XTestFakeButtonEvent(self._display, 1, self._X_False, self._X_CurrentTime)
        self.libX11.XFlush(self._display)
        return True

    def sendType(self, string):
        success = True
        for character in string:
            success = success and self.sendPress(character)
        return success

    def sendTap(self, x, y):
        self.libXtst.XTestFakeMotionEvent(self._display, self._current_screen, int(x), int(y), self._X_CurrentTime)
        self.libXtst.XTestFakeButtonEvent(self._display, 1, self._X_True, self._X_CurrentTime)
        self.libXtst.XTestFakeButtonEvent(self._display, 1, self._X_False, self._X_CurrentTime)
        self.libX11.XFlush(self._display)
        return True

    def recvScreenshot(self, filename):
        # This is a hack to get this stack quickly testable,
        # let's replace this with Xlib/libMagick functions, too...
        import commands
        commands.getstatusoutput("xwd -root -out '%s.xwd'" % (filename,))
        commands.getstatusoutput("convert '%s.xwd' '%s'" % (filename, filename))
        return True

class FMBTX11Error(Exception): pass
class X11ConnectionError(Exception): pass
