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

import base64
import cPickle
import ctypes
import fcntl
import glob
import os
import platform
import re
import shutil
import string
import struct
import subprocess
import sys
import time
import zlib
import termios

import fmbtuinput
fmbtuinput.refreshDeviceInfo()

if "--debug" in sys.argv:
    g_debug = True
else:
    g_debug = False

def debug(msg):
    if g_debug:
        sys.stdout.write("debug: %s\n" % (msg,))
        sys.stdout.flush()

iAmRoot = (os.getuid() == 0)
virtualInputDeviceAdded = False

try:
    libc           = ctypes.CDLL("libc.so.6")
    libX11         = ctypes.CDLL("libX11.so.6")
    libXtst        = ctypes.CDLL("libXtst.so.6")
    g_Xavailable = True
    g_keyb = None # no need for virtual keyboard
except OSError:
    g_Xavailable = False

if g_Xavailable:
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

    libc.write.argtypes           = [ctypes.c_int, ctypes.c_void_p, ctypes.c_size_t]
    libX11.XAllPlanes.restype     = ctypes.c_ulong
    libX11.XGetImage.restype      = ctypes.POINTER(XImage)
    libX11.XRootWindow.restype    = ctypes.c_uint32
    libX11.XOpenDisplay.restype   = ctypes.c_void_p
    libX11.XDefaultScreen.restype = ctypes.c_int
    libX11.XGetKeyboardMapping.restype = ctypes.POINTER(ctypes.c_uint32)

    # X11 constants, see Xlib.h

    X_CurrentTime  = ctypes.c_ulong(0)
    X_False        = ctypes.c_int(0)
    X_NULL         = ctypes.c_void_p(0)
    X_True         = ctypes.c_int(1)
    X_ZPixmap      = ctypes.c_int(2)
    NoSymbol       = 0

# InputKeys contains key names known to input devices, see
# linux/input.h or http://www.usb.org/developers/hidpage. The order is
# significant, because keyCode = InputKeys.index(keyName).
InputKeys = [
    "RESERVED", "ESC","1", "2", "3", "4", "5", "6", "7", "8", "9", "0",
    "MINUS", "EQUAL", "BACKSPACE", "TAB",
    "Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P",
    "LEFTBRACE", "RIGHTBRACE", "ENTER", "LEFTCTRL",
    "A", "S", "D", "F", "G", "H", "J", "K", "L",
    "SEMICOLON", "APOSTROPHE", "GRAVE", "LEFTSHIFT", "BACKSLASH",
    "Z", "X", "C", "V", "B", "N", "M",
    "COMMA", "DOT", "SLASH", "RIGHTSHIFT", "KPASTERISK", "LEFTALT",
    "SPACE", "CAPSLOCK",
    "F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10",
    "NUMLOCK", "SCROLLLOCK",
    "KP7", "KP8", "KP9", "KPMINUS",
    "KP4", "KP5", "KP6", "KPPLUS",
    "KP1", "KP2", "KP3", "KP0", "KPDOT",
    "undefined0",
    "ZENKAKUHANKAKU", "102ND", "F11", "F12", "RO",
    "KATAKANA", "HIRAGANA", "HENKAN", "KATAKANAHIRAGANA", "MUHENKAN",
    "KPJPCOMMA", "KPENTER", "RIGHTCTRL", "KPSLASH", "SYSRQ", "RIGHTALT",
    "LINEFEED", "HOME", "UP", "PAGEUP", "LEFT", "RIGHT", "END", "DOWN",
    "PAGEDOWN", "INSERT", "DELETE", "MACRO",
    "MUTE", "VOLUMEDOWN", "VOLUMEUP",
    "POWER",
    "KPEQUAL", "KPPLUSMINUS", "PAUSE", "SCALE", "KPCOMMA", "HANGEUL",
    "HANGUEL", "HANJA", "YEN", "LEFTMETA", "RIGHTMETA", "COMPOSE"]
_inputKeyNameToCode={}
for c, n in enumerate(InputKeys):
    _inputKeyNameToCode[n] = c

# See struct input_event in /usr/include/linux/input.h
if platform.architecture()[0] == "32bit": _input_event = 'IIHHi'
else: _input_event = 'QQHHi'
# Event and keycodes are in input.h, too.
_EV_KEY = 0x01
_EV_ABS             = 0x03
_ABS_X              = 0x00
_ABS_Y              = 0x01
_ABS_MT_SLOT        = 0x2f
_ABS_MT_POSITION_X  = 0x35
_ABS_MT_POSITION_Y  = 0x36
_ABS_MT_TRACKING_ID = 0x39

_BTN_MOUSE          = 0x110

# Set input device names (in /proc/bus/input/devices)
# for pressing hardware keys.
try: cpuinfo = file("/proc/cpuinfo").read()
except: cpuinfo = ""

def readDeviceInfo():
    global devices
    try:
        devices = file("/proc/bus/input/devices").read()
    except:
        devices = ""
readDeviceInfo()

