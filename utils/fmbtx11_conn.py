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
import getpass
import os
import subprocess
import zlib

try:
    import fmbtpng
except ImportError:
    fmbtpng = None

try:
    import gi
    gi.require_version('Atspi', '2.0')
    import pyatspi
    """gsettings set org.gnome.desktop.interface toolkit-accessibility true"""
except ImportError:
    pyatspi = None

_g_current_user = getpass.getuser()

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

libX11.XFree.argtypes = [ctypes.c_void_p]

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

libX11.XQueryTree.argtypes = [
    ctypes.c_void_p, # display
    ctypes.c_uint32, # window
    ctypes.c_void_p, # root_return
    ctypes.c_void_p, # parent_return
    ctypes.c_void_p, # children_return
    ctypes.c_void_p] # nchildren_return
libX11.XQueryTree.restype = ctypes.c_int

libX11.XFetchName.argtypes = [
    ctypes.c_void_p, # display
    ctypes.c_uint32, # window
    ctypes.c_void_p] # window_name_return
libX11.XFetchName.restype = ctypes.c_int

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

    def _typeChar(self, origChar, press=True, release=True, modifiers=[]):
        _modifiers = [libX11.XKeysymToKeycode(
            self._display, libX11.XStringToKeysym(c)) for c in modifiers]
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
                    _modifiers.append(modifier)
                    break
            except ValueError: pass

        for m in _modifiers:
            libXtst.XTestFakeKeyEvent(self._display, m, _X_True, _X_CurrentTime)
            libX11.XFlush(self._display)

        if press:
            libXtst.XTestFakeKeyEvent(self._display, keycode, _X_True, _X_CurrentTime)
        if release:
            libXtst.XTestFakeKeyEvent(self._display, keycode, _X_False, _X_CurrentTime)
        libX11.XFlush(self._display)

        for m in _modifiers[::-1]:
            libXtst.XTestFakeKeyEvent(self._display, m, _X_False, _X_CurrentTime)
            libX11.XFlush(self._display)

        return True

    def sendKeyDown(self, key, modifiers=[]):
        return self._typeChar(key, press=True, release=False, modifiers=modifiers)

    def sendKeyUp(self, key, modifiers=[]):
        return self._typeChar(key, press=False, release=True, modifiers=modifiers)

    def sendPress(self, key, modifiers=[]):
	return self._typeChar(key, press=True, release=True, modifiers=modifiers)

    def sendTap(self, x, y, button=1):
        libXtst.XTestFakeMotionEvent(self._display, self._current_screen, int(x), int(y), _X_CurrentTime)
        libXtst.XTestFakeButtonEvent(self._display, button, _X_True, _X_CurrentTime)
        libXtst.XTestFakeButtonEvent(self._display, button, _X_False, _X_CurrentTime)
        libX11.XFlush(self._display)
        return True

    def sendTouchMove(self, x, y, button=None):
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

    def recvWindowBbox(self, window, parentBbox=None):
        rw = ctypes.c_uint32(0)
        x = ctypes.c_int(0)
        y = ctypes.c_int(0)
        width = ctypes.c_uint(0)
        height = ctypes.c_uint(0)
        bwidth = ctypes.c_uint(0)
        depth = ctypes.c_uint(0)
        libX11.XGetGeometry(
            self._display, window,
            ctypes.byref(rw),
            ctypes.byref(x), ctypes.byref(y),
            ctypes.byref(width), ctypes.byref(height),
            ctypes.byref(bwidth), ctypes.byref(depth))
        if parentBbox == None:
            parent = self.recvParentWindow(window)
            if parent != 0:
                parentBbox = self.recvWindowBbox(parent)
            else:
                parentBbox = (0, 0, 0, 0)
        left = int(x.value + parentBbox[0])
        top = int(y.value + parentBbox[1])
        bbox = (left, top, int(left + width.value), int(top + height.value))
        return bbox

    def recvParentWindow(self, window):
        root = ctypes.c_uint32(0)
        parent = ctypes.c_uint32(0)
        children = ctypes.POINTER(ctypes.c_uint32)()
        nchildren = ctypes.c_int(0)
        libX11.XQueryTree(self._display,
                          window,
                          ctypes.byref(root),
                          ctypes.byref(parent),
                          ctypes.byref(children),
                          ctypes.byref(nchildren))
        if children:
            libX11.XFree(children)
        return int(parent.value)

    def recvChildWindows(self, window=None, recursive=True, parentBbox=None):
        if window == None:
            window = self._root_window
        if parentBbox == None:
            parentBbox = self.recvWindowBbox(window)
        root = ctypes.c_uint32(0)
        parent = ctypes.c_uint32(0)
        children = ctypes.POINTER(ctypes.c_uint32)()
        nchildren = ctypes.c_int(0)
        libX11.XQueryTree(self._display,
                          window,
                          ctypes.byref(root),
                          ctypes.byref(parent),
                          ctypes.byref(children),
                          ctypes.byref(nchildren))
        windows = []
        window_name = ctypes.c_char_p()
        for c in xrange(nchildren.value):
            if ctypes.sizeof(ctypes.c_void_p) == 4: # 32-bit
                child = int(children[c])
            else: # 64-bit
                child = int(children[c*2])
            libX11.XFetchName(self._display, child, ctypes.byref(window_name))
            if window_name:
                name = window_name
            else:
                name = None
            bbox = self.recvWindowBbox(child, parentBbox=parentBbox)
            window_dict = {
                "window": child,
                "parent": int(parent.value),
                "name": window_name.value,
                "bbox": bbox,
            }
            windows.append(window_dict)
            libX11.XFree(window_name)
            if recursive:
                windows.extend(self.recvChildWindows(child, True, parentBbox=bbox))
        libX11.XFree(children)
        return windows

    def recvScreenshot(self, fmt="FMBTRAWX11"):
        image_p = libX11.XGetImage(self._display, self._root_window,
                                   0, 0, self._width, self._height,
                                   _X_AllPlanes, _X_ZPixmap)
        image = image_p[0]
        if fmt.upper() == "FMBTRAWX11" or fmbtpng == None:
            # FMBTRAWX11 image format header:
            # FMBTRAWX11 [width] [height] [color depth] [bits per pixel]<linefeed>
            # Binary data
            rawfmbt_header = "FMBTRAWX11 %d %d %d %d\n" % (
                image.width, image.height, self._depth, image.bits_per_pixel)
            rawfmbt_data = ctypes.string_at(image.data, image.height * image.bytes_per_line)
            compressed_image = rawfmbt_header + zlib.compress(rawfmbt_data, 3)
        elif fmt.upper() == "PNG" and fmbtpng != None:
            rawdata = ctypes.string_at(image.data, image.height * image.bytes_per_line)
            if image.bits_per_pixel == 16:
                compressed_image = fmbtpng.raw2png(rawdata, image.width, image.height, 5, "RGB565")
            else:
                compressed_image = fmbtpng.raw2png(rawdata, image.width, image.height, image.bits_per_pixel / 4, "BGR_")
        else:
            compressed_image = None

        libX11.XDestroyImage(image_p)
        return compressed_image

    def recvScreenUpdated(self, waitTime, pollDelay):
        return None # optimization not implemented

