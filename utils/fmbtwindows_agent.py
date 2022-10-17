# fMBT, free Model Based Testing tool
# Copyright (c) 2014-2016, Intel Corporation.
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

import __builtin__
import atexit
import base64
import ctypes
try:
    import ctypes.wintypes
except:
    raise ImportError("fmbtwindows_agent runs only on Windows")
import glob
import os
import Queue
import re
import signal
import string
import struct
import subprocess
import sys
import tempfile
import thread
import threading
import time
import zlib

try:
    import wmi # try to import wmi, requires that pywin32 and wmi packages
               # are installed in DUT
except:
    pass

try:
    import _winreg
    _REG_types = {
        0: "REG_NONE",
        1: "REG_SZ",
        2: "REG_EXPAND_SZ",
        3: "REG_BINARY",
        4: "REG_DWORD",
        5: "REG_DWORD_BIG_ENDIAN",
        6: "REG_LINK",
        7: "REG_MULTI_SZ",
        8: "REG_RESOURCE_LIST",
    }
except:
    _winreg = None
    _REG_types = {}

_g_archRegistryKeys = (0,)
_g_arch = os.environ.get('PROCESSOR_ARCHITECTURE', '')
_g_arch64 = os.environ.get('PROCESSOR_ARCHITEW6432', '')
if _winreg:
    if _g_arch.lower() == "x86" and "64" in _g_arch64:
        _g_archRegistryKeys = (_winreg.KEY_WOW64_32KEY, _winreg.KEY_WOW64_64KEY)

_g_rmAtExit = []
def cleanUp():
    for filename in _g_rmAtExit:
        try:
            os.remove(filename)
        except:
            pass
atexit.register(cleanUp)

_HTTPServerProcess = None

INPUT_MOUSE                 = 0
INPUT_KEYBOARD              = 1
INPUT_HARDWARE              = 2

# For touchMask
TOUCH_MASK_NONE             = 0x00000000
TOUCH_MASK_CONTACTAREA      = 0x00000001
TOUCH_MASK_ORIENTATION      = 0x00000002
TOUCH_MASK_PRESSURE         = 0x00000004
TOUCH_MASK_ALL              = 0x00000007

# For touchFlag
TOUCH_FLAG_NONE             = 0x00000000

# For pointerType
PT_POINTER                  = 0x00000001
PT_TOUCH                    = 0x00000002
PT_PEN                      = 0x00000003
PT_MOUSE                    = 0x00000004

# For pointerFlags
POINTER_FLAG_NONE           = 0x00000000
POINTER_FLAG_NEW            = 0x00000001
POINTER_FLAG_INRANGE        = 0x00000002
POINTER_FLAG_INCONTACT      = 0x00000004
POINTER_FLAG_FIRSTBUTTON    = 0x00000010
POINTER_FLAG_SECONDBUTTON   = 0x00000020
POINTER_FLAG_THIRDBUTTON    = 0x00000040
POINTER_FLAG_FOURTHBUTTON   = 0x00000080
POINTER_FLAG_FIFTHBUTTON    = 0x00000100
POINTER_FLAG_PRIMARY        = 0x00002000
POINTER_FLAG_CONFIDENCE     = 0x00004000
POINTER_FLAG_CANCELED       = 0x00008000
POINTER_FLAG_DOWN           = 0x00010000
POINTER_FLAG_UPDATE         = 0x00020000
POINTER_FLAG_UP             = 0x00040000
POINTER_FLAG_WHEEL          = 0x00080000
POINTER_FLAG_HWHEEL         = 0x00100000
POINTER_FLAG_CAPTURECHANGED = 0x00200000

WHEEL_DELTA                 = 120
XBUTTON1                    = 0x0001
XBUTTON2                    = 0x0002
MOUSEEVENTF_ABSOLUTE        = 0x8000
MOUSEEVENTF_HWHEEL          = 0x01000
MOUSEEVENTF_MOVE            = 0x0001
MOUSEEVENTF_MOVE_NOCOALESCE = 0x2000
MOUSEEVENTF_LEFTDOWN        = 0x0002
MOUSEEVENTF_LEFTUP          = 0x0004
MOUSEEVENTF_RIGHTDOWN       = 0x0008
MOUSEEVENTF_RIGHTUP         = 0x0010
MOUSEEVENTF_MIDDLEDOWN      = 0x0020
MOUSEEVENTF_MIDDLEUP        = 0x0040
MOUSEEVENTF_VIRTUALDESK     = 0x4000
MOUSEEVENTF_WHEEL           = 0x0800
MOUSEEVENTF_XDOWN           = 0x0080
MOUSEEVENTF_XUP             = 0x0100

SM_XVIRTUALSCREEN           = 76
SM_YVIRTUALSCREEN           = 77
SM_CXVIRTUALSCREEN          = 78
SM_CYVIRTUALSCREEN          = 79

VK_LBUTTON = 0x01               # Left mouse button
VK_RBUTTON = 0x02               # Right mouse button
VK_CANCEL = 0x03                # Control-break processing
VK_MBUTTON = 0x04               # Middle mouse button (three-button mouse)
VK_XBUTTON1 = 0x05              # X1 mouse button
VK_XBUTTON2 = 0x06              # X2 mouse button
VK_BACK = 0x08                  # BACKSPACE key
VK_TAB = 0x09                   # TAB key
VK_CLEAR = 0x0C                 # CLEAR key
VK_RETURN = 0x0D                # ENTER key
VK_SHIFT = 0x10                 # SHIFT key
VK_CONTROL = 0x11               # CTRL key
VK_MENU = 0x12                  # ALT key
VK_PAUSE = 0x13                 # PAUSE key
VK_CAPITAL = 0x14               # CAPS LOCK key
VK_KANA = 0x15                  # IME Kana mode
VK_HANGUL = 0x15                # IME Hangul mode
VK_JUNJA = 0x17                 # IME Junja mode
VK_FINAL = 0x18                 # IME final mode
VK_HANJA = 0x19                 # IME Hanja mode
VK_KANJI = 0x19                 # IME Kanji mode
VK_ESCAPE = 0x1B                # ESC key
VK_CONVERT = 0x1C               # IME convert
VK_NONCONVERT = 0x1D            # IME nonconvert
VK_ACCEPT = 0x1E                # IME accept
VK_MODECHANGE = 0x1F            # IME mode change request
VK_SPACE = 0x20                 # SPACEBAR
VK_PRIOR = 0x21                 # PAGE UP key
VK_NEXT = 0x22                  # PAGE DOWN key
VK_END = 0x23                   # END key
VK_HOME = 0x24                  # HOME key
VK_LEFT = 0x25                  # LEFT ARROW key
VK_UP = 0x26                    # UP ARROW key
VK_RIGHT = 0x27                 # RIGHT ARROW key
VK_DOWN = 0x28                  # DOWN ARROW key
VK_SELECT = 0x29                # SELECT key
VK_PRINT = 0x2A                 # PRINT key
VK_EXECUTE = 0x2B               # EXECUTE key
VK_SNAPSHOT = 0x2C              # PRINT SCREEN key
VK_INSERT = 0x2D                # INS key
VK_DELETE = 0x2E                # DEL key
VK_HELP = 0x2F                  # HELP key
VK_LWIN = 0x5B                  # Left Windows key (Natural keyboard)
VK_RWIN = 0x5C                  # Right Windows key (Natural keyboard)
VK_APPS = 0x5D                  # Applications key (Natural keyboard)
VK_SLEEP = 0x5F                 # Computer Sleep key
VK_NUMPAD0 = 0x60               # Numeric keypad 0 key
VK_NUMPAD1 = 0x61               # Numeric keypad 1 key
VK_NUMPAD2 = 0x62               # Numeric keypad 2 key
VK_NUMPAD3 = 0x63               # Numeric keypad 3 key
VK_NUMPAD4 = 0x64               # Numeric keypad 4 key
VK_NUMPAD5 = 0x65               # Numeric keypad 5 key
VK_NUMPAD6 = 0x66               # Numeric keypad 6 key
VK_NUMPAD7 = 0x67               # Numeric keypad 7 key
VK_NUMPAD8 = 0x68               # Numeric keypad 8 key
VK_NUMPAD9 = 0x69               # Numeric keypad 9 key
VK_MULTIPLY = 0x6A              # Multiply key
VK_ADD = 0x6B                   # Add key
VK_SEPARATOR = 0x6C             # Separator key
VK_SUBTRACT = 0x6D              # Subtract key
VK_DECIMAL = 0x6E               # Decimal key
VK_DIVIDE = 0x6F                # Divide key
VK_F1 = 0x70                    # F1 key
VK_F2 = 0x71                    # F2 key
VK_F3 = 0x72                    # F3 key
VK_F4 = 0x73                    # F4 key
VK_F5 = 0x74                    # F5 key
VK_F6 = 0x75                    # F6 key
VK_F7 = 0x76                    # F7 key
VK_F8 = 0x77                    # F8 key
VK_F9 = 0x78                    # F9 key
VK_F10 = 0x79                   # F10 key
VK_F11 = 0x7A                   # F11 key
VK_F12 = 0x7B                   # F12 key
VK_F13 = 0x7C                   # F13 key
VK_F14 = 0x7D                   # F14 key
VK_F15 = 0x7E                   # F15 key
VK_F16 = 0x7F                   # F16 key
VK_F17 = 0x80                   # F17 key
VK_F18 = 0x81                   # F18 key
VK_F19 = 0x82                   # F19 key
VK_F20 = 0x83                   # F20 key
VK_F21 = 0x84                   # F21 key
VK_F22 = 0x85                   # F22 key
VK_F23 = 0x86                   # F23 key
VK_F24 = 0x87                   # F24 key
VK_NUMLOCK = 0x90               # NUM LOCK key
VK_SCROLL = 0x91                # SCROLL LOCK key
VK_LSHIFT = 0xA0                # Left SHIFT key
VK_RSHIFT = 0xA1                # Right SHIFT key
VK_LCONTROL = 0xA2              # Left CONTROL key
VK_RCONTROL = 0xA3              # Right CONTROL key
VK_LMENU = 0xA4                 # Left MENU key
VK_RMENU = 0xA5                 # Right MENU key
VK_BROWSER_BACK = 0xA6          # Browser Back key
VK_BROWSER_FORWARD = 0xA7       # Browser Forward key
VK_BROWSER_REFRESH = 0xA8       # Browser Refresh key
VK_BROWSER_STOP = 0xA9          # Browser Stop key
VK_BROWSER_SEARCH = 0xAA        # Browser Search key
VK_BROWSER_FAVORITES = 0xAB     # Browser Favorites key
VK_BROWSER_HOME = 0xAC          # Browser Start and Home key
VK_VOLUME_MUTE = 0xAD           # Volume Mute key
VK_VOLUME_DOWN = 0xAE           # Volume Down key
VK_VOLUME_UP = 0xAF             # Volume Up key
VK_MEDIA_NEXT_TRACK = 0xB0      # Next Track key
VK_MEDIA_PREV_TRACK = 0xB1      # Previous Track key
VK_MEDIA_STOP = 0xB2            # Stop Media key
VK_MEDIA_PLAY_PAUSE = 0xB3      # Play/Pause Media key
VK_LAUNCH_MAIL = 0xB4           # Start Mail key
VK_LAUNCH_MEDIA_SELECT = 0xB5   # Select Media key
VK_LAUNCH_APP1 = 0xB6           # Start Application 1 key
VK_LAUNCH_APP2 = 0xB7           # Start Application 2 key
VK_OEM_1 = 0xBA                 # Used for miscellaneous characters; it can vary by keyboard.
                                # For the US standard keyboard, the ';:' key