if 'TRATS' in cpuinfo:
    # Running on Lunchbox
    hwKeyDevice = {
        "POWER": "gpio-keys",
        "VOLUMEUP": "gpio-keys",
        "VOLUMEDOWN": "gpio-keys",
        "HOME": "gpio-keys"
        }
    _inputKeyNameToCode["HOME"] = 139
    if iAmRoot:
        touch_device = fmbtuinput.Touch().open("/dev/input/event2")
        mtInputDevFd = touch_device._fd
elif 'QEMU Virtual CPU' in cpuinfo:
    # Running on Tizen emulator
    hwKeyDevice = {
        "POWER": "Power Button",
        "VOLUMEUP": "AT Translated Set 2 hardkeys",
        "VOLUMEDOWN": "AT Translated Set 2 hardkeys",
        "HOME": "AT Translated Set 2 hardkeys"
        }
    _inputKeyNameToCode["HOME"] = 139
    if iAmRoot:
        touch_device = fmbtuinput.Touch().open("/dev/input/event2")
        mtInputDevFd = touch_device._fd
elif 'Synaptics_RMI4_touchkey' in devices:
    # Running on Geek
    hwKeyDevice = {
        "POWER": "mid_powerbtn",
        "VOLUMEUP": "gpio-keys",
        "VOLUMEDOWN": "gpio-keys",
        "HOME": "Synaptics_RMI4_touchkey"
        }
    if iAmRoot:
        touch_device = fmbtuinput.Touch().open("/dev/input/event1")
        mtInputDevFd = touch_device._fd
elif 'mxt224_key_0' in devices:
    # Running on Blackbay
    hwKeyDevice = {
        "POWER": "msic_power_btn",
        "VOLUMEUP": "gpio-keys",
        "VOLUMEDOWN": "gpio-keys",
        "HOME": "mxt224_key_0"
        }
    if iAmRoot:
        touch_device = fmbtuinput.Touch().open("/dev/input/event0")
        mtInputDevFd = touch_device._fd
elif 'eGalax Inc. eGalaxTouch EXC7200-7368v1.010          ' in devices:
    if iAmRoot:
        touch_device = fmbtuinput.Touch(maxX=0x8000, maxY=0x8000).open(
            "eGalax Inc. eGalaxTouch EXC7200-7368v1.010          ")
        mtInputDevFd = touch_device._fd
        keyboard_device = fmbtuinput.Keyboard().create()

elif iAmRoot:
    # Unknown platform, guessing best possible defaults for devices
    _d = devices.split("\n\n")
    try:
        power_devname = re.findall('Name=\"([^"]*)\"', [i for i in _d if "power" in i.lower()][0])[0]
    except IndexError:
        power_devname = "gpio-keys"

    touch_device = None
    try:
        touch_device_f = "/dev/input/" + re.findall('[ =](event[0-9]+)\s',  [i for i in _d if "touch" in i.lower()][0])[0]
    except IndexError:
        try:
            touch_device_f = "/dev/input/" + re.findall('[ =](event[0-9]+)\s',  [i for i in _d if "mouse0" in i.lower()][0])[0]
            # TODO: check which mouse is capable of emitting button events
            # if none, then create my own mouse input device
        except IndexError:
            touch_device = None

    try:
        mouse_button_device = fmbtuinput.Mouse().open(
            "/dev/input/" + re.findall(
                '[ =](event[0-9]+)\s',
                [i for i in _d if "Mouse" in i][0])[0])
    except IndexError:
        mouse_button_device = fmbtuinput.Mouse().create()
        virtualInputDeviceAdded = True

    try:
        keyboard_device = fmbtuinput.Keyboard().open(
            "/dev/input/" + re.findall(
                '[ =](event[0-9]+)\s',
                [i for i in _d if "sysrq" in i.lower()][0])[0])
    except IndexError:
        if iAmRoot:
            keyboard_device = fmbtuinput.Keyboard().create()
            virtualInputDeviceAdded = True
        else:
            keyboard_device = None

    # TODO: find keyboard input device for the usual keys (sysrq, etc.)
    # If nothing suitable seems to be present, create my own keyboard.
    hwKeyDevice = {
        "POWER": power_devname,
        "VOLUMEUP": "gpio-keys",
        "VOLUMEDOWN": "gpio-keys",
        "HOME": "gpio-keys"
        }

    if g_debug:
        debug("touch device: %s" % (touch_device,))
        debug("mouse device: %s" % (mouse_button_device,))
        debug("keyb device:  %s" % (keyboard_device,))
    if touch_device:
        mtInputDevFd = touch_device._fd

    if keyboard_device:
        kbInputDevFd = keyboard_device._fd
    else:
        kbInputDevFd = None

    if isinstance(mouse_button_device, fmbtuinput.Mouse):
        time.sleep(1)
        mouse_button_device.move(-4096, -4096)
        mouse_button_device.setXY(0, 0)

    del _d

