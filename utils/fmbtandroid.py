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
#
#
# View._parseDump method contains code that has been published as part
# of the TEMA tool, under the MIT open source license:
#
# Copyright (c) 2006-2010 Tampere University of Technology
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""
This library provides a test interface to Android devices.

Device class implements a test interface that is based on Android
Debug Bridge (adb) and Android monkey.

Device's refreshScreenshot() returns a Screenshot object, from which
bitmaps can be searched for.

Device's refreshView() returns a View object, from which UI elements
can be searched according to their id, class, text and other
properties.

Using this library requires that adb is in PATH.

Tips & tricks
-------------

Take a screenshot and save it to a file

import fmbtandroid
fmbtandroid.Device().refreshScreenshot().save("/tmp/screen.png")

* * *

Print view items on device display

import fmbtandroid
print fmbtandroid.Device().refreshView().dumpTree()

* * *

Save generated device ini for modifications

import fmbtandroid
file("/tmp/mydevice.ini", "w").write(fmbtandroid.Device().dumpIni())

* * *

Connect to device based on an ini file

import fmbtandroid
d = fmbtandroid.Device(iniFile=file("/tmp/mydevice.ini"))
d.pressHome()

* * *

Open screenlock by swiping lock.png bitmap on the display to the
east. The lock.png file needs to be in bitmapPath defined in
mydevice.ini.

import fmbtandroid
d = fmbtandroid.Device(iniFile=file("/tmp/mydevice.ini"))
d.refreshScreenshot()
d.swipeBitmap("lock.png", "east")

* * *

Execute a shell command on Android device, show exit status, standard
output and standard error:

import fmbtandroid
status, out, err = fmbtandroid.Device().shellSOE("mkdir /proc/foo")
print 'status: %s, stdout: "%s", stderr: "%s"' % (status, out, err)

* * *

Enable extensive logging with fmbtlogger. You can use functions or
file objects as backends. Example: log to standard output

import fmbtandroid
import fmbtlogger
import sys

d = fmbtandroid.Device()
d = fmbtlogger.text(d, sys.stdout, logDepth=-1)
d.pressPower()