VK_OEM_PLUS = 0xBB              # For any country/region, the '+' key
VK_OEM_COMMA = 0xBC             # For any country/region, the ',' key
VK_OEM_MINUS = 0xBD             # For any country/region, the '-' key
VK_OEM_PERIOD = 0xBE            # For any country/region, the '.' key
VK_OEM_2 = 0xBF                 # Used for miscellaneous characters; it can vary by keyboard.
                                # For the US standard keyboard, the '/?' key
VK_OEM_3 = 0xC0                 # Used for miscellaneous characters; it can vary by keyboard.
                                # For the US standard keyboard, the '`~' key
VK_OEM_4 = 0xDB                 # Used for miscellaneous characters; it can vary by keyboard.
                                # For the US standard keyboard, the '[{' key
VK_OEM_5 = 0xDC                 # Used for miscellaneous characters; it can vary by keyboard.
                                # For the US standard keyboard, the '\|' key
VK_OEM_6 = 0xDD                 # Used for miscellaneous characters; it can vary by keyboard.
                                # For the US standard keyboard, the ']}' key
VK_OEM_7 = 0xDE                 # Used for miscellaneous characters; it can vary by keyboard.
                                # For the US standard keyboard, the 'single-quote/double-quote' key
VK_OEM_8 = 0xDF                 # Used for miscellaneous characters; it can vary by keyboard.
VK_OEM_102 = 0xE2               # Either the angle bracket key or the backslash key on the RT 102-key keyboard
VK_PROCESSKEY = 0xE5            # IME PROCESS key
VK_PACKET = 0xE7                # Used to pass Unicode characters as if they were keystrokes. The VK_PACKET key is the low word of a 32-bit Virtual Key value used for non-keyboard input methods. For more information, see Remark in KEYBDINPUT, SendInput, WM_KEYDOWN, and WM_KEYUP
VK_ATTN = 0xF6                  # Attn key
VK_CRSEL = 0xF7                 # CrSel key
VK_EXSEL = 0xF8                 # ExSel key
VK_EREOF = 0xF9                 # Erase EOF key
VK_PLAY = 0xFA                  # Play key
VK_ZOOM = 0xFB                  # Zoom key
VK_PA1 = 0xFD                   # PA1 key
VK_OEM_CLEAR = 0xFE             # Clear key

KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_SCANCODE = 0x0008
KEYEVENTF_UNICODE = 0x0004

KEY_0 = 0x30
KEY_1 = 0x31
KEY_2 = 0x32
KEY_3 = 0x33
KEY_4 = 0x34
KEY_5 = 0x35
KEY_6 = 0x36
KEY_7 = 0x37
KEY_8 = 0x38
KEY_9 = 0x39
KEY_A = 0x41
KEY_B = 0x42
KEY_C = 0x43
KEY_D = 0x44
KEY_E = 0x45
KEY_F = 0x46
KEY_G = 0x47
KEY_H = 0x48
KEY_I = 0x49
KEY_J = 0x4A
KEY_K = 0x4B
KEY_L = 0x4C
KEY_M = 0x4D
KEY_N = 0x4E
KEY_O = 0x4F
KEY_P = 0x50
KEY_Q = 0x51
KEY_R = 0x52
KEY_S = 0x53
KEY_T = 0x54
KEY_U = 0x55
KEY_V = 0x56
KEY_W = 0x57
KEY_X = 0x58
KEY_Y = 0x59
KEY_Z = 0x5A

_g_showCmds = [
    "SW_HIDE", "SW_NORMAL", "SW_MINIMIZED", "SW_MAXIMIZE", "SW_NOACTIVATE",
    "SW_SHOW", "SW_MINIMIZE", "SW_MINNOACTIVE", "SW_SHOWNA", "SW_RESTORE",
    "SW_DEFAULT", "SW_FORCEMINIMIZE"]

LONG = ctypes.c_long
DWORD = ctypes.c_ulong
ULONG_PTR = ctypes.POINTER(DWORD)
WORD = ctypes.c_ushort
SIZE_T = ctypes.c_size_t
HANDLE = ctypes.c_void_p

try:
    # Location of GetProcessMemoryInfo depends on Windows version
    GetProcessMemoryInfo = ctypes.windll.kernel32.GetProcessMemoryInfo
except AttributeError:
    GetProcessMemoryInfo = ctypes.windll.psapi.GetProcessMemoryInfo

PROCESS_QUERY_INFORMATION = 0x400
PROCESS_TERMINATE = 0x1
PROCESS_VM_READ = 0x10

WM_GETTEXT = 0x000d
WM_CLOSE = 0x0010

CF_TEXT = 1
CF_UNICODETEXT = 13


GMEM_FIXED = 0x0000
GMEM_MOVEABLE = 0x0002
GMEM_ZEROINIT = 0x0040

try:
    _dpiAware = ctypes.windll.user32.SetProcessDPIAware()
except Exception, e:
    _dpiAware = e

# Structs for mouse and keyboard input

class MOUSEINPUT(ctypes.Structure):
    _fields_ = (('dx', LONG),
                ('dy', LONG),
                ('mouseData', DWORD),
                ('dwFlags', DWORD),
                ('time', DWORD),
                ('dwExtraInfo', ULONG_PTR))

class KEYBDINPUT(ctypes.Structure):
    _fields_ = (('wVk', WORD),
                ('wScan', WORD),
                ('dwFlags', DWORD),
                ('time', DWORD),
                ('dwExtraInfo', ULONG_PTR))

class HARDWAREINPUT(ctypes.Structure):
    _fields_ = (('uMsg', DWORD),
                ('wParamL', WORD),
                ('wParamH', WORD))

class _INPUTunion(ctypes.Union):
    _fields_ = (('mi', MOUSEINPUT),
                ('ki', KEYBDINPUT),
                ('hi', HARDWAREINPUT))

class INPUT(ctypes.Structure):
    _fields_ = (('type', DWORD),
                ('union', _INPUTunion))

# Structs for touch input

class POINTER_INFO(ctypes.Structure):
    _fields_ = [("pointerType", ctypes.c_uint32),
              ("pointerId", ctypes.c_uint32),
              ("frameId", ctypes.c_uint32),
              ("pointerFlags", ctypes.c_int),
              ("sourceDevice", ctypes.wintypes.HANDLE),
              ("hwndTarget", ctypes.wintypes.HWND),
              ("ptPixelLocation", ctypes.wintypes.POINT),
              ("ptHimetricLocation", ctypes.wintypes.POINT),
              ("ptPixelLocationRaw", ctypes.wintypes.POINT),
              ("ptHimetricLocationRaw", ctypes.wintypes.POINT),
              ("dwTime", DWORD),
              ("historyCount", ctypes.c_uint32),
              ("inputData", ctypes.c_int32),
              ("dwKeyStates", DWORD),
              ("PerformanceCount", ctypes.c_uint64),
              ("ButtonChangeType", ctypes.c_int)
              ]


class POINTER_TOUCH_INFO(ctypes.Structure):
    _fields_ = [("pointerInfo", POINTER_INFO),
              ("touchFlags", ctypes.c_int),
              ("touchMask", ctypes.c_int),
              ("rcContact", ctypes.wintypes.RECT),
              ("rcContactRaw", ctypes.wintypes.RECT),
              ("orientation", ctypes.c_uint32),
              ("pressure", ctypes.c_uint32)]

class _PROCESS_MEMORY_COUNTERS_EX(ctypes.Structure):
    _fields_ = [("cb", DWORD),
                ("PageFaultCount", DWORD),
                ("PeakWorkingSetSize", SIZE_T),
                ("WorkingSetSize", SIZE_T),
                ("QuotaPeakPagedPoolUsage", SIZE_T),
                ("QuotaPagedPoolUsage", SIZE_T),
                ("QuotaPeakNonPagedPoolUsage", SIZE_T),
                ("QuotaNonPagedPoolUsage", SIZE_T),
                ("PagefileUsage", SIZE_T),
                ("PeakPagefileUsage", SIZE_T),
                ("PrivateUsage", SIZE_T)]

# Allocate memory only once for often needed out-parameters

_processMemoryCountersEx = _PROCESS_MEMORY_COUNTERS_EX()
_filenameBufferW = ctypes.create_unicode_buffer(4096)
_creationTime = ctypes.wintypes.FILETIME()
_exitTime = ctypes.wintypes.FILETIME()
_kernelTime = ctypes.wintypes.FILETIME()
_userTime = ctypes.wintypes.FILETIME()
_dword = DWORD(0)

# Initialize Pointer and Touch info

pointerInfo = POINTER_INFO(pointerType=PT_TOUCH,
                           pointerId=0,
                           ptPixelLocation=ctypes.wintypes.POINT(90,54))

pointerInfo2 = POINTER_INFO(pointerType=PT_TOUCH,
                            pointerId=1,
                            ptPixelLocation=ctypes.wintypes.POINT(190,154))

touchInfoArray = (POINTER_TOUCH_INFO * 2)()

touchInfo = touchInfoArray[0]

touchInfo2 = touchInfoArray[1]

touchInfo.pointerInfo = pointerInfo
touchInfo.touchFlags = TOUCH_FLAG_NONE
touchInfo.touchMask = TOUCH_MASK_ALL
touchInfo.rcContact = ctypes.wintypes.RECT(
    pointerInfo.ptPixelLocation.x-5,
    pointerInfo.ptPixelLocation.y-5,
    pointerInfo.ptPixelLocation.x+5,
    pointerInfo.ptPixelLocation.y+5)
touchInfo.orientation = 90
touchInfo.pressure = 32000

touchInfo2.pointerInfo = pointerInfo2
touchInfo2.touchFlags = TOUCH_FLAG_NONE
touchInfo2.touchMask = TOUCH_MASK_ALL
touchInfo2.rcContact = ctypes.wintypes.RECT(
    pointerInfo2.ptPixelLocation.x-5,
    pointerInfo2.ptPixelLocation.y-5,
    pointerInfo2.ptPixelLocation.x+5,
    pointerInfo2.ptPixelLocation.y+5)
touchInfo2.orientation = 90
touchInfo2.pressure = 32000

ctypes.windll.user32.VkKeyScanW.argtypes = [ctypes.c_wchar]
ctypes.windll.user32.VkKeyScanW.restype = ctypes.c_short

if not "touchInfoLock" in globals():
    touchInfoLock = thread.allocate_lock()

def setTouchCoords(touchInfo, x, y, fingerRadius=5, finger=0):
    if finger == 0:
        ti = touchInfo
    elif finger == 1:
        ti = touchInfo2
    else:
        raise ValueError("invalid finger number: %s, expected 0 or 1" % (finger,))
    ti.pointerInfo.ptPixelLocation.x = x
    ti.pointerInfo.ptPixelLocation.y = y

    ti.rcContact.left = x - fingerRadius
    ti.rcContact.right = x + fingerRadius
    ti.rcContact.top = y - fingerRadius
    ti.rcContact.bottom = y + fingerRadius