# Read input devices
deviceToEventFile = {}
for _l in devices.splitlines():
    if _l.startswith('N: Name="'): _device = _l.split('"')[1]
    elif _l.startswith("H: Handlers=") and "event" in _l:
        try: deviceToEventFile[_device] = "/dev/input/" + re.findall("(event[0-9]+)", _l)[0]
        except Exception, e: pass

screenWidth = None
screenHeight = None

# Connect to X server, get root window size for screenshots
display = None
if g_Xavailable:
    def resetXConnection():
        global display, current_screen, root_window, X_AllPlanes
        if display != None:
            libX11.XCloseDisplay(display)
        display        = libX11.XOpenDisplay(X_NULL)
        current_screen = libX11.XDefaultScreen(display)
        root_window    = libX11.XRootWindow(display, current_screen)
        X_AllPlanes    = libX11.XAllPlanes()
    resetXConnection()

    ref            = ctypes.byref
    __rw           = ctypes.c_uint(0)
    __x            = ctypes.c_int(0)
    __y            = ctypes.c_int(0)
    root_width     = ctypes.c_uint(0)
    root_height    = ctypes.c_uint(0)
    __bwidth       = ctypes.c_uint(0)
    root_depth     = ctypes.c_uint(0)

    libX11.XGetGeometry(display, root_window, ref(__rw), ref(__x), ref(__y),
                        ref(root_width), ref(root_height), ref(__bwidth),
                        ref(root_depth))

    cMinKeycode        = ctypes.c_int(0)
    cMaxKeycode        = ctypes.c_int(0)
    cKeysymsPerKeycode = ctypes.c_int(0)
    libX11.XDisplayKeycodes(display, ref(cMinKeycode), ref(cMaxKeycode))
    keysyms = libX11.XGetKeyboardMapping(display,
                                         cMinKeycode,
                                         (cMaxKeycode.value - cMinKeycode.value) + 1,
                                         ref(cKeysymsPerKeycode))
    shiftModifier = libX11.XKeysymToKeycode(display, libX11.XStringToKeysym("Shift_R"))

    screenWidth = root_width.value
    screenHeight = root_height.value

def read_cmd():
    return sys.stdin.readline().strip()

def _encode(obj):
    return base64.b64encode(cPickle.dumps(obj))

def _decode(string):
    return cPickle.loads(base64.b64decode(string))

def write_response(ok, value):
    if ok: p = "FMBTAGENT OK "
    else: p = "FMBTAGENT ERROR "
    if not g_debug:
        response = "%s%s\n" % (p, _encode(value))
    else:
        response = "%s%s\n" % (p, value)
    sys.stdout.write(response)
    sys.stdout.flush()

def sendHwTap(x, y, button):
    try:
        if touch_device:
            touch_device.tap(x, y)
        else:
            mouse_button_device.tap(x, y, button)
        return True, None
    except Exception, e:
        return False, str(e)

def sendHwMove(x, y):
    try:
        if touch_device:
            touch_device.move(x, y)
        else:
            mouse_button_device.move(x, y)
        return True, None
    except Exception, e:
        return False, str(e)

def sendHwFingerDown(x, y, button):
    try:
        if touch_device:
            touch_device.pressFinger(button, x, y)
        else:
            mouse_button_device.move(x, y)
            mouse_button_device.press(button)
        return True, None
    except Exception, e:
        return False, str(e)

def sendHwFingerUp(x, y, button):
    try:
        if touch_device:
            touch_device.releaseFinger(button)
        else:
            mouse_button_device.move(x, y)
            mouse_button_device.release(button)
        return True, None
    except Exception, e:
        return False, str(e)

def sendHwKey(keyName, delayBeforePress, delayBeforeRelease):
    fd = None
    closeFd = False
    try: inputDevice = deviceToEventFile[hwKeyDevice[keyName]]
    except: fd = keyboard_device._fd
    try: keyCode = _inputKeyNameToCode[keyName]
    except KeyError:
        try: keyCode = fmbtuinput.toKeyCode(keyName)
        except ValueError: return False, 'No keycode for key "%s"' % (keyName,)
    try:
        if not fd:
            fd = os.open(inputDevice, os.O_WRONLY | os.O_NONBLOCK)
            closeFd = True
    except: return False, 'Unable to open input device "%s" for writing' % (inputDevice,)
    if delayBeforePress > 0: time.sleep(delayBeforePress)
    if delayBeforePress >= 0:
        if os.write(fd, struct.pack(_input_event, int(time.time()), 0, _EV_KEY, keyCode, 1)) > 0:
            os.write(fd, struct.pack(_input_event, 0, 0, 0, 0, 0))
    if delayBeforeRelease > 0: time.sleep(delayBeforeRelease)
    if delayBeforeRelease >= 0:
        if os.write(fd, struct.pack(_input_event, int(time.time()), 0, _EV_KEY, keyCode, 0)) > 0:
            os.write(fd, struct.pack(_input_event, 0, 0, 0, 0, 0))
    if closeFd:
        os.close(fd)
    return True, None

