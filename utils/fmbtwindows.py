# fMBT, free Model Based Testing tool
# Copyright (c) 2014, Intel Corporation.
#
# This program is free software; you can redistribute it and/or modify it
# under the terms and conditions of the GNU Lesser General Public License,
# version 2.1, as published by the Free Software Foundation.
#
# This program is distributed in the hope it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License along with
# this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin St - Fifth Floor, Boston, MA 02110-1301 USA.

"""
This is library implements fMBT GUITestInterface for Windows

Windows host must have pythonshare-server running.
"""

import fmbt
import fmbtgti
import inspect
import os
import pythonshare
import subprocess
import zlib

def _adapterLog(msg):
    fmbt.adapterlog("fmbtwindows %s" % (msg,))

def _run(command, expectedExitStatus=None):
    """
    Execute command in child process, return status, stdout, stderr.
    """
    if type(command) == str:
        shell = True
    else:
        shell = False

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
        msg = "Executing %s failed. Exit status: %s, expected %s" % (
            command, exitStatus, expectedExitStatus)
        _adapterLog("%s\n    stdout: %s\n    stderr: %s\n" % (msg, out, err))
        raise FMBTWindowsError(msg)

    return exitStatus, out, err

class Device(fmbtgti.GUITestInterface):
    def __init__(self, connspec, password=None, screenshotSize=(None, None), **kwargs):
        """Connect to windows device under test.

        Parameters:

          connspec (string):
                  specification for connecting to a pythonshare
                  server that will run fmbtwindows-agent. The format is
                  "socket://<host>[:<port>]".

          password (optional, string or None):
                  authenticate to pythonshare server with given
                  password. The default is None (no authentication).

          rotateScreenshot (integer, optional)
                  rotate new screenshots by rotateScreenshot degrees.
                  Example: rotateScreenshot=-90. The default is 0 (no
                  rotation).

        To prepare a windows device for connection, launch there

        python pythonshare-server --password mysecretpwd

        When not on trusted network, consider ssh port forward, for
        instance.
        """
        fmbtgti.GUITestInterface.__init__(self, **kwargs)
        self.setConnection(WindowsConnection(connspec, password))

    def getFile(self, remoteFilename, localFilename=None):
        """
        Fetch file from the device.

        Parameters:

          remoteFilename (string):
                  file to be fetched on device

          localFilename (optional, string or None):
                  file to be saved to local filesystem. If None,
                  return contents of the file without saving them.
        """
        return self._conn.recvFile(remoteFilename, localFilename)

    def setDisplaySize(self, (width, height)):
        """
        Transform coordinates of synthesized events from screenshot
        resolution to given resolution. By default events are
        synthesized directly to screenshot coordinates.

        Parameters:

          (width, height) (pair of integers):
                  width and height of display in pixels. If not
                  given, values from Android system properties
                  "display.width" and "display.height" will be used.

        Returns None.
        """
        screenWidth, screenHeight = self.screenSize()
        self._conn.setScreenToDisplayCoords(
            lambda x, y: (x * width / screenWidth,
                          y * height / screenHeight))
        self._conn.setDisplayToScreenCoords(
            lambda x, y: (x * screenWidth / width,
                          y * screenHeight / height))

    def setScreenshotSize(self, (width, height)):
        """
        Force screenshots from device to use given resolution.
        Overrides detected monitor resolution on device.
        """
        self._conn.setScreenshotSize((width, height))

    def shell(self, command):
        return self._conn.evalPython('shell("%s")' % (command,))

    def launchHTTPD(self):
        return self._conn.evalPython("launchHTTPD()")

    def stopHTTPD(self):
        return self._conn.evalPython("stopHTTPD()")