def _sendTouch(pointerFlags, errorWhen="doTouch", fingers=1):
    if fingers == 1:
        touchInfo.pointerInfo.pointerFlags = pointerFlags
        try:
            success = ctypes.windll.user32.InjectTouchInput(1, ctypes.byref(touchInfo))
        except AttributeError:
            raise NotImplementedError("this windows version does not support touch injection")
    elif fingers == 2:
        touchInfo.pointerInfo.pointerFlags = pointerFlags
        touchInfo2.pointerInfo.pointerFlags = pointerFlags
        try:
            success = ctypes.windll.user32.InjectTouchInput(2, ctypes.byref(touchInfoArray))
        except AttributeError:
            raise NotImplementedError("this windows version does not support touch injection")
    else:
        success = 1

    if (success == 0):
        return False
    else:
        return True

def _touchHold():
    # Keep updating previous touchDown or touchMove coordinates
    # to avoid InjectTouchInput timeout
    _touchUpdateInterval = 0.25  # seconds
    while True:
        time.sleep(_touchUpdateInterval)
        touchInfoLock.acquire()
        try:
            if not (touchInfo.pointerInfo.pointerFlags & POINTER_FLAG_INCONTACT):
                break

            if not _sendTouch(POINTER_FLAG_UPDATE  |
                              POINTER_FLAG_INRANGE |
                              POINTER_FLAG_INCONTACT, "_touchHold"):
                break

        finally:
            touchInfoLock.release()

def touchDown(x, y, fingerRadius=5, holdEvents=True, finger=0, sendFingers=1):
    touchInfoLock.acquire()
    try:
        setTouchCoords(touchInfo, x, y, fingerRadius, finger)
        ok = _sendTouch(POINTER_FLAG_DOWN    |
                        POINTER_FLAG_INRANGE |
                        POINTER_FLAG_INCONTACT, "touchDown",
                        sendFingers)
        if ok and holdEvents:
            thread.start_new_thread(_touchHold, ()) # update until raised
        return ok
    finally:
        touchInfoLock.release()

def touchMove(x, y, fingerRadius=5, finger=0, sendFingers=1):
    touchInfoLock.acquire()
    try:
        setTouchCoords(touchInfo, x, y, fingerRadius, finger)
        return _sendTouch(POINTER_FLAG_UPDATE  |
                          POINTER_FLAG_INRANGE |
                          POINTER_FLAG_INCONTACT, "touchMove",
                          sendFingers)
    finally:
        touchInfoLock.release()

def touchUp(x, y, fingerRadius=5, finger=0, sendFingers=1):
    touchInfoLock.acquire()
    try:
        setTouchCoords(touchInfo, x, y, fingerRadius, finger)
        moveOk = _sendTouch(POINTER_FLAG_UPDATE  |
                            POINTER_FLAG_INRANGE |
                            POINTER_FLAG_INCONTACT,
                            "touchUp move to final location",
                            sendFingers)
        return _sendTouch(POINTER_FLAG_UP, "touchUp", sendFingers) and moveOk
    finally:
        touchInfoLock.release()

def touchPinch(finger0startXY, finger0endXY,
               finger1startXY, finger1endXY,
               count=10, duration=0.75):
    f0x, f0y = finger0startXY
    f1x, f1y = finger1startXY
    f0dx = float(finger0endXY[0] - finger0startXY[0]) / count
    f0dy = float(finger0endXY[1] - finger0startXY[1]) / count
    f1dx = float(finger1endXY[0] - finger1startXY[0]) / count
    f1dy = float(finger1endXY[1] - finger1startXY[1]) / count
    delay = float(duration) / count
    touchDown(f0x, f0y, finger=0, holdEvents=False, sendFingers=0)
    touchDown(f1x, f1y, finger=1, holdEvents=False, sendFingers=2)
    for i in xrange(count):
        time.sleep(delay)
        f0x += f0dx
        f0y += f0dy
        f1x += f1dx
        f1y += f1dy
        touchMove(int(f0x), int(f0y), finger=0, sendFingers=0)
        touchMove(int(f1x), int(f1y), finger=1, sendFingers=2)
    time.sleep(delay)
    touchUp(*finger0endXY, finger=0, sendFingers=0)
    touchUp(*finger1endXY, finger=1, sendFingers=2)
    return True

def sendInput(*inputs):
    nInputs = len(inputs)
    LPINPUT = INPUT * nInputs
    pInputs = LPINPUT(*inputs)
    cbSize = ctypes.c_int(ctypes.sizeof(INPUT))
    return ctypes.windll.user32.SendInput(nInputs, pInputs, cbSize)

def Input(structure):
    if isinstance(structure, MOUSEINPUT):
        return INPUT(INPUT_MOUSE, _INPUTunion(mi=structure))
    if isinstance(structure, KEYBDINPUT):
        return INPUT(INPUT_KEYBOARD, _INPUTunion(ki=structure))
    if isinstance(structure, HARDWAREINPUT):
        return INPUT(INPUT_HARDWARE, _INPUTunion(hi=structure))
    raise TypeError('Cannot create INPUT structure!')


def MouseInput(flags, x, y, data):
    return MOUSEINPUT(x, y, data, flags, 0, None)


def KeybdInput(code, flags):
    return KEYBDINPUT(code, code, flags, 0, None)

def HardwareInput(message, parameter):
    return HARDWAREINPUT(message & 0xFFFFFFFF,
                         parameter & 0xFFFF,
                         parameter >> 16 & 0xFFFF)

def Mouse(flags, x=0, y=0, data=0):
    return Input(MouseInput(flags, x, y, data))

def Keyboard(code, flags=0):
    return Input(KeybdInput(code, flags))

def Hardware(message, parameter=0):
    return Input(HardwareInput(message, parameter))

################################################################################

UPPER = frozenset('~!@#$%^&*()_+QWERTYUIOP{}|ASDFGHJKL:"ZXCVBNM<>?')
LOWER = frozenset("`1234567890-=qwertyuiop[]\\asdfghjkl;'zxcvbnm,./")
ORDER = string.ascii_letters + string.digits + ' \b\r\t'
OTHER = {'`': VK_OEM_3,
         '~': VK_OEM_3,
         '-': VK_OEM_MINUS,
         '_': VK_OEM_MINUS,
         '=': VK_OEM_PLUS,
         '+': VK_OEM_PLUS,
         '[': VK_OEM_4,
         '{': VK_OEM_4,
         ']': VK_OEM_6,
         '}': VK_OEM_6,
         '\\': VK_OEM_5,
         '|': VK_OEM_5,
         ';': VK_OEM_1,
         ':': VK_OEM_1,
         "'": VK_OEM_7,
         '"': VK_OEM_7,
         ',': VK_OEM_COMMA,
         '<': VK_OEM_COMMA,
         '.': VK_OEM_PERIOD,
         '>': VK_OEM_PERIOD,
         '/': VK_OEM_2,
         '?': VK_OEM_2}

def pressKey(keyName):
    keyCode = keyNameToKeyCode(keyName)
    event = Keyboard(keyCode, 0)
    return sendInput(event)

def releaseKey(keyName):
    keyCode = keyNameToKeyCode(keyName)
    event = Keyboard(keyCode, KEYEVENTF_KEYUP)
    return sendInput(event)

def keyboardStream(string):
    shiftPressed = False
    for character in string.replace('\r\n', '\r').replace('\n', '\r'):
        if shiftPressed and character in LOWER or not shiftPressed and character in UPPER:
            yield Keyboard(VK_SHIFT, shiftPressed and KEYEVENTF_KEYUP)
            shiftPressed = not shiftPressed
        if ctypes.windll.user32.VkKeyScanW(character) != -1:
            code = ctypes.windll.user32.VkKeyScanW(character)
            modifiers = (code & 0xff00) >> 8
            if (modifiers & 1 and not shiftPressed) or (not modifiers & 1 and shiftPressed):
                yield Keyboard(VK_SHIFT, shiftPressed and KEYEVENTF_KEYUP)
                shiftPressed = not shiftPressed
            if modifiers & 2:
                yield Keyboard(VK_CONTROL)
            if modifiers & 4:
                yield Keyboard(VK_MENU)
            yield Keyboard(code)
            yield Keyboard(code, KEYEVENTF_KEYUP)
            if modifiers & 4:
                yield Keyboard(VK_MENU, KEYEVENTF_KEYUP)
            if modifiers & 2:
                yield Keyboard(VK_CONTROL, KEYEVENTF_KEYUP)
            continue
        elif character in ORDER:
            code = ord(character.upper())
        elif character in OTHER:
            code = OTHER[character]
        else:
            continue
            raise ValueError('String is not understood!')
        yield Keyboard(code)
        yield Keyboard(code, KEYEVENTF_KEYUP)
    if shiftPressed:
        yield Keyboard(VK_SHIFT, KEYEVENTF_KEYUP)

def screenshotZYBGR(screenshotSize=(None, None)):
    "Return width, height and zlib-compressed pixel data"
    # Size of both queues is 1. Who manages to put a request in will
    # get the response with requested resolution.
    _g_screenshotRequestQueue.put(screenshotSize)
    return _g_screenshotResponseQueue.get()

def sendType(text):
    for event in keyboardStream(text):
        sendInput(event)
        time.sleep(0.05)
    return True

def keyNameToKeyCode(keyName):
    if isinstance(keyName, int):
        return keyName
    elif isinstance(keyName, str):
        if len(keyName) == 1:
            return ord(keyName.upper())
        elif keyName.startswith("VK_") or keyName.startswith("KEY_") and keyName in globals():
            return globals()[keyName]
        elif ("VK_" + keyName) in globals():
            return globals()["VK_" + keyName]
        elif ("KEY_" + keyName) in globals():
            return globals()["KEY_" + keyName]
        else:
            raise ValueError('invalid key: "%s"' % (keyName,))
    else:
        raise TypeError('invalid key type: %s (key name: %s)' % (type(keyName), keyName))

def sendKey(keyName, modifiers):
    """
    keyName is a name (string) or a code (integer)
    modifiers is a list of keyNames.

    Examples:
      pressKey("s", modifiers=["VK_LWIN"])
      pressKey("KEY_A", modifiers=["VK_LSHIFT"])
    """
    sendKeyDown(keyName, modifiers)
    time.sleep(0.1)
    sendKeyUp(keyName, modifiers)

def sendKeyDown(keyName, modifiers):
    for m in modifiers:
        pressKey(m)
    pressKey(keyName)
    return True

def sendKeyUp(keyName, modifiers):
    releaseKey(keyName)
    for m in modifiers:
        releaseKey(m)
    return True

def sendClick(x, y, button=1):
    sendMouseMove(x, y, button)
    sendMouseDown(button)
    sendMouseUp(button)
    return True

def sendTouchDown(x, y):
    return touchDown(x, y)

def sendTouchUp(x, y):
    return touchUp(x, y)

def sendTouchMove(x, y):
    return touchMove(x, y)

def sendTap(x, y):
    touchDown(x, y)
    time.sleep(0.1)
    touchUp(x, y)
    return True

