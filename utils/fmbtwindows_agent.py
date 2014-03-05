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

import ctypes
import ctypes.wintypes
import glob
import os
import string
import struct
import subprocess
import sys
import time
import zlib

try:
    import wmi # try to import wmi, requires that pywin32 and wmi packages
               # are installed in DUT
except:
    pass

_mouse_input_area = (1920, 1080)
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

LONG = ctypes.c_long
DWORD = ctypes.c_ulong
ULONG_PTR = ctypes.POINTER(DWORD)
WORD = ctypes.c_ushort

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

# Initialize Pointer and Touch info

pointerInfo = POINTER_INFO(pointerType=PT_TOUCH,
                         pointerId=0,
                         ptPixelLocation=ctypes.wintypes.POINT(90,54))

touchInfo = POINTER_TOUCH_INFO(pointerInfo=pointerInfo,
                             touchFlags=TOUCH_FLAG_NONE,
                             touchMask=TOUCH_MASK_ALL,
                             rcContact=ctypes.wintypes.RECT(pointerInfo.ptPixelLocation.x-5,
                                  pointerInfo.ptPixelLocation.y-5,
                                  pointerInfo.ptPixelLocation.x+5,
                                  pointerInfo.ptPixelLocation.y+5),
                             orientation=90,
                             pressure=32000)

def touchDown(x, y, fingerRadius=5):
    touchInfo.pointerInfo.ptPixelLocation.x = x
    touchInfo.pointerInfo.ptPixelLocation.y = y

    touchInfo.rcContact.left = x - fingerRadius
    touchInfo.rcContact.right = x + fingerRadius
    touchInfo.rcContact.top = y - fingerRadius
    touchInfo.rcContact.bottom = y + fingerRadius

    #Press Down
    touchInfo.pointerInfo.pointerFlags = (POINTER_FLAG_DOWN|
                                        POINTER_FLAG_INRANGE|
                                        POINTER_FLAG_INCONTACT)

    if (ctypes.windll.user32.InjectTouchInput(1, ctypes.byref(touchInfo)) == 0):
        print "Touch down failed with error: " + ctypes.FormatError()
        return False

    else:
        print "Touch Down Succeeded!"
        return True

def touchMove(x, y, fingerRadius=5):
    touchInfo.pointerInfo.ptPixelLocation.x = x
    touchInfo.pointerInfo.ptPixelLocation.y = y

    touchInfo.rcContact.left = x - fingerRadius
    touchInfo.rcContact.right = x + fingerRadius
    touchInfo.rcContact.top = y - fingerRadius
    touchInfo.rcContact.bottom = y + fingerRadius

    # send update event
    touchInfo.pointerInfo.pointerFlags = (POINTER_FLAG_UPDATE|
                                        POINTER_FLAG_INRANGE|
                                        POINTER_FLAG_INCONTACT)

    if (ctypes.windll.user32.InjectTouchInput(1, ctypes.byref(touchInfo)) == 0):
        print "Touch Move failed with error: " + ctypes.FormatError()
        return False

    else:
        print "Touch Move Succeeded!"
        return True

def touchUp(x, y, fingerRadius=5):
    touchInfo.pointerInfo.ptPixelLocation.x = x
    touchInfo.pointerInfo.ptPixelLocation.y = y

    touchInfo.rcContact.left = x - fingerRadius
    touchInfo.rcContact.right = x + fingerRadius
    touchInfo.rcContact.top = y - fingerRadius
    touchInfo.rcContact.bottom = y + fingerRadius

    #Initialize Touch Injection
    #if (ctypes.windll.user32.InitializeTouchInjection(1, 1) != 0):
    #    print "Initialized Touch Injection"

    # First update touch position to given coordinates. 
    # This is need for swiping to get touch up from correct place
    
    touchInfo.pointerInfo.pointerFlags = (POINTER_FLAG_UPDATE|
                                        POINTER_FLAG_INRANGE|
                                        POINTER_FLAG_INCONTACT)

    if (ctypes.windll.user32.InjectTouchInput(1, ctypes.byref(touchInfo)) == 0):
        print "Touch up failed with error: " + ctypes.FormatError()
        return False
    touchInfo.pointerInfo.pointerFlags = (POINTER_FLAG_UP)

    if (ctypes.windll.user32.InjectTouchInput(1, ctypes.byref(touchInfo)) == 0):
        print "Touch up failed with error: " + ctypes.FormatError()
        return False
    else:
        print "Pull Up Succeeded!"
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
ALTER = dict(zip('!@#$%^&*()', '1234567890'))
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

def pressKey(hexKeyCode):
    event = Keyboard(hexKeyCode, 0)
    return sendInput(event)

def releaseKey(hexKeyCode):
    event = Keyboard(hexKeyCode, KEYEVENTF_KEYUP)
    return sendInput(event)

def keyboardStream(string):
    shiftPressed = False
    for character in string.replace('\r\n', '\r').replace('\n', '\r'):
        if shiftPressed and character in LOWER or not shiftPressed and character in UPPER:
            yield Keyboard(VK_SHIFT, shiftPressed and KEYEVENTF_KEYUP)
            shiftPressed = not shiftPressed
        character = ALTER.get(character, character)
        if character in ORDER:
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

_g_lastWidth = None
_g_lastHeight = None

def zybgrSize():
    "Return dimensions of most recently returned ZYBGR screenshot"
    return _g_lastWidth, _g_lastHeight