def specialCharToXString(c):
    c2s = {'\n': "Return",
           ' ': "space", '!': "exclam", '"': "quotedbl",
           '#': "numbersign", '$': "dollar", '%': "percent",
           '&': "ampersand", "'": "apostrophe",
           '(': "parenleft", ')': "parenright", '*': "asterisk",
           '+': "plus", '-': "minus", '.': "period", '/': "slash",
           ':': "colon", ';': "semicolon", '<': "less", '=': "equal",
           '>': "greater", '?': "question", '@': "at",
           '_': "underscore"}
    return c2s.get(c, c)

def specialCharToUsKeys(c):
    # character -> ([modifier, [modifier...]] keycode)
    c2s = {'\n': ("KEY_ENTER",),
           ' ': ("KEY_SPACE",),
           '`': ("KEY_GRAVE",),      '~': ("KEY_LEFTSHIFT", "KEY_GRAVE"),
           '!': ("KEY_LEFTSHIFT", "KEY_1"),
           '@': ("KEY_LEFTSHIFT", "KEY_2"),
           '#': ("KEY_LEFTSHIFT", "KEY_3"),
           '$': ("KEY_LEFTSHIFT", "KEY_4"),
           '%': ("KEY_LEFTSHIFT", "KEY_5"),
           '^': ("KEY_LEFTSHIFT", "KEY_6"),
           '&': ("KEY_LEFTSHIFT", "KEY_7"),
           '*': ("KEY_LEFTSHIFT", "KEY_8"),
           '(': ("KEY_LEFTSHIFT", "KEY_9"),
           ')': ("KEY_LEFTSHIFT", "KEY_0"),
           '-': ("KEY_MINUS",),      '_': ("KEY_LEFTSHIFT", "KEY_MINUS"),
           '=': ("KEY_EQUAL",),      '+': ("KEY_LEFTSHIFT", "KEY_EQUAL"),
           '\t': ("KEY_TAB",),
           '[': ("KEY_LEFTBRACE",),  '{': ("KEY_LEFTSHIFT", "KEY_LEFTBRACE"),
           ']': ("KEY_RIGHTBRACE",), '}': ("KEY_LEFTSHIFT", "KEY_RIGHTBRACE"),
           ';': ("KEY_SEMICOLON",),  ':': ("KEY_LEFTSHIFT", "KEY_SEMICOLON"),
           "'": ("KEY_APOSTROPHE",), '"': ("KEY_LEFTSHIFT", "KEY_APOSTROPHE"),
           '\\': ("KEY_BACKSLASH",), '|': ("KEY_LEFTSHIFT", "KEY_BACKSLASH"),
           ',': ("KEY_COMMA",),      '<': ("KEY_LEFTSHIFT", "KEY_COMMA"),
           '.': ("KEY_DOT",),        '>': ("KEY_LEFTSHIFT", "KEY_DOT"),
           '/': ("KEY_SLASH",),      '?': ("KEY_LEFTSHIFT", "KEY_SLASH"),
    }
    return c2s.get(c, c)

mtEvents = {} # slot -> (tracking_id, x, y)

def inputEventSend(inputDevFd, eventType, event, param):
    t = time.time()
    tsec = int(t)
    tusec = int(1000000*(t-tsec))
    os.write(inputDevFd, struct.pack(_input_event,
        tsec, tusec, eventType, event, param))

def mtEventSend(eventType, event, param):
    """multitouch device event"""
    return inputEventSend(mtInputDevFd, eventType, event, param)

def mtGestureStart(x, y):
    mtGestureStart.trackingId += 1
    trackingId = mtGestureStart.trackingId

    for freeSlot in xrange(16):
        if not freeSlot in mtEvents: break
    else: raise ValueError("No free multitouch event slots available")

    mtEvents[freeSlot] = [trackingId, x, y]

    mtEventSend(_EV_ABS, _ABS_MT_SLOT, freeSlot)
    mtEventSend(_EV_ABS, _ABS_MT_TRACKING_ID, trackingId)
    mtEventSend(_EV_ABS, _ABS_MT_POSITION_X, x)
    mtEventSend(_EV_ABS, _ABS_MT_POSITION_Y, y)
    mtEventSend(_EV_ABS, _ABS_X, x)
    mtEventSend(_EV_ABS, _ABS_Y, y)
    mtEventSend(0, 0, 0) # SYNC
    return freeSlot
mtGestureStart.trackingId = 0

def mtGestureMove(slot, x, y):
    if x == mtEvents[slot][1] and y == mtEvents[slot][2]: return
    mtEventSend(_EV_ABS, _ABS_MT_SLOT, slot)
    mtEventSend(_EV_ABS, _ABS_MT_TRACKING_ID, mtEvents[slot][0])
    if x != mtEvents[slot][1] and 0 <= x <= root_width:
        mtEventSend(_EV_ABS, _ABS_MT_POSITION_X, x)
        mtEvents[slot][1] = x
    if y != mtEvents[slot][2] and 0 <= y <= root_height:
        mtEventSend(_EV_ABS, _ABS_MT_POSITION_Y, y)
        mtEvents[slot][2] = y
    if 0 <= x <= root_width:
        mtEventSend(_EV_ABS, _ABS_X, x)
    if 0 <= y <= root_height:
        mtEventSend(_EV_ABS, _ABS_Y, y)
    mtEventSend(0, 0, 0)

