# fMBT, free Model Based Testing tool
# Copyright (c) 2013, Intel Corporation.
#
# This program is free software; you can redistribute it and/or modify it
# under the terms and conditions of the GNU Lesser General Public License,
# version 2.1, as published by the Free Software Foundation.
#
# This program is distributed in the hope it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public
# License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St - Fifth Floor, Boston, MA
# 02110-1301 USA.

# pylint: disable = C0103, C0111, R0913

"""
This library offers Python interface for Linux uinput system.

Mouse, Touch and Keyboard classes can be used for
creating new mouse, touch and keyboard devices and synthesizing user
inputs through those devices.
"""

cmdline_usage = """
Usage: python fmbtuinput.py -p <list-of-input-device-files>

Example: python fmbtuinput.py -p /dev/input/event*
"""

import array
import fcntl
import os
import platform
import re
import struct
import time

# See /usr/include/linux/input.h
eventTypes = {
    "EV_SYN":                  0x00,
    "EV_KEY":                  0x01,
    "EV_REL":                  0x02,
    "EV_ABS":                  0x03,
    "EV_MSC":                  0x04,
    "EV_SW":                   0x05,
    "EV_LED":                  0x11,
    "EV_SND":                  0x12,
    "EV_REP":                  0x14,
    "EV_FF":                   0x15,
    "EV_PWR":                  0x16,
    "EV_FF_STATUS":            0x17,
    "EV_MAX":                  0x1f,
    }

