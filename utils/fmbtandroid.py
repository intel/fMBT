# fMBT, free Model Based Testing tool
# Copyright (c) 2013-2015, Intel Corporation.
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

Open application grid from the home screen, unlock screen if necessary

import fmbtandroid
import time
d = fmbtandroid.Device()
d.pressHome()
time.sleep(1)
whatISee = d.waitAnyBitmap(["lockscreen-lock.png", "home-appgrid.png"])
if "lockscreen-lock.png" in whatISee:
    d.swipeBitmap("lockscreen-lock.png", "east")
    time.sleep(1)
    d.pressHome()
    whatISee = d.waitAnyBitmap(["home-appgrid.png"])
assert "home-appgrid.png" in whatISee, "Cannot find appgrid bitmap at"
d.tapBitmap("home-appgrid.png")

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

Enable extensive logging with screenshots and highlighted content:

import fmbtandroid, time

d = fmbtandroid.Device()
d.enableVisualLog("example.html")
d.pressHome(); time.sleep(1)
d.refreshScreenshot()
d.tapOcrText("Google"); time.sleep(1)
d.refreshScreenshot()

then view the log:
$ chromium example.html

* * *

Connect to devices on remote hosts. As serial number is not given,
this example connects to the first device on the "adb devices" list on
HOST.

# Setup port forwards for ADB, monkey and window services:
$ ssh -N -L10000:127.0.0.1:5037 \
         -L10001:127.0.0.1:10001 \
         -L10002:127.0.0.1:10002 HOST &
# Pass forwarded ports to the Device constructor
import fmbtandroid
d = fmbtandroid.Device(adbPort=10000, adbForwardPort=10001)
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
import gzip
import math
import os
import random
import re
import shutil
import socket
import StringIO
import struct
import subprocess
import tempfile
import time
import uu

import fmbt
import fmbtgti
try:
    import fmbtpng
except ImportError:
    fmbtpng = None

ROTATION_0 = 0
ROTATION_90 = 1
ROTATION_180 = 2
ROTATION_270 = 3
ROTATIONS = [ROTATION_0, ROTATION_90, ROTATION_180, ROTATION_270]
ROTATION_DEGS = [0, 90, 180, 270]

# See imagemagick convert parameters.
fmbtgti._OCRPREPROCESS =  [
    '-sharpen 5 -filter Mitchell %(zoom)s -sharpen 5 -level 60%%,60%%,3.0 -sharpen 5',
    '-sharpen 5 -level 90%%,100%%,3.0 -filter Mitchell -sharpen 5'
    ]

def _adapterLog(msg):
    fmbt.adapterlog("fmbtandroid: %s" % (msg,))

def _logFailedCommand(source, command, exitstatus, stdout, stderr):
    _adapterLog('in %s command "%s" failed:\n    output: %s\n    error: %s\n    status: %s' %
                (source, command, stdout, stderr, exitstatus))

if os.name == "nt":
    _g_closeFds = False
    _g_adbExecutable = "adb.exe"
else:
    _g_closeFds = True
    _g_adbExecutable = "adb"

def _run(command, expectedExitStatus = None, timeout=None):
    if type(command) == str or os.name == "nt":
        if timeout != None and os.name != "nt":
            command = "timeout %s %s" % (timeout, command)
        shell=True
    else:
        if timeout != None:
            command = ["timeout", str(timeout)] + command
        shell=False
    try:
        p = subprocess.Popen(command, shell=shell,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             close_fds=_g_closeFds)
        if expectedExitStatus != None or timeout != None:
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
            if "error: device not found" in err:
                raise AndroidDeviceNotFound(msg)
            else:
                raise FMBTAndroidRunError(msg)

    return (exitStatus, out, err)

_g_keyNames = set((
    "0", "1", "2", "3", "3D_MODE", "4", "5", "6", "7",
    "8", "9", "A", "ALT_LEFT", "ALT_RIGHT", "APOSTROPHE",
    "APP_SWITCH", "ASSIST", "AT", "AVR_INPUT", "AVR_POWER", "B",
    "BACK", "BACKSLASH", "BOOKMARK", "BREAK", "BRIGHTNESS_DOWN",
    "BRIGHTNESS_UP", "BUTTON_1", "BUTTON_10", "BUTTON_11",
    "BUTTON_12", "BUTTON_13", "BUTTON_14", "BUTTON_15", "BUTTON_16",
    "BUTTON_2", "BUTTON_3", "BUTTON_4", "BUTTON_5", "BUTTON_6",
    "BUTTON_7", "BUTTON_8", "BUTTON_9", "BUTTON_A", "BUTTON_B",
    "BUTTON_C", "BUTTON_L1", "BUTTON_L2", "BUTTON_MODE", "BUTTON_R1",
    "BUTTON_R2", "BUTTON_SELECT", "BUTTON_START", "BUTTON_THUMBL",
    "BUTTON_THUMBR", "BUTTON_X", "BUTTON_Y", "BUTTON_Z", "C",
    "CALCULATOR", "CALENDAR", "CALL", "CAMERA", "CAPS_LOCK",
    "CAPTIONS", "CHANNEL_DOWN", "CHANNEL_UP", "CLEAR", "COMMA",
    "CONTACTS", "CTRL_LEFT", "CTRL_RIGHT", "D", "DEL", "DPAD_CENTER",
    "DPAD_DOWN", "DPAD_LEFT", "DPAD_RIGHT", "DPAD_UP", "DVR", "E",
    "EISU", "ENDCALL", "ENTER", "ENVELOPE", "EQUALS", "ESCAPE",
    "EXPLORER", "F", "F1", "F10", "F11", "F12", "F2", "F3", "F4",
    "F5", "F6", "F7", "F8", "F9", "FOCUS", "FORWARD", "FORWARD_DEL",
    "FUNCTION", "G", "GRAVE", "GUIDE", "H", "HEADSETHOOK", "HENKAN",
    "HOME", "I", "INFO", "INSERT", "J", "K", "KANA",
    "KATAKANA_HIRAGANA", "L", "LANGUAGE_SWITCH", "LEFT_BRACKET", "M",
    "MANNER_MODE", "MEDIA_AUDIO_TRACK", "MEDIA_CLOSE", "MEDIA_EJECT",
    "MEDIA_FAST_FORWARD", "MEDIA_NEXT", "MEDIA_PAUSE", "MEDIA_PLAY",
    "MEDIA_PLAY_PAUSE", "MEDIA_PREVIOUS", "MEDIA_RECORD",
    "MEDIA_REWIND", "MEDIA_STOP", "MENU", "META_LEFT", "META_RIGHT",
    "MINUS", "MOVE_END", "MOVE_HOME", "MUHENKAN", "MUSIC", "MUTE",
    "N", "NOTIFICATION", "NUM", "NUMPAD_0", "NUMPAD_1", "NUMPAD_2",
    "NUMPAD_3", "NUMPAD_4", "NUMPAD_5", "NUMPAD_6", "NUMPAD_7",
    "NUMPAD_8", "NUMPAD_9", "NUMPAD_ADD", "NUMPAD_COMMA",
    "NUMPAD_DIVIDE", "NUMPAD_DOT", "NUMPAD_ENTER", "NUMPAD_EQUALS",
    "NUMPAD_LEFT_PAREN", "NUMPAD_MULTIPLY", "NUMPAD_RIGHT_PAREN",
    "NUMPAD_SUBTRACT", "NUM_LOCK", "O", "P", "PAGE_DOWN", "PAGE_UP",
    "PERIOD", "PICTSYMBOLS", "PLUS", "POUND", "POWER", "PROG_BLUE",
    "PROG_GREEN", "PROG_RED", "PROG_YELLOW", "Q", "R",
    "RIGHT_BRACKET", "RO", "S", "SCROLL_LOCK", "SEARCH", "SEMICOLON",
    "SETTINGS", "SHIFT_LEFT", "SHIFT_RIGHT", "SLASH", "SOFT_LEFT",
    "SOFT_RIGHT", "SPACE", "STAR", "STB_INPUT", "STB_POWER",
    "SWITCH_CHARSET", "SYM", "SYSRQ", "T", "TAB", "TV", "TV_INPUT",
    "TV_POWER", "U", "UNKNOWN", "V", "VOLUME_DOWN", "VOLUME_MUTE",
    "VOLUME_UP", "W", "WINDOW", "X", "Y", "YEN", "Z",
    "ZENKAKU_HANKAKU", "ZOOM_IN", "ZOOM_OUT"))

_g_listDevicesCommand = [_g_adbExecutable, "devices"]
def listSerialNumbers(adbPort=None):
    """
    Returns list of serial numbers of Android devices.
    Equivalent for "adb devices".
    """
    if adbPort:
        command = [_g_adbExecutable, "-P", str(adbPort), "devices"]
    else:
        command = _g_listDevicesCommand
    status, output, err = _run(command, expectedExitStatus = [0, 127])
    if status == 127:
        raise FMBTAndroidError('adb not found in PATH. Check your Android SDK installation.')

    outputLines = [l.strip() for l in output.splitlines()]
    try: deviceLines = outputLines[outputLines.index("List of devices attached")+1:]
    except: deviceLines = []

    deviceLines = [l for l in deviceLines if l.strip() != ""]

    potentialDevices = [line.split()[0] for line in deviceLines]

    return potentialDevices