def mtGestureEnd(slot):
    mtEventSend(_EV_ABS, _ABS_MT_SLOT, slot)
    mtEventSend(_EV_ABS, _ABS_MT_TRACKING_ID, -1)
    mtEventSend(0, 0, 0) # SYNC
    del mtEvents[slot]

def mtLinearGesture(listOfStartEndPoints, duration, movePoints, sleepBeforeMove=0, sleepAfterMove=0):
    # listOfStartEndPoints: [ [(finger1startX, finger1startY), (finger1endX, finger1endY)],
    #                         [(finger2startX, finger2startY), (finger2endX, finger2endY)], ...]
    startPoints = [startEnd[0] for startEnd in listOfStartEndPoints]
    xDist = [startEnd[1][0] - startEnd[0][0] for startEnd in listOfStartEndPoints]
    yDist = [startEnd[1][1] - startEnd[0][1] for startEnd in listOfStartEndPoints]
    movePointsF = float(movePoints)
    fingers = []
    for (x, y) in startPoints:
        fingers.append(mtGestureStart(x, y))

    if sleepBeforeMove > 0: time.sleep(sleepBeforeMove)

    if movePoints > 0:
        intermediateSleep = float(duration) / movePoints
        for i in xrange(1, movePoints + 1):
            if intermediateSleep > 0:
                time.sleep(intermediateSleep)
            for fingerIndex, finger in enumerate(fingers):
                mtGestureMove(finger,
                              startPoints[fingerIndex][0] + int(xDist[fingerIndex]*i/movePointsF),
                              startPoints[fingerIndex][1] + int(yDist[fingerIndex]*i/movePointsF))

    if sleepAfterMove > 0: time.sleep(sleepAfterMove)

    for finger in fingers:
        mtGestureEnd(finger)
    return True, None

def typeCharX(origChar):
    modifiers = []
    c         = specialCharToXString(origChar)
    keysym    = libX11.XStringToKeysym(c)
    if keysym == NoSymbol:
        return False
    keycode   = libX11.XKeysymToKeycode(display, keysym)

    first = (keycode - cMinKeycode.value) * cKeysymsPerKeycode.value

    try:
        if chr(keysyms[first + 1]) == origChar:
            modifiers.append(shiftModifier)
    except ValueError: pass

    for m in modifiers:
        libXtst.XTestFakeKeyEvent(display, m, X_True, X_CurrentTime)

    libXtst.XTestFakeKeyEvent(display, keycode, X_True, X_CurrentTime)
    libXtst.XTestFakeKeyEvent(display, keycode, X_False, X_CurrentTime)

    for m in modifiers[::-1]:
        libXtst.XTestFakeKeyEvent(display, m, X_False, X_CurrentTime)
    return True

def typeCharHw(origChar):
    for c in origChar:
        modifiers = []
        keyCode = None
        c = specialCharToUsKeys(c)
        if isinstance(c, tuple):
            modifiers = c[:-1]
            keyCode = c[-1]
        elif c in string.uppercase:
            modifiers = ["KEY_LEFTSHIFT"]
            keyCode = "KEY_" + c
        elif c in string.lowercase or c in string.digits:
            keyCode = "KEY_" + c.upper()
        else:
            # do not know how to type the character
            pass
        if keyCode:
            for m in modifiers:
                keyboard_device.press(m)
            keyboard_device.tap(keyCode)
            for m in modifiers[::-1]:
                keyboard_device.release(m)
    return True

if g_Xavailable:
    typeChar = typeCharX
else:
    typeChar = typeCharHw

def typeSequence(s, delayBetweenChars=0):
    skipped = []
    for c in s:
        if not typeChar(c):
            skipped.append(c)
        if delayBetweenChars != 0:
            time.sleep(delayBetweenChars)
    if skipped: return False, skipped
    else: return True, skipped

def takeScreenshotOnX():
    image_p = libX11.XGetImage(display, root_window,
                               0, 0, root_width, root_height,
                               X_AllPlanes, X_ZPixmap)
    image = image_p[0]
    # FMBTRAWX11 image format header:
    # FMBTRAWX11 [width] [height] [color depth] [bits per pixel]<linefeed>
    # Binary data
    rawfmbt_header = "FMBTRAWX11 %d %d %d %d\n" % (
                     image.width, image.height, root_depth.value, image.bits_per_pixel)
    rawfmbt_data = ctypes.string_at(image.data, image.height * image.bytes_per_line)
    compressed_image = rawfmbt_header + zlib.compress(rawfmbt_data, 3)
    libX11.XDestroyImage(image_p)
    return True, compressed_image