keyCodes = {
    "KEY_RESERVED":            0,
    "KEY_ESC":                 1,
    "KEY_1":                   2,
    "KEY_2":                   3,
    "KEY_3":                   4,
    "KEY_4":                   5,
    "KEY_5":                   6,
    "KEY_6":                   7,
    "KEY_7":                   8,
    "KEY_8":                   9,
    "KEY_9":                   10,
    "KEY_0":                   11,
    "KEY_MINUS":               12,
    "KEY_EQUAL":               13,
    "KEY_BACKSPACE":           14,
    "KEY_TAB":                 15,
    "KEY_Q":                   16,
    "KEY_W":                   17,
    "KEY_E":                   18,
    "KEY_R":                   19,
    "KEY_T":                   20,
    "KEY_Y":                   21,
    "KEY_U":                   22,
    "KEY_I":                   23,
    "KEY_O":                   24,
    "KEY_P":                   25,
    "KEY_LEFTBRACE":           26,
    "KEY_RIGHTBRACE":          27,
    "KEY_ENTER":               28,
    "KEY_LEFTCTRL":            29,
    "KEY_A":                   30,
    "KEY_S":                   31,
    "KEY_D":                   32,
    "KEY_F":                   33,
    "KEY_G":                   34,
    "KEY_H":                   35,
    "KEY_J":                   36,
    "KEY_K":                   37,
    "KEY_L":                   38,
    "KEY_SEMICOLON":           39,
    "KEY_APOSTROPHE":          40,
    "KEY_GRAVE":               41,
    "KEY_LEFTSHIFT":           42,
    "KEY_BACKSLASH":           43,
    "KEY_Z":                   44,
    "KEY_X":                   45,
    "KEY_C":                   46,
    "KEY_V":                   47,
    "KEY_B":                   48,
    "KEY_N":                   49,
    "KEY_M":                   50,
    "KEY_COMMA":               51,
    "KEY_DOT":                 52,
    "KEY_SLASH":               53,
    "KEY_RIGHTSHIFT":          54,
    "KEY_KPASTERISK":          55,
    "KEY_LEFTALT":             56,
    "KEY_SPACE":               57,
    "KEY_CAPSLOCK":            58,
    "KEY_F1":                  59,
    "KEY_F2":                  60,
    "KEY_F3":                  61,
    "KEY_F4":                  62,
    "KEY_F5":                  63,
    "KEY_F6":                  64,
    "KEY_F7":                  65,
    "KEY_F8":                  66,
    "KEY_F9":                  67,
    "KEY_F10":                 68,
    "KEY_NUMLOCK":             69,
    "KEY_SCROLLLOCK":          70,
    "KEY_KP7":                 71,
    "KEY_KP8":                 72,
    "KEY_KP9":                 73,
    "KEY_KPMINUS":             74,
    "KEY_KP4":                 75,
    "KEY_KP5":                 76,
    "KEY_KP6":                 77,
    "KEY_KPPLUS":              78,
    "KEY_KP1":                 79,
    "KEY_KP2":                 80,
    "KEY_KP3":                 81,
    "KEY_KP0":                 82,
    "KEY_KPDOT":               83,

    "KEY_ZENKAKUHANKAKU":      85,
    "KEY_102ND":               86,
    "KEY_F11":                 87,
    "KEY_F12":                 88,
    "KEY_RO":                  89,
    "KEY_KATAKANA":            90,
    "KEY_HIRAGANA":            91,
    "KEY_HENKAN":              92,
    "KEY_KATAKANAHIRAGANA":    93,
    "KEY_MUHENKAN":            94,
    "KEY_KPJPCOMMA":           95,
    "KEY_KPENTER":             96,
    "KEY_RIGHTCTRL":           97,
    "KEY_KPSLASH":             98,
    "KEY_SYSRQ":               99,
    "KEY_RIGHTALT":            100,
    "KEY_LINEFEED":            101,
    "KEY_HOME":                102,
    "KEY_UP":                  103,
    "KEY_PAGEUP":              104,
    "KEY_LEFT":                105,
    "KEY_RIGHT":               106,
    "KEY_END":                 107,
    "KEY_DOWN":                108,
    "KEY_PAGEDOWN":            109,
    "KEY_INSERT":              110,
    "KEY_DELETE":              111,
    "KEY_MACRO":               112,
    "KEY_MUTE":                113,
    "KEY_VOLUMEDOWN":          114,
    "KEY_VOLUMEUP":            115,
    "KEY_POWER":               116,
    "KEY_KPEQUAL":             117,
    "KEY_KPPLUSMINUS":         118,
    "KEY_PAUSE":               119,
    "KEY_SCALE":               120,

    "KEY_KPCOMMA":             121,
    "KEY_HANGEUL":             122,
    "KEY_HANJA":               123,
    "KEY_YEN":                 124,
    "KEY_LEFTMETA":            125,
    "KEY_RIGHTMETA":           126,
    "KEY_COMPOSE":             127,

    "KEY_STOP":                128,
    "KEY_AGAIN":               129,
    "KEY_PROPS":               130,
    "KEY_UNDO":                131,
    "KEY_FRONT":               132,
    "KEY_COPY":                133,
    "KEY_OPEN":                134,
    "KEY_PASTE":               135,
    "KEY_FIND":                136,
    "KEY_CUT":                 137,
    "KEY_HELP":                138,
    "KEY_MENU":                139,
    "KEY_CALC":                140,
    "KEY_SETUP":               141,
    "KEY_SLEEP":               142,
    "KEY_WAKEUP":              143,
    "KEY_FILE":                144,
    "KEY_SENDFILE":            145,
    "KEY_DELETEFILE":          146,
    "KEY_XFER":                147,
    "KEY_PROG1":               148,
    "KEY_PROG2":               149,
    "KEY_WWW":                 150,
    "KEY_MSDOS":               151,
    "KEY_COFFEE":              152,
    "KEY_DIRECTION":           153,
    "KEY_CYCLEWINDOWS":        154,
    "KEY_MAIL":                155,
    "KEY_BOOKMARKS":           156,
    "KEY_COMPUTER":            157,
    "KEY_BACK":                158,
    "KEY_FORWARD":             159,
    "KEY_CLOSECD":             160,
    "KEY_EJECTCD":             161,
    "KEY_EJECTCLOSECD":        162,
    "KEY_NEXTSONG":            163,
    "KEY_PLAYPAUSE":           164,
    "KEY_PREVIOUSSONG":        165,
    "KEY_STOPCD":              166,
    "KEY_RECORD":              167,
    "KEY_REWIND":              168,
    "KEY_PHONE":               169,
    "KEY_ISO":                 170,
    "KEY_CONFIG":              171,
    "KEY_HOMEPAGE":            172,
    "KEY_REFRESH":             173,
    "KEY_EXIT":                174,
    "KEY_MOVE":                175,
    "KEY_EDIT":                176,
    "KEY_SCROLLUP":            177,
    "KEY_SCROLLDOWN":          178,
    "KEY_KPLEFTPAREN":         179,
    "KEY_KPRIGHTPAREN":        180,
    "KEY_NEW":                 181,
    "KEY_REDO":                182,

    "KEY_F13":                 183,
    "KEY_F14":                 184,
    "KEY_F15":                 185,
    "KEY_F16":                 186,
    "KEY_F17":                 187,
    "KEY_F18":                 188,
    "KEY_F19":                 189,
    "KEY_F20":                 190,
    "KEY_F21":                 191,
    "KEY_F22":                 192,
    "KEY_F23":                 193,
    "KEY_F24":                 194,

    "KEY_PLAYCD":              200,
    "KEY_PAUSECD":             201,
    "KEY_PROG3":               202,
    "KEY_PROG4":               203,
    "KEY_DASHBOARD":           204,
    "KEY_SUSPEND":             205,
    "KEY_CLOSE":               206,
    "KEY_PLAY":                207,
    "KEY_FASTFORWARD":         208,
    "KEY_BASSBOOST":           209,
    "KEY_PRINT":               210,
    "KEY_HP":                  211,
    "KEY_CAMERA":              212,
    "KEY_SOUND":               213,
    "KEY_QUESTION":            214,
    "KEY_EMAIL":               215,
    "KEY_CHAT":                216,
    "KEY_SEARCH":              217,
    "KEY_CONNECT":             218,
    "KEY_FINANCE":             219,
    "KEY_SPORT":               220,
    "KEY_SHOP":                221,
    "KEY_ALTERASE":            222,
    "KEY_CANCEL":              223,
    "KEY_BRIGHTNESSDOWN":      224,
    "KEY_BRIGHTNESSUP":        225,
    "KEY_MEDIA":               226,

    "KEY_SWITCHVIDEOMODE":     227,

    "KEY_KBDILLUMTOGGLE":      228,
    "KEY_KBDILLUMDOWN":        229,
    "KEY_KBDILLUMUP":          230,

    "KEY_SEND":                231,
    "KEY_REPLY":               232,
    "KEY_FORWARDMAIL":         233,
    "KEY_SAVE":                234,
    "KEY_DOCUMENTS":           235,

    "KEY_BATTERY":             236,

    "KEY_BLUETOOTH":           237,
    "KEY_WLAN":                238,
    "KEY_UWB":                 239,

    "KEY_UNKNOWN":             240,

    "KEY_VIDEO_NEXT":          241,
    "KEY_VIDEO_PREV":          242,
    "KEY_BRIGHTNESS_CYCLE":    243,
    "KEY_BRIGHTNESS_ZERO":     244,
    "KEY_DISPLAY_OFF":         245,

    "KEY_WIMAX":               246,
    "KEY_RFKILL":              247,

    "KEY_MICMUTE":             248,

    "BTN_MISC":                0x100,
    "BTN_0":                   0x100,
    "BTN_1":                   0x101,
    "BTN_2":                   0x102,
    "BTN_3":                   0x103,
    "BTN_4":                   0x104,
    "BTN_5":                   0x105,
    "BTN_6":                   0x106,
    "BTN_7":                   0x107,
    "BTN_8":                   0x108,
    "BTN_9":                   0x109,

    "BTN_MOUSE":               0x110,
    "BTN_LEFT":                0x110,
    "BTN_RIGHT":               0x111,
    "BTN_MIDDLE":              0x112,
    "BTN_SIDE":                0x113,
    "BTN_EXTRA":               0x114,
    "BTN_FORWARD":             0x115,
    "BTN_BACK":                0x116,
    "BTN_TASK":                0x117,

    "BTN_JOYSTICK":            0x120,
    "BTN_TRIGGER":             0x120,
    "BTN_THUMB":               0x121,
    "BTN_THUMB2":              0x122,
    "BTN_TOP":                 0x123,
    "BTN_TOP2":                0x124,
    "BTN_PINKIE":              0x125,
    "BTN_BASE":                0x126,
    "BTN_BASE2":               0x127,
    "BTN_BASE3":               0x128,
    "BTN_BASE4":               0x129,
    "BTN_BASE5":               0x12a,
    "BTN_BASE6":               0x12b,
    "BTN_DEAD":                0x12f,

    "BTN_GAMEPAD":             0x130,
    "BTN_A":                   0x130,
    "BTN_B":                   0x131,
    "BTN_C":                   0x132,
    "BTN_X":                   0x133,
    "BTN_Y":                   0x134,
    "BTN_Z":                   0x135,
    "BTN_TL":                  0x136,
    "BTN_TR":                  0x137,
    "BTN_TL2":                 0x138,
    "BTN_TR2":                 0x139,
    "BTN_SELECT":              0x13a,
    "BTN_START":               0x13b,
    "BTN_MODE":                0x13c,
    "BTN_THUMBL":              0x13d,
    "BTN_THUMBR":              0x13e,

    "BTN_DIGI":                0x140,
    "BTN_TOOL_PEN":            0x140,
    "BTN_TOOL_RUBBER":         0x141,
    "BTN_TOOL_BRUSH":          0x142,
    "BTN_TOOL_PENCIL":         0x143,
    "BTN_TOOL_AIRBRUSH":       0x144,
    "BTN_TOOL_FINGER":         0x145,
    "BTN_TOOL_MOUSE":          0x146,
    "BTN_TOOL_LENS":           0x147,
    "BTN_TOOL_QUINTTAP":       0x148,
    "BTN_TOUCH":               0x14a,
    "BTN_STYLUS":              0x14b,
    "BTN_STYLUS2":             0x14c,
    "BTN_TOOL_DOUBLETAP":      0x14d,
    "BTN_TOOL_TRIPLETAP":      0x14e,
    "BTN_TOOL_QUADTAP":        0x14f,

    "BTN_WHEEL":               0x150,
    "BTN_GEAR_DOWN":           0x150,
    "BTN_GEAR_UP":             0x151,
    }