def sendMouseDown(button=1):
    if button == 1:
        flags = MOUSEEVENTF_LEFTDOWN
    elif button == 2:
        flags = MOUSEEVENTF_MIDDLEDOWN
    elif button == 3:
        flags = MOUSEEVENTF_RIGHTDOWN
    else:
        return False
    event = Mouse(flags, 0, 0, 0)
    return sendInput(event)

def sendMouseUp(button=1):
    if button == 1:
        flags = MOUSEEVENTF_LEFTUP
    elif button == 2:
        flags = MOUSEEVENTF_MIDDLEUP
    elif button == 3:
        flags = MOUSEEVENTF_RIGHTUP
    else:
        return False
    event = Mouse(flags, 0, 0, 0)
    return sendInput(event)

def sendMouseMove(x, y, button=1):
    flags = MOUSEEVENTF_ABSOLUTE | MOUSEEVENTF_MOVE | MOUSEEVENTF_VIRTUALDESK
    x = x * 65535 /_mouse_input_area[0]
    y = y * 65535 /_mouse_input_area[1]
    event = Mouse(flags, x, y, 0)
    return sendInput(event)

def windowList():
    windows = []
    def enumWindowsProc(hwnd, p):
        props = windowProperties(hwnd)
        bbox = props["bbox"]
        # skip zero-sized windows
        if bbox[0] < bbox[2] and bbox[1] < bbox[3]:
            windows.append(props)
        return True

    EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.wintypes.BOOL,
                                         ctypes.wintypes.HWND,
                                         ctypes.c_void_p)
    callback = EnumWindowsProc(enumWindowsProc)
    ctypes.windll.user32.EnumWindows(callback, 0)
    return windows

def topWindowWidgets():
    hwnd = topWindow()
    if not hwnd:
        return None
    return windowWidgets(hwnd)

def windowWidgets(hwnd):
    """
    Returns dictionary hwnd -> [winfo, ...]
    where winfo is a tuple:
        hwnd, parenthwnd, classname, text, (left, top, right, bottom)
    """
    GetClassName = ctypes.windll.user32.GetClassNameW
    GetWindowRect = ctypes.windll.user32.GetWindowRect
    SendMessage = ctypes.windll.user32.SendMessageW
    SBUFSIZE = 2048
    sbuf = ctypes.create_unicode_buffer(SBUFSIZE)
    r = ctypes.wintypes.RECT()

    rootProp = windowProperties(hwnd)
    rootInfo = (hwnd, None, "", rootProp["title"], rootProp["bbox"])

    widgets = {hwnd: [], "root": [rootInfo]}
    def enumChildProc(child_hwnd, parent_hwnd):
        GetWindowRect(child_hwnd, ctypes.byref(r))
        if r.top == r.bottom or r.left == r.right:
            # nobody can click this size of object or its children
            # => skip them
            return True

        GetClassName(child_hwnd, sbuf, SBUFSIZE)
        cname = sbuf.value

        textLen = SendMessage(child_hwnd, WM_GETTEXT, SBUFSIZE, ctypes.byref(sbuf))
        if textLen:
            text = sbuf.value
        else:
            text = ""

        winfo = (child_hwnd, parent_hwnd, cname, text, (r.left, r.top, r.right, r.bottom))
        widgets[parent_hwnd].append(winfo)
        widgets[child_hwnd] = []
        ctypes.windll.user32.EnumChildWindows(child_hwnd, cb, child_hwnd)
        return True
    EnumChildProc = ctypes.WINFUNCTYPE(ctypes.wintypes.BOOL,
                                       ctypes.wintypes.HWND,
                                       ctypes.c_void_p)
    cb = EnumChildProc(enumChildProc)
    ctypes.windll.user32.EnumChildWindows(hwnd, cb, hwnd)
    return widgets