def westonTakeScreenshotRoot():
    if westonTakeScreenshotRoot.ssFilename == None:
        westonTakeScreenshotRoot.ssFilename = findWestonScreenshotFilenameRoot()
    try:
        keyboard_device.press("KEY_LEFTMETA")
        keyboard_device.tap("s")
        keyboard_device.release("KEY_LEFTMETA")
        time.sleep(0.5)
        # wait for the screenshot writer to finish
        writerPid = fuser(westonTakeScreenshotRoot.ssFilename)
        if writerPid != None:
            time.sleep(0.25)
            while fuser(westonTakeScreenshotRoot.ssFilename, [writerPid]) != None:
                time.sleep(0.25)
        shutil.move(westonTakeScreenshotRoot.ssFilename, "/tmp/screenshot.png")
        os.chmod("/tmp/screenshot.png", 0666)
    except Exception, e:
        return False, str(e)
    return True, None
westonTakeScreenshotRoot.ssFilename = None

def takeScreenshotOnWeston():
    if iAmRoot:
        rv, status = westonTakeScreenshotRoot()
    else:
        rv, status = subAgentCommand("root", "tizen", "ss weston-root")
    if rv == False:
        return rv, status
    return True, file("/tmp/screenshot.png").read()

def fuser(filename, usualSuspects=None):
    """Returns the pid of a user of given file, or None"""
    filepath = os.path.realpath(filename)
    if not os.access(filepath, os.R_OK):
        raise ValueError('No such file: "%s"' % (filename,))
    if usualSuspects == None:
        procFds = glob.glob("/proc/[1-9][0-9][0-9]*/fd/*")
    else:
        procFds = []
        for pid in usualSuspects:
            procFds.extend(glob.glob("/proc/%s/fd/*" % (pid,)))
    for symlink in procFds:
        try:
            if os.path.realpath(symlink) == filepath:
                return int(symlink.split('/')[2])
        except OSError:
            pass

def findWestonScreenshotFilenameRoot():
    # find weston cwd
    for exe in glob.glob("/proc/[1-9][0-9][0-9]*/exe"):
        try:
            if os.path.realpath(exe) == "/usr/bin/weston":
                cwd = os.path.realpath(os.path.dirname(exe) + "/cwd")
                break
        except OSError:
            pass
    else:
        return False, "cannot find weston cwd"
    rv = cwd + "/wayland-screenshot.png"
    return rv

if g_Xavailable:
    takeScreenshot = takeScreenshotOnX
else:
    takeScreenshot = takeScreenshotOnWeston

def shellSOE(command, asyncStatus, asyncOut, asyncError):
    if (asyncStatus, asyncOut, asyncError) != (None, None, None):
        # prepare for decoupled asynchronous execution
        if asyncStatus == None: asyncStatus = "/dev/null"
        if asyncOut == None: asyncOut = "/dev/null"
        if asyncError == None: asyncError = "/dev/null"
        try:
            stdinFile = file("/dev/null", "r")
            stdoutFile = file(asyncOut, "a+")
            stderrFile = file(asyncError, "a+", 0)
            statusFile = file(asyncStatus, "a+")
        except IOError, e:
            return False, (None, None, e)
        try:
            if os.fork() > 0:
                # parent returns after successful fork, there no
                # direct visibility to async child process beyond this
                # point.
                stdinFile.close()
                stdoutFile.close()
                stderrFile.close()
                statusFile.close()
                return True, (0, None, None)
        except OSError, e:
            return False, (None, None, e)
        os.setsid()
    else:
        stdinFile = subprocess.PIPE
        stdoutFile = subprocess.PIPE
        stderrFile = subprocess.PIPE
    try:
        p = subprocess.Popen(command, shell=True,
                             stdin=stdinFile,
                             stdout=stdoutFile,
                             stderr=stderrFile,
                             close_fds=True)
    except Exception, e:
        return False, (None, None, e)
    if asyncStatus == None and asyncOut == None and asyncError == None:
        # synchronous execution, read stdout and stderr
        out, err = p.communicate()
    else:
        # asynchronous execution, store status to file
        statusFile.write(str(p.wait()) + "\n")
        statusFile.close()
        out, err = None, None
    return True, (p.returncode, out, err)

def waitOutput(nonblockingFd, acceptedOutputs, timeout, pollInterval=0.1):
    start = time.time()
    endTime = start + timeout
    s = ""
    try: s += nonblockingFd.read()
    except IOError: pass
    foundOutputs = [ao for ao in acceptedOutputs if ao in s]
    while len(foundOutputs) == 0 and time.time() < endTime:
        time.sleep(pollInterval)
        try: s += nonblockingFd.read()
        except IOError: pass
        foundOutputs = [ao for ao in acceptedOutputs if ao in s]
    return foundOutputs, s