relCodes = {
    "REL_X":                   0x00,
    "REL_Y":                   0x01,
    "REL_Z":                   0x02,
    "REL_RX":                  0x03,
    "REL_RY":                  0x04,
    "REL_RZ":                  0x05,
    "REL_HWHEEL":              0x06,
    "REL_DIAL":                0x07,
    "REL_WHEEL":               0x08,
    "REL_MISC":                0x09,
    "REL_MAX":                 0x0f,
    }

absCodes = {
    "ABS_X":                   0x00,
    "ABS_Y":                   0x01,
    "ABS_Z":                   0x02,
    "ABS_RX":                  0x03,
    "ABS_RY":                  0x04,
    "ABS_RZ":                  0x05,
    "ABS_THROTTLE":            0x06,
    "ABS_RUDDER":              0x07,
    "ABS_WHEEL":               0x08,
    "ABS_GAS":                 0x09,
    "ABS_BRAKE":               0x0a,
    "ABS_HAT0X":               0x10,
    "ABS_HAT0Y":               0x11,
    "ABS_HAT1X":               0x12,
    "ABS_HAT1Y":               0x13,
    "ABS_HAT2X":               0x14,
    "ABS_HAT2Y":               0x15,
    "ABS_HAT3X":               0x16,
    "ABS_HAT3Y":               0x17,
    "ABS_PRESSURE":            0x18,
    "ABS_DISTANCE":            0x19,
    "ABS_TILT_X":              0x1a,
    "ABS_TILT_Y":              0x1b,
    "ABS_TOOL_WIDTH":          0x1c,

    "ABS_VOLUME":              0x20,

    "ABS_MISC":                0x28,

    "ABS_MT_SLOT":             0x2f,
    "ABS_MT_TOUCH_MAJOR":      0x30,
    "ABS_MT_TOUCH_MINOR":      0x31,
    "ABS_MT_WIDTH_MAJOR":      0x32,
    "ABS_MT_WIDTH_MINOR":      0x33,
    "ABS_MT_ORIENTATION":      0x34,
    "ABS_MT_POSITION_X":       0x35,
    "ABS_MT_POSITION_Y":       0x36,
    "ABS_MT_TOOL_TYPE":        0x37,
    "ABS_MT_BLOB_ID":          0x38,
    "ABS_MT_TRACKING_ID":      0x39,
    "ABS_MT_PRESSURE":         0x3a,
    "ABS_MT_DISTANCE":         0x3b,

    "ABS_MAX":                 0x3f,
    }

