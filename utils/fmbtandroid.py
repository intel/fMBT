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
import os
import platform
import random
import re
import shutil
import socket
import StringIO
import subprocess
import tempfile
import time
import uu

import fmbt
import fmbtgti

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

if platform.system() == "Windows":
    _g_closeFds = False
    _g_adbExecutable = "adb.exe"
else:
    _g_closeFds = True
    _g_adbExecutable = "adb"

def _run(command, expectedExitStatus = None, timeout=None):
    if type(command) == str:
        if timeout != None:
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
    def __init__(self, deviceName=None, iniFile=None, connect=True, **kwargs):
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

          rotateScreenshot (integer, optional)
                  rotate new screenshots by rotateScreenshot degrees.
                  Example: rotateScreenshot=-90. The default is 0 (no
                  rotation).

        To create an ini file for a device, use dumpIni. Example:

        file("/tmp/test.ini", "w").write(fmbtandroid.Device().dumpIni())
        """
        fmbtgti.GUITestInterface.__init__(self, **kwargs)

        self._fmbtAndroidHomeDir = os.getenv("FMBTANDROIDHOME", os.getcwd())

        self._platformVersion = None
        self._lastView = None

        self._conf = Ini()

        self._loadDeviceAndTestINIs(self._fmbtAndroidHomeDir, deviceName, iniFile)
        if deviceName == None:
            deviceName = self._conf.value("general", "serial", "")

        if connect == False and deviceName == "":
            deviceName = "nodevice"
            self.setConnection(None)
        elif deviceName == "":
            # Connect to an unspecified device.
            # Go through devices in "adb devices".
            listDevicesCommand = [_g_adbExecutable, "devices"]
            status, output, err = _run(listDevicesCommand, expectedExitStatus = [0, 127])
            if status == 127:
                raise FMBTAndroidError('adb not found in PATH. Check your Android SDK installation.')
            outputLines = [l.strip() for l in output.splitlines()]
            try: deviceLines = outputLines[outputLines.index("List of devices attached")+1:]
            except: deviceLines = []

            deviceLines = [l for l in deviceLines if l.strip() != ""]

            if deviceLines == []:
                raise AndroidDeviceNotFound('No devices found with "%s"' % (listDevicesCommand,))

            potentialDevices = [line.split()[0] for line in deviceLines]

            for deviceName in potentialDevices:
                try:
                    self.serialNumber = deviceName
                    self._conf.set("general", "serial", self.serialNumber)
                    self.setConnection(_AndroidDeviceConnection(self.serialNumber))
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
                self.setConnection(_AndroidDeviceConnection(self.serialNumber))


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
        self.setBitmapPath(self._conf.value("paths", "bitmapPath", ".:" + self._fmbtAndroidHomeDir + os.sep + "bitmaps" + os.sep + self.hardware + "-" + self.platformVersion()), self._fmbtAndroidHomeDir)
        self.setScreenshotDir(self._conf.value("paths", "screenshotDir", self._fmbtAndroidHomeDir + os.sep + "screenshots"))

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
        return fmbtgti.GUITestInterface.pressKey(self, keyName, long, hold)

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
        return self._conn.reboot(reconnect, firstBoot, timeout)

    def reconnect(self):
        """
        Close connections to the device and reconnect.
        """
        self.setConnection(None)
        import gc
        gc.collect()
        try:
            self.setConnection(_AndroidDeviceConnection(self.serialNumber))
            return True
        except Exception, e:
            _adapterLog("reconnect failed: %s" % (e,))
            return False

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
        def formatErrors(errors):
            return "refreshView parse errors:\n    %s" % (
                "\n    ".join(["line %s: %s error: %s" % e for e in errors]),)

        if self._conn:
            displayToScreen = self._conn._displayToScreen
        else:
            displayToScreen = None
        if forcedView != None:
            if isinstance(forcedView, View):
                self._lastView = forcedView
            elif type(forcedView) == str:
                self._lastView = View(self.screenshotDir(), self.serialNumber, file(forcedView).read(), displayToScreen)
                _adapterLog(formatErrors(self._lastView.errors()))
            else:
                raise ValueError("forcedView must be a View object or a filename")
            return self._lastView

        retryCount = 0
        while True:
            dump = self._conn.recvViewData()
            if dump != None:
                view = View(self.screenshotDir(), self.serialNumber, dump, displayToScreen)
            else:
                _adapterLog("refreshView window dump reading failed")
                view = None
                # fail quickly if there is no answer
                retryCount += self._PARSE_VIEW_RETRY_LIMIT / 2
            if dump == None or len(view.errors()) > 0:
                if view:
                    _adapterLog(formatErrors(view.errors()))
                if retryCount < self._PARSE_VIEW_RETRY_LIMIT:
                    retryCount += 1
                    time.sleep(0.2) # sleep before retry
                else:
                    raise AndroidConnectionError("Cannot read window dump")
            else:
                # successfully parsed or parsed with errors but no more retries
                self._lastView = view
                return view

    def useDisplaySize(self, (width, height) = (None, None)):
        """
        Transform coordinates of synthesized events from screenshot
        resolution to given resolution. By default events are
        synthesized directly to screenshot coordinates.

        Parameters:

          (width, height) (pair of integers, optional):
                  width and height of display in pixels. If not
                  given, values from Android system properties
                  "display.width" and "display.height" will be used.

        Returns None.
        """
        if width == None:
            width = int(self.systemProperty("display.width"))
        if height == None:
            height = int(self.systemProperty("display.height"))
        screenWidth, screenHeight = self.screenSize()
        self._conn.setScreenToDisplayCoords(
            lambda x, y: (x * width / screenWidth,
                          y * height / screenHeight))
        self._conn.setDisplayToScreenCoords(
            lambda x, y: (x * screenWidth / width,
                          y * screenHeight / height))

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
        try:
            self._conn.recvViewData()
            return True
        except AndroidConnectionError:
            return False

    def systemProperty(self, propertyName):
        """
        Returns Android Monkey Device properties, such as
        "clock.uptime", refer to Android Monkey documentation.
        """
        return self._conn.recvVariable(propertyName)

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
        # the top window may be None during transitions, therefore
        # retry a couple of times if necessary.
        timeout = 0.5
        pollDelay = 0.2
        start = time.time()
        tw = self._conn.recvTopAppWindow()[1]
        while tw == None and (time.time() - start < timeout):
            time.sleep(pollDelay)
            tw = self._conn.recvTopAppWindow()[1]
        return tw

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

          waitTime, pollDelay (float, optional):
                refer to wait.

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
        return self._conn.sendWake()

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
        self._rawProps = ""
        if not "scrolling:mScrollX" in self._p:
            self._p["scrolling:mScrollX"] = 0
            self._p["scrolling:mScrollY"] = 0
        fmbtgti.GUIItem.__init__(self, className, self._calculateBbox(displayToScreen), dumpFilename)
    def addChild(self, child): self._children.append(child)
    def _calculateBbox(self, displayToScreen):
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
    def __init__(self, screenshotDir, serialNumber, dump, displayToScreen=None):
        self.screenshotDir = screenshotDir
        self.serialNumber = serialNumber
        self._viewItems = []
        self._errors = []
        self._lineRegEx = re.compile("(?P<indent>\s*)(?P<class>[\w.$]+)@(?P<id>[0-9A-Fa-f]{8} )(?P<properties>.*)")
        self._olderAndroidLineRegEx = re.compile("(?P<indent>\s*)(?P<class>[\w.$]+)@(?P<id>\w)(?P<properties>.*)")
        self._propRegEx = re.compile("(?P<prop>(?P<name>[^=]+)=(?P<len>\d+),)(?P<data>[^\s]* ?)")
        self._dump = dump
        self._rawDumpFilename = self.screenshotDir + os.sep + fmbtgti._filenameTimestamp() + "-" + self.serialNumber + ".view"
        file(self._rawDumpFilename, "w").write(self._dump)
        if displayToScreen == None:
            displayToScreen = lambda x, y: (x, y)
        try: self._parseDump(dump, self._rawDumpFilename, displayToScreen)
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
        return "id=%s cls=%s text=%s bbox=%s" % (
            i.id(), i.className(), t, i.bbox())

    def findItems(self, comparator, count=-1, searchRootItem=None, searchItems=None):
        foundItems = []
        if count == 0: return foundItems
        if searchRootItem != None:
            # find from searchRootItem and its children
            if comparator(searchRootItem):
                foundItems.append(searchRootItem)
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

    def save(self, fileOrDirName):
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

            self._viewItems.append(ViewItem(matcher.group("class"), matcher.group("id"), indent, properties, parent, matcher.group("properties"), self._rawDumpFilename, displayToScreen))

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
        self._shellSupportsTar = False
        self.setScreenToDisplayCoords(lambda x, y: (x, y))
        self.setDisplayToScreenCoords(lambda x, y: (x, y))

        self._detectFeatures()
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

    def target(self):
        return self._serialNumber

    def _cat(self, remoteFilename):
        fd, filename = tempfile.mkstemp("fmbtandroid-cat-")
        os.close(fd)
        self._runAdb(["pull", remoteFilename, filename], 0)
        contents = file(filename).read()
        os.remove(filename)
        return contents

    def _runAdb(self, command, expectedExitStatus=0, timeout=None):
        if not self._stopOnError:
            expect = None
        else:
            expect = expectedExitStatus
        if type(command) == list:
            command = ["adb", "-s", self._serialNumber] + command
        else:
            command = ["adb", "-s", self._serialNumber, command]
        return _run(command, expectedExitStatus=expect, timeout=timeout)

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
                         ["forward", "tcp:"+str(self._w_port), "tcp:4939"]]
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
        while time.time() < endTime:
            if not self._runSetupCmd(["shell"] + monkeyLaunch + ["--port", "1080"], None):
                time.sleep(pollDelay)
                failureCountSinceKill += 1
                continue
            time.sleep(pollDelay)
            if not self._runSetupCmd(["forward", "tcp:"+str(self._m_port), "tcp:1080"]):
                time.sleep(pollDelay)
                failureCountSinceKill += 1
                continue
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
        try:
            height = int(self.recvVariable("display.height"))
            width = int(self.recvVariable("display.width"))
        except TypeError:
            return None, None
        return width, height

    def recvTopAppWindow(self):
        _, output, _ = self._runAdb(["shell", "dumpsys", "window"], 0)
        if self._platformVersion >= "4.2":
            s = re.findall("mCurrentFocus=Window\{(#?[0-9A-Fa-f]{8})( [^ ]*)? (?P<winName>[^}]*)\}", output)
        else:
            s = re.findall("mCurrentFocus=Window\{(#?[0-9A-Fa-f]{8}) (?P<winName>[^ ]*) [^ ]*\}", output)
        if s and len(s[-1][-1].strip()) > 1:
            topWindowName = s[-1][-1]
            if len(s) > 0:
                _adapterLog('recvTopAppWindow warning: several mCurrentFocus windows: "%s"'
                            % ('", "'.join([w[-1] for w in s]),))
        else: topWindowName = None

        s = re.findall("mFocusedApp=AppWindowToken.*ActivityRecord\{#?[0-9A-Fa-f]{8}( [^ ]*)? (?P<appName>[^}]*)\}", output)
        if s and len(s[0][-1].strip()) > 1:
            topAppName = s[0][-1].strip()
        else:
            topAppName = None
        return topAppName, topWindowName

    def sendTap(self, xCoord, yCoord):
        xCoord, yCoord = self._screenToDisplay(xCoord, yCoord)
        return self._monkeyCommand("tap " + str(xCoord) + " " + str(yCoord))[0]

    def sendKeyUp(self, key):
        return self._monkeyCommand("key up " + key)[0]

    def sendKeyDown(self, key):
        return self._monkeyCommand("key down " + key)[0]

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

    def sendPress(self, key):
        return self._monkeyCommand("press " + key)[0]

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

    def recvScreenshot(self, filename, retry=2, retryDelay=1.0):
        """
        Capture a screenshot and copy the image file to given path or
        system temp folder.

        Returns True on success, otherwise False.
        """
        remotefile = '/sdcard/' + os.path.basename(filename)

        self._runAdb(['shell', 'screencap', '-p', remotefile], 0)

        status, out, err = self._runAdb(['pull', remotefile, filename], [0, 1])

        if status != 0:
            raise FMBTAndroidError("Failed to fetch screenshot from the device: %s. SD card required." % ((out + err).strip(),))

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
            self._windowSocket.connect( (self._w_host, self._w_port) )
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
class AndroidConnectionError(FMBTAndroidError): pass
class AndroidConnectionLost(AndroidConnectionError): pass
class AndroidDeviceNotFound(AndroidConnectionError): pass
