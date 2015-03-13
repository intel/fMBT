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
import inspect
import os
import sys
import time
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

def formatTime(timeformat="%s", timestamp=None):
    if timestamp == None:
        timestamp = datetime.datetime.now()
    # strftime on Windows does not support conversion to epoch (%s).
    # Calculate it here, if needed.
    if os.name == "nt":
        if "%s" in timeformat:
            epoch_time = time.mktime(timestamp.timetuple())
            timeformat = timeformat.replace("%s", str(int(epoch_time)))
        if "%F" in timeformat:
            timeformat = timeformat.replace("%F", "%Y-%m-%d")
        if "%T" in timeformat:
            timeformat = timeformat.replace("%T", "%H:%M:%S")
    return timestamp.strftime(timeformat)

def heuristic():
    return _fmbt_call_helper("heuristic.get")

def setHeuristic(heuristic):
    return _fmbt_call_helper("heuristic.set",heuristic)

def coverage():
    return _fmbt_call_helper("coverage.get")

def setCoverage(coverage):
    return _fmbt_call_helper("coverage.set",coverage)

def coverageValue():
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
    return fmt % (formatTime(_g_fmbt_adapterlogtimeformat), msg)

def getActionName():
    """deprecated, use actionName()"""
    return _g_actionName

def actionName():
    """
    Return the name of currently executed action (input or output).
    """
    return _g_actionName

def getTestStep():
    """deprecated, use testStep()"""
    return _g_testStep

def testStep():
    """
    Return the number of currently executed test step.
    """
    return _g_testStep

def simulated():
    """
    Returns True if fMBT is simulating execution of an action (guard
    or body block) instead of really executing it.
    """
    return len(_g_simulated_actions) > 0

def _adapterlogWriter(fileObj, formattedMsg):
    fileObj.write(formattedMsg)

def funcSpec(func):
    """
    Return function name and args as they could have been defined
    based on function object.
    """
    argspec = inspect.getargspec(func)
    if argspec.defaults:
        kwarg_count = len(argspec.defaults)
    else:
        kwarg_count = 0
    arg_count = len(argspec.args) - kwarg_count
    arglist = [str(arg) for arg in argspec.args[:arg_count]]
    kwargs = argspec.args[arg_count:]
    for index, kwarg in enumerate(kwargs):
        arglist.append("%s=%s" % (kwarg, repr(argspec.defaults[index])))
    if argspec.varargs:
        arglist.append("*%s" % (argspec.varargs,))
    if argspec.keywords:
        arglist.append("**%s" % (argspec.keywords,))
    try:
        funcspec = "%s(%s)" % (func.func_name, ", ".join(arglist))
    except:
        funcspec = "%s(fmbt.funcSpec error)" % (func.func_name,)
    return funcspec

_g_debug_socket = None
_g_debug_conn = None

def debug(session=0):
    """
    Start debugging with fmbt-debug from the point where this function
    was called. Execution will stop until connection to fmbt-debug
    [session] has been established.

    Parameters:

      session (integer, optional):
              debug session that identifies which fmbt-debug should
              connect to this process. The default is 0.

    Example:

      - execute on command line "fmbt-debug 42"
      - add fmbt.debug(42) in your Python code
      - run the Python code so that it will call fmbt.debug(42)
      - when done the debugging on the fmbt-debug prompt, enter "c"
        for continue.
    """
    import bdb
    import inspect
    import pdb
    import socket

    global _g_debug_conn, _g_debug_socket

    if not _g_debug_socket:
        PORTBASE = 0xf4bd # 62653, fMBD
        host = "127.0.0.1" # accept local host only, by default
        port = PORTBASE + session
        _g_debug_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            _g_debug_socket.bind((host, port))
            _g_debug_socket.listen(1)
            while True:
                (_g_debug_conn, addr) = _g_debug_socket.accept()
                _g_debug_conn.sendall("fmbt.debug\n")
                msg = _g_debug_conn.recv(len("fmbt-debug\n"))
                if msg.startswith("fmbt-debug"):
                    break
                _g_debug_conn.close()
        except socket.error:
            # already in use, perhaps fmbt-debug is already listening to
            # the socket and waiting for this process to connect
            try:
                _g_debug_socket.connect((host, port))
                _g_debug_conn = _g_debug_socket
                whos_there = _g_debug_conn.recv(len("fmbt-debug\n"))
                if not whos_there.startswith("fmbt-debug"):
                    _g_debug_conn.close()
                    _g_debug_socket = None
                    _g_debug_conn = None
                    raise ValueError(
                        'unexpected answer "%s", fmbt-debug expected' %
                        (whos_there.strip(),))
                _g_debug_conn.sendall("fmbt.debug\n")
            except socket.error:
                raise ValueError('debugger cannot listen or connect to %s:%s' % (host, port))

    if not _g_debug_conn:
        fmbtlog("debugger waiting for connection at %s:%s" % (host, port))

    # socket.makefile does not work due to buffering issues
    # therefore, use our own socket-to-file converter
    class SocketToFile(object):
        def __init__(self, socket_conn):
            self._conn = socket_conn
        def read(self, bytes=-1):
            msg = []
            rv = ""
            try:
                c = self._conn.recv(1)
            except KeyboardInterrupt:
                self._conn.close()
                raise
            while c and not rv:
                msg.append(c)
                if c == "\r":
                    rv = "".join(msg)
                elif c == "\n":
                    rv = "".join(msg)
                elif len(msg) == bytes:
                    rv = "".join(msg)
                else:
                    c = self._conn.recv(1)
            return rv
        def readline(self):
            return self.read()
        def write(self, msg):
            self._conn.sendall(msg)
        def flush(self):
            pass

    connfile = SocketToFile(_g_debug_conn)
    debugger = pdb.Pdb(stdin=connfile, stdout=connfile)
    debugger.set_trace(inspect.currentframe().f_back)