abs_count = absCodes['ABS_MAX'] + 1

event_codetables = {
    eventTypes["EV_SYN"]: {},
    eventTypes["EV_KEY"]: keyCodes,
    eventTypes["EV_REL"]: relCodes,
    eventTypes["EV_ABS"]: absCodes,
}

BUS_PCI       = 0x01
BUS_ISAPNP    = 0x02
BUS_USB       = 0x03
BUS_HIL       = 0x04
BUS_BLUETOOTH = 0x05
BUS_VIRTUAL   = 0x06

# See struct input_event in /usr/include/linux/input.h
if platform.architecture()[0] == "32bit":
    struct_timeval = "II"
else:
    struct_timeval = "QQ"

struct_input_event = struct_timeval + 'HHi'
sizeof_input_event = struct.calcsize(struct_input_event)

struct_input_id    = 'HHHH'
struct_uinput_user_dev = ('80s' +
                          struct_input_id +
                          'i' +
                          str(abs_count) + 'i' +
                          str(abs_count) + 'i' +
                          str(abs_count) + 'i' +
                          str(abs_count) + 'i')
sizeof_uinput_user_dev = struct.calcsize(struct_uinput_user_dev)

struct_input_absinfo = 'iiii'

# asm-generic/ioctl.h:
IOC_NRBITS = 8
IOC_TYPEBITS = 8
IOC_SIZEBITS = 14
IOC_DIRBITS = 2

IOC_NRSHIFT = 0
IOC_TYPESHIFT = IOC_NRSHIFT + IOC_NRBITS
IOC_SIZESHIFT = IOC_TYPESHIFT + IOC_TYPEBITS
IOC_DIRSHIFT = IOC_SIZESHIFT + IOC_SIZEBITS

IOC_NONE = 0
IOC_WRITE = 1
IOC_READ = 2

def IOC(dir_, type_, nr, size):
    return ((dir_ << IOC_DIRSHIFT) |
            (type_ << IOC_TYPESHIFT) |
            (nr << IOC_NRSHIFT) |
            (size << IOC_SIZESHIFT))
def IO(type_, nr):
    return IOC(IOC_NONE, type_, nr, 0)
def IOR(type_, nr, size):
    return IOC(IOC_READ, type_, nr, struct.calcsize(size))
def IOW(type_, nr, size):
    return IOC(IOC_WRITE, type_, nr, struct.calcsize(size))
def EVIOCGABS(abs):
    return IOR(ord('E'), 0x40 + (abs), struct_input_absinfo)

UINPUT_IOCTL_BASE = ord('U')
UI_DEV_CREATE = IO(UINPUT_IOCTL_BASE, 1)
UI_DEV_DESTROY = IO(UINPUT_IOCTL_BASE, 2)

UI_SET_EVBIT  = IOW(UINPUT_IOCTL_BASE, 100, 'i')
UI_SET_KEYBIT = IOW(UINPUT_IOCTL_BASE, 101, 'i')
UI_SET_RELBIT = IOW(UINPUT_IOCTL_BASE, 102, 'i')
UI_SET_ABSBIT = IOW(UINPUT_IOCTL_BASE, 103, 'i')