class WindowsConnection(fmbtgti.GUITestConnection):
    def __init__(self, connspec, password):
        fmbtgti.GUITestConnection.__init__(self)
        self._screenshotSize = (None, None) # autodetect
        self._agent_ns = "fmbtwindows-agent"
        self._agent = pythonshare.connection(connspec, password=password)
        agentFilename = os.path.join(
            os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))),
            "fmbtwindows_agent.py")
        self._agent.exec_in(self._agent_ns, file(agentFilename).read())
        self.setScreenToDisplayCoords(lambda x, y: (x, y))
        self.setDisplayToScreenCoords(lambda x, y: (x, y))

    def setScreenshotSize(self, screenshotSize):
        self._screenshotSize = screenshotSize

    def evalPython(self, code):
        return self._agent.eval_in(self._agent_ns, code)

    def recvFile(self, remoteFilename, localFilename=None):
        data = self._agent.eval_in(self._agent_ns, "file(%s).read()" % (repr(remoteFilename),))
        if localFilename:
            file(localFilename, "wb").write(data)
            return True
        else:
            return data

    def recvScreenshot(self, filename, screenshotSize=(None, None)):
        ppmfilename = filename + ".ppm"

        if screenshotSize == (None, None):
            screenshotSize = self._screenshotSize

        if screenshotSize == (None, None):
            zdata = self._agent.eval_in(self._agent_ns, "screenshotZYBGR()")
            width, height = self._agent.eval_in(self._agent_ns, "zybgrSize()")
        else:
            zdata = self._agent.eval_in(
                self._agent_ns, "screenshotZYBGR(%s)" % (screenshotSize,))
            width, height = screenshotSize

        data = zlib.decompress(zdata)

        fmbtgti.eye4graphics.wbgr2rgb(data, width, height)
        ppm_header = "P6\n%d %d\n%d\n" % (width, height, 255)

        f = file(filename + ".ppm", "wb")
        f.write(ppm_header)
        f.write(data)
        f.close()
        _run(["convert", ppmfilename, filename], expectedExitStatus=[0])
        os.remove(ppmfilename)
        return True

    def sendType(self, text):
        command = 'sendType(%s)' % (repr(text),)
        self._agent.eval_in(self._agent_ns, command)
        return True

    def sendPress(self, keyCode, modifiers=None):
        if modifiers == None:
            command = 'sendKey("%s",[])' % (keyCode,)
        else:
            command = 'sendKey("%s",%s)' % (keyCode, repr(modifiers))
        self._agent.eval_in(self._agent_ns, command)
        return True

    def sendKeyDown(self, keyCode, modifiers=None):
        if modifiers == None:
            command = 'sendKeyDown("%s",[])' % (keyCode,)
        else:
            command = 'sendKeyDown("%s",%s)' % (keyCode, repr(modifiers))
        self._agent.eval_in(self._agent_ns, command)
        return True

    def sendKeyUp(self, keyCode, modifiers=None):
        if modifiers == None:
            command = 'sendKeyUp("%s",[])' % (keyCode,)
        else:
            command = 'sendKeyUp("%s",%s)' % (keyCode, repr(modifiers))
        self._agent.eval_in(self._agent_ns, command)
        return True

    def sendTap(self, x, y, button=None):
        x, y = self._screenToDisplay(x, y)
        if button == None:
            command = "sendTap(%s, %s)" % (x, y)
        else:
            command = "sendClick(%s, %s, %s)" % (x, y, button)
        self._agent.eval_in(self._agent_ns, command)
        return True

    def sendTouchDown(self, x, y, button=None):
        x, y = self._screenToDisplay(x, y)
        if button == None:
            command = "sendTouchDown(%s, %s)" % (x, y)
        else:
            command = "sendMouseDown(%s, %s, %s)" % (x, y, button)
        self._agent.eval_in(self._agent_ns, command)
        return True

    def sendTouchMove(self, x, y, button=None):
        x, y = self._screenToDisplay(x, y)
        if button == None:
            command = "sendTouchMove(%s, %s)" % (x, y)
        else:
            command = "sendMouseMove(%s, %s, %s)" % (x, y, button)
        self._agent.eval_in(self._agent_ns, command)
        return True

    def sendTouchUp(self, x, y, button=None):
        x, y = self._screenToDisplay(x, y)
        if button == None:
            command = "sendTouchUp(%s, %s)" % (x, y)
        else:
            command = "sendMouseUp(%s, %s, %s)" % (x, y, button)
        self._agent.eval_in(self._agent_ns, command)
        return True

    def setScreenToDisplayCoords(self, screenToDisplayFunction):
        self._screenToDisplay = screenToDisplayFunction

    def setDisplayToScreenCoords(self, displayToScreenFunction):
        self._displayToScreen = displayToScreenFunction


class FMBTWindowsError(Exception): pass
