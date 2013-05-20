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
This is library implements fMBT GUITestInterface for Tizen devices and
emulators.


Example 1: Take a screenshot on the lock. Run in Python:

import fmbttizen, time
d = fmbttizen.Device()
d.pressPower(), time.sleep(1), d.pressPower(), time.sleep(1)
d.refreshScreenshot().save("/tmp/lockscreen.png")

Then save the lock on the lockscreen and as "lock.png". Install
shutter and run in shell:

display /tmp/lockscreen.png &
shutter -s --exit_after_capture -o lock.png


Example 2: Open the lock screen, launch Settings

import fmbttizen, time
d = fmbttizen.Device()
d.enableVisualLog("device.html")
d.pressHome()
time.sleep(1)
d.refreshScreenshot()
if d.verifyBitmap("lock.png"):
    d.swipeBitmap("lock.png", "east") # open screenlock
    time.sleep(1)
    d.pressHome()

if d.waitOcrText("Settings"):
    d.tapOcrText("Settings", tapPos=(0.5, -1))

"""

import atexit
import base64
import cPickle
import commands
import subprocess
import os
import Queue
import sys
import thread
import time
import zlib

import fmbt
import fmbtgti

def _adapterLog(msg):
    fmbt.adapterlog("fmbttizen: %s" % (msg,))

def _run(command, expectedExitStatus=None):
    if type(command) == str: shell=True
    else: shell=False

    try:
        p = subprocess.Popen(command, shell=shell,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             close_fds=True)
        if expectedExitStatus != None:
            out, err = p.communicate()
        else:
            out, err = ('', None)
    except Exception, e:
        class fakeProcess(object): pass
        p = fakeProcess
        p.returncode = 127
        out, err = ('', e)

    exitStatus = p.returncode

    if (expectedExitStatus != None and
        exitStatus != expectedExitStatus and
        exitStatus not in expectedExitStatus):
        msg = "Executing %s failed. Exit status: %s, expected %s" % (command, exitStatus, expectedExitStatus)
        fmbt.adapterlog("%s\n    stdout: %s\n    stderr: %s\n" % (msg, out, err))
        raise FMBTTizenError(msg)

    return exitStatus, out, err

def _fileToQueue(f, outQueue):
    line = f.readline()
    while line != "":
        outQueue.put(line)
        line = f.readline()
    f.close()

class Device(fmbtgti.GUITestInterface):
    def __init__(self, debugAgentFile=None):
        """
        Parameters:

          debugAgentFile (file-like object)
                  record communication with the fMBT Tizen agent to
                  given file. The default is None: communication is
                  not recorded.
        """
        fmbtgti.GUITestInterface.__init__(self)
        self.setConnection(TizenDeviceConnection(debugAgentFile=debugAgentFile))

    def close(self):
        fmbtgti.GUITestInterface.close(self)
        if hasattr(self, "_conn"):
            self._conn.close()

    def pressPower(self, **pressKeyKwArgs):
        """
        Press the power button.

        Parameters:

          long, hold (optional):
                  refer to pressKey documentation.
        """
        return self.pressKey("POWER", **pressKeyKwArgs)

    def pressVolumeUp(self, **pressKeyKwArgs):
        """
        Press the volume up button.

        Parameters:

          long, hold (optional):
                  refer to pressKey documentation.
        """
        return self.pressKey("VOLUME_UP", **pressKeyKwArgs)

    def pressVolumeDown(self, **pressKeyKwArgs):
        """
        Press the volume down button.

        Parameters:

          long, hold (optional):
                  refer to pressKey documentation.
        """
        return self.pressKey("VOLUME_DOWN", **pressKeyKwArgs)

    def pressHome(self, **pressKeyKwArgs):
        """
        Press the home button.

        Parameters:

          long, hold (optional):
                  refer to pressKey documentation.
        """
        return self.pressKey("HOME", **pressKeyKwArgs)

    def shell(self, shellCommand):
        """
        Execute shell command through sdb shell.

        Parameters:

          shellCommand (string)
                  command to be executed in sdb shell.

        Returns output of "sdb shell" command.

        If you wish to receive exitstatus or standard output and error
        separated from shellCommand, refer to shellSOE().
        """
        return _run(["sdb", "shell", shellCommand], expectedExitStatus=range(256))[1]

    def shellSOE(self, shellCommand):
        """
        Get status, output and error of executing shellCommand on Tizen device

        Parameters:

          shellCommand (string)
                  command to be executed on device.

        Returns tuple (exitStatus, standardOutput, standardError).
        """
        return self._conn.shellSOE(shellCommand)

_g_sdbProcesses = set()
def _forceCloseSdbProcesses():
    for p in _g_sdbProcesses:
        try: p.write("quit\n")
        except: pass
        try: p.terminate()
        except: pass
atexit.register(_forceCloseSdbProcesses)

class TizenDeviceConnection(fmbtgti.GUITestConnection):
    """
    TizenDeviceConnection copies _tizenAgent to Tizen device,
    and runs & communicates with it via sdb shell.
    """
    def __init__(self, debugAgentFile=None):
        self._serialNumber = self.recvSerialNumber()
        self._sdbShell = None
        self._debugAgentFile = debugAgentFile
        self.open()

    def __del__(self):
        self.close()

    def open(self):
        self.close()

        agentFilename = "/tmp/fmbttizen-agent.py"
        agentRemoteFilename = "/tmp/fmbttizen-agent.py"

        file(agentFilename, "w").write(_tizenAgent)

        uploadCmd = ["sdb", "push", agentFilename, agentRemoteFilename]
        try:
            status, out, err = _run(uploadCmd, range(256))
            if status == 127:
                raise TizenConnectionError('Executing "sdb push" failed. Check your Tizen SDK installation.')
            elif status != 0:
                if "device not found" in err:
                    raise TizenDeviceNotFoundError("Tizen device not found.")
                else:
                    raise TizenConnectionError('Executing "%s" failed: %s' % (' '.join(uploadCmd), err + " " + out))

            try:
                self._sdbShell = subprocess.Popen(["sdb", "shell"], shell=False,
                                                  stdin=subprocess.PIPE,
                                                  stdout=subprocess.PIPE,
                                                  stderr=subprocess.PIPE,
                                                  close_fds=True)
            except OSError, msg:
                raise TizenConnectionError('Executing "sdb shell" failed. Check your Tizen SDK installation.')
            _g_sdbProcesses.add(self._sdbShell)
            self._sdbShellErrQueue = Queue.Queue()
            thread.start_new_thread(_fileToQueue, (self._sdbShell.stderr, self._sdbShellErrQueue))

            self._sdbShell.stdin.write("\r")
            try:
                ok, version = self._agentCmd("python %s; exit" % (agentRemoteFilename,))
            except IOError:
                raise TizenConnectionError('Connecting to Tizen device with "sdb shell" failed.')
        finally:
            os.remove(agentFilename)
        return ok

    def reportErrorsInQueue(self):
        while True:
            try: l = self._sdbShellErrQueue.get_nowait()
            except Queue.Empty: return
            if self._debugAgentFile: self._debugAgentFile.write("<2 %s" % (l,))
            _adapterLog("fmbttizen agent error: %s" % (l,))

    def close(self):
        if self._sdbShell != None:
            try: self._agentCmd("quit", retry=0)
            except: pass
            try: self._sdbShell.terminate()
            except: pass
            try: self._sdbShell.stdin.close()
            except: pass
            try: self._sdbShell.stdout.close()
            except: pass
            try: self._sdbShell.stderr.close()
            except: pass
            self.reportErrorsInQueue()
            _g_sdbProcesses.remove(self._sdbShell)
        self._sdbShell = None

    def _agentAnswer(self):
        errorLinePrefix = "FMBTAGENT ERROR "
        okLinePrefix = "FMBTAGENT OK "
        l = self._sdbShell.stdout.readline()
        output = []
        while True:
            if self._debugAgentFile:
                if len(l) > 72: self._debugAgentFile.write("<1 %s...\n" % (l[:72],))
                else: self._debugAgentFile.write("<1 %s\n" % (l,))
            if l.startswith(okLinePrefix):
                return True, cPickle.loads(base64.b64decode(l[len(okLinePrefix):]))
            elif l.startswith(errorLinePrefix):
                return False, cPickle.loads(base64.b64decode(l[len(errorLinePrefix):]))
            else:
                output.append(l)
                pass
            l = self._sdbShell.stdout.readline()
            if l == "":
                raise IOError("Unexpected termination of sdb shell: %s" % ("\n".join(output)))
            l = l.strip()

    def _agentCmd(self, command, retry=3):
        if self._debugAgentFile: self._debugAgentFile.write(">0 %s\n" % (command,))
        try:
            self._sdbShell.stdin.write("%s\r" % (command,))
            self._sdbShell.stdin.flush()
        except IOError, msg:
            if retry > 0:
                time.sleep(.2)
                self.reportErrorsInQueue()
                _adapterLog('Error when sending command "%s": %s.' % (command, msg))
                self.open()
                self._agentCmd(command, retry=retry-1)
            else:
                raise
        return self._agentAnswer()

    def sendPress(self, keyName):
        return self._agentCmd("kp %s" % (keyName,))[0]

    def sendKeyDown(self, keyName):
        return self._agentCmd("kd %s" % (keyName,))[0]

    def sendKeyUp(self, keyName):
        return self._agentCmd("ku %s" % (keyName,))[0]

    def sendTap(self, x, y):
        return self._agentCmd("tt %s %s 1" % (x, y))[0]

    def sendTouchDown(self, x, y):
        return self._agentCmd("td %s %s 1" % (x, y))[0]

    def sendTouchMove(self, x, y):
        return self._agentCmd("tm %s %s" % (x, y))[0]

    def sendTouchUp(self, x, y):
        return self._agentCmd("tu %s %s 1" % (x, y))[0]

    def sendType(self, string):
        return self._agentCmd("kt %s" % (base64.b64encode(cPickle.dumps(string))))[0]

    def recvScreenshot(self, filename):
        rv, img = self._agentCmd("ss")
        if rv == False:
            return False
        try:
            header, data = zlib.decompress(img).split('\n',1)
            width, height, depth, bpp = [int(n) for n in header.split()[1:]]
        except Exception, e:
            raise TizenConnectionError("Corrupted screenshot data: %s" % (e,))
        if len(data) != width * height * 4:
            raise FMBTTizenError("Image data size mismatch.")

        fmbtgti.eye4graphics.bgrx2rgb(data, width, height);

        # TODO: use libimagemagick directly to save data to png?
        ppm_header = "P6\n%d %d\n%d\n" % (width, height, 255)
        f = file(filename + ".ppm", "w").write(ppm_header + data[:width*height*3])
        _run(["convert", filename + ".ppm", filename], expectedExitStatus=0)
        os.remove("%s.ppm" % (filename,))
        return True

    def recvSerialNumber(self):
        s, o = commands.getstatusoutput("sdb get-serialno")
        return o.splitlines()[-1]

    def shellSOE(self, shellCommand):
        _, (s, o, e) = self._agentCmd("es %s" % (base64.b64encode(cPickle.dumps(shellCommand)),))
        return s, o, e

    def target(self):
        return self._serialNumber

# _tizenAgent code is executed on Tizen device through sdb shell.
_tizenAgent = """
import base64
import cPickle
import ctypes
import os
import platform
import re
import struct
import subprocess
import sys
import time
import zlib
import termios