def shellSOE(command, username, asyncStatus, asyncOut, asyncError, usePty):
    """run command as user, return (success, (exit status, output, error))"""
    if not username:
        username = _g_current_user
    if username != _g_current_user:
        command = ["sudo", "-u", username, "bash", "-c", command]
    if usePty:
        if isinstance(command, str):
            spawn_command = shlex.split(command)
        else:
            spawn_command = command
        command = '''python -c "import pty; pty.spawn(%s)" ''' % (repr(spawn_command),)
    in_child_process = False
    if (asyncStatus, asyncOut, asyncError) != (None, None, None):
        # prepare for decoupled asynchronous execution
        if asyncStatus == None: asyncStatus = "/dev/null"
        if asyncOut == None: asyncOut = "/dev/null"
        if asyncError == None: asyncError = "/dev/null"
        try:
            stdinFile = file("/dev/null", "r")
            stdoutFile = file(asyncOut, "w")
            stderrFile = file(asyncError, "w", 0)
            statusFile = file(asyncStatus, "w")
        except IOError, e:
            return False, (None, None, e)
        try:
            in_child_process = (os.fork() == 0)
            if not in_child_process:
                # parent returns after successful fork, there no
                # direct visibility to async child process beyond this
                # point.
                stdinFile.close()
                stdoutFile.close()
                stderrFile.close()
                statusFile.close()
                return True, (0, None, None)
        except OSError, e:
            if in_child_process:
                statusFile.write(str(e) + "\n")
                statusFile.close()
                sys.exit(0)
            return False, (None, None, e)
        os.setsid()
    else:
        stdinFile = subprocess.PIPE
        stdoutFile = subprocess.PIPE
        stderrFile = subprocess.PIPE
    try:
        p = subprocess.Popen(command,
                             shell=isinstance(command, str),
                             stdin=stdinFile,
                             stdout=stdoutFile,
                             stderr=stderrFile,
                             close_fds=True)
    except Exception, e:
        if in_child_process:
            statusFile.write("127\n")
            statusFile.close()
            sys.exit(0)
        return False, (None, None, e)
    if asyncStatus == None and asyncOut == None and asyncError == None:
        # synchronous execution, read stdout and stderr
        out, err = p.communicate()
    else:
        # asynchronous execution, store status to file
        statusFile.write(str(p.wait()) + "\n")
        statusFile.close()
        out, err = None, None
    if in_child_process:
        sys.exit(0) # child process ends here, do not return to pythonshare-server
    return True, (p.returncode, out, err)