def launchUIAutomationServer():
    fromPath=[]
    properties=[]
    powershellCode = r"""
$assemblies = ('System', 'UIAutomationTypes', 'UIAutomationClient')

$source = @'
using System;
using System.Collections.Generic;
using System.IO;
using System.IO.Pipes;
using System.Linq;
using System.Windows.Automation;

namespace FmbtWindows
{
    public class UI
    {
        // Common variables, shared by all requests.
        private static Dictionary<string, TreeWalker> stringToTreeWalker;
        private static Dictionary<string, AutomationProperty> stringToAutomationProperty;
        private static StreamWriter outStream;
        private static Dictionary<long, AutomationElement> elements;
        private static Dictionary<long, long> parents;
        private static bool cacheElements;
        private static string cacheMode;
        private static IntPtr lastWindow;

        // A static constructor is a nicer way to initialize static fields, when there's complicated code.
        static UI()
        {
            stringToTreeWalker = new Dictionary<string, TreeWalker>  {
                { "raw", TreeWalker.RawViewWalker },
                { "control", TreeWalker.ControlViewWalker },
                { "content", TreeWalker.ContentViewWalker },
            };
            stringToAutomationProperty = new Dictionary<string, AutomationProperty>
            {
                { "AcceleratorKey", AutomationElement.AcceleratorKeyProperty},
                { "AccessKey", AutomationElement.AccessKeyProperty},
                { "AutomationId", AutomationElement.AutomationIdProperty},
                { "BoundingRectangle", AutomationElement.BoundingRectangleProperty},
                { "CanSelectMultiple", SelectionPattern.CanSelectMultipleProperty},
                { "ClassName", AutomationElement.ClassNameProperty},
                { "ControlType", AutomationElement.ControlTypeProperty},
                { "CultureProperty", AutomationElement.CultureProperty},
                { "ExpandCollapseState", ExpandCollapsePattern.ExpandCollapseStateProperty},
                { "FrameworkId", AutomationElement.FrameworkIdProperty},
                { "HasKeyboardFocus", AutomationElement.HasKeyboardFocusProperty},
                { "HelpText", AutomationElement.HelpTextProperty},
                { "HorizontalScrollPercent", ScrollPattern.HorizontalScrollPercentProperty},
                { "HorizontalViewSize", ScrollPattern.HorizontalViewSizeProperty},
                { "HorizontallyScrollable", ScrollPattern.HorizontallyScrollableProperty},
                { "IsContentElement", AutomationElement.IsContentElementProperty},
                { "IsControlElement", AutomationElement.IsControlElementProperty},
                { "IsDockPatternAvailable", AutomationElement.IsDockPatternAvailableProperty},
                { "IsEnabled", AutomationElement.IsEnabledProperty},
                { "IsGridItemPatternAvailable", AutomationElement.IsGridItemPatternAvailableProperty},
                { "IsGridPatternAvailable", AutomationElement.IsGridPatternAvailableProperty},
                { "IsInvokePatternAvailable", AutomationElement.IsInvokePatternAvailableProperty},
                { "IsItemContainerPatternAvailable", AutomationElement.IsItemContainerPatternAvailableProperty},
                { "IsKeyboardFocusable", AutomationElement.IsKeyboardFocusableProperty},
                { "IsMultipleViewPatternAvailable", AutomationElement.IsMultipleViewPatternAvailableProperty},
                { "IsOffscreen", AutomationElement.IsOffscreenProperty},
                { "IsPassword", AutomationElement.IsPasswordProperty},
                { "IsRangeValuePatternAvailable", AutomationElement.IsRangeValuePatternAvailableProperty},
                { "IsReadOnly", ValuePattern.IsReadOnlyProperty},
                { "IsScrollItemPatternAvailable", AutomationElement.IsScrollItemPatternAvailableProperty},
                { "IsScrollPatternAvailable", AutomationElement.IsScrollPatternAvailableProperty},
                { "IsSelectionItemPatternAvailable", AutomationElement.IsSelectionItemPatternAvailableProperty},
                { "IsSelectionPatternAvailable", AutomationElement.IsSelectionPatternAvailableProperty},
                { "IsSelectionRequired", SelectionPattern.IsSelectionRequiredProperty},
                { "IsSynchronizedInputPatternAvailable", AutomationElement.IsSynchronizedInputPatternAvailableProperty},
                { "IsTableItemPatternAvailable", AutomationElement.IsTableItemPatternAvailableProperty},
                { "IsTablePatternAvailable", AutomationElement.IsTablePatternAvailableProperty},
                { "IsTextPatternAvailable", AutomationElement.IsTextPatternAvailableProperty},
                { "IsTogglePatternAvailable", AutomationElement.IsTogglePatternAvailableProperty},
                { "IsTransformPatternAvailable", AutomationElement.IsTransformPatternAvailableProperty},
                { "IsValuePatternAvailable", AutomationElement.IsValuePatternAvailableProperty},
                { "IsVirtualizedItemPatternAvailable", AutomationElement.IsVirtualizedItemPatternAvailableProperty},
                { "IsWindowPatternAvailable", AutomationElement.IsWindowPatternAvailableProperty},
                { "ItemStatus", AutomationElement.ItemStatusProperty},
                { "ItemType", AutomationElement.ItemTypeProperty},
                { "LabeledBy", AutomationElement.LabeledByProperty},
                { "LocalizedControlType", AutomationElement.LocalizedControlTypeProperty},
                { "Name", AutomationElement.NameProperty},
                { "Orientation", AutomationElement.OrientationProperty},
                { "ProcessId", AutomationElement.ProcessIdProperty},
                { "RuntimeId", AutomationElement.RuntimeIdProperty},
                { "Selection", SelectionPattern.SelectionProperty},
                { "ToggleState", TogglePattern.ToggleStateProperty},
                { "Value", ValuePattern.ValueProperty},
                { "VerticalViewSize", ScrollPattern.VerticalViewSizeProperty},
                { "VerticallyScrollable", ScrollPattern.VerticallyScrollableProperty},
            };
            elements = new Dictionary<long, AutomationElement>();
            parents = new Dictionary<long, long>();
            cacheElements = true;
            cacheMode = "lastwindow"; // It can only be: "none", "lastdump", "lastwindow", "all"
            lastWindow = new IntPtr(0);
        }

        private static int ReportFail(string message)
        {
            outStream.Write("\0!" + message + '\0');
            return -1;
        }

        private static void DumpElementProperties(AutomationElement elt, AutomationProperty[] supportedProps, string[] properties = null)
        {
            foreach (var p in supportedProps)
            {
                var pName = p.ProgrammaticName.Substring(p.ProgrammaticName.IndexOf(".") + 1);
                if (pName.EndsWith("Property"))
                {
                    pName = pName.Substring(0, pName.LastIndexOf("Property"));
                    if (properties == null || properties.Length == 1 || (properties.Length > 1 && properties.Contains(pName)))
                    {
                        var pValue = "" + elt.GetCurrentPropertyValue(p);
                        outStream.Write(pName + "=" + pValue.Replace("\\", "\\\\").Replace("\r\n", "\\r\\n") + '\0');
                    }
                }
            }
        }

        public static void DumpElementInfo(AutomationElement elt, long eltHash, int depth, long parent, long[] fromPath, string[] properties, int[] bbox,
            string dumpChildClass, string dumpChildName, bool doNotDump)
        {
            string pValue;
            string pName;
            var supportedProps = elt.GetSupportedProperties();
            // If location filtering is requested, skip element after reading only BoundingRectangle
            if (bbox[0] > -1)
            {
                foreach (var p in supportedProps)
                {
                    pName = p.ProgrammaticName.Substring(p.ProgrammaticName.IndexOf(".") + 1);
                    if (pName == "BoundingRectangleProperty")
                    {
                        int eltLeft, eltTop, eltRight, eltBottom;
                        pValue = "" + elt.GetCurrentPropertyValue(p);
                        if (pValue.Contains(";"))
                        {
                            var bRect = Array.ConvertAll(pValue.Split(';'), int.Parse);
                            eltLeft = bRect[0]; eltTop = bRect[1];
                            eltRight = bRect[0] + bRect[2]; eltBottom = bRect[1] + bRect[3];
                        }
                        else if (pValue.Contains(","))
                        {
                            var bRect = Array.ConvertAll(pValue.Split(','), int.Parse);
                            eltLeft = bRect[0]; eltTop = bRect[1];
                            eltRight = bRect[0] + bRect[2]; eltBottom = bRect[1] + bRect[3];
                        }
                        else {
                            continue;
                        }
                        if (eltRight < bbox[0] || eltLeft > bbox[2] || eltBottom < bbox[1] || eltTop > bbox[3])
                        {
                            return; // Skip this element and its descendants
                        }
                        break; // Skip all other properties, since we have nothing else to check.
                    }
                }
            }

            // Print element properties, if dump is allowed and child conditions are satified (if any).
            var dump = !doNotDump;
            if (dump && dumpChildClass != "")
            {
                var className = elt.GetCurrentPropertyValue(AutomationElement.ClassNameProperty, true);
                dump = className != AutomationElement.NotSupported && (className as string) == dumpChildClass;
            }
            if (dump && dumpChildName != "")
            {
                var name = elt.GetCurrentPropertyValue(AutomationElement.NameProperty, true);
                dump = name != AutomationElement.NotSupported && (name as string) == dumpChildName;
            }
            if (dump)
            {
                outStream.Write('\0');
                outStream.Write("hash=" + eltHash.ToString() + '\0');
                outStream.Write("parent=" + parent.ToString() + '\0');
                DumpElementProperties(elt, supportedProps, properties);
            }

            if (cacheElements)
            {
                elements[eltHash] = elt;
                parents[eltHash] = parent;
            }
        }

        public static void DumpElement(AutomationElement elt, int depth, long parent, long[] fromPath, string[] properties, int[] bbox, TreeWalker walker,
            string dumpChildClass, string dumpChildName, bool doNotDump)
        {
            long eltHash = elt.GetHashCode();
            eltHash = (parent << 32) + eltHash;

            if (fromPath.Length > depth && fromPath[depth] != eltHash)
            {
                return;
            }

            DumpElementInfo(elt, eltHash, depth, parent, fromPath, properties, bbox, dumpChildClass, dumpChildName, doNotDump);

            // Print child elements
            var eltChild = walker.GetFirstChild(elt);

            while (eltChild != null)
            {
                DumpElement(eltChild, depth + 1, eltHash, fromPath, properties, bbox, walker, dumpChildClass, dumpChildName, doNotDump);
                eltChild = walker.GetNextSibling(eltChild);
            }
        }

        public static int DumpWindow(string hwndString, string fromPathString, string properties, string bboxString, string walkerString,
            string filterType, string filterCondition, string dumpChildClass, string dumpChildName, string doNotDumpString)
        {
            var hwnd = new IntPtr(UInt32.Parse(hwndString));
            if (cacheMode == "none" || cacheMode == "lastdump" || ((cacheMode == "lastwindow") && (lastWindow != hwnd)))
            {
                ClearCache();
            }
            lastWindow = hwnd;
            var fromPath = Array.ConvertAll(fromPathString.Split(','), long.Parse);
            var bbox = Array.ConvertAll(bboxString.Split(','), int.Parse);
            var doNotDump = bool.Parse(doNotDumpString.ToLower());

            TreeWalker walker;
            if (!stringToTreeWalker.TryGetValue(walkerString, out walker))
            {
                return ReportFail("Unknown walker: " + walker);
            }

            var windowElement = AutomationElement.FromHandle(hwnd);
            var splittedProperties = properties.Split(',');
            if (filterType == "none")
            {
                DumpElement(windowElement, 1, 0, fromPath, splittedProperties, bbox, walker, dumpChildClass, dumpChildName, doNotDump);
            }
            else
            {
                Condition condition = null;
                string lastOperator = "";
                var lastPosition = 0;
                while (lastPosition < filterCondition.Length)
                {
                    if (filterCondition[lastPosition] == ' ')
                    {
                        lastPosition++;
                    }
                    else if (filterCondition.IndexOf("and ", lastPosition) == lastPosition)
                    {
                        if (condition == null)
                        {
                            return ReportFail(String.Format("and operator found (around position {0}) without left argument in the filter condition: {1}", lastPosition, filterCondition));
                        }
                        lastOperator = "and";
                        lastPosition += 4;
                    }
                    else {
                        var position = filterCondition.IndexOf("==", lastPosition);
                        if (position < 0)
                        {
                            return ReportFail(String.Format("== operator not found (around position {0}) in the filter condition: {1}", lastPosition, filterCondition));
                        }
                        var propName = filterCondition.Substring(lastPosition, position - lastPosition).Trim();
                        AutomationProperty propertyField;
                        if (!stringToAutomationProperty.TryGetValue(propName, out propertyField))
                        {
                            return ReportFail(String.Format("Unknown property \"{0}\" (around position {1}) in the filter condition: {2}", propName, lastPosition, filterCondition));
                        }

                        lastPosition = filterCondition.IndexOf("\"", position + 2); ;  // Skip ==, search first "
                        if (lastPosition < 0)
                        {
                            return ReportFail(String.Format("The value in the filter condition doesn't start with a double quote (around position {0}): {1}", position + 2, filterCondition));
                        }
                        position = filterCondition.IndexOf("\"", lastPosition + 1); ;  // Skip the first ", search second one
                        if (position < 0)
                        {
                            return ReportFail(String.Format("The value in the filter condition doesn't end with a double quote (around position {0}): {1}", lastPosition + 1, filterCondition));
                        }
                        var propValue = filterCondition.Substring(lastPosition + 1, position - lastPosition - 1);  // Skip double quotes
                        lastPosition = position + 1;

                        var new_condition = new PropertyCondition(propertyField, propValue);
                        if (lastOperator == "and")
                        {
                            lastOperator = "";
                            condition = new AndCondition(condition, new_condition);
                        }
                        else
                        {
                            condition = new_condition;
                        }
                    }
                }
                if (condition == null)
                {
                    return ReportFail("Invalid condition: " + filterCondition);
                }

                AutomationElement finding = null;
                AutomationElementCollection findings = null;
                if (filterType.StartsWith("all"))
                {
                    findings = windowElement.FindAll(TreeScope.Element | TreeScope.Descendants | TreeScope.Subtree, condition);
                }
                else if (filterType.StartsWith("first"))
                {
                    finding = windowElement.FindFirst(TreeScope.Element | TreeScope.Descendants | TreeScope.Subtree, condition);
                }
                else
                {
                    return ReportFail("Unknown filter type: " + filterType);
                }

                if (finding != null)
                {
                    if (filterType.Contains("children"))
                    {
                        DumpElement(finding, 1, 0, fromPath, splittedProperties, bbox, walker, dumpChildClass, dumpChildName, doNotDump);
                    }
                    else
                    {
                        DumpElementInfo(finding, finding.GetHashCode(), 1, 0, fromPath, splittedProperties, bbox, dumpChildClass, dumpChildName, doNotDump);
                    }
                }
                if (findings != null)
                {
                    if (filterType.Contains("children"))
                    {
                        foreach (AutomationElement elt in findings)
                        {
                            DumpElement(elt, 1, 0, fromPath, splittedProperties, bbox, walker, dumpChildClass, dumpChildName, doNotDump);
                        }
                    }
                    else
                    {
                        foreach (AutomationElement elt in findings)
                        {
                            DumpElementInfo(elt, elt.GetHashCode(), 1, 0, fromPath, splittedProperties, bbox, dumpChildClass, dumpChildName, doNotDump);
                        }
                    }
                }
            }
            return 0;
        }

        // AutomationElement methods

        private static bool GetElementFromHash(string eltHashString, out long eltHash, out AutomationElement elt)
        {
            eltHash = long.Parse(eltHashString);
            if (!elements.TryGetValue(eltHash, out elt))
            {
                return ReportFail("Element not found: " + eltHash) != -1;
            }

            return true;
        }

        public static int DumpCachedElement(string eltHashString)
        {
            long eltHash;
            AutomationElement elt;
            if (!GetElementFromHash(eltHashString, out eltHash, out elt))
                return -1;
            long parent = 0;
            parents.TryGetValue(eltHash, out parent);

            DumpElementInfo(elt, eltHash, 0, parent, new long[0], null, new int[] {-1, -1, -1, -1}, "", "", false);
            return 0;
        }

        private static object GetPattern(AutomationElement elt, AutomationPattern patternType)
        {
            // For a list of supported patterns: https://msdn.microsoft.com/en-us/library/ms752056(v=vs.110).aspx
            object pattern;
            if (!elt.TryGetCurrentPattern(patternType, out pattern))
            {
                ReportFail("This element doesn't support the " + Automation.PatternName(patternType) + " pattern: " + elt.GetHashCode());
                return null;
            }

            return pattern;
        }

        public static int GetProperties(string eltHashString)
        {
            long eltHash;
            AutomationElement elt;
            if (!GetElementFromHash(eltHashString, out eltHash, out elt))
                return -1;

            DumpElementProperties(elt, elt.GetSupportedProperties());

            return 0;
        }

        public static int GetPatterns(string eltHashString)
        {
            long eltHash;
            AutomationElement elt;
            if (!GetElementFromHash(eltHashString, out eltHash, out elt))
                return -1;

            outStream.Write("[\0");
            foreach (var pattern in elt.GetSupportedPatterns())
            {
                outStream.Write(Automation.PatternName(pattern) + '\0');
            }
            outStream.Write("]\0");

            return 0;
        }

        public static int SetFocus(string eltHashString)
        {
            long eltHash;
            AutomationElement elt;
            if (!GetElementFromHash(eltHashString, out eltHash, out elt))
                return -1;

            elt.SetFocus();

            return 0;
        }

        private static void CollectAllTexts(AutomationElement elt, AutomationProperty propertyField,
            string filterSubChildClassName, int maxSubChildren, List<string> texts, TreeWalker walker)
        {
            if (maxSubChildren != 0 && texts.Count >= maxSubChildren)
            {
                return;
            }
            if (filterSubChildClassName == "" || elt.Current.ClassName == filterSubChildClassName)
            {
                var value = elt.GetCurrentPropertyValue(propertyField, true);
                if (value != AutomationElement.NotSupported)
                {
                    texts.Add("" + value);
                }
            }

            // Collect all child elements
            var eltChild = walker.GetFirstChild(elt);
            while (eltChild != null)
            {
                CollectAllTexts(eltChild, propertyField, filterSubChildClassName, maxSubChildren, texts, walker);
                eltChild = walker.GetNextSibling(eltChild);
            }
        }

        private static void CollectAllTextsCached(AutomationElement elt, AutomationProperty propertyField,
            string filterSubChildClassName, int maxSubChildren, List<string> texts)
        {
            if (maxSubChildren != 0 && texts.Count >= maxSubChildren)
            {
                return;
            }
            if (filterSubChildClassName == "" || elt.Cached.ClassName == filterSubChildClassName)
            {
                var value = elt.GetCachedPropertyValue(propertyField, true);
                if (value != AutomationElement.NotSupported) {
                    texts.Add("" + value);
                }

            }

            // Collect all child elements
            foreach (AutomationElement child in elt.CachedChildren)
            {
                CollectAllTextsCached(child, propertyField, filterSubChildClassName, maxSubChildren, texts);
            }
        }

        public static int GetItems(string eltHashString, string propertyName, string separator,
            string filterSubChildClassName, string maxSubChildrenString)
        {
            long eltHash;
            AutomationElement elt;
            if (!GetElementFromHash(eltHashString, out eltHash, out elt))
                return -1;

            AutomationProperty propertyField;
            if (!stringToAutomationProperty.TryGetValue(propertyName, out propertyField))
            {
                return ReportFail(String.Format("Unknown property: \"{0}\"", propertyName));
            }

            var maxSubChildren = int.Parse(maxSubChildrenString);

            var cacheRequest = new CacheRequest();
            cacheRequest.Add(propertyField);
            if (filterSubChildClassName != "")
            {
                cacheRequest.Add(AutomationElement.ClassNameProperty);
            }
            cacheRequest.TreeScope = TreeScope.Element | TreeScope.Descendants | TreeScope.Subtree;
            AutomationElement element;
            using (cacheRequest.Activate())
            {
                // Load the element caching the specified properties for all its descendants.
                var condition = new PropertyCondition(AutomationElement.ControlTypeProperty, elt.Current.ControlType);
                element = elt.FindFirst(cacheRequest.TreeScope, condition);
                if (element == null)
                {
                    return ReportFail("Cannot find the element : " + eltHash);
                }
            }

            var texts = new List<string>();
            outStream.Write("[\0");
            foreach (AutomationElement item in element.CachedChildren)
            {
                CollectAllTextsCached(item, propertyField, filterSubChildClassName, maxSubChildren, texts);
                outStream.Write(String.Join(separator, texts) + '\0');
                texts.Clear();
            }
            outStream.Write("]\0");

            return 0;
        }

        // ExpandCollapsePattern methods

        public static int Collapse(string eltHashString)
        {
            long eltHash;
            AutomationElement elt;
            if (!GetElementFromHash(eltHashString, out eltHash, out elt))
                return -1;

            var pattern = GetPattern(elt, ExpandCollapsePattern.Pattern) as ExpandCollapsePattern;
            if (pattern == null)
                return -1;

            var state = pattern.Current.ExpandCollapseState;
            if (state == ExpandCollapseState.Expanded || state == ExpandCollapseState.PartiallyExpanded)
            {
                pattern.Collapse();
            }

            return 0;
        }

        public static int Expand(string eltHashString)
        {
            long eltHash;
            AutomationElement elt;
            if (!GetElementFromHash(eltHashString, out eltHash, out elt))
                return -1;

            var pattern = GetPattern(elt, ExpandCollapsePattern.Pattern) as ExpandCollapsePattern;
            if (pattern == null)
                return -1;

            var state = pattern.Current.ExpandCollapseState;
            if (state == ExpandCollapseState.Collapsed || state == ExpandCollapseState.PartiallyExpanded)
            {
                pattern.Expand();
            }

            return 0;
        }

        // ItemContainerPattern methods

        public static int GetContainerItems(string eltHashString, string propertyName, string separator,
            string filterSubChildClassName, string maxSubChildrenString, string scrollString)
        {
            long eltHash;
            AutomationElement elt;
            if (!GetElementFromHash(eltHashString, out eltHash, out elt))
                return -1;

            AutomationProperty propertyField;
            if (!stringToAutomationProperty.TryGetValue(propertyName, out propertyField))
            {
                return ReportFail(String.Format("Unknown property: \"{0}\"", propertyName));
            }

            var maxSubChildren = int.Parse(maxSubChildrenString);
            var scroll = bool.Parse(scrollString.ToLower());

            var pattern = GetPattern(elt, ItemContainerPattern.Pattern) as ItemContainerPattern;
            if (pattern == null)
                return -1;

            var texts = new List<string>();
            outStream.Write("[\0");
            AutomationElement item = null;
            while ((item = pattern.FindItemByProperty(item, null, null)) != null)
            {
                if (!ScrolledItem(item, scroll))
                    return -1;
                CollectAllTexts(item, propertyField, filterSubChildClassName, maxSubChildren, texts, TreeWalker.RawViewWalker);
                outStream.Write(String.Join(separator, texts) + '\0');
                texts.Clear();
            }
            outStream.Write("]\0");

            return 0;
        }

        // ScrollItemPattern methods

        private static bool ScrolledItem(AutomationElement elt, bool scroll)
        {
            if (scroll)
            {
                var scrollPattern = GetPattern(elt, ScrollItemPattern.Pattern) as ScrollItemPattern;
                if (scrollPattern == null)
                {
                    return false;
                }
                else
                {
                    scrollPattern.ScrollIntoView();
                }
            }
            return true;
        }

        // SelectionPattern methods

        public static int GetSelectedItems(string eltHashString, string propertyName, string separator,
            string filterSubChildClassName, string maxSubChildrenString, string scrollString)
        {
            long eltHash;
            AutomationElement elt;
            if (!GetElementFromHash(eltHashString, out eltHash, out elt))
                return -1;

            AutomationProperty propertyField;
            if (!stringToAutomationProperty.TryGetValue(propertyName, out propertyField))
            {
                return ReportFail(String.Format("Unknown property: \"{0}\"", propertyName));
            }

            var maxSubChildren = int.Parse(maxSubChildrenString);
            var scroll = bool.Parse(scrollString.ToLower());

            var pattern = GetPattern(elt, SelectionPatternIdentifiers.Pattern) as SelectionPattern;
            if (pattern == null)
                return -1;

            var current = pattern.Current;
            var selection = current.GetSelection();

            var texts = new List<string>();
            outStream.Write("[\0");
            foreach(AutomationElement item in selection)
            {
                if (!ScrolledItem(item, scroll))
                    return -1;
                CollectAllTexts(item, propertyField, filterSubChildClassName, maxSubChildren, texts, TreeWalker.RawViewWalker);
                outStream.Write(String.Join(separator, texts) + '\0');
                texts.Clear();
            }
            outStream.Write("]\0");

            return 0;
        }

        // TextPattern methods

        public static int GetText(string eltHashString, string maxLengthString)
        {
            long eltHash;
            AutomationElement elt;
            if (!GetElementFromHash(eltHashString, out eltHash, out elt))
                return -1;

            var pattern = GetPattern(elt, TextPattern.Pattern) as TextPattern;
            if (pattern == null)
                return -1;

            var text = pattern.DocumentRange.GetText(int.Parse(maxLengthString));
            outStream.Write("text=" + text + '\0');

            return 0;
        }

        // ValuePattern methods

        public static int SetValue(string eltHashString, string value)
        {
            long eltHash;
            AutomationElement elt;
            if (!GetElementFromHash(eltHashString, out eltHash, out elt))
                return -1;

            var pattern = GetPattern(elt, ValuePattern.Pattern) as ValuePattern;
            if (pattern == null)
                return -1;

            pattern.SetValue(value);

            return 0;
        }

        // Server methods

        public static int SetCacheMode(string mode)
        {
            cacheMode = mode;
            cacheElements = mode != "none";

            return 0;
        }

        public static int ClearCache()
        {
            elements.Clear();
            parents.Clear();

            return 0;
        }

        public static void RunServer()
        {
            while (true)
            {
                var pipeServer = new NamedPipeServerStream("fmbtwindows_uiautomation", PipeDirection.InOut);
                pipeServer.WaitForConnection();
                outStream = new StreamWriter(pipeServer);
                var sr = new StreamReader(pipeServer);
                try
                {
                    // Read parameters size and function name
                    var s = sr.ReadLine();
                    var index = s.IndexOf('\0');
                    var requestSize = int.Parse(s.Substring(0, index));
                    outStream.Write("#requestSize: " + requestSize + '\0');
                    var functionName = s.Substring(index + 1);
                    outStream.Write("#functionName: " + functionName + '\0');

                    // Read parameters in a single chunk of data
                    var charBuffer = new Char[requestSize];
                    var currLen = 0;
                    while (currLen < requestSize)
                    {
                        currLen += sr.Read(charBuffer, currLen, requestSize - currLen);
                    }

                    s = new String(charBuffer);
                    // Each parameter is separated by the special \0 character
                    var parameters = (s == "") ? null : s.Split('\0');
                    outStream.Write("#parameters:\0");
                    if (parameters != null)
                    {
                        foreach(var param in parameters)
                        {
                            outStream.Write('#' + param + '\0');
                        }
                    }
                    outStream.Write("#end-of-parameters\0");

                    var method = typeof(UI).GetMethod(functionName);
                    if (method == null)
                    {
                        ReportFail("Unknown function name: " + functionName);
                    }
                    else {
                        method.Invoke(null, parameters);
                    }
                }
                catch (Exception e)
                {
                    ReportFail("Unhandled exception: " + e);
                }
                finally
                {
                    outStream.Write("#end-of-dump");
                    outStream.Flush();
                    outStream.Close();
                    sr.Close();
                }
                pipeServer.Close();
            }
        }
    }
}
'@

Add-Type -ReferencedAssemblies $assemblies -TypeDefinition $source -Language CSharp

[FmbtWindows.UI]::RunServer()
"""
    fd, filename = tempfile.mkstemp(prefix="fmbtwindows-dumpwindow-", suffix=".ps1")
    _g_rmAtExit.append(filename)
    os.write(fd, powershellCode)
    os.close(fd)
    run_script = ["powershell.exe", "-ExecutionPolicy", "Unrestricted", filename]
    server_process = subprocess.Popen(run_script)