def screenshotZYBGR(screenshotSize=(None, None)):
    "Return width, height and zlib-compressed pixel data"
    global _g_lastWidth, _g_lastHeight
    width, height = screenshotSize
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
    _g_lastWidth = width
    _g_lastHeight = height
    print "W x H ==", width, "X", height

    # width = monitor['width']
    # height = monitor['height']
    # left = monitor['left']
    # top = monitor['top']
    SRCCOPY = 0xCC0020
    DIB_RGB_COLORS = 0
    srcdc = ctypes.windll.user32.GetWindowDC(0)
    memdc = ctypes.windll.gdi32.CreateCompatibleDC(srcdc)
    bmp = ctypes.windll.gdi32.CreateCompatibleBitmap(srcdc, width, height)
    ctypes.windll.gdi32.SelectObject(memdc, bmp)
    ctypes.windll.gdi32.BitBlt(memdc, 0, 0, width, height, srcdc, left, top, SRCCOPY)
    bmp_header = struct.pack('LHHHH', struct.calcsize('LHHHH'), width, height, 1, 24)
    c_bmp_header = ctypes.c_buffer(bmp_header)
    c_bits =       ctypes.c_buffer(' ' * (height * ((width * 3 + 3) & -4)))
    got_bits =     ctypes.windll.gdi32.GetDIBits(memdc, bmp, 0, height,
                                c_bits, c_bmp_header, DIB_RGB_COLORS)
    ctypes.windll.gdi32.DeleteObject(bmp)
    ctypes.windll.gdi32.DeleteObject(memdc)
    ctypes.windll.gdi32.DeleteObject(srcdc)
    return zlib.compress(c_bits.raw)

def sendType(text):
    for event in keyboardStream(text):
        sendInput(event)
        time.sleep(0.05)
    return True

def sendKey(keyname, modifiers):
    mods = 0
    '''
    keyname can be either single character or constant defined in keyboard.py
    w.pressKey("a")
    w.pressKey("KEY_A")

    modifier can be either VK_LWIN as defined in keyboard.py
    or pure hex keycode 0x5B
    w.pressKey("s",modifiers=["VK_LWIN"])
    w.pressKey("KEY_A",modifiers=["VK_LSHIFT"])
    '''

    for m in modifiers:
        print m
        if "VK_" in str(m):
            mods |= globals()[m]
        else:
            mods |= m
    print sys._getframe().f_code.co_name, keyname, mods
    if mods:
        for m in modifiers:
            if "VK_" in str(m):
                pressKey(globals()[m])

            else:
                pressKey(m)
            print "modifier down:", m
    if len(keyname) == 1:
        print "key down:", ord(keyname)
        pressKey(ord(keyname.upper()))
        time.sleep(0.1)
        print "key up:", ord(keyname)
        releaseKey(ord(keyname.upper()))
    else:
        print "key down:", globals()[keyname]
        pressKey(globals()[keyname])
        time.sleep(0.1)
        print "key up:", globals()[keyname]
        releaseKey(globals()[keyname])
    if mods:
        for m in modifiers:
            if "VK_" in str(m):
                releaseKey(globals()[m])
            else:
                releaseKey(m)
            print "modifier up:", m

def sendKeyDown(keyname, modifiers):
    for m in modifiers:
        pressKey(m)
    pressKey(keyname)
    return True

def sendKeyUp(keyname, modifiers):
    releaseKey(keyname)
    for m in modifiers:
        releaseKey(m)
    return True

def sendClick(x, y, button=1):
    print "sendClick", x, y
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
    flags = MOUSEEVENTF_ABSOLUTE | MOUSEEVENTF_MOVE
    x = x * 65535 /_mouse_input_area[0]
    y = y * 65535 /_mouse_input_area[1]
    event = Mouse(flags, x, y, 0)
    return sendInput(event)

def shell(command):
    return subprocess.call(command)

def launchHTTPD():
    global _HTTPServerProcess
    _HTTPServerProcess = subprocess.Popen("python -m SimpleHTTPServer 8000")
    return True

def stopHTTPD():
    print "stopping " + str(_HTTPServerProcess)
    _HTTPServerProcess.terminate()
    return True

def enum_display_monitors():
    ''' Get positions and handles of one or more monitors. '''

    def _callback(monitor, dc, rect, data):
        rct = rect.contents
        infos = {}
        infos['left'] = rct.left
        infos['right'] = rct.right
        infos['top'] = rct.top
        infos['bottom'] = rct.bottom
        infos['hmon'] = monitor
        infos['hdc'] = dc
        results.append(infos)
        return 0

    results = []
    MonitorEnumProc = ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_ulong, ctypes.c_ulong,
                                ctypes.POINTER(ctypes.wintypes.RECT), ctypes.c_double)
    callback = MonitorEnumProc(_callback)
    ctypes.windll.user32.EnumDisplayMonitors(0, 0, callback, 0)
    return results

if not "_g_monitors" in globals():
    _g_monitors = enum_display_monitors()
    _mouse_input_area = (
        _g_monitors[0]['right'] - _g_monitors[0]['left'],
        _g_monitors[0]['bottom'] - _g_monitors[0]['top'])

if not "_g_touchInjenctionInitialized" in globals():
    if (ctypes.windll.user32.InitializeTouchInjection(1, 1) != 0):
        print "Initialized Touch Injection"
        _g_touchInjenctionInitialized = True
    else:
        print "InitializeTouchInjection failed"

if __name__ == '__main__':
    start = time.time()
    screenshot(0)
    end = time.time()
    print "total screenshot time:", end-start