def atspiApplicationList():
    if not pyatspi:
        raise ValueError('required library missing: pyatspi')
    rv = []
    for app in pyatspi.Registry.getDesktop(0):
        rv.append(app.name)
    return rv

def atspiAddItem(item, parent, foundItems):
    """Adds an item to foundItems"""
    itemId = repr(item)
    rv = {
        "id": itemId,
        "parent": repr(parent) if parent != None else None,
    }
    try:
        rv["role"] = item.get_role_name()
    except:
        rv["role"] = None
    rv["class"] = rv["role"]
    try:
        rv["name"] = item.name
    except:
        rv["name"] = None
    try:
        bbox = item.queryComponent().getExtents(pyatspi.DESKTOP_COORDS)
        x, y, w, h = bbox
        rv["bbox"] = (x, y, x+w, y+h)
    except NotImplementedError:
        rv["bbox"] = (-1, -1, -1, -1)
    try:
        rv["attributes"] = dict([a.split(':', 1) for a in item.getAttributes()])
    except:
        rv["attributes"] = None
    rv["actions"] = []
    try:
        actions = item.queryAction()
        for action in xrange(actions.nActions):
            rv["actions"].append(actions.getName(action))
    except NotImplementedError:
        pass
    rv["text"] = ""
    try:
        text = item.queryText()
        try:
            rv["text"] = text.getText(0, text.characterCount)
        except Exception, e:
            pass
    except:
        pass
    foundItems.append(rv)

def atspiScanItems(item, parent, foundItems):
    """Scan items

    Parameters:

      item (atspi object):
              item whose children will be scanned

      parent (atspi object or None):
              parent of the item (the first parameter)

      foundItems (list, out parameter):
              found items, including the item, will be appended
              to this list.
    """
    atspiAddItem(item, parent, foundItems)
    for child in item:
        atspiScanItems(child, item, foundItems)

def atspiViewData(window):
    """Return view data on a window

    Parameters:

      window (string):
              Name of the application.
    """
    if not pyatspi:
        raise ValueError('required library missing: pyatspi')
    for app in pyatspi.Registry.getDesktop(0):
        if app.name == window:
            break
    else:
        raise ValueError('cannot find window "%s"' % (window,))
    foundItems = []
    atspiScanItems(app, None, foundItems)
    return foundItems

class X11ConnectionError(Exception): pass