_subAgents = {}
def openSubAgent(username, password):
    p = subprocess.Popen('''python -c 'import pty; pty.spawn(["su", "-c", "python /tmp/fmbttizen-agent.py --sub-agent", "-", "%s"])' ''' % (username,),
            shell=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)

    # Read in non-blocking mode to ensure agent starts correctly
    fl = fcntl.fcntl(p.stdout.fileno(), fcntl.F_GETFL)
    fcntl.fcntl(p.stdout.fileno(), fcntl.F_SETFL, fl | os.O_NONBLOCK)

    output2 = ""
    seenPrompts, output1 = waitOutput(p.stdout, ["Password:", "FMBTAGENT"], 5.0)
    if "Password:" in seenPrompts:
        p.stdin.write(password + "\r")
        output1 = ""
        seenPrompts, output2 = waitOutput(p.stdout, ["FMBTAGENT"], 5.0)

    if not "FMBTAGENT" in seenPrompts:
        p.terminate()
        return (None, 'fMBT agent with username "%s" does not answer.' % (username,),
                output1 + output2)

    # Agent is alive, continue in blocking mode
    fcntl.fcntl(p.stdout.fileno(), fcntl.F_SETFL, fl)

    return p, "", ""

def subAgentCommand(username, password, cmd):
    if not username in _subAgents:
        process, output, error = openSubAgent(username, password)
        if process == None:
            return None, (-1, output, error)
        else:
            _subAgents[username] = process
    p = _subAgents[username]
    p.stdin.write(cmd + "\r")
    p.stdin.flush()
    answer = p.stdout.readline().rstrip()
    if answer.startswith("FMBTAGENT OK "):
        return True, _decode(answer[len("FMBTAGENT OK "):])
    else:
        return False, _decode(answer[len("FMBTAGENT ERROR "):])

def closeSubAgents():
    for username in _subAgents:
        subAgentCommand(username, None, "quit")