class Device(fmbtgti.GUITestInterface):
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
    def __init__(self, deviceName=None, iniFile=None, connect=True,
                 monkeyOptions=[], adbPort=None, adbForwardPort=None,
                 **kwargs):
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

          connect (boolean, optional):
                  Immediately establish connection to the device. The
                  default is True. Example on using without connection:
                    d = fmbtandroid.Device(connect=False)
                    d.refreshView("screenshots/20141127-emulator-5554.view")
                    print d.view().dumpTree()

          adbPort (integer, optional):
                  Find and connect to devices via the ADB server that
                  listens to adbPort. If not given, adb is executed
                  without the port parameter (-P).

          adbForwardPort (integer, optional):
                  Connect to services needed on the device via
                  forwarded ports starting from adbForwardPort. The
                  default is FMBTANDROID_ADB_FORWARD_PORT, or
                  random ports if undefined.

          monkeyOptions (list of strings, optional):
                  Extra command line options to be passed to Android
                  monkey on the device.

          rotateScreenshot (integer or "auto", optional)
                  rotate new screenshots by rotateScreenshot degrees.
                  Example: rotateScreenshot=-90. The default is 0 (no
                  rotation). If "auto" is given, rotate automatically
                  to compensate current display rotation.
        """

        if kwargs.get("rotateScreenshot", None) == "auto":
            # the base class does not understand "auto" rotate screenshot
            del kwargs["rotateScreenshot"]
            self._autoRotateScreenshot = True
        else:
            self._autoRotateScreenshot = False

        adbPortArgs = {}
        if adbPort != None:
            adbPortArgs["adbPort"] = adbPort
        if adbForwardPort != None:
            adbPortArgs["adbForwardPort"] = adbForwardPort

        fmbtgti.GUITestInterface.__init__(self, **kwargs)

        self._fmbtAndroidHomeDir = os.getenv("FMBTANDROIDHOME", os.getcwd())

        self._lastView = None
        self._supportsView = None
        self._monkeyOptions = monkeyOptions
        self._lastConnectionSettings = {}

        self._conf = Ini()

        self._loadDeviceAndTestINIs(self._fmbtAndroidHomeDir, deviceName, iniFile)
        if deviceName == None:
            deviceName = self._conf.value("general", "serial", "")

        if connect == False and deviceName == "":
            deviceName = "nodevice"
            self.serialNumber = self._conf.value("general", "serial", deviceName)
            self.setConnection(None)
        elif deviceName == "":
            # Connect to an unspecified device.
            # Go through devices in "adb devices".
            potentialDevices = listSerialNumbers(adbPort=adbPort)

            if potentialDevices == []:
                raise AndroidDeviceNotFound('No devices found with "%s"' % (_g_listDevicesCommand,))

            for deviceName in potentialDevices:
                try:
                    self.setConnection(_AndroidDeviceConnection(
                        deviceName, monkeyOptions=self._monkeyOptions, **adbPortArgs))
                    self._conf.set("general", "serial", self.serialNumber)
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
                self.setConnection(_AndroidDeviceConnection(
                    self.serialNumber, monkeyOptions=self._monkeyOptions, **adbPortArgs))


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

        if self._conn: hw = self._conn.recvVariable("build.device")
        else: hw = "nohardware"
        self.hardware        = self._conf.value("general", "hardware", hw)
        self.setBitmapPath(self._conf.value("paths", "bitmapPath", ""), self._fmbtAndroidHomeDir)
        self.setScreenshotDir(self._conf.value("paths", "screenshotDir", self._fmbtAndroidHomeDir + os.sep + "screenshots"))

    def accelerometer(self):
        """
        Return 3-axis accelerometer readings.
        """
        if self._conn:
            return self._conn.recvLastAccelerometer()
        else:
            return (None, None, None)

    def autoRotateScreenshot(self):
        """
        Return True if screenshots are rotated automatically,
        otherwise False.

        See also: setAutoRotateScreenshot
        """
        return self._autoRotateScreenshot

    def callContact(self, contact):
        """
        Call to given contact.

        Return True if successful, otherwise False.
        """
        callCommand = 'service call phone 1 s16 "%s"' % (contact,)
        status, out, err = self.shellSOE(callCommand)
        if status != 0:
            _logFailedCommand("callContact", callCommand, status, out, err)
            return False
        else:
            return True

    def callNumber(self, number):
        """
        Call to given phone number.

        Return True if successful, otherwise False.
        """
        callCommand = "am start -a android.intent.action.CALL -d 'tel:%s'" % (number,)
        status, out, err = self.shellSOE(callCommand)
        if status != 0:
            _logFailedCommand("callNumber", callCommand, status, out, err)
            return False
        else:
            return True

    def close(self):
        fmbtgti.GUITestInterface.close(self)

        if hasattr(self, "_conn"):
            del self._conn
        if hasattr(self, "_lastView"):
            del self._lastView
        import gc
        gc.collect()

    def deviceLog(self, msg, priority="i", tag="fMBT"):
        """
        Write a message to device log (seen via logcat)

        Parameters:
          msg (string):
                  message to be written.

          priority (string, optional):
                  priorityChar, one of "v", "d", "i", "w", "e".
                  The default is "i".

          tag (string, optional):
                  tag for the log entry, the default is "fMBT".
        """
        if not priority.lower() in ["v", "d", "i", "w", "e"]:
            return False
        return self.existingConnection().sendDeviceLog(
            msg, priority.lower(), tag)

    def displayRotation(self):
        """
        Returns current rotation of the display.

        Returns integer, that is ROTATION_0, ROTATION_90, ROTATION_180
        or ROTATION_270. Returns None if rotation is not available.

        Example: take a screenshot rotated to current display orientation

          d.refreshScreenshot(rotate=-d.displayRotation())
        """
        if self._conn:
            return self._conn.recvCurrentDisplayOrientation()
        else:
            return None

    def displayPowered(self):
        """
        Returns True if display is powered, otherwise False.
        """
        if self._conn:
            return self._conn.recvDisplayPowered()
        else:
            return None

    def drag(self, (x1, y1), (x2, y2), delayBetweenMoves=None, delayBeforeMoves=None, delayAfterMoves=None, movePoints=None):
        """
        Touch the screen on coordinates (x1, y1), drag along straight
        line to coordinates (x2, y2), and raise fingertip.

        coordinates (floats in range [0.0, 1.0] or integers):
                floating point coordinates in range [0.0, 1.0] are
                scaled to full screen width and height, others are
                handled as absolute coordinate values.

        delayBeforeMoves (float, optional):
                seconds to wait after touching and before dragging.
                If negative, starting touch event is not sent.

        delayBetweenMoves (float, optional):
                seconds to wait when moving between points when
                dragging.

        delayAfterMoves (float, optional):
                seconds to wait after dragging, before raising
                fingertip.
                If negative, fingertip is not raised.

        movePoints (integer, optional):
                the number of intermediate move points between end
                points of the line.

        Returns True on success, False if sending input failed.
        """
        if (delayBetweenMoves == None and
            delayBeforeMoves == None and
            delayAfterMoves == None and
            movePoints == None and
            self.platformVersion() > "4.2"):
            x1, y1 = self.intCoords((x1, y1))
            x2, y2 = self.intCoords((x2, y2))
            return self.existingConnection().sendSwipe(x1, y1, x2, y2)
        else:
            kwArgs = {}
            if delayBetweenMoves != None: kwArgs["delayBetweenMoves"] = delayBetweenMoves
            if delayBeforeMoves != None: kwArgs["delayBeforeMoves"] = delayBeforeMoves
            if delayAfterMoves != None: kwArgs["delayAfterMoves"] = delayAfterMoves
            if movePoints != None: kwArgs["movePoints"] = movePoints
            return fmbtgti.GUITestInterface.drag(
                self, (x1, y1), (x2, y2),
                **kwArgs)

    def dumpIni(self):
        """
        Returns contents of current device configuration as a string (in
        INI format).
        """
        return self._conf.dump()

    def ini(self):
        """
        Returns an Ini object containing effective device
        configuration.
        """
        return self._conf

    def install(self, filename, lock=False, reinstall=False, downgrade=False,
                sdcard=False, algo=None, key=None, iv=None):
        """
        Install apk on the device.

        Parameters:

          filename (string):
                APK filename on host.

          lock (boolean, optional):
                forward-lock the app. Correspond to adb install "-l".
                The default is False.

          reinstall (boolean, optional):
                Reinstall the app, keep its data. Corresponds to "-r".
                The default is False.

          downgrade (boolean, optional):
                Allow downgrading the application. Corresponds to "-d".
                The default is False.

          sdcard (boolean, optional):
                Install on SD card. Corresponds to "-s".
                The default is False.

          algo (string, optional):
                Algorithm name. Corresponds to "--algo".
                The default is None.

          key (string, optional):
                Hex-encoded key. Corresponds to "--key".
                The default is None.

          iv (string, optional):
                Hex-encoded iv. Corresponds to "--iv".
                The default is None.

        Returns True if successful, False if device is not connected,
        and "adb install" command output (string) otherwise.

        Example:
          status = d.install("/tmp/PythonAPK.apk")
          if status != True:
              print "Installation failed, output:", status
        """
        if self._conn:
            return self._conn.install(filename, lock, reinstall, downgrade,
                                      sdcard, algo, key, iv)
        else:
            return False

    def keyNames(self):
        """
        Returns list of keyNames supported by pressKey.
        """
        return sorted(_g_keyNames)

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

    def pinch(self, (x, y), startDistance, endDistance,
              finger1Dir=90, finger2Dir=270, movePoints=100):
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

          movePoints (integer, optional):
                  number of points to which finger tips are moved
                  after laying them to the initial positions. The
                  default is 100.
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
        finger1startY = int(y - math.sin(math.radians(finger1Dir)) * startDistanceInPixels)
        finger1endX = int(x + math.cos(math.radians(finger1Dir)) * endDistanceInPixels)
        finger1endY = int(y - math.sin(math.radians(finger1Dir)) * endDistanceInPixels)

        finger2startX = int(x + math.cos(math.radians(finger2Dir)) * startDistanceInPixels)
        finger2startY = int(y - math.sin(math.radians(finger2Dir)) * startDistanceInPixels)
        finger2endX = int(x + math.cos(math.radians(finger2Dir)) * endDistanceInPixels)
        finger2endY = int(y - math.sin(math.radians(finger2Dir)) * endDistanceInPixels)

        self.existingConnection().sendMonkeyPinchZoom(
            finger1startX, finger1startY, finger1endX, finger1endY,
            finger2startX, finger2startY, finger2endX, finger2endY,
            movePoints)
        return True

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

    def platformVersion(self):
        """
        Returns the platform version of the device.
        """
        if self._conn:
            return self._conn._platformVersion
        else:
            return "nosoftware"

    def pressAppSwitch(self, **pressKeyKwArgs):
        """
        Press the app switch button.

        Optional parameters are the same as for pressKey.
        """
        return self.pressKey("KEYCODE_APP_SWITCH", **pressKeyKwArgs)

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

    def pressKey(self, keyName, long=False, hold=0.0, modifiers=None):
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

          modifiers (list of strings, optional):
                  modifier key(s) to be pressed at the same time.
        """
        if not keyName.upper().startswith("KEYCODE_"):
            keyName = "KEYCODE_" + keyName
        keyName = keyName.upper()
        if modifiers != None:
            modifiers = [
                m.upper() if m.upper().startswith("KEYCODE_") else "KEYCODE_" + m.upper()
                for m in modifiers]
        return fmbtgti.GUITestInterface.pressKey(self, keyName, long, hold, modifiers)

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

    def pressSearch(self, **pressKeyKwArgs):
        """
        Press the search button.

        Optional parameters are the same as for pressKey.
        """
        return self.pressKey("KEYCODE_SEARCH", **pressKeyKwArgs)

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

    def reboot(self, reconnect=True, firstBoot=False, timeout=120):
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

          timeout (integer, optional)
                  Timeout in seconds for reconnecting after reboot.
                  The default is 120 s.

        Returns True on success, otherwise False.
        """
        return self.existingConnection().reboot(reconnect, firstBoot, timeout)

    def reconnect(self):
        """
        Close connections to the device and reconnect.
        """
        conn = self.connection()
        if hasattr(conn, "settings"):
            self._lastConnectionSettings = conn.settings()
        connSettings = self._lastConnectionSettings
        self.setConnection(None)
        self._lastConnectionSettings = connSettings
        del conn # make sure gc will collect the connection object
        import gc
        gc.collect()
        try:
            self.setConnection(_AndroidDeviceConnection(
                self.serialNumber, **connSettings))
            return True
        except Exception, e:
            _adapterLog("reconnect failed: %s" % (e,))
            return False

    def refreshScreenshot(self, forcedScreenshot=None, rotate=None):
        # convert Android display/user rotation to degrees
        if rotate in ROTATIONS:
            rotate = ROTATION_DEGS[rotate]
        elif rotate in [-ROTATION_0, -ROTATION_90, -ROTATION_180, -ROTATION_270]:
            rotate = -ROTATION_DEGS[-rotate]
        elif rotate == None:
            if self._autoRotateScreenshot:
                drot = self.displayRotation()
                if drot != None:
                    return self.refreshScreenshot(forcedScreenshot, rotate=-drot)
        return fmbtgti.GUITestInterface.refreshScreenshot(self, forcedScreenshot, rotate)
    refreshScreenshot.__doc__ = fmbtgti.GUITestInterface.refreshScreenshot.__doc__

    def refreshView(self, forcedView=None):
        """
        (Re)reads view items on display and updates the latest View
        object.

        Parameters:

          forcedView (View or filename, optional):
                use given View object or view file instead of reading
                items from the device.

        Returns created View object.
        """
        def formatErrors(errors, filename):
            return 'refreshView parse errors in "%s":\n    %s' % (
                filename,
                "\n    ".join(["line %s: %s error: %s" % e for e in errors]),)

        if self._conn:
            displayToScreen = self._conn._displayToScreen
        else:
            displayToScreen = None
        if forcedView != None:
            if isinstance(forcedView, View):
                self._lastView = forcedView
            elif type(forcedView) == str:
                self._lastView = View(self.screenshotDir(), self.serialNumber, file(forcedView).read(), displayToScreen, self.itemOnScreen, self.intCoords)
                _adapterLog(formatErrors(self._lastView.errors(), self._lastView.filename()))
            else:
                raise ValueError("forcedView must be a View object or a filename")
            return self._lastView

        retryCount = 0
        while True:
            dump = self.existingConnection().recvViewData()
            if dump != None:
                viewDir = os.path.dirname(self._newScreenshotFilepath())
                view = View(viewDir, self.serialNumber, dump, displayToScreen, self.itemOnScreen, self.intCoords)
            else:
                _adapterLog("refreshView window dump reading failed")
                view = None
                # fail quickly if there is no answer
                retryCount += self._PARSE_VIEW_RETRY_LIMIT / 2
            if dump == None or len(view.errors()) > 0:
                if view:
                    _adapterLog(formatErrors(view.errors(), view.filename()))
                if retryCount < self._PARSE_VIEW_RETRY_LIMIT:
                    retryCount += 1
                    time.sleep(0.2) # sleep before retry
                else:
                    raise AndroidConnectionError("Cannot read window dump")
            else:
                # successfully parsed or parsed with errors but no more retries
                self._lastView = view
                return view

    def screenLocked(self):
        """
        Return True if showing lockscreen, otherwise False.
        """
        if self._conn:
            return self._conn.recvShowingLockscreen()
        else:
            return None

    def setAccelerometer(self, abc):
        """
        Set emulator accelerometer readings

        Parameters:

          abc (tuple of floats):
                  new 3-axis accelerometer readings, one to three values.

        Returns True if successful, False if failed. Raises an exception
        if emulator cannot be connected to. Does not work with real hardware.

        Note: to rotate display with real hardware, see setUserRotation().

        Example:
          d.setAccelerometer((9.8, 0))
          d.setAccelerometer((0, 9.8))
          d.setAccelerometer((-9.6, 0.2, 0.8))
        """
        if self._conn:
            return self._conn.sendAcceleration(abc)
        else:
            return False

    def setAccelerometerRotation(self, value):
        """
        Enable or disable accelerometer-based screen rotation

        Parameters:

          value (boolean):
                  True: enable accelerometer-based rotation
                  False: disable accelerometer-based rotation.

        Returns True if successful, otherwise False.
        """
        if self._conn:
            return self._conn.sendAccelerometerRotation(value)
        else:
            return False

    def setAutoRotateScreenshot(self, value):
        """
        Enable or disable automatic screenshot rotation.

        Parameters:

          value (boolean):
                  If True, rotate screenshot automatically to compensate
                  current display rotation.

        refreshScreenshot()'s optional rotate parameter overrides this
        setting.

        See also autoRotateScreenshot(), displayRotation().
        """
        if value:
            self._autoRotateScreenshot = True
        else:
            self._autoRotateScreenshot = False

    def setConnection(self, connection):
        self._lastConnectionSettings = {}
        fmbtgti.GUITestInterface.setConnection(self, connection)
        if hasattr(self.connection(), "_serialNumber"):
            self.serialNumber = self.connection()._serialNumber

    def setDisplaySize(self, size=(None, None)):
        """
        Transform coordinates of synthesized events from screenshot
        resolution to given input area size. By default events are
        synthesized directly to screenshot coordinates.

        Parameters:

          size (pair of integers (width, height), optional):
                  width and height of display in pixels. If not
                  given, values from Android system properties
                  "mDisplayWidth" and "mDisplayHeight" will be used.

        Returns None.
        """
        width, height = size
        if width == None or height == None:
            w, h = self.existingConnection().recvScreenSize()
            if w == h == 0:
                w, h = self.existingConnection().recvDefaultViewportSize()
        if width == None:
            width = w
        if height == None:
            height = h
        screenWidth, screenHeight = self.screenSize()
        self.existingConnection().setScreenToDisplayCoords(
            lambda x, y: (x * width / screenWidth,
                          y * height / screenHeight))
        self.existingConnection().setDisplayToScreenCoords(
            lambda x, y: (x * screenWidth / width,
                          y * screenHeight / height))

    def setUserRotation(self, rotation):
        """
        Enable or disable accelerometer-based screen rotation

        Parameters:

          rotation (integer):
                  values 0, 1, 2 and 3 correspond to
                  ROTATION_0, ROTATION_90, ROTATION_180, ROTATION_270.

        Returns True if successful, otherwise False.

        Example:
          # Disable accelerometer-based rotation for user rotation
          # to take effect.
          d.setAccelerometerRotation(False)
          d.setUserRotation(fmbtandroid.ROTATION_90)
          time.sleep(2)
          d.setUserRotation(fmbtandroid.ROTATION_0)
          time.sleep(2)
          d.setAccelerometerRotation(True)
        """
        if rotation in ROTATIONS:
            pass # already in correct scale
        elif rotation in ROTATION_DEGS:
            rotation = ROTATION_DEGS.index(rotation)
        else:
            raise ValueError('invalid rotation "%s"' % (rotation,))

        if self._conn:
            return self._conn.sendUserRotation(rotation)
        else:
            return False

    def shell(self, shellCommand):
        """
        Execute shellCommand in adb shell.

        shellCommand is a string (arguments separated by whitespace).

        Returns output of "adb shell" command.

        If you wish to receive exitstatus or standard output and error
        separated from shellCommand, refer to shellSOE().
        """
        return self.existingConnection()._runAdb(["shell", shellCommand])[1]

    def shellSOE(self, shellCommand):
        """
        Execute shellCommand in adb shell.

        shellCommand is a string (arguments separated by whitespace).

        Returns tuple (exitStatus, standardOutput, standardError).

        Requires tar and uuencode to be available on the device.
        """
        return self.existingConnection().shellSOE(shellCommand)

    def smsNumber(self, number, message):
        """
        Send message using SMS to given number.

        Parameters:

          number (string)
                  phone number to which the SMS will be sent

          message (string)
                  the message to be sent.

        Returns True on success, otherwise False.
        """
        smsCommand = ('am start -a android.intent.action.SENDTO ' +
                      '-d sms:%s --es sms_body "%s"' +
                      ' --ez exit_on_sent true')  % (number, message)
        status, out, err = self.shellSOE(smsCommand)
        if status != 0:
            _logFailedCommand("sms", smsCommand, status, out, err)
            return False
        _adapterLog("SMS command returned %s" % (out + err,))
        time.sleep(2)
        if 'talk' in self.topWindow():
            _adapterLog("Messaging app is Hangouts")
            self.pressKey("KEYCODE_ENTER")
            time.sleep(1)
            self.pressKey("KEYCODE_BACK")
            time.sleep(1)
            self.pressKey("KEYCODE_BACK")
        else:
            self.pressKey("KEYCODE_DPAD_RIGHT")
            time.sleep(1)
            self.pressKey("KEYCODE_ENTER")
        return True

    def supportsView(self):
        """
        Check if connected device supports reading view data.

        View data is needed by refreshView(), view(), verifyText() and
        waitText(). It is produced by Android window dump.

        Returns True if view data can be read, otherwise False.
        """
        if self._supportsView == None:
            try:
                self.existingConnection().recvViewData()
                self._supportsView = True
            except AndroidConnectionError:
                self._supportsView = False
        return self._supportsView

    def systemProperty(self, propertyName):
        """
        Returns Android Monkey Device properties, such as
        "clock.uptime", refer to Android Monkey documentation.
        """
        return self.existingConnection().recvVariable(propertyName)

    def tapId(self, viewItemId, **tapKwArgs):
        """
        Find an item with given id from the latest view, and tap it.
        """
        assert self._lastView != None, "View required."
        items = self._lastView.findItemsById(viewItemId, count=1, onScreen=True)
        if len(items) > 0:
            return self.tapItem(items[0], **tapKwArgs)
        else:
            _adapterLog("tapItemById(%s): no items found" % (viewItemId,))
            return False

    def tapText(self, text, partial=False, **tapKwArgs):
        """
        Find an item with given text from the latest view, and tap it.

        Parameters:

          partial (boolean, optional):
                  refer to verifyText documentation. The default is
                  False.

          tapPos (pair of floats (x, y)):
                  refer to tapItem documentation.

          long, hold, count, delayBetweenTaps (optional):
                  refer to tap documentation.

        Returns True if successful, otherwise False.
        """
        assert self._lastView != None, "View required."
        items = self._lastView.findItemsByText(text, partial=partial, count=1, onScreen=True)
        if len(items) == 0: return False
        return self.tapItem(items[0], **tapKwArgs)

    def topApp(self):
        """
        Returns the name of the top application.
        """
        if not self._conn:
            return None
        else:
            return self._conn.recvTopAppWindow()[0]

    def topWindow(self):
        """
        Returns the name of the top window.
        """
        # the top window may be None during transitions, therefore
        # retry a couple of times if necessary.
        if not self._conn:
            return None
        timeout = 0.5
        pollDelay = 0.2
        start = time.time()
        tw = self.existingConnection().recvTopAppWindow()[1]
        while tw == None and (time.time() - start < timeout):
            time.sleep(pollDelay)
            tw = self.existingConnection().recvTopAppWindow()[1]
        return tw

    def topWindowStack(self):
        """
        Returns window names in the stack of the top fullscreen application.

        The topmost window is the last one in the list.
        """
        return self.existingConnection().recvTopWindowStack()

    def uninstall(self, apkname, keepData=False):
        """
        Uninstall a package from the device.

        Parameters:
          package (string):
                  the package to be uninstalled.

          keepData (boolean, optional):
                  keep app data and cache.
                  Corresponds to adb uninstall "-k".
                  The default is False.

        Returns True on success, otherwise False.

        Example:
          d.uninstall("com.android.python27")
        """
        if self._conn:
            return self._conn.uninstall(apkname, keepData)
        else:
            return False

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
        return self._lastView.findItemsByText(text, partial=partial, count=1, onScreen=True) != []

    def view(self):
        """
        Returns the last view (the most recently refreshed view).
        """
        return self._lastView

    def waitText(self, text, partial=False, **waitKwArgs):
        """
        Wait until text appears in any view item.

        Parameters:

          text (string):
                text to be waited for.

          partial (boolean, optional):
                refer to verifyText. The default is False.

          waitTime, pollDelay, beforeRefresh, afterRefresh (optional):
                refer to wait documentation.

        Returns True if text appeared within given time limit,
        otherwise False.

        Updates the last view.
        """
        return self.wait(self.refreshView,
                         self.verifyText, (text,), {'partial': partial},
                         **waitKwArgs)

    def wake(self):
        """
        Force the device to wake up.
        """
        return self.existingConnection().sendWake()

    def _loadDeviceAndTestINIs(self, homeDir, deviceName, iniFile):
        if deviceName != None:
            _deviceIniFilename = homeDir + os.sep + "etc" + os.sep + deviceName + ".ini"
            self.loadConfig(_deviceIniFilename, override=True, level="device")
        if iniFile:
            self.loadConfig(iniFile, override=True, level="test")

class Ini:
    """
    Container for device configuration loaded from INI files.

    INI file syntax:
    [section1]
    key1 = value1
    ; commented = out
    # commented = out
    """
    def __init__(self, iniFile=None):
        """
        Initialise the container, optionally with an initial configuration.

        Parameters:

          iniFile (file object, optional):
                  load the initial configuration from iniFile.
                  The default is None: start with empty configuration.
        """
        # _conf is a dictionary:
        # (section, key) -> value
        self._conf = {}
        if iniFile:
            self.addFile(iniFile)

    def addFile(self, iniFile, override=True):
        """
        Add values from a file to the current configuration.

        Parameters:

          iniFile (file object):
                  load values from this file object.

          override (boolean, optional):
                  If True, loaded values override existing values.
                  Otherwise, only currently undefined values are
                  loaded. The default is True.
        """
        for line in iniFile:
            line = line.strip()
            if line.startswith('[') and line.endswith(']'):
                section = line[1:-1].strip()
            elif line.startswith(";") or line.startswith("#"):
                continue
            elif '=' in line:
                key, value = line.split('=', 1)
                if override or (section, key.strip()) not in self._conf:
                    self._conf[(section, key.strip())] = value.strip()

    def sections(self):
        """
        Returns list of sections in the current configuration.
        """
        return list(set([k[0] for k in self._conf.keys()]))

    def keys(self, section):
        """
        Returns list of keys in a section in the current configuration.

        Parameters:

          section (string):
                  the name of the section.
        """
        return [k[1] for k in self._conf.keys() if k[0] == section]

    def dump(self):
        """
        Returns the current configuration as a single string in the
        INI format.
        """
        lines = []
        for section in sorted(self.sections()):
            lines.append("[%s]" % (section,))
            for key in sorted(self.keys(section)):
                lines.append("%-16s = %s" % (key, self._conf[(section, key)]))
            lines.append("")
        return "\n".join(lines)

    def set(self, section, key, value):
        """
        Set new value for a key in a section.

        Parameters:

          section, key (strings):
                  the section, the key.

          value (string):
                  the new value. If not string already, it will be
                  converted to string, and it will be loaded as a
                  string when loaded from file object.
        """
        self._conf[(section, key)] = str(value)

    def value(self, section, key, default=""):
        """
        Returns the value (string) associated with a key in a section.

        Parameters:

          section, key (strings):
                  the section and the key.

          default (string, optional):
                  the default value to be used and stored if there is
                  no value associated to the key in the section. The
                  default is the empty string.

        Reading a value of an undefined key in an undefined section
        adds the key and the section to the configuration with the
        returned (the default) value. This makes all returned values
        visible in dump().
        """
        if not (section, key) in self._conf:
            self._conf[(section, key)] = default
        return self._conf[(section, key)]

# For backward compatibility, someone might be using old _DeviceConf
_DeviceConf = Ini

class ViewItem(fmbtgti.GUIItem):
    """
    ViewItem holds the information of a single GUI element.
    """
    def __init__(self, className, code, indent, properties, parent, rawProps, dumpFilename, displayToScreen):
        self._p = properties
        self._parent = parent
        self._className = className
        self._code = code
        self._indent = indent
        self._children = []
        self._parentsVisible = True
        self._rawProps = ""
        if not "scrolling:mScrollX" in self._p:
            self._p["scrolling:mScrollX"] = 0
            self._p["scrolling:mScrollY"] = 0
        fmbtgti.GUIItem.__init__(self, className, self._calculateBbox(displayToScreen), dumpFilename)
    def addChild(self, child):
        child._parentsVisible = self.visibleBranch()
        self._children.append(child)
    def _calculateBbox(self, displayToScreen):
        if "layout:getLocationOnScreen_x()" in self._p:
            left = int(self._p["layout:getLocationOnScreen_x()"])
            top = int(self._p["layout:getLocationOnScreen_y()"])
        elif "layout:mLeft" in self._p:
            left = int(self._p["layout:mLeft"])
            top = int(self._p["layout:mTop"])
            parent = self._parent
            while parent:
                pp = parent._p
                left += int(pp["layout:mLeft"]) - int(pp["scrolling:mScrollX"])
                top += int(pp["layout:mTop"]) - int(pp["scrolling:mScrollY"])
                parent = parent._parent
        else:
            raise ValueError("bounding box not found, layout fields missing")
        height = int(self._p["layout:getHeight()"])
        width = int(self._p["layout:getWidth()"])
        screenLeft, screenTop = displayToScreen(left, top)
        screenRight, screenBottom = displayToScreen(left + width, top + height)
        return (screenLeft, screenTop, screenRight, screenBottom)
    def children(self):   return self._children
    def className(self):  return self._className
    def code(self):       return self._code
    def indent(self):     return self._indent
    def id(self):         return self.property("mID")
    def parent(self):     return self._parent
    def properties(self): return self._p
    def property(self, propertyName):
        return self._p.get(propertyName, None)
    def visibleBranch(self):
        """Returns True if this item and all items containing this are visible
        up to the root node"""
        return self._parentsVisible and self.visible()
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
        if "text:mText" in self._p:
            text = ", text='%s'" % (self.text(),)
        else:
            text = ""
        return ("ViewItem(className='%s', id=%s, bbox=%s%s)"  % (
                self._className, self.id(), self.bbox(), text))

class View(object):
    """
    View provides interface to screen dumps from Android. It parses
    the dump to a hierarchy of ViewItems. find* methods enable searching
    for ViewItems based on their properties.
    """
    def __init__(self, screenshotDir, serialNumber, dump, displayToScreen=None,
                 itemOnScreen=None, intCoords=None):
        self.screenshotDir = screenshotDir
        self.serialNumber = serialNumber
        self._viewItems = []
        self._errors = []
        self._lineRegEx = re.compile("(?P<indent>\s*)(?P<class>[\w.$]+)@(?P<id>[0-9A-Fa-f]{4,8} )(?P<properties>.*)")
        self._olderAndroidLineRegEx = re.compile("(?P<indent>\s*)(?P<class>[\w.$]+)@(?P<id>\w)(?P<properties>.*)")
        self._propRegEx = re.compile("(?P<prop>(?P<name>[^=]+)=(?P<len>\d+),)(?P<data>[^\s]* ?)")
        self._dump = dump
        self._rawDumpFilename = self.screenshotDir + os.sep + fmbtgti._filenameTimestamp() + "-" + self.serialNumber + ".view"
        file(self._rawDumpFilename, "w").write(self._dump)
        if displayToScreen == None:
            displayToScreen = lambda x, y: (x, y)
        if itemOnScreen == None:
            itemOnScreen = lambda item: True
        self._itemOnScreen = itemOnScreen
        if intCoords == None:
            intCoords = lambda x, y: (int(x), int(y))
        self._intCoords = intCoords
        try:
            self._parseDump(dump, self._rawDumpFilename, displayToScreen)
        except Exception, e:
            self._errors.append((-1, "", "Parser error"))

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
        return "id=%s cls=%s text=%s bbox=%s vis=%s" % (
            i.id(), i.className(), t, i.bbox(), i.visibleBranch())
    def filename(self):
        return self._rawDumpFilename
    def findItems(self, comparator, count=-1, searchRootItem=None, searchItems=None, onScreen=False):
        foundItems = []
        if count == 0: return foundItems
        if searchRootItem != None:
            # find from searchRootItem and its children
            if comparator(searchRootItem) and (
                    not onScreen or
                    searchRootItem.visibleBranch() and self._itemOnScreen(searchRootItem)):
                foundItems.append(searchRootItem)
            for c in searchRootItem.children():
                foundItems.extend(self.findItems(comparator, count=count-len(foundItems), searchRootItem=c, onScreen=onScreen))
        else:
            if searchItems != None:
                # find from listed items only
                searchDomain = searchItems
            else:
                # find from all items
                searchDomain = self._viewItems
            for i in searchDomain:
                if comparator(i) and (
                        not onScreen or
                        i.visibleBranch() and self._itemOnScreen(i)):
                    foundItems.append(i)
                    if count > 0 and len(foundItems) >= count:
                        break
        return foundItems

    def findItemsByText(self, text, partial=False, count=-1, searchRootItem=None, searchItems=None, onScreen=False):
        """
        Returns list of ViewItems with given text.
        """
        if partial:
            c = lambda item: (
                item.properties().get("text:mText", "").find(text) != -1 )
        else:
            c = lambda item: (
                item.properties().get("text:mText", None) == text )
        return self.findItems(c, count=count, searchRootItem=searchRootItem, searchItems=searchItems, onScreen=onScreen)

    def findItemsById(self, id, count=-1, searchRootItem=None, searchItems=None, onScreen=False):
        """
        Returns list of ViewItems with given id.
        """
        c = lambda item: item.properties().get("mID", "") == id
        return self.findItems(c, count=count, searchRootItem=searchRootItem, searchItems=searchItems, onScreen=onScreen)

    def findItemsByClass(self, className, partial=True, count=-1, searchRootItem=None, searchItems=None, onScreen=False):
        """
        Returns list of ViewItems with given class.
        """
        if partial: c = lambda item: item.className().find(className) != -1
        else: c = lambda item: item.className() == className
        return self.findItems(c, count=count, searchRootItem=searchRootItem, searchItems=searchItems, onScreen=onScreen)

    def findItemsByIdAndClass(self, id, className, partial=True, count=-1, searchRootItem=None, searchItems=None, onScreen=False):
        """
        Returns list of ViewItems with given id and class.
        """
        idOk = self.findItemsById(id, count=-1, searchRootItem=searchRootItem, onScreen=onScreen)
        return self.findItemsByClass(className, partial=partial, count=count, searchItems=idOk, onScreen=onScreen)

    def findItemsByRawProps(self, s, count=-1, searchRootItem=None, searchItems=None, onScreen=False):
        """
        Returns list of ViewItems with given string in properties.
        """
        c = lambda item: item._rawProps.find(s) != -1
        return self.findItems(c, count=count, searchRootItem=searchRootItem, searchItems=searchItems, onScreen=onScreen)

    def findItemsByPos(self, (x, y), count=-1, searchRootItem=None, searchItems=None, onScreen=False):
        """
        Returns list of ViewItems whose bounding box contains the position.

        Items are listed in ascending order based on area. They may
        or may not be from the same branch in the widget hierarchy.
        """
        x, y = self._intCoords((x, y))
        c = lambda item: (item.bbox()[0] <= x <= item.bbox()[2] and item.bbox()[1] <= y <= item.bbox()[3])
        items = self.findItems(c, count=count, searchRootItem=searchRootItem, searchItems=searchItems, onScreen=onScreen)
        # sort from smallest to greatest area
        area_items = [((i.bbox()[2] - i.bbox()[0]) * (i.bbox()[3] - i.bbox()[1]), i) for i in items]
        return [i for _, i in sorted(area_items)]

    def save(self, fileOrDirName):
        """
        Save view dump to a file.
        """
        shutil.copy(self._rawDumpFilename, fileOrDirName)

    def _parseDump(self, dump, rawDumpFilename, displayToScreen):
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
        last_line = set(["DONE", "DONE."])

        for lineIndex, line in enumerate(dump.splitlines()):
            if line in last_line:
                break

            # separate indent, class and properties for each GUI object
            # TODO: branch here according to self._androidVersion
            matcher = self._lineRegEx.match(line)

            if not matcher:
                # FIXME: this hack falls back to old format,
                # should branch according to self._androidVersion!
                matcher = self._olderAndroidLineRegEx.match(line)
                if not matcher:
                    self._errors.append((lineIndex + 1, line, "illegal line"))
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
                if not propMatch:
                    self._errors.append((lineIndex, line,
                                         "property parse error"))
                    break

                name = propMatch.group("name")
                if not name:
                    self._errors.append(
                        (lineIndex, line,
                         'illegal property name "%s"' % (name,)))
                    break

                try:
                    dataLength = int(propMatch.group("len"))
                except ValueError:
                    self._errors.append(
                        (lineIndex, line,
                         'illegal length (int) "%s"' % (propMatch.group("len"),)))
                    break

                data = propMatch.group("data")
                dataStart = index + propMatch.start("data")

                if len(data) < dataLength:
                    if not data:
                        self._errors.append(
                            (lineIndex, line,
                             'property "%s": data missing, expected %s' % (name, dataLength, len(data))))
                        break

                properties[name] = propertiesData[dataStart:dataStart + dataLength]
                index = dataStart + dataLength + 1

            try:
                vi = ViewItem(matcher.group("class"), matcher.group("id"), indent, properties, parent, matcher.group("properties"), self._rawDumpFilename, displayToScreen)
                self._viewItems.append(vi)
                if parent:
                    parent.addChild(self._viewItems[-1])
            except Exception, e:
                self._errors.append(
                    (lineIndex, line,
                     "creating view item failed (%s: %s)" % (type(e), e)))
        return self._viewItems

    def __str__(self):
        return 'View(items=%s, dump="%s")' % (
            len(self._viewItems), self._rawDumpFilename)

class _AndroidDeviceConnection(fmbtgti.GUITestConnection):
    """
    Connection to the Android Device being tested.

    """
    _m_host = os.getenv("FMBTANDROID_ADB_FORWARD_HOST", 'localhost')
    _m_port = int(os.getenv("FMBTANDROID_ADB_FORWARD_PORT", random.randint(20000, 29999)))
    _w_host = _m_host

    def __init__(self, serialNumber, **kwArgs):
        fmbtgti.GUITestConnection.__init__(self)
        self._serialNumber = serialNumber
        self._adbPort = kwArgs.pop("adbPort", None)
        self._monkeyPortForward = kwArgs.pop(
            "adbForwardPort", _AndroidDeviceConnection._m_port)
        self._windowPortForward = kwArgs.pop(
            "windowPortForward", self._monkeyPortForward + 1)
        self._stopOnError = kwArgs.pop("stopOnError", True)
        self._monkeyOptions = kwArgs.pop("monkeyOptions", [])
        self._screencapArgs = kwArgs.pop("screencapArgs", [])
        self._screencapFormat = kwArgs.pop("screencapFormat", "raw")
        self.setScreenToDisplayCoords(
            kwArgs.pop("screenToDisplay", lambda x, y: (x, y)))
        self.setDisplayToScreenCoords(
            kwArgs.pop("displayToScreen", lambda x, y: (x, y)))
        if kwArgs:
            raise TypeError('_AndroidDeviceConnection.__init__() got an '
                            'unexpected keyword argument %s=%s' % (
                kwArgs.keys()[0], repr(kwArgs[kwArgs.keys()[0]])))

        self._detectFeatures()
        self._emulatorSocket = None
        try:
            self._resetMonkey()
            self._resetWindow()

        finally:
            # Next _AndroidDeviceConnection instance will use different ports
            _AndroidDeviceConnection._m_port += 100

    def __del__(self):
        try: self._monkeySocket.close()
        except: pass
        try: self._emulatorSocket.close()
        except: pass

    def settings(self):
        """Returns restorable property values"""
        rv = {
            "adbPort": self._adbPort,
            "adbForwardPort": self._monkeyPortForward,
            "stopOnError": self._stopOnError,
            "monkeyOptions": self._monkeyOptions,
            "screencapArgs": self._screencapArgs,
            "screencapFormat": self._screencapFormat,
            "screenToDisplay": self._screenToDisplay,
            "displayToScreen": self._displayToScreen,
        }
        return rv

    def target(self):
        return self._serialNumber

    def _cat(self, remoteFilename):
        fd, filename = tempfile.mkstemp("fmbtandroid-cat-")
        os.close(fd)
        self._runAdb(["pull", remoteFilename, filename], 0)
        contents = file(filename).read()
        os.remove(filename)
        return contents

    def _runAdb(self, adbCommand, expectedExitStatus=0, timeout=None):
        if not self._stopOnError:
            expect = None
        else:
            expect = expectedExitStatus
        if self._adbPort:
            adbPortArgs = ["-P", str(self._adbPort)]
        else:
            adbPortArgs = []
        command = ["adb", "-s", self._serialNumber] + adbPortArgs
        if type(adbCommand) == list or type(adbCommand) == tuple:
            command.extend(adbCommand)
        else:
            command.append(adbCommand)
        return _run(command, expectedExitStatus=expect, timeout=timeout)

    def _emulatorCommand(self, command):
        if not self._emulatorSocket:
            try:
                emulatorPort = int(re.findall("emulator-([0-9]*)", self._serialNumber)[0])
            except (IndexError, ValueError):
                raise FMBTAndroidError("emulator port detection failed")
            try:
                self._emulatorSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self._emulatorSocket.connect(("localhost", emulatorPort))
            except socket.error, e:
                raise FMBTAndroidError("connecting to the emulator failed: %s" % (e,))
        self._emulatorSocket.sendall(command + "\n")
        data = self._emulatorSocket.recv(4096)
        try:
            data = data.splitlines()[-1].strip()
        except IndexError:
            raise FMBTAndroidError("no response from the emulator")
        if data.startswith("OK"):
            return True, data
        else:
            return False, data

    def _runSetupCmd(self, cmd, expectedExitStatus = 0):
        _adapterLog('setting up connections: "%s"' % (cmd,))
        try:
            self._runAdb(cmd, expectedExitStatus)
        except (FMBTAndroidRunError, AndroidDeviceNotFound), e:
            _adapterLog("connection setup problem: %s" % (e,))
            return False
        return True

    def _detectFeatures(self):
        # check supported features
        outputLines = self._runAdb(["shell", "getprop", "ro.build.version.release"])[1].splitlines()
        if len(outputLines) >= 1:
            self._platformVersion = outputLines[0].strip().split("=")[-1]
        else:
            self._platformVersion = "N/A"

        outputLines = self._runAdb(["shell", "id"])[1].splitlines()
        if len(outputLines) == 1 and "uid=0" in outputLines[0]:
            self._shellUid0 = True
        else:
            self._shellUid0 = False

        outputLines = self._runAdb(["shell", "su", "root", "id"])[1].splitlines()
        if len(outputLines) == 1 and "uid=0" in outputLines[0]:
            self._shellSupportsSu = True
        else:
            self._shellSupportsSu = False

        outputLines = self._runAdb(["shell", "tar"])[1].splitlines()
        if len(outputLines) == 1 and "bin" in outputLines[0]:
            self._shellSupportsTar = False
        else:
            self._shellSupportsTar = True

    def _resetWindow(self):
        setupCommands = [["shell", "service" , "call", "window", "1", "i32", "4939"],
                         ["forward", "tcp:"+str(self._windowPortForward), "tcp:4939"]]
        for c in setupCommands:
            self._runSetupCmd(c)

    def _resetMonkey(self, timeout=3, pollDelay=.25):
        tryKillingMonkeyOnFailure = 1
        failureCountSinceKill = 0
        endTime = time.time() + timeout
        if self._shellUid0:
            monkeyLaunch = ["monkey"]
        elif self._shellSupportsSu:
            monkeyLaunch = ["su", "root", "monkey"]
        else:
            monkeyLaunch = ["monkey"]

        if self._monkeyOptions:
            monkeyLaunch += self._monkeyOptions

        while time.time() < endTime:
            monkeyShellCmd = (" ".join(monkeyLaunch + ["--port", "1080"]) +
                              " >/sdcard/fmbtandroid.monkey.outerr 2>&1")
            _adapterLog('launching monkey: adb shell "%s"' % (monkeyShellCmd,))
            self._runAdb(["shell", monkeyShellCmd], expectedExitStatus=None)
            time.sleep(pollDelay)
            if not self._runSetupCmd(["forward", "tcp:"+str(self._monkeyPortForward), "tcp:1080"]):
                time.sleep(pollDelay)
                failureCountSinceKill += 1
                continue
            try:
                self._monkeySocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self._monkeySocket.connect((self._m_host, self._monkeyPortForward))
                self._monkeySocket.setblocking(0)
                self._monkeySocket.settimeout(1.0)
                _ping = self._monkeyCommand("getvar build.version.release", retry=0)[1]
                if len(_ping) > 0:
                    self._monkeySocket.settimeout(5.0)
                    return True
            except Exception, e:
                _, monkeyOutput, _ = self._runAdb(["shell", "cat /sdcard/fmbtandroid.monkey.outerr"])
                if "Error: Unknown option:" in monkeyOutput:
                    uo = [l for l in monkeyOutput.splitlines() if "Error: Unknown option:" in l][0].split(":")[-1].strip()
                    _adapterLog('detected an unknown option for monkey: "%s". Disabling it.' % (uo,))
                    try:
                        monkeyLaunch.remove(uo)
                    except ValueError:
                        pass
                    continue
                _adapterLog("monkey connection failed, output: %s" % (monkeyOutput,))
                failureCountSinceKill += 1
            time.sleep(pollDelay)
            if failureCountSinceKill > 2 and tryKillingMonkeyOnFailure > 0:
                if self._shellSupportsSu:
                    self._runSetupCmd(["shell", "su", "root", "pkill", "monkey"])
                else:
                    self._runSetupCmd(["shell", "pkill", "monkey"])
                tryKillingMonkeyOnFailure -= 1
                failureCountSinceKill = 0
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
            try: self._monkeySocket.close()
            except: pass

            if retry > 0:
                self._resetMonkey()
                return self._monkeyCommand(command, retry=retry-1)
            else:
                raise AndroidConnectionError('Android monkey socket connection lost while sending command "%s"' % (command,))

    def install(self, filename, lock, reinstall, downgrade,
                sdcard, algo, key, iv):
        cmd = ["install"]
        if lock:
            cmd.append("-l")
        if reinstall:
            cmd.append("-r")
        if downgrade:
            cmd.append("-d")
        if sdcard:
            cmd.append("-s")
        if algo != None:
            cmd.extend(["--algo", algo])
        if key != None:
            cmd.extend(["--key", key])
        if iv != None:
            cmd.extend(["--iv", iv])
        cmd.append(filename)
        status, output, error = self._runAdb(cmd, [0, 1])
        if "Success" in output:
            return True
        else:
            return output + "\n" + error

    def uninstall(self, apkname, keepData):
        cmd = ["uninstall"]
        if keepData:
            cmd.append("-k")
        cmd.append(apkname)
        status, output, error = self._runAdb(cmd)
        if "Success" in output:
            return True
        else:
            return False

    def reboot(self, reconnect, firstBootAfterFlashing, timeout):
        if firstBootAfterFlashing:
            self._runAdb("root")
            time.sleep(2)
            self._runAdb(["shell", "rm", "/data/data/com.android.launcher/shared_prefs/com.android.launcher2.prefs.xml"])

        self._runAdb("reboot")
        _adapterLog("rebooting " + self._serialNumber)

        if reconnect:
            time.sleep(2)
            endTime = time.time() + timeout
            status, _, _ = self._runAdb("wait-for-device", expectedExitStatus=None, timeout=timeout)
            if status != 0:
                raise AndroidDeviceNotFound('"timeout %s adb wait-for-device" status %s' % (timeout, status))
            self._detectFeatures()
            while time.time() < endTime:
                try:
                    if self._resetMonkey(timeout=1, pollDelay=1):
                        break
                except AndroidConnectionError:
                    pass
                time.sleep(1)
            else:
                msg = "reboot: reconnecting to " + self._serialNumber + " failed"
                _adapterLog(msg)
                raise AndroidConnectionError(msg)
            self._resetWindow()
        return True

    def recvVariable(self, variableName):
        ok, value = self._monkeyCommand("getvar " + variableName)
        if ok: return value
        else:
            # LOG: getvar variableName failed
            return None

    def recvScreenSize(self):
        _, output, _ = self._runAdb(["shell", "dumpsys", "display"], 0)
        try:
            # parse default display properties
            ddName, ddWidth, ddHeight, ddWdpi, ddHdpi = re.findall(
                r'DisplayDeviceInfo\{[^,]*"([^"]*)"[:,] ([0-9]*) x ([0-9]*),.*, ([0-9.]*) x ([0-9.]*) dpi,.*FLAG_DEFAULT_DISPLAY.*\}',
                output)[0]
        except (IndexError, ValueError), e:
            _adapterLog('recvScreenSize: cannot read size from "%s"' %
                        (output,))
            raise FMBTAndroidError('cannot read screen size from dumpsys')
        return int(ddWidth), int(ddHeight)

    def recvDefaultViewportSize(self):
        _, output, _ = self._runAdb(["shell", "dumpsys", "display"], 0)
        try:
            w, h = re.findall("mDefaultViewport=DisplayViewport\{.*deviceWidth=([0-9]*), deviceHeight=([0-9]*)\}", output)[0]
            width = int(w)
            height = int(h)
        except (IndexError, ValueError), e:
            _adapterLog('recvScreenSize: cannot read size from "%s"' %
                        (output,))
            raise FMBTAndroidError('cannot read screen size from dumpsys')
        return width, height

    def recvCurrentDisplayOrientation(self):
        _, output, _ = self._runAdb(["shell", "dumpsys", "display"], 0)
        s = re.findall("mCurrentOrientation=([0-9])", output)
        if s:
            return int(s[0])
        else:
            return None

    def recvDisplayPowered(self):
        _, output, _ = self._runAdb(["shell", "dumpsys", "power"], 0)
        s = re.findall("Display Power: state=(OFF|ON)", output)
        if s:
            return s[0] == "ON"
        else:
            return None

    def recvShowingLockscreen(self):
        _, output, _ = self._runAdb(["shell", "dumpsys", "window"], 0)
        s = re.findall("mShowingLockscreen=(true|false)", output)
        if s:
            if s[0] == "true":
                return True
            else:
                return False
        else:
            return None

    def recvLastAccelerometer(self):
        _, output, _ = self._runAdb(["shell", "dumpsys", "sensorservice"], 0)
        s = re.findall("3-axis Accelerometer.*last=<([- .0-9]*),([- .0-9]*),([- .0-9]*)>", output)
        try:
            rv = tuple([float(d) for d in s[0]])
        except (IndexError, ValueError):
            rv = (None, None, None)
        return rv

    def sendAcceleration(self, abc):
        """abc is a tuple of 1, 2 or 3 floats, new accelerometer readings"""
        try:
            self._emulatorCommand("sensor set acceleration %s" %
                                  (":".join([str(value) for value in abc]),))
        except FMBTAndroidError, e:
            raise FMBTAndroidError(
                "accelerometer can be set only on emulator (%s)" % (e,))
        return True

    def sendAccelerometerRotation(self, value):
        if value:
            sendValue = "i:1"
        else:
            sendValue = "i:0"
        try:
            self._runAdb(["shell", "content", "insert",
                          "--uri", "content://settings/system",
                          "--bind", "name:s:accelerometer_rotation",
                          "--bind", "value:" + sendValue])
        except Exception:
            return False
        return True

    def sendDeviceLog(self, msg, priority, tag):
        self._runAdb(["shell", "log", "-p", priority, "-t", tag, msg])
        return True

    def sendUserRotation(self, rotation):
        allowedRotations = [ROTATION_0, ROTATION_90, ROTATION_180, ROTATION_270]
        if not rotation in allowedRotations:
            raise ValueError("invalid rotation: %s, use one of %s" %
                             (allowedRotations,))
        sendValue = "i:%s" % (rotation,)
        try:
            self._runAdb(["shell", "content", "insert",
                          "--uri", "content://settings/system",
                          "--bind", "name:s:user_rotation",
                          "--bind", "value:" + sendValue])
        except Exception:
            return False
        return True

    def recvTopAppWindow(self):
        _, output, _ = self._runAdb(["shell", "dumpsys", "window"], 0)
        if self._platformVersion >= "4.2":
            s = re.findall("mCurrentFocus=Window\{(#?[0-9A-Fa-f]{4,16})( [^ ]*)? (?P<winName>[^}]*)\}", output)
        else:
            s = re.findall("mCurrentFocus=Window\{(#?[0-9A-Fa-f]{4,16}) (?P<winName>[^ ]*) [^ ]*\}", output)
        if s and len(s[-1][-1].strip()) > 1:
            topWindowName = s[-1][-1]
            if len(s) > 0:
                _adapterLog('recvTopAppWindow warning: several mCurrentFocus windows: "%s"'
                            % ('", "'.join([w[-1] for w in s]),))
        else: topWindowName = None

        if self._platformVersion >= "4.2":
            s = re.findall("mFocusedApp=AppWindowToken.*ActivityRecord\{#?[0-9A-Fa-f]*( [^ ]*)? (?P<appName>[^} ]*)[^}]*\}", output)
        else:
            s = re.findall("mFocusedApp=AppWindowToken.*ActivityRecord\{#?[0-9A-Fa-f]*( [^ ]*)? (?P<appName>[^}]*)\}", output)
        if s and len(s[0][-1].strip()) > 1:
            topAppName = s[0][-1].strip()
        else:
            topAppName = None
        return topAppName, topWindowName

    def recvTopWindowStack(self):
        rv = None
        _, output, _ = self._runAdb(["shell", "dumpsys", "window"], 0)
        # Find out top window id.
        s = re.findall("mTopFullscreenOpaqueWindowState=Window\{(?P<winId>[0-9A-Fa-f]*) ", output)
        if s:
            win_id = s[0]
            # Find out top task id (cannot directly rely on mFocusedApp,
            # it may be outdated)
            t = re.findall(r"AppWindowToken\{[0-9A-Fa-f]* token=Token\{[0-9A-Fa-f]* ActivityRecord\{[0-9A-Fa-f]* [^ ]* [^ ]* t(?P<taskId>[0-9]*)\}\}\}:[ \r\n]*windows=\[Window\{%s " % (win_id,), output)
            if t:
                task_id = t[0]
                # Find window stack of the task
                stack_line = re.findall(r"(\{taskId=%s appTokens=\[.*)" % (task_id,), output)
                if stack_line:
                    # Find names of windows on the stack
                    rv = re.findall(r"ActivityRecord\{[0-9A-Fa-f]* [^ ]* ([^ ]*) t%s\}" % (task_id,), stack_line[0])
        return rv

    def sendMonkeyScript(self, eventLines):
        monkey_script = "type= raw events\ncount= %s\nspeed= 1.0\nstart data >>\n%s" % (
            len(eventLines.splitlines()), eventLines)
        remote_filename = "/sdcard/fmbtandroid.%s.monkey_script" % (fmbt.formatTime("%s.%f"),)
        cmd = ["shell", "echo \"" + monkey_script + "\" > " + remote_filename
               + "; monkey -f" + remote_filename + " 1 ; rm -f " +
               remote_filename]
        self._runAdb(cmd)

    def sendMonkeyPinchZoom(self,
                  pt1XStart, pt1YStart, pt1XEnd, pt1YEnd,
                  pt2XStart, pt2YStart, pt2XEnd, pt2YEnd, count):
        self.sendMonkeyScript("capturePinchZoom(%s,%s,%s,%s, %s,%s,%s,%s, %s)" % (
                  pt1XStart, pt1YStart, pt1XEnd, pt1YEnd,
                  pt2XStart, pt2YStart, pt2XEnd, pt2YEnd, count))

    def sendSwipe(self, x1, y1, x2, y2):
        _x1, _y1 = self._screenToDisplay(x1, y1)
        _x2, _y2 = self._screenToDisplay(x2, y2)
        self._runAdb(["shell", "input", "swipe",
                      str(_x1), str(_y1), str(_x2), str(_y2)])
        return True

    def sendTap(self, xCoord, yCoord):
        xCoord, yCoord = self._screenToDisplay(xCoord, yCoord)
        return self._monkeyCommand("tap " + str(xCoord) + " " + str(yCoord))[0]

    def sendKeyUp(self, key, modifiers=[]):
        rv = self._monkeyCommand("key up " + key)[0]
        for m in reversed(modifiers):
            rv &= self._monkeyCommand("key up " + m)[0]
        return rv

    def sendKeyDown(self, key, modifiers=[]):
        rv = True
        for m in modifiers:
            rv &= self._monkeyCommand("key down " + m)[0]
        rv &= self._monkeyCommand("key down " + key)[0]
        return rv

    def sendTouchUp(self, xCoord, yCoord):
        xCoord, yCoord = self._screenToDisplay(xCoord, yCoord)
        return self._monkeyCommand("touch up " + str(xCoord) + " " + str(yCoord))[0]

    def sendTouchDown(self, xCoord, yCoord):
        xCoord, yCoord = self._screenToDisplay(xCoord, yCoord)
        return self._monkeyCommand("touch down " + str(xCoord) + " " + str(yCoord))[0]

    def sendTouchMove(self, xCoord, yCoord):
        xCoord, yCoord = self._screenToDisplay(xCoord, yCoord)
        return self._monkeyCommand("touch move " + str(xCoord) + " " + str(yCoord))[0]

    def sendTrackBallMove(self, dx, dy):
        dx, dy = self._screenToDisplay(dx, dy)
        return self._monkeyCommand("trackball " + str(dx) + " " + str(dy))[0]

    def sendPress(self, key, modifiers=[]):
        if not modifiers:
            return self._monkeyCommand("press " + key)[0]
        else:
            rv = True
            for m in modifiers:
                rv &= self.sendKeyDown(m)
            # A press with modifiers must be sent using "key down" and "key up"
            # primitives, not with "press".
            rv &= self.sendKeyDown(key)
            rv &= self.sendKeyUp(key)
            for m in reversed(modifiers):
                rv &= self.sendKeyUp(m)
            return rv

    def sendType(self, text):
        for lineIndex, line in enumerate(text.split('\n')):
            if lineIndex > 0: self.sendPress("KEYCODE_ENTER")
            for wordIndex, word in enumerate(line.split(' ')):
                if wordIndex > 0: self.sendPress("KEYCODE_SPACE")
                if len(word) > 0 and not self._monkeyCommand("type " + word)[0]:
                    _adapterLog('sendType("%s") failed when sending word "%s"' %
                                (text, word))
                    return False
        return True

    def sendWake(self):
        return self._monkeyCommand("wake")[0]

    def setRawScreenshotFormat(self, fmt):
        """DEPRECATED - use setScreencapFormat("raw") instead.
        Set fmt to True or tuple (depth, colorspace) to fetch
        screenshots from the device without converting them to PNG
        on the device. The conversion will be done on host, which
        is often much faster. True is autodetect.
        """
        if fmt == True:
            return self.setScreencapFormat("raw")
        elif fmt == False:
            return self.setScreencapFormat("png")
        else:
            return self.setScreencapFormat(fmt)

    def setScreencapFormat(self, fmt):
        """
        Set screencap tool output format.

        Parameters:
          fmt (string or tuple):
                  Valid formats are:
                  "png" - save screenshot as PNG on device (the default).
                  "raw" - output screenshot in raw format from device,
                          PNG conversion takes place on host.
                  (bits_per_channel, colorspace) - same as "raw", but
                          use given raw data order instead of autodetect.
                          Example: setScreencapFormat((8, "RGBA"))
        """
        if isinstance(fmt, basestring):
            if not fmt.lower() in ("png", "raw"):
                raise ValueError('invalid format "%s"' % (fmt,))
            self._screencapFormat = fmt.lower()
        else:
            self._screencapFormat = fmt

    def setScreencapArgs(self, args):
        """
        Set screencap tool arguments.

        Parameters:
          args (list of strings):
                  current screencap arguments will be replaced by args.

        See also: screencapArgs()

        Example: shrink screenshots to 1/4 of the pixels
            # (requires screencap -s parameter support)
            # Use input resolution from display.* variables instead
            # of screenshot resolution.
            sut.setDisplaySize()
            # Divide screenshot width and height by 2, that is, set
            # divider exponent (two to the power of n) to 1.
            args = sut.connection().screencapArgs()
            sut.connection().setScreencapArgs(args + ["-s1"])
        """
        self._screencapArgs = args

    def screencapArgs(self):
        """
        Return screencap tool arguments.
        """
        return self._screencapArgs[:] # return a copy

    def recvScreenshot(self, filename, retry=2, retryDelay=1.0):
        """
        Capture a screenshot and copy the image file to given path or
        system temp folder.

        Returns True on success, otherwise False.
        """
        _screenshotTimeout = 60
        if self._screencapFormat != "png" and fmbtpng != None:
            # EXPERIMENTAL: PNG encoding moved from device to host
            remotefile = '/sdcard/fmbtandroid-s.raw'
            cmd = ['shell', 'screencap %s | gzip -3 > %s' % (
                ' '.join(self._screencapArgs), remotefile)]
            status, out, err = self._runAdb(cmd, [0, 124], timeout=_screenshotTimeout)
            if status != 0:
                errmsg = "screenshot timeout: command='adb %s' status=%s, stdout=%s, stderr=%s" % (
                    " ".join(cmd), status, out, err)
            else:
                cmd = ['pull', remotefile, filename + ".raw"]
                status, out, err = self._runAdb(cmd, [0, 1, 124], timeout=_screenshotTimeout)
                if status == 124:
                    errmsg = "screenshot timeout: command='adb %s' status=%s, stdout=%s, stderr=%s" % (
                        " ".join(cmd), status, out, err)
                else:
                    errmsg = "screenshot 'adb %s' failed, exit status %s" % (" ".join(cmd), status)
            if status != 0:
                _adapterLog(errmsg)
                raise FMBTAndroidError(errmsg)
            try:
                data = gzip.open(filename + ".raw").read()
            except Exception, e:
                msg = 'reading screenshot from "%s" failed: %s' % (
                    filename + ".raw", e)
                _adapterLog(msg)
                raise FMBTAndroidError(msg)
            os.unlink(filename + ".raw")

            width, height, fmt = struct.unpack("<LLL", data[:12])
            if isinstance(self._screencapFormat, tuple):
                depth, colorspace = self._screencapFormat
            elif fmt == 1:
                depth, colorspace = 8, "RGBA"
            elif fmt == 2:
                depth, colorspace = 8, "RGB_"
            elif fmt == 3:
                depth, colorspace = 8, "RGB"
            elif fmt == 5:
                depth, colorspace = 8, "BGR_" # ignore alpha
            else:
                _adapterLog("unsupported screencap raw format %s" % (fmt,))
                depth, colorspace = None, None

            if depth != None:
                file(filename, "w").write(fmbtpng.raw2png(
                    data[12:], width, height, depth, colorspace))
                return True
            else:
                # fallback to slower screenshot method
                pass

        remotefile = '/sdcard/' + os.path.basename(filename)
        remotefile = remotefile.replace(':', '_') # vfat dislikes colons

        cmd = ['shell', 'screencap %s -p %s' % (' '.join(self._screencapArgs), remotefile)]
        status, out, err = self._runAdb(cmd, [0, 124], timeout=_screenshotTimeout)
        if status != 0:
            errmsg = "screenshot timeout: command='adb %s' status=%s, stdout=%s, stderr=%s" % (
                " ".join(cmd), status, out, err)
        else:
            status, out, err = self._runAdb(['pull', remotefile, filename], [0, 1, 124])
            if status == 124:
                errmsg = "screenshot timeout: command='adb %s' status=%s, stdout=%s, stderr=%s" % (
                    " ".join(cmd), status, out, err)
            else:
                errmsg = "screenshot 'adb %s' failed, exit status: %s" % (" ".join(cmd), status)
        if status != 0:
            _adapterLog(errmsg)
            raise FMBTAndroidError(errmsg)

        status, _, _ = self._runAdb(['shell', 'rm', remotefile], 0)

        if os.path.getsize(filename) == 0:
            _adapterLog("received screenshot of size 0")
            if retry > 0:
                time.sleep(retryDelay)
                return self.recvScreenshot(filename, retry-1, retryDelay)
            else:
                raise FMBTAndroidError("Screenshot file size 0")

        return True

    def setScreenToDisplayCoords(self, screenToDisplayFunction):
        self._screenToDisplay = screenToDisplayFunction

    def setDisplayToScreenCoords(self, displayToScreenFunction):
        self._displayToScreen = displayToScreenFunction

    def shellSOE(self, shellCommand):
        fd, filename = tempfile.mkstemp(prefix="fmbtandroid-shellcmd-")
        remotename = '/sdcard/' + os.path.basename(filename)
        os.write(fd, shellCommand + "\n")
        os.close(fd)
        self._runAdb(["push", filename, remotename], 0)
        os.remove(filename)
        cmd = "source %s >%s.out 2>%s.err; echo $? > %s.status" % ((remotename,)*4)
        if self._shellSupportsTar:
            # do everything we can in one command to minimise adb
            # commands: execute command, record results, package,
            # print uuencoded package and remove remote temp files
            cmd += "; cd %s; tar czf - %s.out %s.err %s.status | uuencode %s.tar.gz; rm -f %s*" % (
                (os.path.dirname(remotename),) + ((os.path.basename(remotename),) * 5))
            status, output, error = self._runAdb(["shell", cmd], 0)
            file(filename, "w").write(output)
            uu.decode(filename, out_file=filename + ".tar.gz")
            import tarfile
            tar = tarfile.open(filename + ".tar.gz")
            basename = os.path.basename(filename)
            stdout = tar.extractfile(basename + ".out").read()
            stderr = tar.extractfile(basename + ".err").read()
            try: exitstatus = int(tar.extractfile(basename + ".status").read())
            except: exitstatus = None
            os.remove(filename)
            os.remove(filename + ".tar.gz")
        else:
            # need to pull files one by one, slow.
            self._runAdb(["shell", cmd], 0)
            stdout = self._cat(remotename + ".out")
            stderr = self._cat(remotename + ".err")
            try: exitstatus = int(self._cat(remotename + ".status"))
            except: exitstatus = None
            self._runAdb(["shell", "rm -f "+remotename+"*"])
        return exitstatus, stdout, stderr

    def recvViewData(self, retry=3):
        _dataBufferLen = 4096 * 16
        try:
            self._windowSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._windowSocket.connect( (self._w_host, self._windowPortForward) )
            self._windowSocket.settimeout(60)

            # DUMP -1: get foreground window info
            if self._windowSocket.sendall("DUMP -1\n") == 0:
                # LOG: readGUI cannot write to window socket
                raise AndroidConnectionError("writing socket failed")

            # Read until a "DONE" line or timeout
            data = ""
            while True:
                newData = ''
                try:
                    newData = self._windowSocket.recv(_dataBufferLen)
                except socket.timeout:
                    data = None
                    break
                data += newData
                if data.splitlines()[-1] == "DONE" or newData == '':
                    break
            return data
        except Exception, msg:
            _adapterLog("recvViewData: window socket error: %s" % (msg,))
            if retry > 0:
                try: self._windowSocket.close()
                except: pass
                self._resetWindow()
                time.sleep(0.5)
                return self.recvViewData(retry=retry-1)
            else:
                msg = "recvViewData: cannot read window socket"
                _adapterLog(msg)
                raise AndroidConnectionError(msg)
        finally:
            try: self._windowSocket.close()
            except: pass

class FMBTAndroidError(Exception): pass
class FMBTAndroidRunError(FMBTAndroidError): pass
class AndroidConnectionError(FMBTAndroidError, fmbtgti.ConnectionError): pass
class AndroidConnectionLost(AndroidConnectionError): pass
class AndroidDeviceNotFound(AndroidConnectionError): pass
