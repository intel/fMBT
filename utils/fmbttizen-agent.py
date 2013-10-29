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
import os
import platform
import re
import struct
import subprocess
import sys
import time
import zlib
import termios

iAmRoot = (os.getuid() == 0)

try:
    libc           = ctypes.CDLL("libc.so.6")
    libX11         = ctypes.CDLL("libX11.so.6")
    libXtst        = ctypes.CDLL("libXtst.so.6")
    g_Xavailable = True
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

# Set input device names (in /proc/bus/input/devices)
# for pressing hardware keys.
try: cpuinfo = file("/proc/cpuinfo").read()
except: cpuinfo = ""
try: devices = file("/proc/bus/input/devices").read()
except: devices = ""

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
        mtInputDevFd = os.open("/dev/input/event2", os.O_WRONLY | os.O_NONBLOCK)
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
        mtInputDevFd = os.open("/dev/input/event2", os.O_WRONLY | os.O_NONBLOCK)
elif 'Synaptics_RMI4_touchkey' in devices:
    # Running on Geek
    hwKeyDevice = {
        "POWER": "mid_powerbtn",
        "VOLUMEUP": "gpio-keys",
        "VOLUMEDOWN": "gpio-keys",
        "HOME": "Synaptics_RMI4_touchkey"
        }
    if iAmRoot:
        mtInputDevFd = os.open("/dev/input/event1", os.O_WRONLY | os.O_NONBLOCK)
elif 'mxt224_key_0' in devices:
    # Running on Blackbay
    hwKeyDevice = {
        "POWER": "msic_power_btn",
        "VOLUMEUP": "gpio-keys",
        "VOLUMEDOWN": "gpio-keys",
        "HOME": "mxt224_key_0"
        }
    if iAmRoot:
        mtInputDevFd = os.open("/dev/input/event0", os.O_WRONLY | os.O_NONBLOCK)
else:
    # Unknown platform, guessing best possible defaults
    _d = devices.split("\n\n")
    try:
        power_devname = re.findall('Name=\"([^"]*)\"', [i for i in _d if "power" in i.lower()][0])[0]
    except IndexError:
        power_devname = "gpio-keys"
    try:
        touch_device = "/dev/input/" + re.findall('[ =](event[0-9]+)\s',  [i for i in _d if "touch" in i.lower()][0])[0]
    except IndexError:
        try:
            touch_device = "/dev/input/" + re.findall('[ =](event[0-9]+)\s',  [i for i in _d if "mouse0" in i.lower()][0])[0]
        except IndexError:
            touch_device = "/dev/input/event0"
    hwKeyDevice = {
        "POWER": power_devname,
        "VOLUMEUP": "gpio-keys",
        "VOLUMEDOWN": "gpio-keys",
        "HOME": "gpio-keys"
        }
    if iAmRoot:
        mtInputDevFd = os.open(touch_device, os.O_WRONLY | os.O_NONBLOCK)
    del _d

# Read input devices
deviceToEventFile = {}
for _l in devices.splitlines():
    if _l.startswith('N: Name="'): _device = _l.split('"')[1]
    elif _l.startswith("H: Handlers=") and "event" in _l:
        try: deviceToEventFile[_device] = "/dev/input/" + re.findall("(event[0-9]+)", _l)[0]
        except Exception, e: pass

# Connect to X server, get root window size for screenshots
if g_Xavailable:
    display = None
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

def read_cmd():
    return sys.stdin.readline().strip()

def write_response(ok, value):
    if ok: p = "FMBTAGENT OK "
    else: p = "FMBTAGENT ERROR "
    response = "%s%s\n" % (p, base64.b64encode(cPickle.dumps(value)))
    sys.stdout.write(response)
    sys.stdout.flush()

def sendHwKey(keyName, delayBeforePress, delayBeforeRelease):
    try: inputDevice = deviceToEventFile[hwKeyDevice[keyName]]
    except: return False, 'No input device for key "%s"' % (keyName,)
    try: keyCode = _inputKeyNameToCode[keyName]
    except: return False, 'No keycode for key "%s"' % (keyName,)
    try: fd = os.open(inputDevice, os.O_WRONLY | os.O_NONBLOCK)
    except: return False, 'Unable to open input device "%s" for writing' % (inputDevice,)
    if delayBeforePress > 0: time.sleep(delayBeforePress)
    if delayBeforePress >= 0:
        if os.write(fd, struct.pack(_input_event, int(time.time()), 0, _EV_KEY, keyCode, 1)) > 0:
            os.write(fd, struct.pack(_input_event, 0, 0, 0, 0, 0))
    if delayBeforeRelease > 0: time.sleep(delayBeforeRelease)
    if delayBeforeRelease >= 0:
        if os.write(fd, struct.pack(_input_event, int(time.time()), 0, _EV_KEY, keyCode, 0)) > 0:
            os.write(fd, struct.pack(_input_event, 0, 0, 0, 0, 0))
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