libc           = ctypes.CDLL("libc.so.6")
libX11         = ctypes.CDLL("libX11.so")
libXtst        = ctypes.CDLL("libXtst.so.6")

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

# Set input device names (in /proc/bus/input/devices)
# for pressing hardware keys.
try: cpuinfo = file("/proc/cpuinfo").read()
except: cpuinfo = ""

if 'TRATS' in cpuinfo:
    # Running on Lunchbox
    hwKeyDevice = {
        "POWER": "gpio-keys",
        "VOLUMEUP": "gpio-keys",
        "VOLUMEDOWN": "gpio-keys",
        "HOME": "gpio-keys"
        }
    _inputKeyNameToCode["HOME"] = 139
elif 'QEMU Virtual CPU' in cpuinfo:
    # Running on Tizen emulator
    hwKeyDevice = {
        "POWER": "Power Button",
        "VOLUMEUP": "AT Translated Set 2 hardkeys",
        "VOLUMEDOWN": "AT Translated Set 2 hardkeys",
        "HOME": "AT Translated Set 2 hardkeys"
        }
else:
    # Running on some other device
    hwKeyDevice = {
        "POWER": "msic_power_btn",
        "VOLUMEUP": "gpio-keys",
        "VOLUMEDOWN": "gpio-keys",
        "HOME": "mxt224_key_0"
        }

