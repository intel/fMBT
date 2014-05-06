# fMBT, free Model Based Testing tool
# Copyright (c) 2014, Intel Corporation.
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

"""This library implements routines for simulating user input through
Xtst and taking screenshots with XGetImage.
"""

import ctypes
import zlib

libX11 = ctypes.CDLL("libX11.so.6")
libXtst = ctypes.CDLL("libXtst.so.6")

class XImage(ctypes.Structure):
    _fields_ = [
        ('width'            , ctypes.c_int),
        ('height'           , ctypes.c_int),
        ('xoffset'          , ctypes.c_int),
        ('format'           , ctypes.c_int),
        ('data'             , ctypes.c_void_p),
        ('byte_order'       , ctypes.c_int),
        ('bitmap_unit'      , ctypes.c_int),
        ('bitmap_bit_order' , ctypes.c_int),
        ('bitmap_pad'       , ctypes.c_int),
        ('depth'            , ctypes.c_int),
        ('bytes_per_line'   , ctypes.c_int),
        ('bits_per_pixel'   , ctypes.c_int)]

libX11.XAllPlanes.restype = ctypes.c_ulong

libX11.XOpenDisplay.argtypes = [ctypes.c_char_p]
libX11.XOpenDisplay.restype = ctypes.c_void_p

libX11.XCloseDisplay.argtypes = [ctypes.c_void_p]

libX11.XDefaultScreen.argtypes = [ctypes.c_void_p]
libX11.XDefaultScreen.restype = ctypes.c_int

libX11.XDisplayKeycodes.argtypes = [
    ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]

libX11.XFlush.argtypes = [ctypes.c_void_p]

libX11.XGetGeometry.argtypes = [
    ctypes.c_void_p, ctypes.c_uint, # display, drawable
    ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, # root, x, y
    ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, # width, height, borderw
    ctypes.c_void_p] # depth

libX11.XGetImage.argtypes = [
    ctypes.c_void_p, ctypes.c_uint, # display, drawable
    ctypes.c_int, ctypes.c_int, # x, y
    ctypes.c_int, ctypes.c_int, # width, height
    ctypes.c_int, ctypes.c_int] # plane_mask, format
libX11.XGetImage.restype = ctypes.POINTER(XImage)

libX11.XGetKeyboardMapping.argtypes = [
    ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_void_p]
if ctypes.sizeof(ctypes.c_void_p) == 4: # 32-bit
    libX11.XGetKeyboardMapping.restype = ctypes.POINTER(ctypes.c_uint32)
else: # 64-bit
    libX11.XGetKeyboardMapping.restype = ctypes.POINTER(ctypes.c_uint64)

libX11.XKeysymToKeycode.argtypes = [
    ctypes.c_void_p, ctypes.c_int]

libX11.XRootWindow.argtypes = [
    ctypes.c_void_p, ctypes.c_int]
libX11.XRootWindow.restype = ctypes.c_uint32

libXtst.XTestFakeKeyEvent.argtypes = [
    ctypes.c_void_p, ctypes.c_uint, ctypes.c_int, ctypes.c_ulong]
libXtst.XTestFakeButtonEvent.argtypes = [
    ctypes.c_void_p, ctypes.c_uint, ctypes.c_int, ctypes.c_ulong]
libXtst.XTestFakeMotionEvent.argtypes = [
    ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_ulong]

_NULL           = ctypes.c_char_p(0)
_NoSymbol       = 0
_X_AllPlanes    = libX11.XAllPlanes()
_X_CurrentTime  = ctypes.c_ulong(0)
_X_False        = ctypes.c_int(0)
_X_True         = ctypes.c_int(1)
_X_ZPixmap      = ctypes.c_int(2)