"""

DEVICE_INI_DEFAULTS = '''
[objects]
appsButtonId = id/0x0
appsButtonClass = BubbleTextView

; [application.NAME] sections:
; gridname = exact caption of the application in application grid (text
;            property)
; window   = string included in topWindow() when application is running

[homescreen]
window = Launcher
'''

import commands
import datetime
import os
import random
import re
import shutil
import socket
import StringIO
import subprocess
import tempfile
import time
import uu

import eyenfinger
import fmbt

_OCRPREPROCESS = [
    '-sharpen 5 -level 60%%,60%%,1.0 -filter Mitchell %(zoom)s',
    '-sharpen 5 -level 90%%,100%%,3.0 -filter Mitchell -sharpen 5'
    ]

def _adapterLog(msg):
    fmbt.adapterlog("fmbtandroid: %s" % (msg,))

def _logFailedCommand(source, command, exitstatus, stdout, stderr):
    _adapterLog('in %s command "%s" failed:\n    output: %s\n    error: %s\n    status: %s' %
                (source, command, stdout, stderr, exitstatus))

def _fmbtLog(msg):
    fmbt.fmbtlog("fmbtandroid: %s" % (msg,))

def _filenameTimestamp():
    return datetime.datetime.now().strftime("%Y%m%d-%H%M%S-%f")

def _run(command, expectedExitStatus = None):
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

    if expectedExitStatus != None:
        if ((type(expectedExitStatus) in [list, tuple] and
             not exitStatus in expectedExitStatus) or
            (type(expectedExitStatus) == int and
             not exitStatus == expectedExitStatus)):
            msg = 'Unexpected exit status %s from command "%s".\n    Output: %s\n    Error: %s' % (
                exitStatus, command, out, err)
            _adapterLog(msg)
            raise Exception(msg)

    return (exitStatus, out, err)

class Device(object):
    """
    The Device class provides

    - keywords as its methods

    - device properties from device's INI file

    - view() returns the most recently refreshed View, that contains
      items parsed from window dump.

    - screenshot() returns the most recently refreshed Screenshot,
      bitmaps can be searched from this.
    """
    _PARSE_VIEW_RETRY_LIMIT = 10
    def __init__(self, deviceName=None, iniFile=None, connect=True):
        """
        Connect to given device, or the first not-connected Android
        device in the "adb devices" list, if nothing is defined.

        Parameters:

          deviceName (string, optional):
                  If deviceName is a device serial number (an item in
                  the left most column in "adb devices"), connect to
                  that device. Device information is read from
                  $FMBTANDROIDHOME/etc/SERIALNUMBER.ini, if it exists.

                  If deviceName is a nick name, device information is
                  looked for from $FMBTANDROIDHOME/etc/deviceName.ini,
                  and the connection is established to the device with
                  the serial number given in the ini file.

                  The default is None. The first disconnected device
                  in the "adb devices" list is connected to. Device
                  information is read from
                  $FMBTANDROIDHOME/etc/SERIALNUMBER.ini, if it exists.

          iniFile (file object, optional):
                  A file object that contains device information
                  ini. Connect to the device with a serial number
                  given in this file. The default is None.

        To create an ini file for a device, use dumpIni. Example:

        file("/tmp/test.ini", "w").write(fmbtandroid.Device().dumpIni())
        """
        self._fmbtAndroidHomeDir = os.getenv("FMBTANDROIDHOME", os.getcwd())

        self._screenSize = None
        self._platformVersion = None
        self._lastView = None
        self._lastScreenshot = None
        self._longPressHoldTime = 2.0
        self._longTapHoldTime = 2.0

        self._conf = _DeviceConf()

        self._loadDeviceAndTestINIs(self._fmbtAndroidHomeDir, deviceName, iniFile)
        if deviceName == None:
            deviceName = self._conf.value("general", "serial", None)

        if connect == False and deviceName == None:
            deviceName = "nodevice"
            self._conn = None
        elif deviceName == None:
            # Connect to an unspecified device.
            # Go through devices in "adb devices".
            listDevicesCommand = "adb devices"
            status, output, err = _run(listDevicesCommand, expectedExitStatus = [0, 127])
            if status == 127:
                raise Exception('adb not found in PATH. Check your Android SDK installation.')
            outputLines = [l.strip() for l in output.splitlines()]
            try: deviceLines = outputLines[outputLines.index("List of devices attached")+1:]
            except: deviceLines = []

            deviceLines = [l for l in deviceLines if l.strip() != ""]

            if deviceLines == []:
                raise Exception('No devices found with "%s"' % (listDevicesCommand,))

            potentialDevices = [line.split()[0] for line in deviceLines]

            for deviceName in potentialDevices:
                try:
                    self.serialNumber = deviceName
                    self._conf.set("general", "serial", self.serialNumber)
                    self._conn = _AndroidDeviceConnection(self.serialNumber)
                    break
                except AndroidConnectionError, e:
                    continue
            else:
                raise AndroidConnectionError("Could not connect to device(s): %s." % (
                        ", ".join(potentialDevices)))

            # Found a device (deviceName).
            self._loadDeviceAndTestINIs(self._fmbtAndroidHomeDir, deviceName, iniFile)
        else:
            # Device name given, find out the serial number to connect to.
            # It may be given in device or test run INI files.
            self.serialNumber = self._conf.value("general", "serial", deviceName)
            if connect:
                self._conn = _AndroidDeviceConnection(self.serialNumber)


        _deviceIniFilename = self._fmbtAndroidHomeDir + os.sep + "etc" + os.sep + deviceName + ".ini"
        self.loadConfig(_deviceIniFilename, override=True, level="device")

        # Fetch  properties from device configuration
        self.nickName        = self._conf.value("general", "name", deviceName)
        self.phoneNumber     = self._conf.value("general", "phonenumber")


        # Loading platform-specific configuration requires a
        # connection to the device for checking the platform version.
        _platformIniFilename = self._fmbtAndroidHomeDir + os.sep + "etc" + os.sep + "android" + self.platformVersion() + ".ini"

        # would we need a form-factor ini, too?
        self.loadConfig(_platformIniFilename, override=False, level="platform")
        self.loadConfig(StringIO.StringIO(DEVICE_INI_DEFAULTS), override=False, level="global default")

        self.wlanAP          = self._conf.value("environment", "wlanAP")
        self.wlanPass        = self._conf.value("environment", "wlanPass")
        self.btName          = self._conf.value("environment", "BTName")
        self.btAccessory     = self._conf.value("environment", "BTAccessory")
        self.serverIP        = self._conf.value("environment", "ServerIP")
        self.androidUser     = self._conf.value("environment", "AndroidUser")
        self.voiceMailNumber = self._conf.value("environment", "VoiceMailNumber")

        if self._conn: hw = self._conn._monkeyCommand("getvar build.device")[1]
        else: hw = "nohardware"
        self.hardware        = self._conf.value("general", "hardware", hw)
        self.bitmapPath       = self._conf.value("paths", "bitmapPath", self._fmbtAndroidHomeDir + os.sep + "bitmaps" + os.sep + self.hardware + "-" + self.platformVersion() + ":.")
        self.screenshotDir  = self._conf.value("paths", "screenshotDir", self._fmbtAndroidHomeDir + os.sep + "screenshots")
        if not os.path.isdir(self.screenshotDir):
            try:
                os.makedirs(self.screenshotDir)
                _adapterLog('created directory "%s" for screenshots' % (self.screenshotDir,))
            except Exception, e:
                _adapterLog('creating directory "%s" for screenshots failed: %s' (self.screenshotDir, e))
                raise

        # Caches
        self._itemCache = {}

    def callContact(self, contact):
        """
        Call to given contact.

        Return True if successful, otherwise False.
        """
        callCommand = 'service call phone 1 s16 "%s"' % (contact,)
        status, out, err = self.shellSOE(callCommand)
        if status != 0: # TODO: check out/err, too?
            _logFailedCommand("callContact", callCommand, status, out, err)
            return False
        else:
            return True

    def callNumber(self, number):
        """
        Call to given phone number.

        Return True if successful, otherwise False.
        """
        callCommand = "service call phone 2 s16 %s" % (number,)
        status, out, err = self.shellSOE(callCommand)
        if status != 0: # TODO: check out/err, too?
            _logFailedCommand("callNumber", callCommand, status, out, err)
            return False
        else:
            return True

    def close(self):
        if hasattr(self, "_conn"):
            del self._conn
            del self._lastView
            import gc
            gc.collect()

    def dumpIni(self):
        """
        Returns contents of current device configuration as a string (in
        INI format).
        """
        return self._conf.dump()

    def drag(self, (x1, y1), (x2, y2), delayBetweenMoves=0.01, delayBeforeMoves=0, delayAfterMoves=0, movePoints=20):
        """
        Touch the screen on coordinates (x1, y1), drag along straight
        line to coordinates (x2, y2), and raise fingertip.

        coordinates (floats in range [0.0, 1.0] or integers):
                floating point coordinates in range [0.0, 1.0] are
                scaled to full screen width and height, others are
                handled as absolute coordinate values.

        delayBeforeMoves (float, optional):
                seconds to wait after touching and before dragging.

        delayBetweenMoves (float, optional):
                seconds to wait when moving between points when
                dragging.

        delayAfterMoves (float, optional):
                seconds to wait after dragging, before raising
                fingertip.

        movePoints (integer, optional):
                the number of intermediate move points between end
                points of the line.

        Returns True on success, False if sending input failed.
        """
        x1, y1 = self.intCoords((x1, y1))
        x2, y2 = self.intCoords((x2, y2))
        if not self._conn.sendTouchDown(x1, y1): return False
        time.sleep(delayBeforeMoves)
        for i in xrange(0, movePoints):
            nx = x1 + int(round(((x2 - x1) / float(movePoints+1)) * (i+1)))
            ny = y1 + int(round(((y2 - y1) / float(movePoints+1)) * (i+1)))
            if not self._conn.sendTouchMove(nx, ny): return False
            if i < movePoints - 1: time.sleep(delayBetweenMoves)
        time.sleep(delayAfterMoves)
        if self._conn.sendTouchUp(x2, y2): return True
        return False

    def intCoords(self, (x, y)):
        """
        Convert floating point coordinate values in range [0.0, 1.0] to
        screen coordinates.
        """
        width, height = self.screenSize()
        if 0 <= x <= 1 and type(x) == float: x = x * width
        if 0 <= y <= 1 and type(y) == float: y = y * height
        return (int(round(x)), int(round(y)))

    def loadConfig(self, filenameOrObj, override=True, level=""):
        try:
            if type(filenameOrObj) == str:
                filename = filenameOrObj
                fileObj = file(filenameOrObj)
            else:
                fileObj = filenameOrObj
                filename = getattr(fileObj, "name", "<string>")
                if hasattr(fileObj, "seek"):
                    fileObj.seek(0)
            self._conf.addFile(fileObj, override=override)
        except Exception, e:
            _adapterLog('Loading %s configuration from "%s" failed: %s' % (level, filename, e))
            return
        _adapterLog('Loaded %s configuration from "%s"' % (level, filename))

    def platformVersion(self):
        """
        Returns the platform version of the device.
        """
        if self._platformVersion == None:
            if self._conn:
                self._platformVersion = self._conn.recvVariable("build.version.release")
            else:
                self._platformVersion = "nosoftware"
        return self._platformVersion

    def pressBack(self, **pressKeyKwArgs):
        """
        Press the back button.

        Optional parameters are the same as for pressKey.
        """
        return self.pressKey("KEYCODE_BACK", **pressKeyKwArgs)

    def pressHome(self, **pressKeyKwArgs):
        """
        Press the home button.

        Optional parameters are the same as for pressKey.
        """
        return self.pressKey("KEYCODE_HOME", **pressKeyKwArgs)

    def pressKey(self, keyName, long=False, hold=0.0):
        """
        Press a key on the device.

        Parameters:

          keyName (string):
                  the name of the key, like KEYCODE_HOME. If KEYCODE_
                  prefix is not given, it is added. Refer to Android
                  KeyEvent documentation.

          long (boolean, optional):
                  if True, press the key for long time.

          hold (float, optional):
                  time in seconds to hold the key down.
        """
        if not keyName.upper().startswith("KEYCODE_"):
            keyName = "KEYCODE_" + keyName
        keyName = keyName.upper()
        if long and hold == None:
            hold = self._longPressHoldTime
        if hold > 0.0:
            try:
                assert self._conn.sendKeyDown(keyName)
                time.sleep(hold)
                assert self._conn.sendKeyUp(keyName)
            except:
                return False
            return True
        return self._conn.sendPress(keyName)

    def pressMenu(self, **pressKeyKwArgs):
        """
        Press the menu button.

        Optional parameters are the same as for pressKey.
        """
        return self.pressKey("KEYCODE_MENU", **pressKeyKwArgs)

    def pressPower(self, **pressKeyKwArgs):
        """
        Press the power button.

        Optional parameters are the same as for pressKey.
        """
        return self.pressKey("KEYCODE_POWER", **pressKeyKwArgs)

    def pressVolumeUp(self, **pressKeyKwArgs):
        """
        Press the volume up button.

        Optional parameters are the same as for pressKey.
        """
        return self.pressKey("KEYCODE_VOLUME_UP", **pressKeyKwArgs)

    def pressVolumeDown(self, **pressKeyKwArgs):
        """
        Press the volume down button.

        Optional parameters are the same as for pressKey.
        """
        return self.pressKey("KEYCODE_VOLUME_DOWN", **pressKeyKwArgs)

    def reboot(self, reconnect=True, firstBoot=False):
        """
        Reboot the device.

        Parameters

          reconnect (boolean, optional)
                  If True, do not return until the device has been
                  connected after boot. Otherwise return once reboot
                  command has been sent. The default is True.

          firstBoot (boolean, optional)
                  If True, the device boots like it would have been
                  flashed. Requires that "adb root" works. The default
                  is False.

        Returns True on success, otherwise False.
        """
        return self._conn.reboot(reconnect, firstBoot, 120)

    def reconnect(self):
        """
        Close connections to the device and reconnect.
        """
        del self._conn
        try:
            self._conn = _AndroidDeviceConnection(self.serialNumber)
            return True
        except Exception, e:
            _adapterLog("reconnect failed: %s" % (e,))
            return False

    def refreshScreenshot(self, forcedScreenshot=None):
        """
        Takes new screenshot from the device and updates latest
        screenshot object.

        Parameters:

          forcedScreenshot (Screenshot or string, optional):
                  use given screenshot or image file, do not take new
                  screenshot.

        Returns created Screenshot object.
        """
        if forcedScreenshot != None:
            if type(forcedScreenshot) == str:
                self._lastScreenshot = Screenshot(
                    None, screenshotDir=forcedScreenshot,
                    pathSolver=self._bitmapFilename, screenSize=self.screenSize())
            else:
                self._lastScreenshot = forcedScreenshot
        else:
            self._lastScreenshot = Screenshot(
                self._conn, screenshotDir=self.screenshotDir,
                pathSolver=self._bitmapFilename, screenSize=self.screenSize())
        return self._lastScreenshot

    def refreshView(self):
        """
        (Re)reads view items on display and updates the latest View
        object.

        Returns created View object.
        """
        retryCount = 0
        while True:
            dump = self._conn.recvViewData()
            if dump == None: # dump unreadable
                return None
            view = View(self.screenshotDir, self.serialNumber, dump)
            if len(view.errors()) > 0 and retryCount < self._PARSE_VIEW_RETRY_LIMIT:
                _adapterLog("refreshView parse errors:\n    %s" % ("\n    ".join(view.errors(),)))
                retryCount += 1
                time.sleep(0.2) # sleep before retry
            else:
                # successfully parsed or parsed with errors but no more retries
                self._lastView = view
                return view

    def screenshot(self):
        """
        Returns the latest Screenshot object.

        Use refreshScreenshot() to get a new screenshot.
        """
        return self._lastScreenshot

    def screenSize(self):
        """
        Returns screen size in pixels in tuple (width, height).
        """
        if self._screenSize == None:
            self._screenSize = self._conn.recvScreenSize()
        return self._screenSize

    def shell(self, shellCommand):
        """
        Execute shellCommand in adb shell.

        shellCommand is a string (arguments separated by whitespace).

        Returns output of "adb shell" command.

        If you wish to receive exitstatus or standard output and error
        separated from shellCommand, refer to shellSOE().
        """
        return self._conn._runAdb(["shell", shellCommand])[1]

    def shellSOE(self, shellCommand):
        """
        Execute shellCommand in adb shell.

        shellCommand is a string (arguments separated by whitespace).

        Returns tuple (exitStatus, standardOutput, standardError).

        Requires tar and uuencode to be available on the device.
        """
        return self._conn.shellSOE(shellCommand)

    def smsNumber(self, number, message):
        """
        Send message using SMS to given number.

        Returns True on success, otherwise False.
        """
        smsCommand = ('am start -a android.intent.action.SENDTO ' +
                      '-d sms:%s --es sms_body "%s"' +
                      '--ez exit_on_sent true')  % (number, message)
        status, out, err = self.shellSOE(smsCommand)
        if status != 0:
            _logFailedCommand("sms", smsCommand, status, out, err)
            return False
        _adapterLog("SMS command returned %s" % (out + err,))
        time.sleep(1)
        self.pressKey("KEYCODE_DPAD_RIGHT")
        time.sleep(1)
        self.pressKey("KEYCODE_ENTER")
        return True

    def swipe(self, (x, y), direction, **dragKwArgs):
        """
        swipe starting from coordinates (x, y) to direction ("n", "s",
        "e" or "w"). Swipe ends to the edge of the screen.

        Coordinates and keyword arguments are the same as for the drag
        function.

        Returns True on success, False if sending input failed.
        """
        d = direction.lower()
        if d in ["n", "north"]: x2, y2 = self.intCoords((x, 0.0))
        elif d in ["s", "south"]: x2, y2 = self.intCoords((x, 1.0))
        elif d in ["e", "east"]: x2, y2 = self.intCoords((1.0, y))
        elif d in ["w", "west"]: x2, y2 = self.intCoords((0.0, y))
        else:
            msg = 'Illegal direction "%s"' % (direction,)
            _adapterLog(msg)
            raise Exception(msg)
        return self.drag((x, y), (x2, y2), **dragKwArgs)

    def swipeBitmap(self, bitmap, direction, colorMatch=1.0, area=(0.0, 0.0, 1.0, 1.0), **dragKwArgs):
        """
        swipe starting from bitmap to direction ("n", "s", "e", or
        "w"). Swipe ends to the edge of the screen.

        Parameters:

          colorMatch, area
                  refer to verifyBitmap documentation.

          delayBeforeMoves, delayBetweenMoves, delayAfterMoves,
          movePoints
                  refer to drag documentation.

        Returns True on success, False if sending input failed.
        """
        assert self._lastScreenshot != None, "Screenshot required."
        items = self._lastScreenshot.findItemsByBitmap(bitmap, colorMatch=colorMatch, area=area)
        if len(items) == 0:
            _adapterLog("swipeBitmap: bitmap %s not found from %s" % (bitmap, self._lastScreenshot.filename()))
            return False
        return self.swipeItem(items[0], direction, **dragKwArgs)

    def swipeItem(self, viewItem, direction, **dragKwArgs):
        """
        swipe starting from viewItem to direction ("n", "s", "e" or
        "w"). Swipe ends to the edge of the screen.

        Keyword arguments are the same as for the drag function.

        Returns True on success, False if sending input failed.
        """
        return self.swipe(viewItem.coords(), direction, **dragKwArgs)

    def systemProperty(self, propertyName):
        """
        Returns Android Monkey Device properties, such as
        "clock.uptime", refer to Android Monkey documentation.
        """
        return self._conn.recvVariable(propertyName)

    def tap(self, (x, y), long=False, hold=0.0):
        """
        Tap screen on coordinates (x, y).

        Parameters:

          coordinates (floats in range [0.0, 1.0] or integers):
                  floating point coordinates in range [0.0, 1.0] are
                  scaled to full screen width and height, others are
                  handled as absolute coordinate values.

          long (boolean, optional):
                  if True, touch the screen for a long time.

          hold (float, optional):
                  time in seconds to touch the screen.

        Returns True if successful, otherwise False.
        """
        x, y = self.intCoords((x, y))
        if long and hold == None:
            hold = self._longTapHoldTime
        if hold > 0.0:
            try:
                assert self._conn.sendTouchDown(x, y)
                time.sleep(hold)
                assert self._conn.sendTouchUp(x, y)
            except:
                return False
            return True
        else:
            return self._conn.sendTap(x, y)

    def tapBitmap(self, bitmap, **tapKwArgs):
        """
        Find a bitmap from the latest screenshot, and tap it.
        """
        assert self._lastScreenshot != None, "Screenshot required."
        items = self._lastScreenshot.findItemsByBitmap(bitmap)
        if len(items) == 0:
            _adapterLog("tapBitmap: bitmap %s not found from %s" % (bitmap, self._lastScreenshot.filename()))
            return False
        return self.tapItem(items[0], **tapKwArgs)

    def tapId(self, viewItemId, **tapKwArgs):
        """
        Find an item with given id from the latest view, and tap it.
        """
        assert self._lastView != None, "View required."
        items = self._lastView.findItemsById(viewItemId, count=1)
        if len(items) > 0:
            return self.tapItem(items[0], **tapKwArgs)
        else:
            _adapterLog("tapItemById(%s): no items found" % (viewItemId,))
            return False

    def tapItem(self, viewItem, **tapKwArgs):
        """
        Tap the center point of viewItem.
        """
        return self.tap(viewItem.coords(), **tapKwArgs)

    def tapOcrText(self, word, match=1.0, preprocess=None, **tapKwArgs):
        """
        Find the given word from the latest screenshot using OCR, and
        tap it.

        Parameters:

          word (string):
                  the word to be tapped.

          match (float, optional):
                  minimum match score in range [0.0, 1.0].
                  The default is 1.0 (exact match).

          preprocess (string, optional):
                  preprocess filter to be used in OCR for better
                  result. Refer to eyenfinger.autoconfigure to search
                  for a good one.

          long, hold (optional):
                  refer to tap documentation.

          Returns True if successful, otherwise False.
        """
        assert self._lastScreenshot != None, "Screenshot required."
        items = self._lastScreenshot.findItemsByOcr(word, match=match, preprocess=preprocess)
        if len(items) == 0: return False
        return self.tapItem(items[0], **tapKwArgs)

    def tapText(self, text, partial=False, **tapKwArgs):
        """
        Find an item with given text from the latest view, and tap it.

        Parameters:

          partial (boolean, optional):
                  refer to verifyText documentation. The default is
                  False.

          long, hold (optional):
                  refer to tap documentation.

        Returns True if successful, otherwise False.
        """
        assert self._lastView != None, "View required."
        items = self._lastView.findItemsByText(text, partial=partial, count=1)
        if len(items) == 0: return False
        return self.tapItem(items[0], **tapKwArgs)

    def topApp(self):
        """
        Returns the name of the top application.
        """
        return self._conn.recvTopAppWindow()[0]

    def topWindow(self):
        """
        Returns the name of the top window.
        """
        return self._conn.recvTopAppWindow()[1]

    def type(self, text):
        return self._conn.sendType(text)

    def verifyOcrText(self, word, match=1.0, preprocess=None):
        """
        Verify using OCR that the last screenshot contains the given word.

        Parameters:

          word (string):
                  the word to be searched for.

          match (float, optional):
                  minimum match score in range [0.0, 1.0].
                  The default is 1.0 (exact match).

          preprocess (string, optional):
                  preprocess filter to be used in OCR for better
                  result. Refer to eyenfinger.autoconfigure to search
                  for a good one.

          long, hold (optional):
                  refer to tap documentation.

          Returns True if successful, otherwise False.
        """
        assert self._lastScreenshot != None, "Screenshot required."
        return self._lastScreenshot.findItemsByOcr(word, match=match, preprocess=preprocess) != []

    def verifyText(self, text, partial=False):
        """
        Verify that the last view has at least one item with given
        text.

        Parameters:

          text (string):
                  text to be searched for in items.

          partial (boolean, optional):
                  if True, match items if item text contains given
                  text, otherwise match only if item text is equal to
                  the given text. The default is False (exact match).
        """
        assert self._lastView != None, "View required."
        return self._lastView.findItemsByText(text, partial=partial, count=1) != []

    def verifyBitmap(self, bitmap, colorMatch=1.0, area=(0.0, 0.0, 1.0, 1.0)):
        """
        Verify that bitmap is present in the last screenshot.

        Parameters:

          bitmap (string):
                  filename of the bitmap file to be searched for.

          colorMatch (float, optional):
                  required color matching accuracy. The default is 1.0
                  (exact match). For instance, 0.75 requires that
                  every pixel's every RGB component value on the
                  bitmap is at least 75 % match with the value of
                  corresponding pixel's RGB component in the
                  screenshot.

          area ((left, top, right, bottom), optional):
                  search bitmap from the given area only. Left, top
                  right and bottom are either absolute coordinates
                  (integers) or floats in range [0.0, 1.0]. In the
                  latter case they are scaled to screenshot
                  dimensions. The default is (0.0, 0.0, 1.0, 1.0),
                  that is, search everywhere in the screenshot.
        """
        assert self._lastScreenshot != None, "Screenshot required."
        if self._lastScreenshot == None:
            return False
        return self._lastScreenshot.findItemsByBitmap(bitmap, colorMatch=colorMatch, area=area) != []

    def view(self):
        """
        Returns the last view (the most recently refreshed view).
        """
        return self._lastView

    def wait(self, refreshFunc, waitFunc, waitFuncArgs, waitFuncKwargs={}, waitTime = 5.0, pollDelay = 1.0):
        """
        Wait until waitFunc returns True or waitTime has expired.

        Parameters:

          refreshFunc (function):
                  this function is called before re-evaluating
                  waitFunc. For instance, refreshView or
                  refreshScreenshot.

          waitFunc, waitFuncArgs, waitFuncKwargs (function, tuple,
          dictionary):
                  wait for waitFunc(waitFuncArgs, waitFuncKwargs) to
                  return True

          waitTime (float, optional):
                  max. time in seconds to wait for.

          pollDelay (float, optional):
                  time in seconds to sleep between refreshs.

        Returns True if waitFunc returns True - either immediately or
        before waitTime has expired - otherwise False.
        """
        if waitFunc(*waitFuncArgs, **waitFuncKwargs):
            return True
        startTime = time.time()
        endTime = startTime + waitTime
        now = startTime
        while now < endTime:
            time.sleep(min(pollDelay, (endTime - now)))
            now = time.time()
            refreshFunc()
            if waitFunc(*waitFuncArgs, **waitFuncKwargs):
                return True
        return False

    def waitBitmap(self, bitmap, colorMatch=None, area=None, **waitKwArgs):
        """
        Wait until bitmap appears on screen.

        Parameters:

          bitmap (string):
                  filename of the bitmap to be waited for.

          colorMatch, area (optional):
                  refer to verifyBitmap documentation.

          waitTime, pollDelay (float, optional):
                  refer to wait documentation.

        Returns True if bitmap appeared within given time limit,
        otherwise False.

        Updates the last screenshot.
        """
        verifyBitmapKwArgs = {}
        if colorMatch != None: verifyBitmapKwArgs['colorMatch'] = colorMatch
        if area != None: verifyBitmapKwArgs['area'] = area
        return self.wait(self.refreshScreenshot,
                         self.verifyBitmap, (bitmap,), verifyBitmapKwArgs,
                         **waitKwArgs)

    def waitText(self, text, partial=False, **waitKwArgs):
        """
        Wait until text appears in any view item.

        Parameters:

          text (string):
                text to be waited for.

          partial (boolean, optional):
                refer to verifyText. The default is False.

          waitTime, pollDelay (float, optional):
                refer to wait.

        Returns True if text appeared within given time limit,
        otherwise False.

        Updates the last view.
        """
        return self.wait(self.refreshView,
                         self.verifyText, (text,), {'partial': partial},
                         **waitKwArgs)

    def _bitmapFilename(self, bitmap, checkReadable=True):
        if bitmap.startswith("/") or os.access(bitmap, os.R_OK):
            path = [os.path.dirname(bitmap)]
            bitmap = os.path.basename(bitmap)
        else:
            path = []

            for singleDir in self.bitmapPath.split(":"):
                if not singleDir.startswith("/"):
                    path.append(os.path.join(self._fmbtAndroidHomeDir, singleDir))
                else:
                    path.append(singleDir)

        for singleDir in path:
            retval = os.path.join(singleDir, bitmap)
            if not checkReadable or os.access(retval, os.R_OK):
                break

        if checkReadable and not os.access(retval, os.R_OK):
            raise ValueError('Bitmap "%s" not readable in bitmapPath %s' % (bitmap, ':'.join(path)))
        return retval

    def _loadDeviceAndTestINIs(self, homeDir, deviceName, iniFile):
        if deviceName != None:
            _deviceIniFilename = homeDir + os.sep + "etc" + os.sep + deviceName + ".ini"
            self.loadConfig(_deviceIniFilename, override=True, level="device")
        if iniFile:
            self.loadConfig(iniFile, override=True, level="test")

class _DeviceConf:
    """
    Miniparser for INI files like:
    [section1]
    key1 = value1
    ; commented = out
    # commented = out
    """
    def __init__(self, fileObj=None):
        # _conf is a dictionary:
        # (section, key) -> value
        self._conf = {}
        if fileObj:
            self.addFile(fileObj)
    def addFile(self, fileObj, override=True):
        for line in fileObj:
            line = line.strip()
            if line.startswith('[') and line.endswith(']'):
                section = line[1:-1].strip()
            elif line.startswith(";") or line.startswith("#"):
                continue
            elif '=' in line:
                key, value = line.split('=')
                if override or (section, key.strip()) not in self._conf:
                    self._conf[(section, key.strip())] = value.strip()
    def sections(self):
        return list(set([k[0] for k in self._conf.keys()]))
    def keys(self, section):
        return [k[1] for k in self._conf.keys() if k[0] == section]
    def dump(self):
        lines = []
        for section in sorted(self.sections()):
            lines.append("[%s]" % (section,))
            for key in sorted(self.keys(section)):
                lines.append("%-16s = %s" % (key, self._conf[(section, key)]))
            lines.append("")
        return "\n".join(lines)
    def set(self, section, key, value):
        self._conf[(section, key)] = value
    def value(self, section, key, default=""):
        """
        Returns the value associated with the key in the section.
        The default is returned if the key is not found.
        dump() will dump also sections and keys with
        default values that have been returned.
        """
        if not (section, key) in self._conf:
            self._conf[(section, key)] = default
        return self._conf[(section, key)]

class Screenshot(object):
    """
    Screenshot class takes and holds a screenshot (bitmap) of device
    display, or a forced bitmap file if device connection is not given.
    """
    def __init__(self, deviceConn, screenshotDir=None, pathSolver=None, screenSize=None):
        if deviceConn:
            self._conn = deviceConn
            self._filename = self._conn.screenshot(screenshotDir=screenshotDir)
        else:
            self._conn = None
            self._filename = screenshotDir
        self._pathSolver = pathSolver
        self._screenSize = screenSize
        # The bitmap held inside screenshot object is never updated.
        # If new screenshot is taken, this screenshot object disappears.
        # => cache all search hits
        self._cache = {}
        self._ocrWords = None
        self._ocrPreprocess = _OCRPREPROCESS

    def dumpOcrWords(self, preprocess=None):
        self._assumeOcrWords(preprocess=preprocess)
        w = []
        for ppfilter in self._ocrWords:
            for word in self._ocrWords[ppfilter]:
                for appearance, (wid, middle, bbox) in enumerate(self._ocrWords[ppfilter][word]):
                    (x1, y1, x2, y2) = bbox
                    w.append((word, x1, y1))
        return sorted(set(w), key=lambda i:(i[2]/8, i[1]))

    def filename(self):
        return self._filename

    def findItemsByBitmap(self, bitmap, colorMatch=1.0, area=(0.0, 0.0, 1.0, 1.0)):
        bitmap = self._pathSolver(bitmap)
        if (bitmap, colorMatch) in self._cache:
            return self._cache[(bitmap, colorMatch)]
        eyenfinger.iRead(source=self._filename, ocr=False)
        try:
            score, bbox = eyenfinger.iVerifyIcon(bitmap, colorMatch=colorMatch, opacityLimit=.95, area=area)
            foundItem = self._item("bitmap", bbox, bitmap=bitmap)
            self._cache[(bitmap, colorMatch)] = [foundItem]
        except eyenfinger.BadMatch:
            _adapterLog('findItemsByBitmap no match for "%s" in "%s"' % (bitmap, self._filename))
            self._cache[(bitmap, colorMatch)] = []
        return self._cache[(bitmap, colorMatch)]

    def findItemsByOcr(self, text, preprocess=None, match=1.0):
        self._assumeOcrWords(preprocess=preprocess)
        for ppfilter in self._ocrWords.keys():
            try:
                eyenfinger._g_words = self._ocrWords[ppfilter]
                (score, word), bbox = eyenfinger.iVerifyWord(text, match=match)
                break
            except eyenfinger.BadMatch:
                continue
        else:
            return []
        return [self._item("OCR word", bbox, ocrFind=text, ocrFound=word)]

    def save(self, fileOrDirName):
        shutil.copy(self._filename, fileOrDirName)

    def _assumeOcrWords(self, preprocess=None):
        if self._ocrWords == None:
            if preprocess == None:
                preprocess = self._ocrPreprocess
            if not type(preprocess) in (list, tuple):
                preprocess = [preprocess]
            self._ocrWords = {}
            for ppfilter in preprocess:
                pp = ppfilter % { "zoom": "-resize %sx" % (self._screenSize[0] * 2) }
                eyenfinger.iRead(source=self._filename, ocr=True, preprocess=pp)
                self._ocrWords[ppfilter] = eyenfinger._g_words

    def _item(self, className, (x1, y1, x2, y2), bitmap=None, ocrFind=None, ocrFound=None):
        return ViewItem(
            className, None, 0,
            {"layout:mLeft": x1,
             "layout:mTop": y1,
             "layout:getHeight()": y2-y1,
             "layout:getWidth()": x2-x1,
             "screenshot": self._filename,
             "bitmap": bitmap,
             "ocrFind": ocrFind,
             "ocrFound": ocrFound,
             },
            None, "")

    def __str__(self):
        return 'Screenshot(filename="%s")' % (self._filename,)

class ViewItem(object):
    """
    ViewItem holds the information of a single GUI element.
    """
    def __init__(self, className, code, indent, properties, parent, rawProps):
        self._className = className
        self._code = code
        self._indent = indent
        self._p = properties
        self._parent = parent
        self._children = []
        self._bbox = []
        self._rawProps = ""
    def addChild(self,child): self._children.append(child)
    def bbox(self):
        if self._bbox == []:
            left = int(self._p["layout:mLeft"])
            top = int(self._p["layout:mTop"])
            parent = self._parent
            while parent:
                pp = parent._p
                left += int(pp["layout:mLeft"]) - int(pp["scrolling:mScrollX"])
                top += int(pp["layout:mTop"]) - int(pp["scrolling:mScrollY"])
                parent = parent._parent
            height = int(self._p["layout:getHeight()"])
            width = int(self._p["layout:getWidth()"])
            self._bbox = (left, top, left + width, top + height)
        return self._bbox
    def children(self):   return self._children
    def className(self):  return self._className
    def code(self):       return self._code
    def coords(self):
        left, top, right, bottom = self.bbox()
        return (left + (right-left)/2, top + (bottom-top)/2)
    def indent(self):     return self._indent
    def id(self):         return self.property("mID")
    def parent(self):     return self._parent
    def properties(self): return self._p
    def property(self, propertyName):
        return self._p.get(propertyName, None)
    def text(self):       return self.property("text:mText")
    def visible(self):
        return self._p.get("getVisibility()", "") == "VISIBLE"
    def dump(self):
        p = self._p
        return ("ViewItem(\n\tchildren = %d\n\tclassName = '%s'\n\tcode = '%s'\n\t" +
                "indent = %d\n\tproperties = {\n\t\t%s\n\t})") % (
            len(self._children), self._className, self._code, self._indent,
            '\n\t\t'.join(['"%s": %s' % (key, p[key]) for key in sorted(p.keys())]))
    def __str__(self):
        return ("ViewItem(className='%s', id=%s, bbox=%s)"  % (
                self._className, self.id(), self.bbox()))

class View(object):
    """
    View provides interface to screen dumps from Android. It parses
    the dump to a hierarchy of ViewItems. find* methods enable searching
    for ViewItems based on their properties.
    """
    def __init__(self, screenshotDir, serialNumber, dump):
        self.screenshotDir = screenshotDir
        self.serialNumber = serialNumber
        self._viewItems = []
        self._errors = []
        self._lineRegEx = re.compile("(?P<indent>\s*)(?P<class>[\w.$]+)@(?P<id>[0-9A-Fa-f]{8} )(?P<properties>.*)")
        self._olderAndroidLineRegEx = re.compile("(?P<indent>\s*)(?P<class>[\w.$]+)@(?P<id>\w)(?P<properties>.*)")
        self._propRegEx = re.compile("(?P<prop>(?P<name>[^=]+)=(?P<len>\d+),)(?P<data>[^\s]* ?)")
        self._dump = dump
        self._rawDumpFilename = self.screenshotDir + os.sep + _filenameTimestamp() + "-" + self.serialNumber + ".view"
        file(self._rawDumpFilename, "w").write(self._dump)
        self._parseDump(dump)

    def viewItems(self): return self._viewItems
    def errors(self): return self._errors
    def dumpRaw(self): return self._dump
    def dumpItems(self, itemList = None):
        if itemList == None: itemList = self._viewItems
        l = []
        for i in itemList:
            l.append(self._dumpItem(i))
        return '\n'.join(l)
    def dumpTree(self, rootItem = None):
        l = []
        if rootItem != None:
            l.extend(self._dumpSubTree(rootItem, 0))
        else:
            for i in self._viewItems:
                if i._indent == 0:
                    l.extend(self._dumpSubTree(i, 0))
        return '\n'.join(l)
    def _dumpSubTree(self, viewItem, indent):
        l = []
        i = viewItem
        l.append(" "*indent + self._dumpItem(viewItem))
        for i in viewItem.children():
            l.extend(self._dumpSubTree(i, indent + 4))
        return l
    def _dumpItem(self, viewItem):
            i = viewItem
            if i.text() != None: t = '"%s"' % (i.text(),)
            else: t = None
            return "id=%s cls=%s text=%s bbox=%s" % (
                i.id(), i.className(), t, i.bbox())

    def findItems(self, comparator, count=-1, searchRootItem=None, searchItems=None):
        foundItems = []
        if count == 0: return foundItems
        if searchRootItem != None:
            # find from searchRootItem and its children
            if comparator(searchRootItem):
                foundItems.append(i)
            for c in searchRootItem.children():
                foundItems.extend(self.findItems(comparator, count=count-len(foundItems), searchRootItem=c))
        else:
            if searchItems != None:
                # find from listed items only
                searchDomain = searchItems
            else:
                # find from all items
                searchDomain = self._viewItems
            for i in searchDomain:
                if comparator(i):
                    foundItems.append(i)
                    if count > 0 and len(foundItems) >= count:
                        break
        return foundItems

    def findItemsByText(self, text, partial=False, count=-1, searchRootItem=None, searchItems=None):
        """
        Searches the GUI hiearhy for a object with a given text
        """
        if partial:
            c = lambda item: (
                item.properties().get("text:mText", "").find(text) != -1 )
        else:
            c = lambda item: (
                item.properties().get("text:mText", None) == text )
        return self.findItems(c, count=count, searchRootItem=searchRootItem, searchItems=searchItems)

    def findItemsById(self, id, count=-1, searchRootItem=None, searchItems=None):
        c = lambda item: item.properties().get("mID", "") == id
        return self.findItems(c, count=count, searchRootItem=searchRootItem, searchItems=searchItems)

    def findItemsByClass(self, className, partial=True, count=-1, searchRootItem=None, searchItems=None):
        if partial: c = lambda item: item.className().find(className) != -1
        else: c = lambda item: item.className() == className
        return self.findItems(c, count=count, searchRootItem=searchRootItem, searchItems=searchItems)

    def findItemsByIdAndClass(self, id, className, partial=True, count=-1, searchRootItem=None, searchItems=None):
        idOk = self.findItemsById(id, count=-1, searchRootItem=searchRootItem)
        return self.findItemsByClass(className, partial=partial, count=count, searchItems=idOk)

    def findItemsByRawProps(self, s, count=-1, searchRootItem=None, searchItems=None):
        c = lambda item: item._rawProps.find(s) != -1
        return self.findItems(c, count=count, searchRootItem=searchRootItem, searchItems=searchItems)

    def _parseDump(self, dump):
        """
        Process the raw dump data and create a tree of ViewItems
        """
        # This code originates from tema-android-adapter-3.2,
        # AndroidAdapter/guireader.py.
        self._viewItems = []
        cellLayout = ""

        parent = None
        previousItem = None
        currentIndent = 0
        visible = True
        self.TOP_PAGED_VIEW = ""

        for lineIndex, line in enumerate(dump.splitlines()):
            if line == "DONE.":
                break

            # separate indent, class and properties for each GUI object
            # TODO: branch here according to self._androidVersion
            matcher = self._lineRegEx.match(line)

            if not matcher:
                # FIXME: this hack falls back to old format,
                # should branch according to self._androidVersion!
                matcher = self._olderAndroidLineRegEx.match(line)
                if not matcher:
                    self._errors.append((lineIndex + 1, line, "Illegal line"))
                    continue # skip this line

            className = matcher.group("class")

            # Indent specifies the hierarchy level of the object
            indent = len(matcher.group("indent"))

            # If the indent is bigger that previous, this object is a
            # child for the previous object
            if indent > currentIndent:
                parent = self._viewItems[-1]

            elif indent < currentIndent:
                for tmp in range(0, currentIndent - indent):
                    parent = parent.parent()

            currentIndent = indent

            propertiesData = matcher.group("properties")
            properties = {}
            index = 0

            x = 0
            y = 0

            # Process the properties of each GUI object
            while index < len(propertiesData):
                # Separate name and value for each property [^=]*=
                propMatch = self._propRegEx.match(propertiesData[index:-1])
                if not propMatch or len(propMatch.group("data")) < int(propMatch.group("len")):
                    if not propMatch.group("data"):
                        self._errors.append((lineIndex, propertiesData[index:-1], "Illegal property"))
                        return None
                    startFrom = index + propertiesData[index:-1].find(propMatch.group("data"))
                    currFixedData = propertiesData[startFrom:(startFrom + int(propMatch.group("len")))]
                    length = int(propMatch.group("len"))
                    # [^=]+=?, == data
                    properties[propMatch.group("name")] = currFixedData[0:length].lstrip()
                else:
                    length = int(propMatch.group("len"))
                    # [^=]+=?, == data
                    properties[propMatch.group("name")] = propMatch.group("data")[0:length].lstrip()

                index += len(propMatch.group("prop")) + length + 1

            self._viewItems.append(ViewItem(matcher.group("class"), matcher.group("id"), indent, properties, parent, matcher.group("properties")))

            if parent:
                parent.addChild(self._viewItems[-1])
        return self._viewItems

    def __str__(self):
        return 'View(items=%s, dump="%s")' % (
            len(self._viewItems), self._rawDumpFilename)

class _AndroidDeviceConnection:
    """
    Connection to the Android Device being tested.

    """
    _m_host = 'localhost'
    _m_port = random.randint(20000, 29999)
    _w_host = 'localhost'
    _w_port = _m_port + 1

    def __init__(self, serialNumber, stopOnError=True):
        self._serialNumber = serialNumber
        self._stopOnError = stopOnError
        try:
            self._resetMonkey()
            self._resetWindow()
        finally:
            # Next _AndroidDeviceConnection instance will use different ports
            self._w_port = _AndroidDeviceConnection._w_port
            self._m_port = _AndroidDeviceConnection._m_port
            _AndroidDeviceConnection._w_port += 100
            _AndroidDeviceConnection._m_port += 100

    def __del__(self):
        try: self._monkeySocket.close()
        except: pass

    def _cat(self, remoteFilename):
        fd, filename = tempfile.mkstemp("fmbtandroid-cat-")
        os.close(fd)
        self._runAdb("pull '%s' %s" % (remoteFilename, filename), 0)
        contents = file(filename).read()
        os.remove(filename)
        return contents

    def _runAdb(self, command, expectedExitStatus=0):
        if not self._stopOnError:
            expect = None
        else:
            expect = expectedExitStatus
        if type(command) == list:
            command = ["adb", "-s", self._serialNumber] + command
        else:
            command = ("adb -s '%s' " % (self._serialNumber,)) + command
        return _run(command, expectedExitStatus = expect)

    def _runSetupCmd(self, cmd, expectedExitStatus = 0):
        _adapterLog('setting up connections: "%s"' % (cmd,))
        exitStatus, _, _ = self._runAdb(cmd, expectedExitStatus)
        if exitStatus == 0: return True
        else: return True

    def _resetWindow(self):
        setupCommands = ["shell service call window 1 i32 4939",
                         "forward tcp:%s tcp:4939" % (self._w_port,)]
        for c in setupCommands:
            self._runSetupCmd(c)

    def _resetMonkey(self, timeout=3, pollDelay=.25):
        self._runSetupCmd("shell monkey --port 1080", None)
        time.sleep(pollDelay)
        endTime = time.time() + timeout

        while time.time() < endTime:
            self._runSetupCmd("forward tcp:%s tcp:1080" % (self._m_port,), 0)
            try:
                self._monkeySocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self._monkeySocket.connect((self._m_host, self._m_port))
                self._monkeySocket.setblocking(0)
                self._monkeySocket.settimeout(1.0)
                self._platformVersion = self._monkeyCommand("getvar build.version.release", retry=0)[1]
                if len(self._platformVersion) > 0:
                    self._monkeySocket.settimeout(5.0)
                    return True
            except Exception, e:
                pass
            time.sleep(pollDelay)
        if self._stopOnError:
            msg = 'Android monkey error: cannot connect to "adb shell monkey --port 1080" to device %s' % (self._serialNumber)
            _adapterLog(msg)
            raise AndroidConnectionError(msg)
        else:
            return False

    def _monkeyCommand(self, command, retry=3):
        try:
            self._monkeySocket.sendall(command + "\n")
            data = self._monkeySocket.recv(4096).strip()
            if len(data) == 0 and retry > 0:
                return self._monkeyCommand(command, retry-1)
            if data == "OK":
                return True, None
            elif data.startswith("OK:"):
                return True, data.split("OK:")[1]
            _adapterLog("monkeyCommand failing... command: '%s' response: '%s'" % (command, data))
            return False, None
        except socket.error:
            try: self.sock.close()
            except: pass

            if retry > 0:
                self._resetMonkey()
                return self._monkeyCommand(command, retry=retry-1)
            else:
                raise AndroidConnectionError('Android monkey socket connection lost while sending command "%s"' % (command,))

    def reboot(self, reconnect, firstBootAfterFlashing, timeout):
        if firstBootAfterFlashing:
            self._runAdb("root")
            time.sleep(2)
            self._runAdb("shell rm /data/data/com.android.launcher/shared_prefs/com.android.launcher2.prefs.xml")

        self._runAdb("reboot")
        _adapterLog("rebooting " + self._serialNumber)

        if reconnect:
            self._runAdb("wait-for-device")
            endTime = time.time() + timeout
            while time.time() < endTime:
                try:
                    if self._resetMonkey(timeout=1, pollDelay=1):
                        break
                except AndroidConnectionError:
                    pass
                time.sleep(1)
            else:
                _adapterLog("reboot: reconnecting to " + self._serialNumber + " failed")
                return False
            self._resetWindow()
        return True

    def recvVariable(self, variableName):
        ok, value = self._monkeyCommand("getvar " + variableName)
        if ok: return value
        else:
            # LOG: getvar variableName failed
            return None

    def recvScreenSize(self):
        try:
            height = int(self.recvVariable("display.height"))
            width = int(self.recvVariable("display.width"))
        except TypeError:
            return None, None
        return width, height

    def recvTopAppWindow(self):
        _, output, _ = self._runAdb("shell dumpsys window", 0)
        if self._platformVersion >= "4.2":
            s = re.findall("mCurrentFocus=Window\{(#?[0-9A-Fa-f]{8})( [^ ]*)? (?P<winName>[^}]*)\}", output)
        else:
            s = re.findall("mCurrentFocus=Window\{(#?[0-9A-Fa-f]{8}) (?P<winName>[^ ]*) [^ ]*\}", output)
        if s and len(s[0][-1].strip()) > 1: topWindowName = s[0][-1]
        else: topWindowName = None

        s = re.findall("mFocusedApp=AppWindowToken.*ActivityRecord\{#?[0-9A-Fa-f]{8}( [^ ]*)? (?P<appName>[^}]*)\}", output)
        if s and len(s[0][-1].strip()) > 1:
            topAppName = s[0][-1].strip()
        else:
            topAppName = None
        return topAppName, topWindowName

    def sendTap(self, xCoord, yCoord):
        return self._monkeyCommand("tap " + str(xCoord) + " " + str(yCoord))[0]

    def sendKeyUp(self, key):
        return self._monkeyCommand("key up " + key)[0]

    def sendKeyDown(self, key):
        return self._monkeyCommand("key down " + key)[0]

    def sendTouchUp(self, xCoord, yCoord):
        return self._monkeyCommand("touch up " + str(xCoord) + " " + str(yCoord))[0]

    def sendTouchDown(self, xCoord, yCoord):
        return self._monkeyCommand("touch down " + str(xCoord) + " " + str(yCoord))[0]

    def sendTouchMove(self, xCoord, yCoord):
        return self._monkeyCommand("touch move " + str(xCoord) + " " + str(yCoord))[0]

    def sendTrackBallMove(self, dx, dy):
        return self._monkeyCommand("trackball " + str(dx) + " " + str(dy))[0]

    def sendPress(self, key):
        return self._monkeyCommand("press " + key)[0]

    def sendType(self, text):
        return self._monkeyCommand("type " + text)[0]

    def screenshot(self, screenshotDir=None, imageFilename=None):
        """
        Capture a screenshot and copy the image file to given path or
        system temp folder.

        Returns screenshot filename.
        """
        if imageFilename == None:
            filename = _filenameTimestamp() + "-" + self._serialNumber + '.png'
        else:
            filename = imageFilename
        remotefile = '/sdcard/' + filename

        status, _, _ = self._runAdb(['shell', 'screencap', '-p', remotefile], 0)

        if status != 0: return None

        if screenshotDir == None:
            status, _, _ = self._runAdb(['pull', remotefile, tempfile.gettempdir()], 0)
        else:
            status, _, _ = self._runAdb(['pull', remotefile, os.path.join(screenshotDir, filename)], 0)

        if status != 0: return None

        status, _, _ = self._runAdb(['shell','rm', remotefile], 0)

        if screenshotDir == None:
            return os.path.join(tempfile.gettempdir(), filename)
        else:
            return os.path.join(screenshotDir, filename)

    def shellSOE(self, shellCommand):
        fd, filename = tempfile.mkstemp(prefix="fmbtandroid-shellcmd-")
        remotename = '/sdcard/' + os.path.basename(filename)
        os.write(fd, shellCommand + "\n")
        os.close(fd)
        self._runAdb("push %s %s" % (filename, remotename), 0)
        # do everything we can in one command to minimise adb commands:
        # execute command, record results, package, print uuencoded package and remove remote temp files
        cmd = "shell 'source %s >%s.out 2>%s.err; echo $? > %s.status; cd %s; tar cf - %s.out %s.err %s.status | uuencode %s.tar; rm -f %s*'" % (
            ((remotename,) * 4) + (os.path.dirname(remotename),) + ((os.path.basename(remotename),) * 5))
        status, output, error = self._runAdb(cmd, 0)
        file(filename, "w").write(output)
        uu.decode(filename, out_file=filename + ".tar")
        import tarfile
        tar = tarfile.open(filename + ".tar")
        basename = os.path.basename(filename)
        stdout = tar.extractfile(basename + ".out").read()
        stderr = tar.extractfile(basename + ".err").read()
        try: exitstatus = int(tar.extractfile(basename + ".status").read())
        except: exitstatus = None
        os.remove(filename)
        os.remove(filename + ".tar")
        return exitstatus, stdout, stderr

    def recvViewData(self, retry=3):
        _dataBufferLen = 4096 * 16
        try:
            self._windowSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._windowSocket.connect( (self._w_host, self._w_port) )

            # DUMP -1: get foreground window info
            if self._windowSocket.sendall("DUMP -1\n") == 0:
                # LOG: readGUI cannot write to window socket
                raise Exception("writing socket failed")

            # Read until a "DONE" line
            data = ""
            while True:
                try: newData = self._windowSocket.recv(_dataBufferLen)
                except socket.timeout:
                    continue
                data += newData
                if data.splitlines()[-1] == "DONE" or newData == '':
                    break
            return data
        except Exception, msg:
            _adapterLog("recvViewData: window socket error: %s" % (msg,))
            if retry > 0:
                self._resetWindow()
                return self.recvViewData(retry=retry-1)
            else:
                msg = "recvViewData: cannot read window socket"
                _adapterLog(msg)
                raise AndroidConnectionError(msg)
        finally:
            try: self._windowSocket.close()
            except: pass

class AndroidConnectionError(Exception): pass
class AndroidConnectionLost(AndroidConnectionError): pass