def _callServer(functionName, *args):
    def toString(value):
        if isinstance(value, (list, tuple)):
            return ",".join(str(item) for item in value)
        else:
            return str(value)

    serverLaunched = False
    endTime = time.time() + 30
    while True:
        try:
            f = open(r"\\.\pipe\fmbtwindows_uiautomation", "r+")
            break
        except IOError:
            if not serverLaunched:
                launchUIAutomationServer()
                serverLaunched = True
            time.sleep(0.5)
            if time.time() > endTime:
                raise Exception("dump timed out: cannot connect to uiautomation server")

    buf = "\0".join(toString(arg) for arg in args)
    # \n counts as two characters on Windows!
    request = "%s\0%s\n%s" % (len(buf) + buf.count('\n'), functionName, buf)
    f.write(request)
    f.flush()
    rv = f.read()
    f.close()
    return rv

def dumpUIAutomationElements(window=None, fromPath=[], properties=[], area=None, walker="raw",
  filterType="none", filterCondition="", dumpChildClass="", dumpChildName="", doNotDump=False):
    return _callServer("DumpWindow",
        window or topWindow(), ["-1"] + fromPath, ["nonemptylist"] + properties, area or (-1, -1, -1, -1), walker,
        filterType, filterCondition, dumpChildClass, dumpChildName, doNotDump)

def serverSetCacheMode(mode):
    return _callServer("SetCacheMode", mode)

def serverClearCache():
    return _callServer("ClearCache")

def getCachedAutomationElement(eltHash):
    return _callServer("DumpCachedElement", eltHash)