# inverse lookup tables for event/key/rel/abs codes
eventTypesInv = {}
keyCodesInv = {}
relCodesInv = {}
absCodesInv = {}
for d in ["eventTypes", "keyCodes",
          "relCodes", "absCodes"]:
    globals()[d + "Inv"] = dict([(v, k) for k, v in globals()[d].iteritems()])

def toKeyCode(keyCodeOrName):
    if isinstance(keyCodeOrName, int):
        return keyCodeOrName
    elif keyCodeOrName in keyCodes:
        return keyCodes[keyCodeOrName]
    elif keyCodeOrName.upper() in keyCodes:
        return keyCodes[keyCodeOrName.upper(keyCodeOrName)]
    elif ("KEY_" + keyCodeOrName.upper()) in keyCodes:
        return keyCodes["KEY_" + keyCodeOrName.upper()]
    else:
        raise ValueError('Invalid keycode "%s"' % (keyCodeOrName,))

def toButtonCode(buttonCodeOrName):
    if isinstance(buttonCodeOrName, str):
        buttonCode = toKeyCode(buttonCodeOrName)
    elif buttonCodeOrName < 0xf:
        buttonCode = keyCodes["BTN_MOUSE"] + buttonCodeOrName
    else:
        buttonCode = buttonCodeOrName
    return buttonCode

_g_devices = file("/proc/bus/input/devices").read().split("\n\n")
_g_deviceNames = {}
for d in _g_devices:
    if d.strip() == "":
        continue
    _name = [line.split('"')[1] for line in d.split('\n')
             if line.startswith('N: ')][0]
    _g_deviceNames[_name] = ("/dev/input/" +
                             re.findall('[ =](event[0-9]+)\s', d)[0])

def toEventFilename(deviceName):
    return _g_deviceNames[deviceName]

class InputDevice(object):
    def __init__(self):
        self._fd = -1
        self._uidev = None
        self._created = False
        self._opened = False

    def __del__(self):
        if self._created:
            self.destroy()

    def startCreating(self, name, vendor, product, version,
                      absmin=None, absmax=None):
        if self._fd > 0:
            raise InputDeviceError("InputDevice is already open")
        self._fd = os.open("/dev/uinput", os.O_WRONLY | os.O_NONBLOCK)
        if absmin == None:
            absmin = [0 for _ in xrange(abs_count)]
        if absmax == None:
            absmax = [0 for _ in xrange(abs_count)]
        absfuzz = [0 for _ in xrange(abs_count)]
        absflat = [0 for _ in xrange(abs_count)]
        self._uidev = struct.pack(struct_uinput_user_dev,
                                  name, # name
                                  BUS_USB, # id.bus_type
                                  vendor, # id.vendor
                                  product, # id.product
                                  version, # id.version
                                  0, # ff_effects_max
                                  # TODO: why absmin + absmax gives
                                  # error for touch?
                                  *(absmax + absmin + absfuzz + absflat)
                              )

    def finishCreating(self):
        if self._fd < 1:
            raise InputDeviceError("startCreating() not called")
        bytes_written = os.write(self._fd, self._uidev)
        if bytes_written != sizeof_uinput_user_dev:
            raise InputDeviceError(
                "Writing to /dev/uinput failed, wrote %s/%s bytes"
                % (bytes_written, sizeof_uinput_user_dev))
        rv = fcntl.ioctl(self._fd, UI_DEV_CREATE)
        if rv != 0:
            raise InputDeviceError(
                "Creating device failed, ioctl UI_DEV_CREATE returned %s"
                % (rv,))
        self._created = True
        return True

    def destroy(self):
        if self._created:
            fcntl.ioctl(self._fd, UI_DEV_DESTROY)
            self._created = False
        self.close()

    def open(self, filename):
        if self._fd > 0:
            raise InputDeviceError("InputDevice is already open")
        if not filename.startswith("/dev/input"):
            filename = toEventFilename(filename)
        self._fd = os.open(filename, os.O_WRONLY | os.O_NONBLOCK)
        self._created = False
        return self

    def close(self):
        if self._fd > 0:
            os.close(self._fd)
            self._fd = -1

    def addCap(self, capBit, capCodeOrName, capCode2Name):
        if self._fd < 1:
            raise InputDeviceError("startCreating() not called")
        if self._created or self._opened:
            raise InputDeviceError("Cannot add capabilities after creation")
        if isinstance(capCodeOrName, int):
            capCode = capCodeOrName
        elif capCodeOrName in capCode2Name:
            capCode = capCode2Name[capCodeOrName]
        else:
            raise InputDeviceError('Unknown name "%s"' % (capCodeOrName,))
        return fcntl.ioctl(self._fd, capBit, capCode)

    def addEvent(self, eventCodeOrName):
        return self.addCap(UI_SET_EVBIT, eventCodeOrName, eventTypes)

    def addKey(self, keyCodeOrName):
        return self.addCap(UI_SET_KEYBIT, keyCodeOrName, keyCodes)

    def addRel(self, relCodeOrName):
        return self.addCap(UI_SET_RELBIT, relCodeOrName, relCodes)

    def addAbs(self, absCodeOrName):
        return self.addCap(UI_SET_ABSBIT, absCodeOrName, absCodes)

    def send(self, type_, code, value):
        if self._fd < 1:
            raise InputDeviceError("InputDevice is not open")
        if isinstance(type_, str):
            typeCode = eventTypes[type_]
        else:
            typeCode = type_
        if isinstance(code, str):
            codeCode = event_codetables[typeCode][code]
        else:
            codeCode = code
        return sendInputEvent(self._fd, typeCode, codeCode, value)

    def sync(self):
        if self._fd < 1:
            raise InputDeviceError("InputDevice is not open")
        return sendInputSync(self._fd)

