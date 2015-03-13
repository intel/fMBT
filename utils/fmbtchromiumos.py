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

"""
This library implements fmbt GUITestInterface for Chromium OS
"""

import distutils.spawn
import fmbt_config
import fmbtgti
import inspect
import os
import pythonshare
import shlex
import StringIO
import subprocess
import tarfile
import zlib

def _run(command, sendStdin=None):
    try:
        p = subprocess.Popen(command,
                             stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             close_fds=(os.name != "nt"))
    except OSError, e:
        raise FMBTChromiumOsError('Cannot execute (%s): %s' %
                                  (e, command))
    if sendStdin:
        p.stdin.write(sendStdin)
    out, err = p.communicate()
    return p.returncode, out, err

class Device(fmbtgti.GUITestInterface):
    def __init__(self, loginCommand, **kwargs):
        """Parameters:

          loginCommand (string)
                  Command to connect to Chromium OS device. Example:
                  "ssh -P9222 chronos@localhost".

          rotateScreenshot (integer, optional)
                  rotate new screenshots by rotateScreenshot degrees.
                  Example: rotateScreenshot=-90. The default is 0 (no
                  rotation).
        """
        fmbtgti.GUITestInterface.__init__(self, **kwargs)
        self.setConnection(ChromiumOSConnection(loginCommand))

    def shellSOE(self, shellCommand, username="", password="", asyncStatus=None, asyncOut=None, asyncError=None, usePty=False):
        """
        Get status, output and error of executing shellCommand on Chromium OS device

        Parameters:

          shellCommand (string)
                  command to be executed on device.

          username (string, optional)
                  username who should execute the command. The default
                  is "root".

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

          usePty (optional, boolean)
                  execute shellCommand in pseudoterminal. The default
                  is False.

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
        return self._conn.shellSOE(shellCommand, username, asyncStatus, asyncOut, asyncError, usePty)

class ChromiumOSConnection(fmbtgti.GUITestConnection):
    def __init__(self, loginCommand):
        fmbtgti.GUITestConnection.__init__(self)
        self._loginCommand = loginCommand
        self._loginTuple = tuple(shlex.split(self._loginCommand))
        self.open()

    def sendFilesInTar(self, localDir, files, destDir):
        package = StringIO.StringIO()
        t = tarfile.TarFile(mode="w", fileobj=package)
        for filename in files:
            t.add(os.path.join(localDir, filename), arcname=filename)
        t.close()
        package.seek(0)
        _run(self._loginTuple +
             ("mkdir -p %s; tar x -C %s" % (destDir, destDir),),
             package.read())

    def agentExec(self, pythonCode):
        self._agent.exec_in(self._agent_ns, pythonCode)

    def agentEval(self, pythonExpression):
        return self._agent.eval_in(self._agent_ns, pythonExpression)

    def open(self):
        myDir = os.path.dirname(os.path.abspath(
            inspect.getfile(inspect.currentframe())))

        self.sendFilesInTar(myDir,
                            ("fmbtx11_conn.py",
                             "fmbtpng.py",
                             "fmbtuinput.py"),
                            "/tmp/fmbtchromiumos")

        if os.access(os.path.join(myDir, "pythonshare", "__init__.py"), os.R_OK):
            pythonshareDir = myDir
        elif os.access(os.path.join(myDir, "..", "pythonshare", "pythonshare",
                                    "__init__.py"), os.R_OK):
            pythonshareDir = os.path.join(myDir, "..", "pythonshare")

        self.sendFilesInTar(pythonshareDir,
                            ("pythonshare/__init__.py",
                             "pythonshare/server.py",
                             "pythonshare/client.py",
                             "pythonshare/messages.py"),
                            "/tmp/fmbtchromiumos")

        if os.name != "nt":
            pythonshareServer = distutils.spawn.find_executable("pythonshare-server")
        else:
            pythonshareServer = os.path.join(
                os.path.dirname(__file__), "..", "Scripts", "pythonshare-server")

        if not pythonshareServer or not os.access(pythonshareServer, os.R_OK):
            raise FMBTChromiumOsError("cannot find pythonshare-server executable")

        self.sendFilesInTar(os.path.dirname(pythonshareServer),
                            ("pythonshare-server",),
                            "/tmp/fmbtchromiumos")

        agentCmd = (self._loginCommand +
                    " sudo DISPLAY=:0 XAUTHORITY=/home/chronos/.Xauthority" +
                    " LD_LIBRARY_PATH=/usr/local/lib:/usr/local/lib64:/usr/lib:/usr/lib64" +
                    " python /tmp/fmbtchromiumos/pythonshare-server -p stdin")

        self._agent = pythonshare.connection("shell://" + agentCmd)
        self._agent_ns = "fmbtchromiumos-agent"
        try:
            self.agentExec("import fmbtx11_conn")
        except pythonshare.PythonShareError, e:
            raise FMBTChromiumOsError(
                "Cannot connect to pythonshare-server on device (%s): %s" %
                (e, agentCmd))
        self.agentExec("x = fmbtx11_conn.Display()")

    def recvScreenshot(self, filename):
        img = self.agentEval("x.recvScreenshot()")

        if img.startswith("FMBTRAWX11"):
            try:
                header, zdata = img.split('\n', 1)
                width, height, depth, bpp = [int(n) for n in header.split()[1:]]
                data = zlib.decompress(zdata)
            except Exception, e:
                raise FMBTChromiumOsError("Corrupted screenshot data: %s" % (e,))

            if len(data) != width * height * 4:
                raise FMBTChromiumOsError("Image data size mismatch.")

            fmbtgti.eye4graphics.bgrx2rgb(data, width, height)
            # TODO: use libimagemagick directly to save data to png?
            ppm_header = "P6\n%d %d\n%d\n" % (width, height, 255)
            f = file(filename + ".ppm", "wb").write(ppm_header + data[:width*height*3])
            _run([fmbt_config.imagemagick_convert, filename + ".ppm", filename])
            os.remove("%s.ppm" % (filename,))
        else:
            file(filename, "wb").write(img)
        return True

    def sendType(self, text):
        return self.agentEval('x.sendType(%s)' % (repr(text),))

    def sendPress(self, keyCode, modifiers=None):
        if modifiers != None:
            raise NotImplementedError
        return self.agentEval("x.sendPress(%s)" % (repr(keyCode),))

    def sendKeyDown(self, keyCode, modifiers=None):
        if modifiers != None:
            raise NotImplementedError
        return self.agentEval("x.sendKeyDown(%s)" % (repr(keyCode),))

    def sendKeyUp(self, keyCode, modifiers=None):
        if modifiers != None:
            raise NotImplementedError
        return self.agentEval("x.sendKeyUp(%s)" % (repr(keyCode),))

    def sendTap(self, x, y, button=None):
        if button == None:
            # TODO: synthesize touch display event, if available
            command = "x.sendTap(%s, %s)" % (x, y)
        else:
            command = "x.sendTap(%s, %s, %s)" % (x, y, button)
        return self.agentEval(command)

    def sendTouchDown(self, x, y, button=None):
        if button == None:
            # TODO: synthesize touch display event, if available
            command = "x.sendTouchDown(%s, %s)" % (x, y)
        else:
            command = "x.sendTouchDown(%s, %s, %s)" % (x, y, button)
        return self.agentEval(command)

    def sendTouchMove(self, x, y, button=None):
        if button == None:
            # TODO: synthesize touch display event, if available
            command = "x.sendTouchMove(%s, %s)" % (x, y)
        else:
            command = "x.sendTouchMove(%s, %s)" % (x, y)
        return self.agentEval(command)

    def sendTouchUp(self, x, y, button=None):
        if button == None:
            # TODO: synthesize touch display event, if available
            command = "x.sendTouchUp(%s, %s)" % (x, y)
        else:
            command = "x.sendMouseUp(%s, %s, %s)" % (x, y, button)
        return self.agentEval(command)

    def shellSOE(self, shellCommand, username, asyncStatus, asyncOut, asyncError, usePty):
        _, (s, o, e) = self.agentEval(
            "fmbtx11_conn.shellSOE(%s, %s, %s, %s, %s, %s)" % (
                repr(shellCommand), repr(username), repr(asyncStatus),
                repr(asyncOut), repr(asyncError), repr(usePty)))

        return s, o, e

class FMBTChromiumOsError(Exception): pass