def getAutomationElementPatterns(eltHash):
    return _callServer("GetPatterns", eltHash)

def getAutomationElementProperties(eltHash):
    return _callServer("GetProperties", eltHash)

def setAutomationElementFocus(eltHash):
    return _callServer("SetFocus", eltHash)

def getAutomationElementItems(eltHash, propertyName, separator, filterSubChildClassName, maxSubChildren):
    return _callServer("GetItems", eltHash, propertyName, separator, filterSubChildClassName, maxSubChildren)

def AutomationElementCollapse(eltHash):
    return _callServer("Collapse", eltHash)

def AutomationElementExpand(eltHash):
    return _callServer("Expand", eltHash)

def getAutomationElementContainerItems(eltHash, propertyName, separator, filterSubChildClassName, maxSubChildren, scroll):
    return _callServer("GetContainerItems", eltHash, propertyName, separator, filterSubChildClassName, maxSubChildren, scroll)

def getAutomationElementSelectedItems(eltHash, propertyName, separator, filterSubChildClassName, maxSubChildren, scroll):
    return _callServer("GetSelectedItems", eltHash, propertyName, separator, filterSubChildClassName, maxSubChildren, scroll)

def getAutomationElementText(eltHash, maxLength):
    return _callServer("GetText", eltHash, maxLength)

def setAutomationElementValue(eltHash, value):
    return _callServer("SetValue", eltHash, value)

def _openRegistryKey(key, accessRights):
    firstKey = key.split("\\", 1)[0]
    subKey = key[len(firstKey) + 1:]
    HKEY = getattr(_winreg, firstKey, None)
    if not firstKey.startswith("HKEY_") or HKEY == None:
        raise ValueError("invalid HKEY_* at the beginning of the key %s" % (repr(key),))
    regKey = _winreg.OpenKey(HKEY, subKey, 0, accessRights)
    return regKey

def _openRegistryKeyAnyArch(key, accessRights):
    regKey = None
    regError = None
    for archBits in _g_archRegistryKeys:
        try:
            regKey = _openRegistryKey(key, accessRights | archBits)
            break
        except OSError, e:
            regError = e
            continue
    if regKey == None:
        raise regError
    return regKey

def kill(*pids):
    rv = True
    for pid in pids:
        handle = ctypes.windll.kernel32.OpenProcess(PROCESS_TERMINATE, False, pid)
        if handle:
            rv = rv and (ctypes.windll.kernel32.TerminateProcess(handle, -1) != 0)
            ctypes.windll.kernel32.CloseHandle(handle)
        else:
            rv = False
    return rv

def processList():
    retval = []
    MAX_NUMBER_OF_PROCESSES = 1024 * 64
    processIds = (MAX_NUMBER_OF_PROCESSES * DWORD)()
    bytesReturned = DWORD()
    if ctypes.windll.psapi.EnumProcesses(processIds,
                                         ctypes.sizeof(processIds),
                                         ctypes.byref(bytesReturned)) != 0:
        for procIndex in xrange(bytesReturned.value / ctypes.sizeof(DWORD)):
            processId = processIds[procIndex]
            hProcess = ctypes.windll.kernel32.OpenProcess(
                PROCESS_QUERY_INFORMATION, False, processId)
            if hProcess:
                bytesReturned.value = ctypes.sizeof(_filenameBufferW)
                if ctypes.windll.kernel32.QueryFullProcessImageNameW(
                        hProcess,
                        0, # Win32 path format
                        ctypes.byref(_filenameBufferW),
                        ctypes.byref(bytesReturned)) != 0:
                    retval.append({
                        "pid": int(processId),
                        "ProcessImageFileName": _filenameBufferW.value})
                ctypes.windll.kernel32.CloseHandle(hProcess)
    return retval

def processStatus(pid):
    hProcess = ctypes.windll.kernel32.OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, pid)

    if hProcess == 0:
        raise ValueError('cannot get status of process %s' % (pid,))

    rv = {"pid": pid}

    if GetProcessMemoryInfo(hProcess,
                            ctypes.byref(_processMemoryCountersEx),
                            ctypes.sizeof(_processMemoryCountersEx)) != 0:
        for fieldName, fieldType in _processMemoryCountersEx._fields_:
            if fieldName == "cb":
                continue
            rv[fieldName] = int(getattr(_processMemoryCountersEx, fieldName))

    bytesReturned = DWORD()
    bytesReturned.value = ctypes.sizeof(_filenameBufferW)
    if ctypes.windll.kernel32.QueryFullProcessImageNameW(
            hProcess,
            0, # Win32 path format
            ctypes.byref(_filenameBufferW),
            ctypes.byref(bytesReturned)) != 0:
        rv["ProcessImageFileName"] = _filenameBufferW.value

    if ctypes.windll.kernel32.GetProcessTimes(
            hProcess,
            ctypes.byref(_creationTime),
            ctypes.byref(_exitTime),
            ctypes.byref(_kernelTime),
            ctypes.byref(_userTime)) != 0:
        rv["UserTime"] = ((_userTime.dwHighDateTime << 32) + _userTime.dwLowDateTime) / 10000000.0
        rv["KernelTime"] = ((_kernelTime.dwHighDateTime << 32) + _kernelTime.dwLowDateTime) / 10000000.0

    if ctypes.windll.kernel32.GetProcessHandleCount(
            hProcess,
            ctypes.byref(_dword)) != 0:
        rv["HandleCount"] = int(_dword.value)

    ctypes.windll.kernel32.CloseHandle(hProcess)
    return rv

def products(properties=("ProductName", "Publisher",
                         "Version", "VersionString",
                         "InstallDate", "InstallLocation",
                         "InstallSource", "LocalPackage")):
    retval = []
    iProductIndex = 0
    cchValueBuf = DWORD(0)
    enumStatus = ctypes.windll.msi.MsiEnumProductsW(iProductIndex, _filenameBufferW)
    while enumStatus == 0:
        productCode = _filenameBufferW.value
        productInfo = {"ProductCode": productCode}
        for pname in properties:
            cchValueBuf.value = ctypes.sizeof(_filenameBufferW)
            if ctypes.windll.msi.MsiGetProductInfoW(
                    productCode, unicode(pname), _filenameBufferW,
                    ctypes.byref(cchValueBuf)) == 0:
                productInfo[pname] = _filenameBufferW.value
        retval.append(productInfo)
        iProductIndex += 1
        enumStatus = ctypes.windll.msi.MsiEnumProductsW(iProductIndex, _filenameBufferW)
    return retval

def setRegistry(key, valueName, value, valueType=None):
    key = key.replace("/", "\\")
    if not _winreg:
        return False
    if valueType == None:
        if isinstance(value, basestring):
            valueType = "REG_SZ"
        elif isinstance(value, int) or isinstance(value, long):
            valueType = "REG_DWORD"
        else:
            raise TypeError("valueType must be specified for value of %s" %
                            (type(value),))
    REG_type = getattr(_winreg, valueType, None)
    if not valueType.startswith("REG_") or REG_type == None:
        raise ValueError("invalid value type (REG_*): %s" % (repr(valueType),))
    regKey = _openRegistryKeyAnyArch(key, _winreg.KEY_SET_VALUE)
    try:
        _winreg.SetValueEx(regKey, valueName, 0, REG_type, value)
    finally:
        _winreg.CloseKey(regKey)
    return True

def getRegistry(key, valueName):
    key = key.replace("/", "\\")
    regKey = _openRegistryKeyAnyArch(key, _winreg.KEY_QUERY_VALUE)
    try:
        value, valueType = _winreg.QueryValueEx(regKey, valueName)
    finally:
        _winreg.CloseKey(regKey)
    return value, _REG_types.get(valueType, None)

def findRegistry(rootKey, key=None, valueName=None, limit=None):
    rootKey = rootKey.replace('/', '\\')
    if key != None:
        key = re.compile(key.replace('/', '\\'))
    if valueName != None:
        valueName = re.compile(valueName)
    if limit == None:
        limit = -1
    resultList = []
    _findRegistry(rootKey, key, valueName, limit, resultList)
    return sorted(set(resultList))

def _findRegistry(rootKey, key, valueName, limit, resultList):
    """returns matching (key, valueName) pairs in registry
    if valueName is not searched for, value will be None"""
    for archBits in _g_archRegistryKeys:
        try:
            root = _openRegistryKey(rootKey, _winreg.KEY_READ | archBits)
        except OSError:
            continue
        try:
            if valueName != None:
                valueCount = _winreg.QueryInfoKey(root)[1]
                for valueIndex in xrange(valueCount):
                    _valueName, _valueData, _valueType = _winreg.EnumValue(root, valueIndex)
                    if key == None:
                        # Look for a valueName only
                        if valueName.match(_valueName):
                            resultList.append((rootKey, _valueName))
                            if len(resultList) == limit:
                                return
                    else:
                        # Look for key-valueName combination
                        if valueName.match(_valueName) and key.search(rootKey):
                            resultList.append((rootKey, _valueName))
                            if len(resultList) == limit:
                                return
            else:
                # Look for a key only
                if key.search(rootKey):
                    resultList.append((rootKey, None))
                    if len(resultList) == limit:
                        return

            # Recursive step - look among subkeys
            subkeyCount = _winreg.QueryInfoKey(root)[0]
            for subkeyIndex in xrange(subkeyCount):
                subkeyName = _winreg.EnumKey(root, subkeyIndex)
                fullPathBackslash = rootKey + "\\" + subkeyName
                _findRegistry(fullPathBackslash, key, valueName, limit, resultList)
                if len(resultList) == limit:
                    return
        finally:
            _winreg.CloseKey(root)

def getClipboardText():
    if ctypes.windll.user32.IsClipboardFormatAvailable(CF_TEXT) == 0:
        return None
    if ctypes.windll.user32.OpenClipboard(0) == 0:
        raise Exception("error in opening clipboard")
    handle = ctypes.windll.user32.GetClipboardData(CF_TEXT)
    if handle != 0:
        string_p = ctypes.windll.kernel32.GlobalLock(handle)
        try:
            rv = ctypes.string_at(string_p)
        finally:
            ctypes.windll.kernel32.GlobalUnlock(handle)
    else:
        rv = None
    ctypes.windll.user32.CloseClipboard()
    return rv

def setClipboardText(text):
    if ctypes.windll.user32.OpenClipboard(0) == 0:
        raise Exception("error in opening clipboard")
    handle = ctypes.windll.kernel32.GlobalAlloc(GMEM_MOVEABLE, len(text)+1)
    if handle == 0:
        ctypes.windll.user32.CloseClipboard()
        raise Exception("error in allocating global memory for text")
    string_p = ctypes.windll.kernel32.GlobalLock(handle)
    if string_p == 0:
        ctypes.windll.user32.CloseClipboard()
        raise Exception("error in locking global memory block")
    try:
        ctypes.memmove(string_p, text, len(text))
    finally:
        ctypes.windll.kernel32.GlobalUnlock(handle)
    ctypes.windll.user32.EmptyClipboard()
    ctypes.windll.user32.SetClipboardData(CF_TEXT, handle)
    ctypes.windll.user32.CloseClipboard()