mtEvents = {} # slot -> (tracking_id, x, y)

def mtEventSend(eventType, event, param):
    t = time.time()
    tsec = int(t)
    tusec = int(1000000*(t-tsec))
    os.write(mtInputDevFd, struct.pack(_input_event,
        tsec, tusec, eventType, event, param))

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

def typeChar(origChar):
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

def typeSequence(s):
    skipped = []
    for c in s:
        if not typeChar(c):
            skipped.append(c)
    if skipped: return False, skipped
    else: return True, skipped

def takeScreenshot():
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
    compressed_image = zlib.compress(rawfmbt_header + rawfmbt_data, 3)
    libX11.XDestroyImage(image_p)
    return True, compressed_image

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
    answer = p.stdout.readline().rstrip()
    if answer.startswith("FMBTAGENT OK "):
        return True, cPickle.loads(base64.b64decode(answer[len("FMBTAGENT OK "):]))
    else:
        return False, cPickle.loads(base64.b64decode(answer[len("FMBTAGENT ERROR "):]))

def closeSubAgents():
    for username in _subAgents:
        subAgentCommand(username, None, "quit")

if __name__ == "__main__":
    if not "--keep-echo" in sys.argv:
        # Disable terminal echo
        origTermAttrs = termios.tcgetattr(sys.stdin.fileno())
        newTermAttrs = origTermAttrs
        newTermAttrs[3] = origTermAttrs[3] &  ~termios.ECHO
        termios.tcsetattr(sys.stdin.fileno(), termios.TCSANOW, newTermAttrs)

    # Send version number, enter main loop
    write_response(True, "0.0")
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
            libXtst.XTestFakeMotionEvent(display, current_screen, int(xs), int(ys), X_CurrentTime)
            libX11.XFlush(display)
            write_response(True, None)
        elif cmd.startswith("tt "): # touch tap(x, y, button)
            xs, ys, button = cmd[3:].strip().split()
            button = int(button)
            libXtst.XTestFakeMotionEvent(display, current_screen, int(xs), int(ys), X_CurrentTime)
            libXtst.XTestFakeButtonEvent(display, button, X_True, X_CurrentTime)
            libXtst.XTestFakeButtonEvent(display, button, X_False, X_CurrentTime)
            libX11.XFlush(display)
            write_response(True, None)
        elif cmd.startswith("td "): # touch down(x, y, button)
            xs, ys, button = cmd[3:].strip().split()
            button = int(button)
            libXtst.XTestFakeMotionEvent(display, current_screen, int(xs), int(ys), X_CurrentTime)
            libXtst.XTestFakeButtonEvent(display, button, X_True, X_CurrentTime)
            libX11.XFlush(display)
            write_response(True, None)
        elif cmd.startswith("tu "): # touch up(x, y, button)
            xs, ys, button = cmd[3:].strip().split()
            button = int(button)
            libXtst.XTestFakeMotionEvent(display, current_screen, int(xs), int(ys), X_CurrentTime)
            libXtst.XTestFakeButtonEvent(display, button, X_False, X_CurrentTime)
            libX11.XFlush(display)
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
            rv, skippedSymbols = typeSequence(cPickle.loads(base64.b64decode(cmd[3:])))
            libX11.XFlush(display)
            write_response(rv, skippedSymbols)
        elif cmd.startswith("ml "): # send multitouch linear gesture
            if iAmRoot:
                file("/tmp/debug-root","w").write(cmd[3:]+"\n")
                rv, _ = mtLinearGesture(*cPickle.loads(base64.b64decode(cmd[3:])))
            else:
                file("/tmp/debug-user","w").write(cmd)
                rv, _ = subAgentCommand("root", "tizen", cmd)
            write_response(rv, _)
        elif cmd.startswith("ss"): # save screenshot
            if "R" in cmd:
                resetXConnection()
            rv, compressedImage = takeScreenshot()
            write_response(rv, compressedImage)
        elif cmd.startswith("es "): # execute shell
            shellCmd, username, password, asyncStatus, asyncOut, asyncError = cPickle.loads(base64.b64decode(cmd[3:]))
            if username == "":
                rv, soe = shellSOE(shellCmd, asyncStatus, asyncOut, asyncError)
            else:
                rv, soe = subAgentCommand(username, password,
                    "es " + base64.b64encode(cPickle.dumps((shellCmd, "", "", asyncStatus, asyncOut, asyncError))))
            write_response(rv, soe)
        elif cmd.startswith("quit"): # quit
            write_response(rv, True)
            break
        else:
            write_response(False, 'Unknown command: "%s"' % (cmd,))
        cmd = read_cmd()

    closeSubAgents()

    libX11.XCloseDisplay(display)

    termios.tcsetattr(sys.stdin.fileno(), termios.TCSANOW, origTermAttrs)