class Display(object):
    def __init__(self, display=""):
        """Parameters:

          display (string, optional)
                  X display to connect to.
                  Example: display=":0". The default is "", that is,
                  the default X display in the DISPLAY environment
                  variable will be used.
        """
        self._displayName = display
        if display and isinstance(display, str):
            self._display = libX11.XOpenDisplay(display)
        elif not display:
            self._display = libX11.XOpenDisplay(_NULL)
        else:
            raise ValueError('Invalid display: "%s"')
        if not self._display:
            raise X11ConnectionError("Cannot connect to X11 display")
        self._current_screen = libX11.XDefaultScreen(self._display)
        self._root_window = libX11.XRootWindow(self._display, self._current_screen)

        _rw = ctypes.c_uint(0)
        _x = ctypes.c_int(0)
        _y = ctypes.c_int(0)
        root_width = ctypes.c_uint(0)
        root_height = ctypes.c_uint(0)
        _bwidth = ctypes.c_uint(0)
        root_depth = ctypes.c_uint(0)
        libX11.XGetGeometry(
            self._display, self._root_window,
            ctypes.byref(_rw),
            ctypes.byref(_x), ctypes.byref(_y),
            ctypes.byref(root_width), ctypes.byref(root_height),
            ctypes.byref(_bwidth), ctypes.byref(root_depth))
        self._width, self._height = root_width.value, root_height.value
        self._depth = root_depth.value

        self._cMinKeycode        = ctypes.c_int(0)
        self._cMaxKeycode        = ctypes.c_int(0)
        self._cKeysymsPerKeycode = ctypes.c_int(0)
        libX11.XDisplayKeycodes(self._display,
                                ctypes.byref(self._cMinKeycode),
                                ctypes.byref(self._cMaxKeycode))
        self._keysyms = libX11.XGetKeyboardMapping(
            self._display,
            self._cMinKeycode,
            (self._cMaxKeycode.value - self._cMinKeycode.value) + 1,
            ctypes.byref(self._cKeysymsPerKeycode))
        self._modifierKeycodes = []
        self._shiftModifier  = libX11.XKeysymToKeycode(self._display, libX11.XStringToKeysym("Shift_L"))
        self._level3Modifier = libX11.XKeysymToKeycode(self._display, libX11.XStringToKeysym("ISO_Level3_Shift"))
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
            libX11.XCloseDisplay(self._display)

    def _typeChar(self, origChar, press=True, release=True):
        modifiers = []
        c = self._specialCharToXString.get(origChar, origChar)
        keysym = libX11.XStringToKeysym(c)
        if keysym == _NoSymbol:
            return False
        keycode = libX11.XKeysymToKeycode(self._display, keysym)

        first = (keycode - self._cMinKeycode.value) * self._cKeysymsPerKeycode.value

        for modifier_index, modifier in enumerate([self._shiftModifier, None, None, self._level3Modifier]):
            if modifier == None: continue
            try:
                if chr(self._keysyms[first + modifier_index + 1]) == origChar:
                    modifiers.append(modifier)
                    break
            except ValueError: pass

        for m in modifiers:
            libXtst.XTestFakeKeyEvent(self._display, m, _X_True, _X_CurrentTime)
            libX11.XFlush(self._display)

        if press:
            libXtst.XTestFakeKeyEvent(self._display, keycode, _X_True, _X_CurrentTime)
        if release:
            libXtst.XTestFakeKeyEvent(self._display, keycode, _X_False, _X_CurrentTime)
        libX11.XFlush(self._display)

        for m in modifiers[::-1]:
            libXtst.XTestFakeKeyEvent(self._display, m, _X_False, _X_CurrentTime)
            libX11.XFlush(self._display)

        return True

    def sendKeyDown(self, key):
        return self._typeChar(key, press=True, release=False)

    def sendKeyUp(self, key):
        return self._typeChar(key, press=False, release=True)

    def sendPress(self, key):
	return self._typeChar(key, press=True, release=True)

    def sendTap(self, x, y, button=1):
        libXtst.XTestFakeMotionEvent(self._display, self._current_screen, int(x), int(y), _X_CurrentTime)
        libXtst.XTestFakeButtonEvent(self._display, button, _X_True, _X_CurrentTime)
        libXtst.XTestFakeButtonEvent(self._display, button, _X_False, _X_CurrentTime)
        libX11.XFlush(self._display)
        return True

    def sendTouchMove(self, x, y):
        libXtst.XTestFakeMotionEvent(self._display, self._current_screen, int(x), int(y), _X_CurrentTime)
        libX11.XFlush(self._display)
        return True

    def sendTouchDown(self, x, y, button=1):
        libXtst.XTestFakeMotionEvent(self._display, self._current_screen, int(x), int(y), _X_CurrentTime)
        libXtst.XTestFakeButtonEvent(self._display, button, _X_True, _X_CurrentTime)
        libX11.XFlush(self._display)
        return True

    def sendTouchUp(self, x, y, button=1):
        libXtst.XTestFakeMotionEvent(self._display, self._current_screen, int(x), int(y), _X_CurrentTime)
        libXtst.XTestFakeButtonEvent(self._display, button, _X_False, _X_CurrentTime)
        libX11.XFlush(self._display)
        return True

    def sendType(self, string):
        success = True
        for character in string:
            success = success and self.sendPress(character)
        return success

    def recvScreenshot(self):
        image_p = libX11.XGetImage(self._display, self._root_window,
                                   0, 0, self._width, self._height,
                                   _X_AllPlanes, _X_ZPixmap)
        image = image_p[0]
        # FMBTRAWX11 image format header:
        # FMBTRAWX11 [width] [height] [color depth] [bits per pixel]<linefeed>
        # Binary data
        rawfmbt_header = "FMBTRAWX11 %d %d %d %d\n" % (
            image.width, image.height, self._depth, image.bits_per_pixel)
        rawfmbt_data = ctypes.string_at(image.data, image.height * image.bytes_per_line)
        compressed_image = rawfmbt_header + zlib.compress(rawfmbt_data, 3)
        libX11.XDestroyImage(image_p)
        return compressed_image

class X11ConnectionError(Exception): pass
