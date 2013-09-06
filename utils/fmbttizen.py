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
import math
import subprocess
import os
import Queue
import sys
import thread
import time
import zlib

import fmbt
import fmbtgti

# See imagemagick convert parameters.
fmbtgti._OCRPREPROCESS =  [
    '-sharpen 5 -filter Mitchell %(zoom)s -sharpen 5 -level 60%%,60%%,3.0 -sharpen 5',
    '-sharpen 5 -level 90%%,100%%,3.0 -filter Mitchell -sharpen 5'
    ]

def _takePinchArgs(d):
    return fmbtgti._takeArgs(("finger1Dir", "finger2Dir", "duration",
                              "movePoints", "sleepBeforeMove",
                              "sleepAfterMove"), d)

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
    def __init__(self, serialNumber=None, debugAgentFile=None):
        """
        Parameters:

          serialNumber (string, optional)
                  the serial number of the device to be connected.
                  The default is the first device in "sdb devices"
                  list.

          debugAgentFile (file-like object, optional)
                  record communication with the fMBT Tizen agent to
                  given file. The default is None: communication is
                  not recorded.
        """
        fmbtgti.GUITestInterface.__init__(self)
        self.setConnection(TizenDeviceConnection(serialNumber=serialNumber, debugAgentFile=debugAgentFile))
        self._serialNumber = self._conn._serialNumber

    def close(self):
        fmbtgti.GUITestInterface.close(self)
        if hasattr(self, "_conn"):
            self._conn.close()

    def connect(self):
        """
        Connect to the Tizen device.
        """
        if hasattr(self, "_conn"):
            self._conn.open()
            return True
        else:
            return False

    def disconnect(self):
        """
        Close the current connection to Tizen device.

        Returns True on success, otherwise False.
        """
        if hasattr(self, "_conn"):
            self._conn.close()
            return True
        else:
            return False

    def pinch(self, (x, y), startDistance, endDistance,
              finger1Dir=90, finger2Dir=270, duration=1.0, movePoints=20,
              sleepBeforeMove=0, sleepAfterMove=0):
        """
        Pinch (open or close) on coordinates (x, y).

        Parameters:
          x, y (integer):
                  the central point of the gesture. Values in range
                  [0.0, 1.0] are scaled to full screen width and
                  height.

          startDistance, endDistance (float):
                  distance from both finger tips to the central point
                  of the gesture, at the start and at the end of the
                  gesture. Values in range [0.0, 1.0] are scaled up to
                  the distance from the coordinates to the edge of the
                  screen. Both finger tips will reach an edge if
                  distance is 1.0.

          finger1Dir, finger2Dir (integer, optional):
                  directions for finger tip movements, in range [0,
                  360]. 0 is to the east, 90 to the north, etc. The
                  defaults are 90 and 270.

          duration (float, optional):
                  duration of the movement in seconds. The default is
                  1.0.

          movePoints (integer, optional):
                  number of points to which finger tips are moved
                  after laying them to the initial positions. The
                  default is 20.

          sleepBeforeMove, sleepAfterMove (float, optional):
                  seconds to be slept after laying finger tips on the
                  display 1) before the first move, and 2) after the
                  last move before raising finger tips. The defaults
                  are 0.0.
        """
        screenWidth, screenHeight = self.screenSize()
        screenDiagonal = math.sqrt(screenWidth**2 + screenHeight**2)

        if x == None: x = 0.5
        if y == None: y = 0.5

        x, y = self.intCoords((x, y))

        if type(startDistance) == float and 0.0 <= startDistance <= 1.0:
            startDistanceInPixels = (startDistance *
                                     max(fmbtgti._edgeDistanceInDirection((x, y), self.screenSize(), finger1Dir),
                                         fmbtgti._edgeDistanceInDirection((x, y), self.screenSize(), finger2Dir)))
        else: startDistanceInPixels = int(startDistance)

        if type(endDistance) == float and 0.0 <= endDistance <= 1.0:
            endDistanceInPixels = (endDistance *
                                   max(fmbtgti._edgeDistanceInDirection((x, y), self.screenSize(), finger1Dir),
                                       fmbtgti._edgeDistanceInDirection((x, y), self.screenSize(), finger2Dir)))
        else: endDistanceInPixels = int(endDistance)

        finger1startX = int(x + math.cos(math.radians(finger1Dir)) * startDistanceInPixels)
        finger1startY = int(y + math.sin(math.radians(finger1Dir)) * startDistanceInPixels)
        finger1endX = int(x + math.cos(math.radians(finger1Dir)) * endDistanceInPixels)
        finger1endY = int(y + math.sin(math.radians(finger1Dir)) * endDistanceInPixels)

        finger2startX = int(x + math.cos(math.radians(finger2Dir)) * startDistanceInPixels)
        finger2startY = int(y + math.sin(math.radians(finger2Dir)) * startDistanceInPixels)
        finger2endX = int(x + math.cos(math.radians(finger2Dir)) * endDistanceInPixels)
        finger2endY = int(y + math.sin(math.radians(finger2Dir)) * endDistanceInPixels)

        return self._conn.sendMtLinearGesture([[(finger1startX, finger1startY), (finger1endX, finger1endY)],
                                               [(finger2startX, finger2startY), (finger2endX, finger2endY)]],
                                              duration, movePoints, sleepBeforeMove, sleepAfterMove)

    def pinchBitmap(self, bitmap, startDistance, endDistance,
                    **pinchAndOirArgs):
        """
        Make the pinch gesture using the bitmap as central point.

        Parameters:
          bitmap (string):
                  filename of the bitmap to be pinched.

          startDistance, endDistance (float):
                  distance from both finger tips to the central point
                  of the gesture, at the start and at the end of the
                  gesture. Values in range [0.0, 1.0] are scaled up to
                  the distance from the bitmap to screen edge. Both
                  finger tips will reach an edge if distance is 1.0.

          optical image recognition arguments (optional)
                  refer to help(obj.oirEngine()).

          rest of the parameters: refer to pinch documentation.

        Returns True if successful, otherwise False.
        """
        assert self._lastScreenshot != None, "Screenshot required."
        pinchArgs, rest = _takePinchArgs(pinchAndOirArgs)
        oirArgs, _ = fmbtgti._takeOirArgs(self._lastScreenshot, rest, thatsAll=True)
        oirArgs["limit"] = 1
        items = self._lastScreenshot.findItemsByBitmap(bitmap, **oirArgs)
        if len(items) == 0:
            return False
        return self.pinchItem(items[0], startDistance, endDistance, **pinchArgs)

    def pinchClose(self, (x, y) = (0.5, 0.5), startDistance=0.5, endDistance=0.1, **pinchKwArgs):
        """
        Make the close pinch gesture.

        Parameters:
          x, y (integer, optional):
                  the central point of the gesture, the default is in
                  the middle of the screen.

          startDistance, endDistance (float, optional):
                  refer to pinch documentation. The default is 0.5 and
                  0.1.

          rest of the parameters: refer to pinch documentation.
        """
        return self.pinch((x, y), startDistance, endDistance, **pinchKwArgs)

    def pinchItem(self, viewItem, startDistance, endDistance, **pinchKwArgs):
        """
        Pinch the center point of viewItem.

        Parameters:

          viewItem (GUIItem object):
                  item to be tapped, possibly returned by
                  findItemsBy... methods in Screenshot or View.

          pinchPos (pair of floats (x,y)):
                  position to tap, relational to the bitmap.
                  (0.0, 0.0) is the top-left corner,
                  (1.0, 0.0) is the top-right corner,
                  (1.0, 1.0) is the lower-right corner.
                  Values < 0 and > 1 tap coordinates outside the item.

          rest of the parameters: refer to pinch documentation.
        """
        if "pinchPos" in pinchKwArgs:
            posX, posY = pinchKwArgs["pinchPos"]
            del pinchKwArgs["pinchPos"]
            x1, y1, x2, y2 = viewItem.bbox()
            pinchCoords = (x1 + (x2-x1) * posX,
                           y1 + (y2-y1) * posY)
        else:
            pinchCoords = viewItem.coords()
        return self.pinch(pinchCoords, startDistance, endDistance, **pinchKwArgs)

    def pinchOpen(self, (x, y) = (0.5, 0.5), startDistance=0.1, endDistance=0.5, **pinchKwArgs):
        """
        Make the open pinch gesture.

        Parameters:
          x, y (integer, optional):
                  the central point of the gesture, the default is in
                  the middle of the screen.

          startDistance, endDistance (float, optional):
                  refer to pinch documentation. The default is 0.1 and
                  0.5.

          for the rest of the parameters, refer to pinch documentation.
        """
        return self.pinch((x, y), startDistance, endDistance, **pinchKwArgs)

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
        return self.pressKey("VOLUMEUP", **pressKeyKwArgs)

    def pressVolumeDown(self, **pressKeyKwArgs):
        """
        Press the volume down button.

        Parameters:

          long, hold (optional):
                  refer to pressKey documentation.
        """
        return self.pressKey("VOLUMEDOWN", **pressKeyKwArgs)

    def pressHome(self, **pressKeyKwArgs):
        """
        Press the home button.

        Parameters:

          long, hold (optional):
                  refer to pressKey documentation.
        """
        return self.pressKey("HOME", **pressKeyKwArgs)

    def setDisplayBacklightTime(self, timeout):
        """
        Set time the LCD backlight will be kept on.

        Parameters:

          timeout (integer):
                  inactivity time in seconds after which the backlight
                  will be switched off.
        """
        return self._conn.setDisplayBacklightTime(timeout)

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

    def shellSOE(self, shellCommand, username="", password="", asyncStatus=None, asyncOut=None, asyncError=None):
        """
        Get status, output and error of executing shellCommand on Tizen device

        Parameters:

          shellCommand (string)
                  command to be executed on device.

          username (string, optional)
                  username who should execute the command. The default
                  is "", that is, run as the default user when logged
                  in using "sdb shell".

          password (string, optional)
                  if username is given, use given string as
                  password. The default is "tizen" for user "root",
                  otherwise "".

          asyncStatus (string or None)
                  filename (on device) to which the status of
                  asynchronously executed shellCommand will be
                  written. The default is None, that is, command will
                  be run synchronously, and status will be returned in
                  the tuple.

          asyncOut (string or None)
                  filename (on device) to which the standard output of
                  asynchronously executed shellCommand will be
                  written. The default is None.

          asyncError (string or None)
                  filename (on device) to which the standard error of
                  asynchronously executed shellCommand will be
                  written. The default is None.

        Returns tuple (exitStatus, standardOutput, standardError).

        If asyncStatus, asyncOut or asyncError is a string,
        shellCommand will be run asynchronously, and (0, None, None)
        will be returned. In case of asynchronous execution, if any of
        asyncStatus, asyncOut or asyncError is None, corresponding
        output will be written to /dev/null. The shellCommand will be
        executed even if the device would be disconnected. All async
        files are opened for appending, allowing writes to the same
        file.
        """
        if username == "root" and password == "":
            return self._conn.shellSOE(shellCommand, username, "tizen", asyncStatus, asyncOut, asyncError)
        else:
            return self._conn.shellSOE(shellCommand, username, password, asyncStatus, asyncOut, asyncError)

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
    def __init__(self, serialNumber=None, debugAgentFile=None):
        if serialNumber == None: self._serialNumber = self.recvSerialNumber()
        else: self._serialNumber = serialNumber

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

        uploadCmd = ["sdb", "-s", self._serialNumber, "push", agentFilename, agentRemoteFilename]
        try:
            if self._serialNumber == "unknown":
                raise TizenDeviceNotFoundError("Tizen device not found.")

            status, out, err = _run(uploadCmd, range(256))
            if status == 127:
                raise TizenConnectionError('Executing "sdb -s %s push" failed. Check your Tizen SDK installation.' % (self._serialNumber,))
            elif status != 0:
                if "device not found" in err:
                    raise TizenDeviceNotFoundError('Tizen device "%s" not found.' % (self._serialNumber,))
                else:
                    raise TizenConnectionError('Executing "%s" failed: %s' % (' '.join(uploadCmd), err + " " + out))

            try:
                self._sdbShell = subprocess.Popen(["sdb", "-s", self._serialNumber, "shell"],
                                                  shell=False,
                                                  stdin=subprocess.PIPE,
                                                  stdout=subprocess.PIPE,
                                                  stderr=subprocess.PIPE,
                                                  close_fds=True)
            except OSError, msg:
                raise TizenConnectionError('Executing "sdb -s %s shell" failed. Check your Tizen SDK installation.' % (self._serialNumber,))
            _g_sdbProcesses.add(self._sdbShell)
            self._sdbShellErrQueue = Queue.Queue()
            thread.start_new_thread(_fileToQueue, (self._sdbShell.stderr, self._sdbShellErrQueue))

            self._sdbShell.stdin.write("\r")
            try:
                ok, version = self._agentCmd("python %s; exit" % (agentRemoteFilename,))
            except IOError:
                raise TizenConnectionError('Connecting to a Tizen device/emulator with "sdb -s %s shell" failed.' % (self._serialNumber,))
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
        if self._sdbShell == None: return False, "disconnected"
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

    def sendMtLinearGesture(self, *args):
        return self._agentCmd("ml %s" % (base64.b64encode(cPickle.dumps(args))))[0]

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

    def setDisplayBacklightTime(self, timeout):
        """
        Set time the LCD backlight will be kept on.

        Parameters:

          timeout (integer):
                  inactivity time in seconds after which the backlight
                  will be switched off.
        """
        return self._agentCmd("bl %s" % (timeout,))[0]

    def recvScreenshot(self, filename, blankFrameRetry=3):
        if blankFrameRetry > 5:
            rv, img = self._agentCmd("ss")
        else:
            rv, img = self._agentCmd("ss R") # resetXConnection
        if rv == False:
            return False
        try:
            header, data = zlib.decompress(img).split('\n',1)
            width, height, depth, bpp = [int(n) for n in header.split()[1:]]
        except Exception, e:
            raise TizenConnectionError("Corrupted screenshot data: %s" % (e,))
        if len(data) != width * height * 4:
            raise FMBTTizenError("Image data size mismatch.")

        if fmbtgti.eye4graphics.bgrx2rgb(data, width, height) == 0 and blankFrameRetry > 0:
            time.sleep(0.5)
            return self.recvScreenshot(filename, blankFrameRetry - 1)

        # TODO: use libimagemagick directly to save data to png?
        ppm_header = "P6\n%d %d\n%d\n" % (width, height, 255)
        f = file(filename + ".ppm", "w").write(ppm_header + data[:width*height*3])
        _run(["convert", filename + ".ppm", filename], expectedExitStatus=0)
        os.remove("%s.ppm" % (filename,))
        return True

    def recvSerialNumber(self):
        s, o = commands.getstatusoutput("sdb get-serialno")
        return o.splitlines()[-1]

    def shellSOE(self, shellCommand, username, password, asyncStatus, asyncOut, asyncError):
        _, (s, o, e) = self._agentCmd("es %s" % (base64.b64encode(cPickle.dumps(
                        (shellCommand, username, password, asyncStatus, asyncOut, asyncError))),))
        return s, o, e

    def target(self):
        return self._serialNumber