class InputDeviceError(Exception):
    pass

class Mouse(InputDevice):
    def __init__(self, absoluteMove=False):
        """
        Parameters:

          absoluteMove (boolean, optional)
                  force move(x,y) to send absolute coordinates instead
                  of standard relative movement. This helps avoiding
                  mouse pointer drift in some occasions. The default
                  is False.
        """
        InputDevice.__init__(self)
        self._x = 0
        self._y = 0
        self._sendAbs = absoluteMove

    def create(self, name="Virtual fMBT Mouse",
               vendor=0xf4b7, product=0x4053, version=1):

        self.startCreating(name, vendor, product, version)
        self.addEvent("EV_KEY")
        self.addEvent("EV_REL")
        if self._sendAbs:
            self.addEvent("EV_ABS")
        self.addEvent("EV_SYN")
        self.addRel("REL_X")
        self.addRel("REL_Y")
        self.addRel("REL_HWHEEL")
        self.addRel("REL_WHEEL")
        self.addKey("BTN_LEFT")
        self.addKey("BTN_RIGHT")
        self.addKey("BTN_MIDDLE")
        self.addKey("BTN_SIDE")
        self.addKey("BTN_EXTRA")
        self.addKey("BTN_FORWARD")
        self.addKey("BTN_BACK")
        self.addKey("BTN_TASK")
        if self._sendAbs:
            self.addAbs("ABS_X")
            self.addAbs("ABS_Y")
        self.finishCreating()
        return self

    def move(self, x, y):
        """
        Move mouse cursor to coordinates x, y.
        """
        if self._sendAbs:
            self.send("EV_ABS", "ABS_X", x)
            self.send("EV_ABS", "ABS_Y", y)
        else:
            deltaX = x - self._x
            deltaY = y - self._y
            self.send("EV_REL", "REL_X", deltaX)
            self.send("EV_REL", "REL_Y", deltaY)
        self.sync()
        self.setXY(x, y)

    def moveRel(self, deltaX, deltaY):
        self.send("EV_REL", "REL_X", deltaX)
        self.send("EV_REL", "REL_Y", deltaY)
        self.sync()
        self.setXY(self._x + deltaX, self._y + deltaY)

    def press(self, button):
        buttonCode = toButtonCode(button)
        self.send("EV_KEY", buttonCode, 1)
        self.sync()

    def release(self, button):
        buttonCode = toButtonCode(button)
        self.send("EV_KEY", buttonCode, 0)
        self.sync()

    def setXY(self, x, y):
        """
        Resets relative mouse position to (x, y), does not synthesize
        event. Example: disable possible mouse pointer drift:

        mouse.moveRel(-4096, -4096) # move to the top-left corner
        mouse.setXY(0, 0) # set current pointer coordinates to 0, 0

        After this, mouse.move(x, y) will synthesize relative mouse
        move event which will drive cursor to coordinates x, y.
        """
        self._x = x
        self._y = y

    def xy(self):
        return (self._x, self._y)

    def tap(self, x, y, button):
        self.move(x, y)
        self.press(button)
        self.release(button)