if __name__ == "__main__":
    try:
        origTermAttrs = termios.tcgetattr(sys.stdin.fileno())
        hasTerminal = True
    except termios.error:
        origTermAttrs = None
        hasTerminal = False
    if hasTerminal and not "--keep-echo" in sys.argv and not "--debug" in sys.argv:
        # Disable terminal echo
        newTermAttrs = origTermAttrs
        newTermAttrs[3] = origTermAttrs[3] &  ~termios.ECHO
        termios.tcsetattr(sys.stdin.fileno(), termios.TCSANOW, newTermAttrs)

    if "--no-x" in sys.argv:
        debug("X disabled")
        g_Xavailable = False

    platformInfo = {}
    platformInfo["input devices"] = fmbtuinput._g_deviceNames.keys()

    # Send version number, enter main loop
    write_response(True, platformInfo)
    cmd = read_cmd()
    while cmd:
        if cmd.startswith("bl "): # set display backlight time
            if iAmRoot:
                timeout = int(cmd[3:].strip())
                try:
                    file("/opt/var/kdb/db/setting/lcd_backlight_normal","wb").write(struct.pack("ii",0x29,timeout))
                    write_response(True, None)
                except Exception, e: write_response(False, e)
            else:
                write_response(*subAgentCommand("root", "tizen", cmd))
        elif cmd.startswith("er "): # event recorder
            if iAmRoot:
                cmd, arg = cmd.split(" ", 1)
                if arg.startswith("start "):
                    filterOpts = _decode(arg.split()[1])
                    fmbtuinput.startQueueingEvents(filterOpts)
                    write_response(True, None)
                elif arg == "stop":
                    events = fmbtuinput.stopQueueingEvents()
                    write_response(True, None)
                elif arg == "fetch":
                    events = fmbtuinput.fetchQueuedEvents()
                    write_response(True, events)
            else:
                write_response(*subAgentCommand("root", "tizen", cmd))
        elif cmd.startswith("gd"):   # get display status
            try:
                p = subprocess.Popen(['/usr/bin/xset', 'q'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                out, err = p.communicate()
                if "Monitor is Off" in out: write_response(True, "Off")
                elif "Monitor is On" in out: write_response(True, "On")
                else: write_response(False, err)
            except Exception, e: write_response(False, e)
        elif cmd.startswith("tm "):   # touch move(x, y)
            xs, ys = cmd[3:].strip().split()
            if g_Xavailable:
                libXtst.XTestFakeMotionEvent(display, current_screen, int(xs), int(ys), X_CurrentTime)
                libX11.XFlush(display)
            else:
                if iAmRoot: rv, msg = sendHwMove(int(xs), int(ys))
                else: rv, msg = subAgentCommand("root", "tizen", cmd)
            write_response(True, None)
        elif cmd.startswith("tt "): # touch tap(x, y, button)
            x, y, button = [int(i) for i in cmd[3:].strip().split()]
            if g_Xavailable:
                libXtst.XTestFakeMotionEvent(display, current_screen, x, y, X_CurrentTime)
                libXtst.XTestFakeButtonEvent(display, button, X_True, X_CurrentTime)
                libXtst.XTestFakeButtonEvent(display, button, X_False, X_CurrentTime)
                libX11.XFlush(display)
                rv, msg = True, None
            else:
                if iAmRoot: rv, msg = sendHwTap(x, y, button-1)
                else: rv, msg = subAgentCommand("root", "tizen", cmd)
            write_response(rv, msg)
        elif cmd.startswith("td "): # touch down(x, y, button)
            xs, ys, button = cmd[3:].strip().split()
            button = int(button)
            if g_Xavailable:
                libXtst.XTestFakeMotionEvent(display, current_screen, int(xs), int(ys), X_CurrentTime)
                libXtst.XTestFakeButtonEvent(display, button, X_True, X_CurrentTime)
                libX11.XFlush(display)
            else:
                if iAmRoot: rv, msg = sendHwFingerDown(int(xs), int(ys), button-1)
                else: rv, msg = subAgentCommand("root", "tizen", cmd)
            write_response(True, None)
        elif cmd.startswith("tu "): # touch up(x, y, button)
            xs, ys, button = cmd[3:].strip().split()
            button = int(button)
            if g_Xavailable:
                libXtst.XTestFakeMotionEvent(display, current_screen, int(xs), int(ys), X_CurrentTime)
                libXtst.XTestFakeButtonEvent(display, button, X_False, X_CurrentTime)
                libX11.XFlush(display)
            else:
                if iAmRoot: rv, msg = sendHwFingerUp(int(xs), int(ys), button-1)
                else: rv, msg = subAgentCommand("root", "tizen", cmd)
            write_response(True, None)
        elif cmd.startswith("kd "): # hw key down
            if iAmRoot: rv, msg = sendHwKey(cmd[3:], 0, -1)
            else: rv, msg = subAgentCommand("root", "tizen", cmd)
            write_response(rv, msg)
        elif cmd.startswith("kp "): # hw key press
            if iAmRoot: rv, msg = sendHwKey(cmd[3:], 0, 0)
            else: rv, msg = subAgentCommand("root", "tizen", cmd)
            write_response(rv, msg)
        elif cmd.startswith("ku "): # hw key up
            if iAmRoot: rv, msg = sendHwKey(cmd[3:], -1, 0)
            else: rv, msg = subAgentCommand("root", "tizen", cmd)
            write_response(rv, msg)
        elif cmd.startswith("kt "): # send x events
            if g_Xavailable:
                rv, skippedSymbols = typeSequence(_decode(cmd[3:]))
                libX11.XFlush(display)
            elif iAmRoot:
                rv, skippedSymbols = typeSequence(_decode(cmd[3:]),
                                                  delayBetweenChars=0.05)
            else:
                rv, skippedSymbols = subAgentCommand("root", "tizen", cmd)
            write_response(rv, skippedSymbols)
        elif cmd.startswith("ml "): # send multitouch linear gesture
            if iAmRoot:
                rv, _ = mtLinearGesture(*_decode(cmd[3:]))
            else:
                rv, _ = subAgentCommand("root", "tizen", cmd)
            write_response(rv, _)
        elif cmd.startswith("ss"): # save screenshot
            if "R" in cmd.split() and g_Xavailable:
                resetXConnection()
            if "weston-root" in cmd.split(): # do Weston root part only
                write_response(*westonTakeScreenshotRoot())
            else:
                rv, compressedImage = takeScreenshot()
                write_response(rv, compressedImage)
        elif cmd.startswith("sd "): # set screen dimensions (width and height)
            _sw, _sh = cmd[3:].split()
            screenWidth, screenHeight = int(_sw), int(_sh)
            if iAmRoot:
                if touch_device:
                    touch_device.setScreenSize((screenWidth, screenHeight))
                    rv, msg = True, None
                else:
                    rv, msg = True, "no touch device"
            else:
                rv, msg = subAgentCommand("root", "tizen", cmd)
            write_response(rv, msg)
        elif cmd.startswith("sa "): # set screenshot rotation angle (degrees)
            if iAmRoot:
                if touch_device:
                    _sa = int(cmd[3:])
                    # compensate it with opposite rotation
                    touch_device.setScreenAngle(-_sa)
                    rv, msg = True, None
                else:
                    rv, msg = True, "no touch device"
            else:
                rv, msg = subAgentCommand("root", "tizen", cmd)
            write_response(rv, msg)
        elif cmd.startswith("es "): # execute shell
            shellCmd, username, password, asyncStatus, asyncOut, asyncError = _decode(cmd[3:])
            if username == "":
                rv, soe = shellSOE(shellCmd, asyncStatus, asyncOut, asyncError)
            else:
                rv, soe = subAgentCommand(username, password,
                    "es " + _encode((shellCmd, "", "", asyncStatus, asyncOut, asyncError)))
            write_response(rv, soe)
        elif cmd.startswith("quit"): # quit
            write_response(rv, True)
            break
        else:
            write_response(False, 'Unknown command: "%s"' % (cmd,))
        cmd = read_cmd()

    closeSubAgents()

    if g_Xavailable:
        libX11.XCloseDisplay(display)

    if hasTerminal:
        termios.tcsetattr(sys.stdin.fileno(), termios.TCSANOW, origTermAttrs)