# _tizenAgent code is executed on Tizen device through sdb shell.
_tizenAgent = """
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

libc           = ctypes.CDLL("libc.so.6")
libX11         = ctypes.CDLL("libX11.so.6")
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
else:
    # Running on Blackbay
    hwKeyDevice = {
        "POWER": "msic_power_btn",
        "VOLUMEUP": "gpio-keys",
        "VOLUMEDOWN": "gpio-keys",
        "HOME": "mxt224_key_0"
        }
    if iAmRoot:
        mtInputDevFd = os.open("/dev/input/event0", os.O_WRONLY | os.O_NONBLOCK)

# Read input devices
deviceToEventFile = {}
for _l in file("/proc/bus/input/devices"):
    if _l.startswith('N: Name="'): _device = _l.split('"')[1]
    elif _l.startswith("H: Handlers=") and "event" in _l:
        try: deviceToEventFile[_device] = "/dev/input/" + re.findall("(event[0-9]+)", _l)[0]
        except Exception, e: pass

# Connect to X server, get root window size for screenshots
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

def specialCharToXString(c):
    c2s = {'\\n': "Return",
           ' ': "space", '!': "exclam", '"': "quotedbl",
           '#': "numbersign", '$': "dollar", '%': "percent",
           '&': "ambersand", "'": "apostrophe",
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
    rawfmbt_header = "FMBTRAWX11 %d %d %d %d\\n" % (
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
        statusFile.write(str(p.wait()) + "\\n")
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
        p.stdin.write(password + "\\r")
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
    p.stdin.write(cmd + "\\r")
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
                file("/tmp/debug-root","w").write(cmd[3:]+"\\n")
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
"""

class FMBTTizenError(Exception): pass
class TizenConnectionError(FMBTTizenError): pass
class TizenDeviceNotFoundError(TizenConnectionError): pass