# Read input devices
deviceToEventFile = {}
for _l in file("/proc/bus/input/devices"):
    if _l.startswith('N: Name="'): _device = _l.split('"')[1]
    elif _l.startswith("H: Handlers=") and "event" in _l:
        try: deviceToEventFile[_device] = "/dev/input/" + re.findall("(event[0-9]+)", _l)[0]
        except Exception, e: pass

# Connect to X server, get root window size for screenshots
display        = libX11.XOpenDisplay(X_NULL)
current_screen = libX11.XDefaultScreen(display)
root_window    = libX11.XRootWindow(display, current_screen)
X_AllPlanes    = libX11.XAllPlanes()

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

def read_cmd():
    return sys.stdin.readline().strip()

def write_response(ok, value):
    if ok: p = "FMBTAGENT OK "
    else: p = "FMBTAGENT ERROR "
    response = "%s%s\\n" % (p, base64.b64encode(cPickle.dumps(value)))
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

def typeSequence(s):
    skipped = []
    for c in s:
        keysym = libX11.XStringToKeysym(c)
        if keysym == NoSymbol:
            skipped.append(c)
            continue
        keycode = libX11.XKeysymToKeycode(display, keysym)
        libXtst.XTestFakeKeyEvent(display, keycode, X_True, X_CurrentTime)
        libXtst.XTestFakeKeyEvent(display, keycode, X_False, X_CurrentTime)
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
    rawfmbt_header = "FMBTRAWX11 %d %d %d %d\\n" % (
                     image.width, image.height, root_depth.value, image.bits_per_pixel)
    rawfmbt_data = ctypes.string_at(image.data, image.height * image.bytes_per_line)
    compressed_image = zlib.compress(rawfmbt_header + rawfmbt_data, 3)
    libX11.XDestroyImage(image_p)
    return True, compressed_image

