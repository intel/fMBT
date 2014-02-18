# fMBT, free Model Based Testing tool
# Copyright (c) 2012 Intel Corporation.
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

# Import this to test step implementations written in Python
# in order to enable logging.

# fmbtlog writes given message to the fmbt log (XML)
#         messages can be viewed using format $al of
#         fmbt-log -f '$al' logfile
#
# adapterlog writes given message to the adapter log (plain text)
#         written by remote_python or remote_pyaal, for instance.

# Log function implementations are provided by the adapter
# component such as remote_python or remote_pyaal.

import datetime
import sys
import urllib

_g_fmbt_adapterlogtimeformat="%s.%f"
_g_actionName = "undefined"
_g_testStep = -1
_g_simulated_actions = []

def _fmbt_call_helper(func,param = ""):
    if simulated():
        return ""
    sys.stdout.write("fmbt_call %s.%s\n" % (func,param))
    sys.stdout.flush()
    response = sys.stdin.readline().rstrip()
    magic,code = response.split(" ")
    if magic == "fmbt_call":
        if code[0] == "1":
            return urllib.unquote(code[1:])
    return ""


def getHeuristic():
    return _fmbt_call_helper("heuristic.get")

def setHeuristic(heuristic):
    return _fmbt_call_helper("heuristic.set",heuristic)

def getCoverage():
    return _fmbt_call_helper("coverage.get")

def setCoverage(coverage):
    return _fmbt_call_helper("coverage.set",coverage)

def getCoverageValue():
    return _fmbt_call_helper("coverage.getValue")

def fmbtlog(msg, flush=True):
    try: file("/tmp/fmbt.fmbtlog", "a").write("%s\n" % (msg,))
    except: pass

def adapterlog(msg, flush=True):
    try:
        _adapterlogWriter(file("/tmp/fmbt.adapterlog", "a"),
                          formatAdapterLogMessage(msg,))
    except: pass

def setAdapterLogWriter(func):
    """
    Override low-level adapter log writer with the given function. The
    function should take two parameters: a file-like object and a log
    message. The message is formatted and ready to be written to the
    file. The default is

    lambda fileObj, formattedMsg: fileObj.write(formattedMsg)
    """
    global _adapterlogWriter
    _adapterlogWriter = func

def adapterLogWriter():
    """
    Return current low-level adapter log writer function.
    """
    global _adapterlogWriter
    return _adapterlogWriter

def reportOutput(msg):
    try: file("/tmp/fmbt.reportOutput", "a").write("%s\n" % (msg,))
    except: pass

def setAdapterLogTimeFormat(strftime_format):
    """
    Use given time format string in timestamping adapterlog messages
    """
    global _g_fmbt_adapterlogtimeformat
    _g_fmbt_adapterlogtimeformat = strftime_format

def formatAdapterLogMessage(msg, fmt="%s %s\n"):
    """
    Return timestamped adapter log message
    """
    return fmt % (
        datetime.datetime.now().strftime(_g_fmbt_adapterlogtimeformat),
        msg)

def getActionName():
    return _g_actionName

def getTestStep():
    return _g_testStep

def simulated():
    """
    Returns True if fMBT is simulating execution of an action (guard
    or body block) instead of really executing it.
    """
    return len(_g_simulated_actions) > 0

def _adapterlogWriter(fileObj, formattedMsg):
    fileObj.write(formattedMsg)