def _check_output(*args, **kwargs):
    """subprocess.check_output, for Python 2.6 compatibility"""
    p = subprocess.Popen(*args, stdout=subprocess.PIPE, **kwargs)
    out, err = p.communicate()
    exitstatus = p.poll()
    if exitstatus:
        raise subprocess.CalledProcessError(exitstatus, args[0])
    return out

def shell(command):
    if isinstance(command, list):
        useShell = False
    else:
        useShell = True
    try:
        output = _check_output(command, shell=useShell)
    except subprocess.CalledProcessError, e:
        if hasattr(e, "output"):
            output = e.output
        else:
            output = None
    return output

def saveFile(srcFilename, destFilepath, data, append=False):
    if os.path.isdir(destFilepath):
        destFilename = os.path.join(destFilepath, srcFilename)
    else:
        destFilename = destFilepath
    if not append:
        file(destFilename, "wb").write(data)
    else:
        file(destFilename, "ab").write(data)
    return True

def _exitStatusWriter(process, statusFile, filesToBeCleaned):
    statusFile.write(str(process.wait()))
    statusFile.close()
    for f in filesToBeCleaned:
        try: os.remove(f)
        except: pass

def shellSOE(command, asyncStatus=None, asyncOut=None, asyncError=None,
             cwd=None, timeout=None):
    filesToBeCleaned = []
    if isinstance(command, list):
        useShell = False
    else:
        if len(command.splitlines()) > 1:
            # multiline command, write a BAT and run it
            fd, filename = tempfile.mkstemp(prefix="fmbtwindows-shellcmd-", suffix=".bat")
            os.write(fd, command)
            os.close(fd)
            command = [filename]
            filesToBeCleaned.append(filename)
            useShell = False
        else:
            useShell = True

    if (asyncStatus, asyncOut, asyncError) != (None, None, None):
        # asynchronous execution
        if not asyncStatus or asyncStatus == True:
            asyncStatus = os.devnull
        if not asyncOut or asyncOut == True:
            asyncOut = os.devnull
        if not asyncError or asyncError == True:
            asyncError = os.devnull
        sFile = file(os.path.expandvars(asyncStatus), "w")
        oFile = file(os.path.expandvars(asyncOut), "w")
        eFile = file(os.path.expandvars(asyncError), "w")
        p = subprocess.Popen(command, shell=useShell,
                             stdin = file(os.devnull),
                             stdout = oFile,
                             stderr = eFile,
                             cwd = cwd)
        thread.start_new_thread(_exitStatusWriter, (p, sFile, filesToBeCleaned))
        return (None, None, None)

    # synchronous execution
    p = None
    try:
        p = subprocess.Popen(command, shell=useShell,
                             stdin = subprocess.PIPE,
                             stdout = subprocess.PIPE,
                             stderr = subprocess.PIPE,
                             cwd = cwd)
    except OSError:
        status, out, err = None, None, None
    if p != None: # process successfully launched
        if timeout == None:
            # read out/err/status without timeout
            out, err = p.communicate()
            status = p.returncode
        else:
            # read out/err/status with timeout
            out_err_queue = Queue.Queue()
            status_queue = Queue.Queue()
            def out_err_reader():
                out_err_queue.put(p.communicate())
                status_queue.put(p.returncode)
            def terminate_p():
                status_queue.put("TIMEOUT %s" % (p.pid,))
                subprocess.Popen("taskkill /F /PID %s /T" % (p.pid,))
                # Typically here p.communicate() will return, and
                # thus out_err_reader produces out/err to the queue.
                # However, if the process tree refuses to get killed in
                # reasonable time, write (None, None) out/err queue from here
                # allowing the shellSOE call to return.
                time.sleep(0.5)
                out_err_queue.put((None, None))
            timer = threading.Timer(timeout, terminate_p)
            thread.start_new_thread(out_err_reader, ())
            try:
                timer.start()
                status = status_queue.get()
                out, err = out_err_queue.get()
            finally:
                timer.cancel()
    for f in filesToBeCleaned:
        try: os.remove(f)
        except: pass
    return status, out, err

def showWindow(hwnd, showCmd):
    if isinstance(showCmd, str) or isinstance(showCmd, unicode):
        if showCmd in _g_showCmds:
            showCmd = _g_showCmds.index(showCmd)
        else:
            raise ValueError('invalid showCmd: "%s"' % (showCmd,))
    return 0 != ctypes.windll.user32.ShowWindow(hwnd, showCmd)

def topWindow():
    return ctypes.windll.user32.GetForegroundWindow()

def topWindowProperties():
    hwnd = topWindow()
    if not hwnd:
        return None
    return windowProperties(hwnd)

def setTopWindow(hwnd):
    status = windowStatus(hwnd)
    if not status["visible"] or not status["foreground"]:
        showWindow(hwnd, "SW_MINIMIZE")
        showWindow(hwnd, "SW_RESTORE")
    elif status["iconic"]:
        showWindow(hwnd, "SW_RESTORE")
    return (ctypes.windll.user32.SetForegroundWindow(hwnd) != 0 and
            ctypes.windll.user32.BringWindowToTop(hwnd) != 0 and
            topWindow() == hwnd)

def windowProperties(hwnd):
    hwnd &= 0xffffffff
    try:
        titleLen = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
        titleLen = min(titleLen, 2047) # limit max length for safety
        titleBuf = ctypes.create_unicode_buffer(titleLen + 1)
        ctypes.windll.user32.GetWindowTextW(hwnd, titleBuf, titleLen + 1)

        r = ctypes.wintypes.RECT()
        ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(r))

        pid = ctypes.c_uint(-1)
        ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))

        return {'bbox': (r.left, r.top, r.right, r.bottom),  # x1, y1, x2, y2
            'hwnd': hwnd, 'title': titleBuf.value, 'pid': int(pid.value)}
    except ctypes.ArgumentError:
        return {'bbox': (-1, -1, -1, -1,),
            'hwnd': hwnd, 'title': '', 'pid': 0}

def windowStatus(hwnd):
    status = {
        "enabled": ctypes.windll.user32.IsWindowEnabled(hwnd) != 0,
        "iconic": ctypes.windll.user32.IsIconic(hwnd) != 0,
        "zoomed": ctypes.windll.user32.IsZoomed(hwnd) != 0,
        "visible": ctypes.windll.user32.IsWindowVisible(hwnd) != 0,
        "hung": ctypes.windll.user32.IsHungAppWindow(hwnd) != 0,
        "foreground": ctypes.windll.user32.GetForegroundWindow() == hwnd
    }
    return status

def closeWindow(hwnd):
    return ctypes.windll.user32.PostMessageW(hwnd, WM_CLOSE, 0, 0) != 0

def screenshotTakerThread():
    # Screenshots must be taken in the same thread. If BitBlt is
    # called from different threads, screenshots are not update. On the
    # other hand, creating new GetDC + ... for every screenshot worked
    # on 32-bit Python in separate threads, but did not work in 64-bit
    # after the first thread. Pythonshare-server creates a new thread for
    # each connection. Therefore we need a single screenshot taker thread.
    global _g_lastWidth, _g_lastHeight

    def takerFree(srcdc, memdc, bmp):
        if bmp != None:
            ctypes.windll.gdi32.DeleteObject(bmp)
        if memdc != None:
            ctypes.windll.gdi32.DeleteObject(memdc)
        if srcdc != None:
            ctypes.windll.user32.ReleaseDC(0, srcdc)

    def takerRealloc(width, height, srcdc, memdc, bmp, c_bmp_header, c_bits):
        takerFree(srcdc, memdc, bmp)
        bmp_header = struct.pack('LHHHH', struct.calcsize('LHHHH'), width, height, 1, 24)
        srcdc = ctypes.windll.user32.GetDC(0)
        memdc = ctypes.windll.gdi32.CreateCompatibleDC(srcdc)
        bmp = ctypes.windll.gdi32.CreateCompatibleBitmap(srcdc, width, height)
        c_bmp_header = ctypes.c_buffer(bmp_header)
        c_bits = ctypes.c_buffer(' ' * (height * ((width * 3 + 3) & -4)))
        return srcdc, memdc, bmp, c_bmp_header, c_bits

    srcdc, memdc, bmp, c_bmp_header, c_bits = (None,) * 5

    SRCCOPY = 0xCC0020
    DIB_RGB_COLORS = 0

    width, height = _g_screenshotRequestQueue.get()
    while width != "QUIT":

        if width == None: # try autodetect
            left = ctypes.windll.user32.GetSystemMetrics(SM_XVIRTUALSCREEN)
            right =ctypes.windll.user32.GetSystemMetrics(SM_CXVIRTUALSCREEN)
            width = right - left
        else:
            left = 0

        if height == None:
            top = ctypes.windll.user32.GetSystemMetrics(SM_YVIRTUALSCREEN)
            bottom = ctypes.windll.user32.GetSystemMetrics(SM_CYVIRTUALSCREEN)
            height = bottom - top
        else:
            top = 0

        if (width, height) != (_g_lastWidth, _g_lastHeight):
            srcdc, memdc, bmp, c_bmp_header, c_bits = takerRealloc(
                width, height, srcdc, memdc, bmp, c_bmp_header, c_bits)
            _g_lastWidth = width
            _g_lastHeight = height

        ctypes.windll.gdi32.SelectObject(memdc, bmp)
        ctypes.windll.gdi32.BitBlt(memdc, 0, 0, width, height, srcdc, left, top, SRCCOPY)
        got_bits = ctypes.windll.gdi32.GetDIBits(
            memdc, bmp, 0, height, c_bits, c_bmp_header, DIB_RGB_COLORS)

        _g_screenshotResponseQueue.put((width, height, zlib.compress(c_bits.raw)))

        width, height = _g_screenshotRequestQueue.get()

    takerFree(srcdc, memdc, bmp)

def wmicGet(component, componentArgs=()):
    cmd = (["wmic", component] +
           list(componentArgs) +
           ["get", "/format:textvaluelist"])
    s, o, e = shellSOE(cmd)
    rv = {}
    for l in o.splitlines():
        try:
            key, value = l.split("=", 1)
        except ValueError:
            continue
        rv[key] = value
    return rv

if not "_mouse_input_area" in globals():
    left = ctypes.windll.user32.GetSystemMetrics(SM_XVIRTUALSCREEN)
    right =ctypes.windll.user32.GetSystemMetrics(SM_CXVIRTUALSCREEN)
    top = ctypes.windll.user32.GetSystemMetrics(SM_YVIRTUALSCREEN)
    bottom = ctypes.windll.user32.GetSystemMetrics(SM_CYVIRTUALSCREEN)
    width = right - left
    height = bottom - top
    _mouse_input_area = (width, height)

if not "_g_touchInjenctionInitialized" in globals():
    try:
        if (ctypes.windll.user32.InitializeTouchInjection(2, 1) != 0):
            _g_touchInjenctionInitialized = True
        else:
            pass
    except:
        _g_touchInjenctionInitialized = False

if not "_g_screenshotRequestQueue" in globals():
    # Initialize screenshot thread and communication channels
    _g_lastWidth = None
    _g_lastHeight = None
    _g_screenshotRequestQueue = Queue.Queue(1)
    _g_screenshotResponseQueue = Queue.Queue(1)
    thread.start_new_thread(screenshotTakerThread, ())

if __name__ == '__main__':
    start = time.time()
    screenshot(0)
    end = time.time()
    print "total screenshot time:", end-start
