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
shutter -s -e -o lock.png


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
import shlex
import subprocess
import os
import Queue
import sys
import thread
import time
import zlib
import inspect

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
    def __init__(self, serialNumber=None, loginCommand=None, debugAgentFile=None, **kwargs):
        """Parameters:

          serialNumber (string, optional)
                  the serial number of the device to be connected.
                  The default is the first device in "sdb devices"
                  list.

          loginCommand (string, optional)
                  Shell command for establishing SSH connection to the
                  device. Example:

                  loginCommand = "/usr/bin/ssh tizen@192.168.99.20"

                  If loginCommand is given, sdb will not be used.

          debugAgentFile (file-like object, optional)
                  record communication with the fMBT Tizen agent to
                  given file. The default is None: communication is
                  not recorded.

          rotateScreenshot (integer, optional)
                  rotate new screenshots by rotateScreenshot degrees.
                  Example: rotateScreenshot=-90. The default is 0 (no
                  rotation).
        """
        fmbtgti.GUITestInterface.__init__(self, **kwargs)
        c = TizenDeviceConnection(serialNumber=serialNumber,
                                  loginCommand=loginCommand,
                                  debugAgentFile=debugAgentFile)
        self.setConnection(c)
        if "rotateScreenshot" in kwargs:
            c.sendScreenshotRotation(kwargs["rotateScreenshot"])
        c._gti = self
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

    def displayStatus(self):
        """
        Returns status of device display, "On" or "Off".
        """
        return self._conn.recvDisplayStatus()

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

        return self._conn.sendMtLinearGesture(
            [[(finger1startX, finger1startY), (finger1endX, finger1endY)],
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
        return self._conn.sendDisplayBacklightTime(timeout)

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
    def __init__(self, serialNumber=None, loginCommand=None, debugAgentFile=None):
        if loginCommand == None:
            if serialNumber == None:
                self._serialNumber = self.recvSerialNumber()
            else:
                self._serialNumber = serialNumber
            self._loginCommand = None
        else:
            if serialNumber == None:
                self._serialNumber = "unknown"
            else:
                self._serialNumber = serialNumber
            if isinstance(loginCommand, str):
                self._loginCommand = shlex.split(loginCommand)
            else:
                self._loginCommand = loginCommand
        self._useSdb = (self._loginCommand == None)
        self._useSsh = not self._useSdb
        self._sdbShell = None
        self._debugAgentFile = debugAgentFile
        self._agentNeedsResolution = True
        self.open()

    def __del__(self):
        self.close()

    def open(self):
        if self._serialNumber == "unknown" and self._useSdb:
            raise TizenDeviceNotFoundError("Tizen device not found.")

        self.close()

        agentFilename = os.path.join(
            os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))),
            "fmbttizen-agent.py")
        remoteUploadPath = "/tmp"
        agentRemoteFilename = remoteUploadPath + "/fmbttizen-agent.py"
        uploadFiles = [(agentFilename,
                        agentRemoteFilename),
                       (os.path.join(os.path.dirname(agentFilename),
                                     "fmbtuinput.py"),
                        remoteUploadPath + "/fmbtuinput.py")]

        # Upload fmbttizen-agent to the device
        if self._useSdb:
            for src, dst in uploadFiles:
                uploadCmd = ["sdb", "-s", self._serialNumber, "push", src, dst]
                status, out, err = _run(uploadCmd, range(256))
                if status == 127:
                    raise TizenConnectionError('Executing "sdb -s %s push" failed. Check your Tizen SDK installation.' % (self._serialNumber,))
                elif status != 0:
                    if "device not found" in err:
                        raise TizenDeviceNotFoundError('Tizen device "%s" not found.' % (self._serialNumber,))
                    else:
                        raise TizenConnectionError('Executing "%s" failed: %s' % (' '.join(uploadCmd), err + " " + out))
        else: # using SSH
            for src, dst in uploadFiles:
                uploadCmd = self._loginCommand + ["cat", ">", dst]
                p = subprocess.Popen(uploadCmd, shell=False, stdin=subprocess.PIPE)
                p.stdin.write(file(src).read())
                p.stdin.close()
                p.wait()

        # Launch agent, create persistent connection to it
        if self._useSdb:
            remoteShellCmd = ["sdb", "-s", self._serialNumber, "shell"]
        else: # using SSH
            remoteShellCmd = self._loginCommand + ["python", agentRemoteFilename]

        try:
            self._sdbShell = subprocess.Popen(remoteShellCmd,
                                              shell=False,
                                              stdin=subprocess.PIPE,
                                              stdout=subprocess.PIPE,
                                              stderr=subprocess.PIPE,
                                              close_fds=True)
        except OSError, msg:
            raise TizenConnectionError('Executing "%s" failed.' % (
                " ".join(remoteShellCmd),))

        _g_sdbProcesses.add(self._sdbShell)
        self._sdbShellErrQueue = Queue.Queue()
        thread.start_new_thread(_fileToQueue, (self._sdbShell.stderr, self._sdbShellErrQueue))

        if self._useSdb:
            self._sdbShell.stdin.write("\r")
            try:
                ok, version = self._agentCmd("python %s; exit" % (agentRemoteFilename,))
            except IOError:
                raise TizenConnectionError('Connecting to a Tizen device/emulator with "sdb -s %s shell" failed.' % (self._serialNumber,))
        else: # using SSH
            ok, version = self._agentCmd("")
            pass # agent already started by remoteShellCmd
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
        if command[:2] in ["tt", "td", "tm", "tu"]:
            # Operating on coordinates on with a touch devices
            # may require information on screen resolution.
            # The agent does not know about possible rotation, so
            # the resolution needs to be sent from here.
            if self._agentNeedsResolution:
                self._agentCmd("sd %s %s" % self._gti.screenSize())
                self._agentNeedsResolution = False
        if self._sdbShell == None: return False, "disconnected"
        if self._debugAgentFile: self._debugAgentFile.write(">0 %s\n" % (command,))
        if self._useSdb:
            eol = "\r"
        else:
            eol = "\n"
        try:
            if len(command) > 0:
                self._sdbShell.stdin.write("%s%s" % (command, eol))
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

    def sendScreenshotRotation(self, angle):
        return self._agentCmd("sa %s" % (angle,))[0]

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

    def sendDisplayBacklightTime(self, timeout):
        return self._agentCmd("bl %s" % (timeout,))[0]

    def recvDisplayStatus(self):
        status = self._agentCmd("gd")
        if status[0] == False:
            raise FMBTTizenError("Error reading display status '%s'" % (status[2],))
        return status[1]

    def recvScreenshot(self, filename, blankFrameRetry=3):
        if blankFrameRetry > 2:
            rv, img = self._agentCmd("ss")
        else:
            rv, img = self._agentCmd("ss R") # retry
        if rv == False:
            return False
        if img.startswith("FMBTRAWX11"):
            try:
                header, zdata = img.split('\n', 1)
                width, height, depth, bpp = [int(n) for n in header.split()[1:]]
                data = zlib.decompress(zdata)
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
        else:
            file(filename, "w").write(img)
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

class FMBTTizenError(Exception): pass
class TizenConnectionError(FMBTTizenError): pass
class TizenDeviceNotFoundError(TizenConnectionError): pass