class Touch(InputDevice):
    """
    Simulates touchpanel and touchpad
    """
    def __init__(self, maxX = None, maxY = None,
                 screenWidth = None, screenHeight = None, screenAngle = None):
        InputDevice.__init__(self)
        self._maxX = maxX
        self._maxY = maxY
        self._screenW = screenWidth
        self._screenH = screenHeight
        self._screenA = screenAngle
        self._maxPressure = None
        self._multiTouch = True
        self._mtTrackingId = 0
        self._mtTracking = {}
        self._hoover = (0, 0)

    def create(self, name="Virtual fMBT Touch",
               vendor=0xf4b7, product=0x70c5, version=1,
               maxX=0xffff, maxY=0xffff, maxPressure=None,
               multiTouch = True):
        absmin = [0 for _ in xrange(abs_count)]
        absmax = [0 for _ in xrange(abs_count)]
        absmax[absCodes["ABS_X"]] = maxX
        absmax[absCodes["ABS_Y"]] = maxY
        if maxPressure != None:
            self._maxPressure = maxPressure
            absmax[absCodes["ABS_PRESSURE"]] = self._maxPressure
        absmax[absCodes["ABS_MT_SLOT"]] = 16
        absmax[absCodes["ABS_MT_TRACKING_ID"]] = 0x0fffffff
        absmax[absCodes["ABS_MT_POSITION_X"]] = maxX
        absmax[absCodes["ABS_MT_POSITION_Y"]] = maxY
        self._maxX = maxX
        self._maxY = maxY
        self._multiTouch = multiTouch

        self.startCreating(name, vendor, product, version,
                           absmin=absmin, absmax=absmax)
        self.addEvent("EV_KEY")
        self.addEvent("EV_ABS")
        self.addEvent("EV_SYN")
        self.addKey("BTN_TOUCH")
        self.addAbs("ABS_X")
        self.addAbs("ABS_Y")
        if self._maxPressure != None:
            self.addAbs("ABS_PRESSURE")
        if self._multiTouch:
            self.addAbs("ABS_MT_SLOT")
            self.addAbs("ABS_MT_TRACKING_ID")
            self.addAbs("ABS_MT_POSITION_X")
            self.addAbs("ABS_MT_POSITION_Y")
        self.finishCreating()
        return self

    def open(self, filename):
        InputDevice.open(self, filename)
        # detect touch device capabilities and max values
        # nfo is struct input_absinfo
        nfo = array.array('i', range(6))
        fcntl.ioctl(self._fd, EVIOCGABS(absCodes["ABS_X"]), nfo, 1)
        self._maxX = nfo[2]
        fcntl.ioctl(self._fd, EVIOCGABS(absCodes["ABS_Y"]), nfo, 1)
        self._maxY = nfo[2]
        return self

    def setScreenSize(self, (width, height)):
        self._screenW, self._screenH = (width, height)

    def setScreenAngle(self, angle):
        self._screenA = angle

    def _angleXY(self, x, y):
        """return x, y in screen without rotation"""
        angle = self._screenA
        sw, sh = self._screenW, self._screenH
        if angle:
            while angle < 0:
                angle += 360
            while angle > 360:
                angle -= 360
            if angle == 90:
                ax = self._screenH - y
                ay = x
                sw, sh = self._screenH, self._screenW
            elif angle == 180:
                ax = self._screenH - x
                ay = self._screenW - y
            elif angle == 270:
                ax = y
                ay = self._screenW - x
                sw, sh = self._screenH, self._screenW
            else:
                raise ValueError('Illegal screen rotation angle %s' %
                                 (self._screenA,))
        else:
            ax, ay = x, y
        return (sw, sh, ax, ay)

    def _tXY(self, x, y):
        """convert x, y to touch screen coordinates"""
        if self._screenW and self._maxX and self._screenH and self._maxY:
            w, h, x, y = self._angleXY(x, y)
            x = int((self._maxX * x) / w)
            y = int((self._maxY * y) / h)
            return (x, y)
        else:
            return (x, y)

    def _startTracking(self, finger, x, y):
        self._mtTrackingId += 1
        usedSlots = set([self._mtTracking[fngr][0]
                         for fngr in self._mtTracking])
        for freeSlot in xrange(16):
            if not freeSlot in usedSlots:
                break
        else:
            raise ValueError("No free slots for multitouch")
        self._mtTracking[finger] = [freeSlot, self._mtTrackingId, x, y]
        self._sendSlot(finger)
        self.send("EV_ABS", "ABS_MT_TRACKING_ID", self._mtTrackingId)
        tx, ty = self._tXY(x, y)
        self.send("EV_ABS", "ABS_MT_POSITION_X", tx)
        self.send("EV_ABS", "ABS_MT_POSITION_Y", ty)
        return self._mtTrackingId

    def _stopTracking(self, finger):
        self._sendSlot(finger)
        self.send("EV_ABS", "ABS_MT_TRACKING_ID", -1)
        del self._mtTracking[finger]

    def _sendSlot(self, finger):
        slot = self._mtTracking[finger][0]
        self.send("EV_ABS", "ABS_MT_SLOT", slot)

    def tap(self, x, y, pressure=None):
        self.pressFinger(-1, x, y, pressure)
        self.releaseFinger(-1)

    # Compatibility API to allow using a Touch almost like a Mouse
    def move(self, x, y):
        if len(self._mtTracking.keys()) == 0:
            self._hoover = (x, y)
        else:
            finger = sorted(self._mtTracking.keys())[0]
            return self.moveFinger(finger, x, y)

    def press(self, finger):
        return self.pressFinger(finger, *self._hoover)

    def release(self, finger):
        return self.releaseFinger(finger)
    # end of compatibility API

    # Multi-touch API
    def pressFinger(self, finger, x, y, pressure=None):
        """Add a finger to current multitouch gesture. If multitouch gesture
        is not started, it starts automatically.
        """
        if self._multiTouch and not finger in self._mtTracking:
            self._startTracking(finger, x, y)
        if pressure != None and self._maxPressure != None:
            self.send("EV_ABS", "ABS_PRESSURE", pressure)
        self.send("EV_KEY", "BTN_TOUCH", 1)
        tx, ty = self._tXY(x, y)
        self.send("EV_ABS", "ABS_X", tx)
        self.send("EV_ABS", "ABS_Y", ty)
        self.sync()

    def releaseFinger(self, finger):
        """Remove a finger from current multitouch gesture. When last finger
        is raised from the screen, multitouch gesture ends."""
        if self._multiTouch:
            self._stopTracking(finger)
        self.send("EV_KEY", "BTN_TOUCH", 0)
        for fngr in self._mtTracking:
            # still some finger pressed, non-multitouch reader gets
            # coordinates from one of those
            tx, ty = self._tXY(self._mtTracking[fngr][2],
                               self._mtTracking[fngr][3])
            self.send("EV_ABS", "ABS_X", tx)
            self.send("EV_ABS", "ABS_Y", ty)
            break # only one coordinates will be sent.
        self.sync()

    def moveFinger(self, finger, x, y):
        """Move a finger in current multitouch gesture"""
        lastX, lastY = self._mtTracking[finger][2:4]
        self._sendSlot(finger)
        tx, ty = self._tXY(x, y)
        if lastX != x:
            if self._multiTouch:
                self.send("EV_ABS", "ABS_MT_POSITION_X", tx)
            self.send("EV_ABS", "ABS_X", tx)
            self._mtTracking[finger][2] = x
        if lastY != y:
            if self._multiTouch:
                self.send("EV_ABS", "ABS_MT_POSITION_Y", ty)
            self.send("EV_ABS", "ABS_Y", ty)
            self._mtTracking[finger][3] = y
        self.sync()

