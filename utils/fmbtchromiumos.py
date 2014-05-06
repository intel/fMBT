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

import fmbtgti
import inspect
import os
import pythonshare
import shlex
import subprocess
import zlib

def _run(command, sendStdin=None):
    p = subprocess.Popen(command,
                         stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE,
                         close_fds=True)
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

class ChromiumOSConnection(fmbtgti.GUITestConnection):
    def __init__(self, loginCommand):
        fmbtgti.GUITestConnection.__init__(self)
        self._loginCommand = loginCommand
        self._loginTuple = tuple(shlex.split(self._loginCommand))
        self.open()

    def sendFilesInTar(self, localDir, files, destDir):
        _, package, _ = _run(("tar", "-C", localDir, "-c") + files)
        _run(self._loginTuple +
             ("mkdir -p %s; tar x -C %s" % (destDir, destDir),),
             package)

    def agentExec(self, pythonCode):
        self._agent.exec_in(self._agent_ns, pythonCode)

    def agentEval(self, pythonExpression):
        return self._agent.eval_in(self._agent_ns, pythonExpression)

    def open(self):
        myDir = os.path.dirname(os.path.abspath(
            inspect.getfile(inspect.currentframe())))

        self.sendFilesInTar(myDir,
                            ("fmbtx11_conn.py",
                             "fmbtuinput.py"),
                            "/tmp/fmbtchromiumos")

        if os.access(os.path.join(myDir, "pythonshare/__init__.py"), os.R_OK):
            pythonshareDir = myDir
        elif os.access(os.path.join(myDir, "..", "pythonshare", "pythonshare",
                                    "__init__.py"), os.R_OK):
            pythonshareDir = os.path.join(myDir, "..", "pythonshare")

        self.sendFilesInTar(pythonshareDir,
                            ("pythonshare-client",
                             "pythonshare-server",
                             "pythonshare/__init__.py",
                             "pythonshare/server.py",
                             "pythonshare/client.py",
                             "pythonshare/messages.py"),
                            "/tmp/fmbtchromiumos")

        self._agent = pythonshare.connection(
            "shell://" +
            self._loginCommand +
            " sudo DISPLAY=:0 XAUTHORITY=/home/chronos/.Xauthority" +
            " python /tmp/fmbtchromiumos/pythonshare-server -p stdin",)
        self._agent_ns = "fmbtchromiumos-agent"
        self.agentExec("import fmbtx11_conn")
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
            f = file(filename + ".ppm", "w").write(ppm_header + data[:width*height*3])
            _run(["convert", filename + ".ppm", filename])
            os.remove("%s.ppm" % (filename,))
        else:
            file(filename, "w").write(img)
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

class FMBTChromiumOsError(Exception): pass
