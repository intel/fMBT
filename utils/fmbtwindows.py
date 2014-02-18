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

Windows host must have pythonshare-server with fmbtwindows-agent.py
running.
"""

import fmbt
import fmbtgti
import pythonshare

import os
import subprocess
import zlib

def _adapterLog(msg):
    fmbt.adapterlog("fmbtwindows %s" % (msg,))

def _run(command, expectedExitStatus=None):
    """
    Execute command in child process, return status, stdout, stderr.
    """
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
        msg = "Executing %s failed. Exit status: %s, expected %s" % (
            command, exitStatus, expectedExitStatus)
        _adapterLog("%s\n    stdout: %s\n    stderr: %s\n" % (msg, out, err))
        raise FMBTWindowsError(msg)

    return exitStatus, out, err

class Device(fmbtgti.GUITestInterface):
    def __init__(self, connspec, **kwargs):
        """Parameters:

          connspec (string)
                  specification for connecting to
                  fmbtwindows-agent. The format is
                  "socket://<host>[:<port>]".

          rotateScreenshot (integer, optional)
                  rotate new screenshots by rotateScreenshot degrees.
                  Example: rotateScreenshot=-90. The default is 0 (no
                  rotation).

        """
        fmbtgti.GUITestInterface.__init__(self, **kwargs)
        self.setConnection(WindowsConnection(connspec))

class WindowsConnection(fmbtgti.GUITestConnection):
    def __init__(self, connspec):
        fmbtgti.GUITestConnection.__init__(self)
        # Assume that there is pythonshare-server running on the windows host,
        # it has "fmbtwindows-agent" namespace in place, and
        # fmbtwindows_agent.py has been imported into that namespace.
        # Launch such a process, for instance by
        #
        # pythonshare-server -n "fmbtwindows-agent" -i "import fmbtwindows_agent"
        self._agent_ns = "fmbtwindows-agent"
        self._agent = pythonshare.connection(connspec)
        version = self._agent.eval_in(self._agent_ns, "fmbtwindows_agent.version()")
        if not (type(version) == str and version):
            raise FMBTWindowsError("reading fmbtwindows agent version failed")

    def recvScreenshot(self, filename):
        ppmfilename = filename + ".ppm"
        img = self._agent.eval_in(self._agent_ns, "fmbtwindows_agent.screenshot(0)")
        file(ppmfilename, "w").write(zlib.decompress(img))
        _run(["convert", ppmfilename, filename], expectedExitStatus=[0])
        os.remove(ppmfilename)
        return True

class FMBTWindowsError(Exception): pass