class Keyboard(InputDevice):
    def __init__(self):
        InputDevice.__init__(self)

    def create(self, name="Virtual fMBT Keyboard",
               vendor=0xf4b7, product=0x4ebd, version=1):
        self.startCreating(name, vendor, product, version)
        self.addEvent("EV_KEY")
        self.addEvent("EV_SYN")
        for keyName in keyCodes:
            if keyName.startswith("KEY_"):
                self.addKey(keyCodes[keyName])
        self.finishCreating()
        return self

    def press(self, keyCodeOrName):
        self.send("EV_KEY", toKeyCode(keyCodeOrName), 1)
        self.sync()

    def release(self, keyCodeOrName):
        self.send("EV_KEY", toKeyCode(keyCodeOrName), 0)
        self.sync()

    def tap(self, keyCodeOrName):
        keyCode = toKeyCode(keyCodeOrName)
        self.press(keyCode)
        self.release(keyCode)

def sendInputSync(devFd):
    return sendInputEvent(devFd, 0, 0, 0)

def sendInputEvent(devFd, type_, code, value):
    t = time.time()
    t_sec = int(t)
    t_usec = int(1000000*(t-t_sec))
    rv = os.write(devFd,
                  struct.pack(struct_input_event,
                              t_sec, t_usec,
                              type_,
                              code,
                              value))
    return rv == sizeof_input_event

def eventToString(inputEvent):
    tim, tus, typ, cod, val = struct.unpack(struct_input_event, inputEvent)
    styp = eventTypesInv.get(typ, "?")
    if styp == "EV_KEY":
        scod = keyCodesInv.get(cod, "?")
    elif styp == "EV_REL":
        scod = relCodesInv.get(cod, "?")
    elif styp == "EV_ABS":
        scod = absCodesInv.get(cod, "?")
    else:
        scod = "N/A"
    if typ == 0:
        return styp
    else:
        return "%8s.%s type: %4s (%5s), code: %5s (%15s) value: %8s" % \
            (tim, str(tus).zfill(6), typ, styp, cod, scod, val)

def printEventsFromFile(filename):
    fd = os.open(filename, os.O_RDONLY)

    sdev = filename.split("/")[-1]

    try:
        while 1:
            inputEvent = os.read(fd, struct.calcsize(struct_input_event))
            if not inputEvent:
                break
            print sdev, eventToString(inputEvent)
    finally:
        os.close(fd)

if __name__ == "__main__":
    import getopt
    import sys
    import thread

    opt_print_devices = []

    opts, remainder = getopt.getopt(
        sys.argv[1:], 'hp',
        ['help', 'print'])
    for opt, arg in opts:
        if opt in ['-h', '--help']:
            print cmdline_usage
            sys.exit(0)
        elif opt in ['-p', '--print']:
            if not remainder:
                print cmdline_usage
            opt_print_devices = remainder

    if opt_print_devices:
        for deviceFilename in opt_print_devices:
            thread.start_new_thread(printEventsFromFile, (deviceFilename,))
        raw_input("Press ENTER to stop printing...\n")