def shellSOE(command):
    try:
        p = subprocess.Popen(command, shell=True,
                             stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             close_fds=True)
    except Exception, e:
        return False, (None, None, e)
    out, err = p.communicate()
    return True, (p.returncode, out, err)

# Disable terminal echo
origTermAttrs = termios.tcgetattr(sys.stdin.fileno())
newTermAttrs = origTermAttrs
newTermAttrs[3] = origTermAttrs[3] &  ~termios.ECHO
termios.tcsetattr(sys.stdin.fileno(), termios.TCSANOW, newTermAttrs)

# Send version number, enter main loop
write_response(True, "0.0")
cmd = read_cmd()
while cmd:
    if cmd.startswith("tm "):   # touch move(x, y)
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
        rv, msg = sendHwKey(cmd[3:], 0, -1)
        write_response(rv, msg)
    elif cmd.startswith("kp "): # hw key press
        rv, msg = sendHwKey(cmd[3:], 0, 0)
        write_response(rv, msg)
    elif cmd.startswith("ku "): # hw key up
        rv, msg = sendHwKey(cmd[3:], -1, 0)
        write_response(rv, msg)
    elif cmd.startswith("kt "): # send x events
        rv, skippedSymbols = typeSequence(cPickle.loads(base64.b64decode(cmd[3:])))
        libX11.XFlush(display)
        write_response(rv, skippedSymbols)
    elif cmd.startswith("ss"): # save screenshot
        rv, compressedImage = takeScreenshot()
        write_response(rv, compressedImage)
    elif cmd.startswith("es "): # execute shell
        rv, soe = shellSOE(cPickle.loads(base64.b64decode(cmd[3:])))
        write_response(rv, soe)
    elif cmd.startswith("quit"): # quit
        write_response(rv, True)
        break
    else:
        write_response(False, 'Unknown command: "%s"' % (cmd,))
    cmd = read_cmd()

libX11.XCloseDisplay(display)

termios.tcsetattr(sys.stdin.fileno(), termios.TCSANOW, origTermAttrs)
"""

class FMBTTizenError(Exception): pass
class TizenConnectionError(FMBTTizenError): pass
class TizenDeviceNotFoundError(TizenConnectionError): pass
